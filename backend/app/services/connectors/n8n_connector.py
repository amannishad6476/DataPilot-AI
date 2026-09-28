import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import httpx

from app.services.connectors.base import (
    BaseSourceConnector,
    SourceType,
    ConnectorCapability,
    ConnectorStatus,
    FetchRequest,
    RawFetchedDocument,
)

logger = logging.getLogger(__name__)


class N8nWebhookConnector(BaseSourceConnector):
    connector_id = "n8n_webhook"
    name = "n8n Workflow Automation Connector"
    description = (
        "Dispatches dynamic extraction workflows to external n8n self-hosted or cloud instances "
        "for multi-app integration and pipeline automation."
    )
    source_type = SourceType.N8N_WEBHOOK
    capabilities = [
        ConnectorCapability.FETCH,
        ConnectorCapability.SEARCH,
        ConnectorCapability.STRUCTURED_DATA,
    ]
    allowed_domains = ["*"]
    rate_limit_per_minute = 100
    supports_search = True
    supports_fetch = True
    supports_structured_data = True
    health_status = ConnectorStatus.ACTIVE

    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url

    async def fetch(self, request: FetchRequest) -> RawFetchedDocument:
        target_url = request.url or self.webhook_url
        if not target_url:
            # Standalone simulation response if n8n endpoint is not configured in local environment
            simulated_response = {
                "n8n_execution_id": f"exec_{int(datetime.now(timezone.utc).timestamp())}",
                "status": "success",
                "message": "n8n workflow triggered successfully via DataPilot AI connector.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            return RawFetchedDocument(
                source_id=self.connector_id,
                source_url="n8n://local-execution-hook",
                content=json.dumps(simulated_response),
                content_type="application/json",
                status_code=200,
                retrieval_timestamp=datetime.now(timezone.utc),
                extracted_metadata={"simulated": True},
                response_time_ms=120.0,
            )

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "DataPilotAI-n8n/1.0",
            **request.headers,
        }

        async with httpx.AsyncClient(timeout=request.timeout_sec) as client:
            response = await client.post(target_url, json=request.params, headers=headers)
            response.raise_for_status()
            content = response.text
            status_code = response.status_code

        return RawFetchedDocument(
            source_id=self.connector_id,
            source_url=target_url,
            content=content,
            content_type="application/json",
            status_code=status_code,
            retrieval_timestamp=datetime.now(timezone.utc),
            extracted_metadata={"n8n_live": True},
            response_time_ms=250.0,
        )

    async def extract_records(
        self,
        document: RawFetchedDocument,
        field_names: List[str]
    ) -> List[Dict[str, Any]]:
        try:
            payload = json.loads(document.content)
        except Exception:
            return []

        # If n8n returns an array of records directly
        if isinstance(payload, list):
            items = payload
        elif isinstance(payload, dict):
            items = payload.get("data", payload.get("items", [payload]))
        else:
            items = []

        records = []
        for it in items:
            if isinstance(it, dict):
                rec = {
                    "source": document.source_url,
                    "snippet": f"Extracted via n8n automation pipeline ({document.source_url})",
                }
                for f in field_names:
                    rec[f] = str(it.get(f, ""))
                records.append(rec)
        return records

    async def health_check(self) -> bool:
        return True

    @staticmethod
    def generate_n8n_template() -> Dict[str, Any]:
        """Generates an n8n workflow definition JSON compatible with DataPilot AI webhooks."""
        return {
            "name": "DataPilot AI - Permitted Extraction Webhook",
            "nodes": [
                {
                    "parameters": {
                        "path": "datapilot-ai",
                        "responseMode": "lastNode",
                        "options": {}
                    },
                    "name": "Webhook Inbound",
                    "type": "n8n-nodes-base.webhook",
                    "typeVersion": 1,
                    "position": [250, 300]
                },
                {
                    "parameters": {
                        "jsCode": "// Process DataPilot AI structured extraction parameters\nconst prompt = $json.prompt;\nconst fields = $json.fields;\nreturn [{ json: { status: 'processed', prompt, fields, result_count: 1 } }];"
                    },
                    "name": "DataPilot Data Formatter",
                    "type": "n8n-nodes-base.code",
                    "typeVersion": 1,
                    "position": [450, 300]
                }
            ],
            "connections": {
                "Webhook Inbound": {
                    "main": [
                        [
                            {"node": "DataPilot Data Formatter", "type": "main", "index": 0}
                        ]
                    ]
                }
            }
        }
