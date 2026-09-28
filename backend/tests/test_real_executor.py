import time
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_connectors_api():
    resp = client.get("/api/connectors")
    assert resp.status_code == 200
    connectors = resp.json()
    assert len(connectors) >= 3

    # Health endpoint
    health_resp = client.get("/api/connectors/public_webpage/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["connector_id"] == "public_webpage"


def test_n8n_endpoints():
    # Template endpoint
    tpl_resp = client.get("/api/connectors/n8n/template")
    assert tpl_resp.status_code == 200
    assert "nodes" in tpl_resp.json()

    # Webhook receiver endpoint
    hook_resp = client.post(
        "/api/connectors/webhooks/n8n",
        json={
            "workflow_id": "test-wf-id",
            "records": [{"company_name": "N8N Partner", "website": "https://n8n.io"}],
            "metadata": {"source": "n8n"}
        }
    )
    assert hook_resp.status_code == 200
    assert hook_resp.json()["status"] == "received"


def test_real_execution_with_resilient_fallback():
    # 1. Create a workflow
    prompt = "Find 30 sponsors for a technical fest in Lucknow. Collect company name, website, email, phone."
    plan_resp = client.post("/api/workflows/plan", json={"prompt": prompt, "target_record_count": 30})
    assert plan_resp.status_code == 201
    wf_id = plan_resp.json()["id"]

    # 2. Trigger run in 'real' mode with an unreachable test domain to verify resilient fallback
    run_resp = client.post(
        f"/api/workflows/{wf_id}/run",
        json={
            "execution_mode": "real",
            "target_url": "https://unreachable-external-test-domain-12345.org"
        }
    )
    assert run_resp.status_code == 202
    run_id = run_resp.json()["run_id"]

    # 3. Poll for completion
    for _ in range(30):
        status_resp = client.get(f"/api/runs/{run_id}")
        assert status_resp.status_code == 200
        cur_status = status_resp.json()["status"]
        if cur_status in ["completed", "failed"]:
            break
        time.sleep(0.4)

    assert cur_status == "completed"

    # 4. Verify records were recovered and delivered through fallback
    ds_resp = client.get(f"/api/runs/{run_id}/dataset")
    assert ds_resp.status_code == 200
    data = ds_resp.json()
    assert data["total_records"] > 0
    assert data["execution_mode"] == "real"
