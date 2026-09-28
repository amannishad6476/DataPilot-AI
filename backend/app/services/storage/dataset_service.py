import io
import csv
import json
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc

from app.models.workflow import Workflow, WorkflowRun
from app.models.dataset import DatasetRecord, EvidenceRecord
from app.schemas.planner import FieldSpec
from app.schemas.dataset import DatasetResponse, RecordItem, EvidenceItem


class DatasetService:
    @staticmethod
    def get_dataset(
        db: Session,
        run_id: str,
        search: Optional[str] = None,
        valid_filter: Optional[str] = None,  # "all", "valid", "invalid"
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        page: int = 1,
        page_size: int = 50
    ) -> DatasetResponse:
        run = db.query(WorkflowRun).filter(WorkflowRun.id == run_id).first()
        if not run:
            raise ValueError(f"WorkflowRun {run_id} not found")

        workflow = db.query(Workflow).filter(Workflow.id == run.workflow_id).first()
        if not workflow:
            raise ValueError(f"Workflow {run.workflow_id} not found")

        # Query all records for this run
        query = db.query(DatasetRecord).filter(DatasetRecord.run_id == run_id)

        if valid_filter == "valid":
            query = query.filter(DatasetRecord.is_valid == True)
        elif valid_filter == "invalid":
            query = query.filter(DatasetRecord.is_valid == False)

        records_all = query.all()

        # Apply in-memory search across JSON data fields
        filtered_records = []
        if search:
            s_lower = search.lower().strip()
            for r in records_all:
                matched = False
                for val in r.data.values():
                    if s_lower in str(val).lower():
                        matched = True
                        break
                if matched:
                    filtered_records.append(r)
        else:
            filtered_records = records_all

        # Apply sorting
        if sort_by:
            def sort_key(rec: DatasetRecord):
                if sort_by == "confidence":
                    return rec.confidence_score
                elif sort_by == "is_valid":
                    return 1 if rec.is_valid else 0
                return str(rec.data.get(sort_by, "")).lower()

            filtered_records.sort(key=sort_key, reverse=(sort_order.lower() == "desc"))

        total_count = len(filtered_records)
        total_pages = max(1, (total_count + page_size - 1) // page_size)
        start_idx = (page - 1) * page_size
        paged_records = filtered_records[start_idx : start_idx + page_size]

        # Convert to Pydantic models
        record_items: List[RecordItem] = []
        for r in paged_records:
            evidence_models = [
                EvidenceItem(
                    id=e.id,
                    field_name=e.field_name,
                    source_url=e.source_url,
                    snippet=e.snippet,
                    confidence=e.confidence,
                    collected_at=e.collected_at
                )
                for e in r.evidence_items
            ]
            record_items.append(RecordItem(
                id=r.id,
                data=r.data,
                is_valid=r.is_valid,
                confidence_score=r.confidence_score,
                validation_errors=r.validation_errors or [],
                deduplicated_with=r.deduplicated_with,
                evidence_items=evidence_models,
                created_at=r.created_at
            ))

        field_specs = [FieldSpec(**f) for f in (workflow.fields_spec or [])]

        return DatasetResponse(
            run_id=run.id,
            workflow_id=workflow.id,
            prompt=workflow.prompt,
            goal=workflow.goal,
            execution_mode=run.execution_mode,
            total_records=run.total_records,
            valid_records=run.valid_records,
            duplicate_records=run.duplicate_records,
            fields=field_specs,
            records=record_items,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    @staticmethod
    def export_csv(db: Session, run_id: str) -> str:
        run = db.query(WorkflowRun).filter(WorkflowRun.id == run_id).first()
        if not run:
            raise ValueError(f"WorkflowRun {run_id} not found")
        workflow = db.query(Workflow).filter(Workflow.id == run.workflow_id).first()
        records = db.query(DatasetRecord).filter(DatasetRecord.run_id == run_id).all()

        fields = [f["name"] for f in (workflow.fields_spec or [])]
        extra_headers = ["is_valid", "confidence_score", "validation_issues"]
        all_headers = fields + extra_headers

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(all_headers)

        for r in records:
            row = []
            for f in fields:
                row.append(r.data.get(f, ""))
            row.append(str(r.is_valid))
            row.append(f"{r.confidence_score:.2f}")
            row.append("; ".join(r.validation_errors or []))
            writer.writerow(row)

        return output.getvalue()

    @staticmethod
    def export_json(db: Session, run_id: str) -> List[Dict[str, Any]]:
        records = db.query(DatasetRecord).filter(DatasetRecord.run_id == run_id).all()
        result = []
        for r in records:
            item = dict(r.data)
            item["_quality"] = {
                "is_valid": r.is_valid,
                "confidence_score": r.confidence_score,
                "validation_errors": r.validation_errors or [],
                "evidence_count": len(r.evidence_items)
            }
            result.append(item)
        return result


dataset_service = DatasetService()
