import pytest
import json
from app.database import get_db
from app.models.workflow import Workflow, WorkflowRun
from app.models.dataset import DatasetRecord
from app.services.storage.dataset_service import DatasetService


def test_streaming_csv_and_json():
    db = next(get_db())

    # Create dummy workflow
    wf = Workflow(
        prompt="Test streaming export prompt",
        goal="Collect streaming data",
        domain="technology",
        fields_spec=[
            {"name": "company_name", "type": "string"},
            {"name": "revenue", "type": "number"},
        ],
        steps_spec=[],
        validation_rules=[],
        deduplication_strategy="fuzzy",
    )
    db.add(wf)
    db.commit()
    db.refresh(wf)

    run = WorkflowRun(
        workflow_id=wf.id,
        status="completed",
        execution_mode="demo",
        total_records=3,
        valid_records=3,
        duplicate_records=0,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    for i in range(3):
        rec = DatasetRecord(
            run_id=run.id,
            workflow_id=wf.id,
            data={"company_name": f"Company {i}", "revenue": 1000 * (i + 1)},
            is_valid=True,
            confidence_score=0.95,
            duplicate_group_id=f"grp_{i}",
            match_method="none",
        )
        db.add(rec)
    db.commit()

    # Test CSV stream
    csv_chunks = list(DatasetService.stream_csv(db, run.id, chunk_size=2))
    assert len(csv_chunks) >= 2  # header chunk + data chunk(s)
    full_csv = "".join(csv_chunks)
    assert "company_name" in full_csv
    assert "revenue" in full_csv
    assert "Company 0" in full_csv
    assert "Company 2" in full_csv

    # Test JSON stream
    json_chunks = list(DatasetService.stream_json(db, run.id, chunk_size=2))
    full_json_str = "".join(json_chunks)
    parsed = json.loads(full_json_str)
    assert len(parsed) == 3
    assert parsed[0]["company_name"] == "Company 0"
    assert parsed[0]["_quality"]["confidence_score"] == 0.95

    # Cleanup
    db.query(DatasetRecord).filter(DatasetRecord.run_id == run.id).delete()
    db.query(WorkflowRun).filter(WorkflowRun.id == run.id).delete()
    db.query(Workflow).filter(Workflow.id == wf.id).delete()
    db.commit()
