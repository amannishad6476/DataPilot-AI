import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.planner.heuristic_planner import DynamicSemanticPlanner
from app.services.processing.validator import DataValidator
from app.services.processing.normalizer import DataNormalizer
from app.schemas.planner import ValidationRuleSpec
from app.services.connectors.registry import connector_registry

client = TestClient(app)


@pytest.mark.asyncio
async def test_planner_reasoning():
    planner = DynamicSemanticPlanner()
    prompt = "Find 25 high-growth AI companies in Bangalore with founders, contact emails, and websites"
    plan = await planner.generate_plan(prompt, target_count=25)

    assert plan.reasoning is not None
    assert len(plan.reasoning) >= 4
    # Check that reasoning explains sources, schema, validation, and deduplication
    reasoning_text = " ".join(plan.reasoning).lower()
    assert "source" in reasoning_text
    assert "schema" in reasoning_text or "fields" in reasoning_text or "ingestion" in reasoning_text
    assert "validation" in reasoning_text or "integrity" in reasoning_text
    assert "deduplication" in reasoning_text or "similarity" in reasoning_text


def test_validator_detailed_and_normalizer_audit():
    validator = DataValidator()
    normalizer = DataNormalizer()

    # Test normalization audit
    raw_record = {
        "company_name": "  Acme Corp   ",
        "website": "acme.com?utm_source=twitter&ref=123",
        "email": "MAILTO:Contact@Acme.Com ",
        "phone": "+91 (522) 666-4000"
    }
    normalized, transforms = normalizer.normalize_record_with_audit(raw_record)
    assert normalized["website"].startswith("https://")
    assert "utm_source" not in normalized["website"]
    assert normalized["email"] == "contact@acme.com"
    assert "stripped_tracking_parameters" in transforms["website"]
    assert "lowercased" in transforms["email"] or "stripped_mailto_prefix" in transforms["email"]

    # Test detailed validator
    rules = [
        ValidationRuleSpec(field="company_name", rule_type="non_empty", description="Name required", severity="error"),
        ValidationRuleSpec(field="email", rule_type="email_rfc", description="RFC email", severity="error"),
        ValidationRuleSpec(field="website", rule_type="url_format", description="URL check", severity="error"),
    ]
    is_valid, errors, conf, field_val, conf_level = validator.validate_record_detailed(normalized, rules)
    assert is_valid is True
    assert errors == []
    assert conf >= 0.85
    assert conf_level == "HIGH"
    assert field_val["company_name"] == "VALID"
    assert field_val["email"] == "VALID"
    assert field_val["website"] == "VALID"

    # Test with invalid email
    bad_record = dict(normalized)
    bad_record["email"] = "not-an-email"
    is_valid_bad, errors_bad, conf_bad, field_val_bad, conf_level_bad = validator.validate_record_detailed(bad_record, rules)
    assert is_valid_bad is False
    assert len(errors_bad) >= 1
    assert field_val_bad["email"] == "INVALID"
    assert conf_level_bad == "LOW"


def test_e2e_phase3_workflow_lifecycle():
    # 1. Create a workflow
    plan_resp = client.post(
        "/api/workflows/plan",
        json={"prompt": "Find 20 AI robotics startups with founders, emails and websites", "target_record_count": 20}
    )
    assert plan_resp.status_code == 201
    wf_data = plan_resp.json()
    wf_id = wf_data["id"]
    assert "reasoning" in wf_data["plan"]
    assert len(wf_data["plan"]["reasoning"]) > 0

    # 2. Run the workflow (Demo mode)
    run_resp = client.post(
        f"/api/workflows/{wf_id}/run",
        json={"execution_mode": "demo"}
    )
    assert run_resp.status_code == 202
    run_1_data = run_resp.json()
    run_1_id = run_1_data["run_id"]

    # Let background task complete
    import time
    for _ in range(25):
        st = client.get(f"/api/runs/{run_1_id}").json()
        if st["status"] in ["completed", "failed"]:
            break
        time.sleep(0.3)

    assert st["status"] == "completed"
    assert st["total_records"] > 0
    assert "execution_timeline" in st
    assert len(st["execution_timeline"]) > 0
    assert "quality_summary" in st
    assert st["quality_summary"] is not None
    assert st["quality_summary"]["valid_rate_percent"] >= 0

    # 3. Test timeline endpoint
    timeline_resp = client.get(f"/api/runs/{run_1_id}/timeline")
    assert timeline_resp.status_code == 200
    timeline = timeline_resp.json()
    assert len(timeline) >= 3

    # 4. Test quality summary endpoint
    quality_resp = client.get(f"/api/runs/{run_1_id}/quality")
    assert quality_resp.status_code == 200
    q_data = quality_resp.json()
    assert "total_evaluated" in q_data
    assert "confidence_breakdown" in q_data

    # 5. Test dataset with filters
    ds_resp = client.get(f"/api/runs/{run_1_id}/dataset?confidence_filter=HIGH")
    assert ds_resp.status_code == 200
    ds = ds_resp.json()
    assert "quality_summary" in ds
    assert len(ds["records"]) > 0
    first_rec = ds["records"][0]
    assert "confidence_level" in first_rec
    assert "field_validations" in first_rec
    assert "field_transformations" in first_rec

    # 6. Test rerun endpoint
    rerun_resp = client.post(f"/api/runs/{run_1_id}/rerun")
    assert rerun_resp.status_code == 202
    rerun_data = rerun_resp.json()
    run_2_id = rerun_data["run_id"]
    assert run_2_id != run_1_id

    # Wait for rerun to complete
    for _ in range(25):
        st2 = client.get(f"/api/runs/{run_2_id}").json()
        if st2["status"] in ["completed", "failed"]:
            break
        time.sleep(0.3)
    assert st2["status"] == "completed"

    # 7. Test list workflow runs
    runs_resp = client.get(f"/api/workflows/{wf_id}/runs")
    assert runs_resp.status_code == 200
    wf_runs = runs_resp.json()
    assert len(wf_runs) >= 2
    run_ids = [r["run_id"] for r in wf_runs]
    assert run_1_id in run_ids
    assert run_2_id in run_ids

    # 8. Test run comparison endpoint
    compare_resp = client.get(f"/api/runs/compare?run_a={run_1_id}&run_b={run_2_id}")
    assert compare_resp.status_code == 200
    comp = compare_resp.json()
    assert comp["run_a_id"] == run_1_id
    assert comp["run_b_id"] == run_2_id
    assert "total_records_delta" in comp
    assert "summary" in comp

    # 9. Test connector health endpoint
    health_resp = client.get("/api/connectors/health")
    assert health_resp.status_code == 200
    h_data = health_resp.json()
    assert "overall_status" in h_data
    assert len(h_data["connectors"]) >= 2


def test_run_cancellation():
    # Create workflow
    plan_resp = client.post(
        "/api/workflows/plan",
        json={"prompt": "Collect 50 software firms in Pune", "target_record_count": 50}
    )
    wf_id = plan_resp.json()["id"]

    # Start run
    run_resp = client.post(
        f"/api/workflows/{wf_id}/run",
        json={"execution_mode": "demo"}
    )
    run_id = run_resp.json()["run_id"]

    # Immediately cancel
    cancel_resp = client.post(f"/api/runs/{run_id}/cancel")
    assert cancel_resp.status_code == 200
    c_status = cancel_resp.json()
    assert c_status["status"] in ["cancelled", "completed"]
