import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_e2e_workflow_lifecycle():
    # 1. Plan workflow from prompt
    prompt = "Find 30 potential sponsors for a college technical fest in Lucknow. Collect company name, industry, website, public business email, phone, location and source. Remove duplicates and validate the results."
    plan_resp = client.post("/api/workflows/plan", json={"prompt": prompt, "target_record_count": 30})
    assert plan_resp.status_code == 201
    wf_data = plan_resp.json()
    wf_id = wf_data["id"]
    assert wf_id is not None
    assert len(wf_data["plan"]["steps"]) >= 6

    # 2. Get workflow details
    get_resp = client.get(f"/api/workflows/{wf_id}")
    assert get_resp.status_code == 200

    # 3. Trigger execution
    run_resp = client.post(f"/api/workflows/{wf_id}/run", json={"execution_mode": "demo"})
    assert run_resp.status_code == 202
    run_data = run_resp.json()
    run_id = run_data["run_id"]
    assert run_id is not None

    # 4. Check run status (wait briefly for completion)
    import time
    for _ in range(30):
        status_resp = client.get(f"/api/runs/{run_id}")
        assert status_resp.status_code == 200
        cur_status = status_resp.json()["status"]
        if cur_status == "completed":
            break
        time.sleep(0.5)

    assert cur_status == "completed"

    # 5. Query dataset
    ds_resp = client.get(f"/api/runs/{run_id}/dataset?page=1&page_size=10")
    assert ds_resp.status_code == 200
    ds_data = ds_resp.json()
    assert ds_data["total_records"] > 0
    assert len(ds_data["records"]) > 0

    # 6. Verify evidence attached
    first_record = ds_data["records"][0]
    assert len(first_record["evidence_items"]) > 0

    # 7. Test CSV export
    csv_resp = client.get(f"/api/runs/{run_id}/export/csv")
    assert csv_resp.status_code == 200
    assert "company_name" in csv_resp.text
    assert "website" in csv_resp.text

    # 8. Test JSON export
    json_resp = client.get(f"/api/runs/{run_id}/export/json")
    assert json_resp.status_code == 200
    assert isinstance(json_resp.json(), list)
