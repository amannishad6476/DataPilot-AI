import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

import time
from app.services.connectors.registry import connector_registry
from app.services.connectors.base import ConnectorDescriptor
from app.services.connectors.n8n_connector import N8nWebhookConnector

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/connectors", tags=["Connectors"])


class N8nWebhookPayload(BaseModel):
    workflow_id: str
    run_id: Optional[str] = None
    records: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


@router.get("", response_model=List[ConnectorDescriptor])
def list_registered_connectors():
    """Returns the list of all approved and permitted source connectors."""
    return connector_registry.list_all()


@router.get("/{connector_id}/health")
async def check_connector_health(connector_id: str):
    """Verifies health and connectivity of a specific connector with live latency tracking."""
    conn = connector_registry.get(connector_id)
    if not conn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Connector '{connector_id}' not found")
    start = time.perf_counter()
    healthy = await conn.health_check()
    lat = round((time.perf_counter() - start) * 1000, 2)
    connector_registry.record_call(
        connector_id=connector_id,
        success=healthy,
        latency_ms=lat,
        status_code=200 if healthy else 503,
        error=None if healthy else "Ping test failed"
    )
    return {
        "connector_id": connector_id,
        "name": conn.name,
        "is_healthy": healthy,
        "latency_ms": lat,
        "status": "HEALTHY" if healthy else "UNAVAILABLE"
    }


@router.get("/n8n/template")
def get_n8n_workflow_template():
    """Generates an exportable n8n workflow JSON compatible with DataPilot AI webhooks."""
    return N8nWebhookConnector.generate_n8n_template()


@router.post("/webhooks/n8n", status_code=status.HTTP_200_OK)
async def receive_n8n_webhook(payload: N8nWebhookPayload):
    """
    Webhook receiver endpoint for external n8n instances to return extracted records
    to DataPilot AI.
    """
    logger.info(f"Received n8n webhook payload for workflow {payload.workflow_id} ({len(payload.records)} records)")
    return {
        "status": "received",
        "workflow_id": payload.workflow_id,
        "records_received": len(payload.records),
        "message": "Payload registered successfully for pipeline normalization."
    }
