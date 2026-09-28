import time
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
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


class JsonFeedConnector(BaseSourceConnector):
    connector_id = "json_feed"
    name = "Public JSON & REST Feed Connector"
    description = (
        "Consumes public open-data feeds, public REST endpoints, and structured JSON catalogues."
    )
    source_type = SourceType.JSON_FEED
    capabilities = [
        ConnectorCapability.FETCH,
        ConnectorCapability.SEARCH,
        ConnectorCapability.STRUCTURED_DATA,
    ]
    allowed_domains = ["*"]
    rate_limit_per_minute = 120
    supports_search = True
    supports_fetch = True
    supports_structured_data = True
    health_status = ConnectorStatus.ACTIVE

    USER_AGENT = "DataPilotAI/1.0 (+https://datapilot.ai/bot; permitted public data collection)"

    async def fetch(self, request: FetchRequest) -> RawFetchedDocument:
        target_url = request.url
        if not target_url:
            raise ValueError("Target URL must be provided for JsonFeedConnector.")

        if not self.is_domain_permitted(target_url):
            raise PermissionError(f"Target domain for URL '{target_url}' is not on the permitted list.")

        headers = {
            "User-Agent": self.USER_AGENT,
            "Accept": "application/json, text/plain, */*",
            **request.headers,
        }

        start_time = time.perf_counter()
        async with httpx.AsyncClient(timeout=request.timeout_sec, follow_redirects=True) as client:
            response = await client.get(target_url, headers=headers, params=request.params)
            response.raise_for_status()
            content = response.text
            status_code = response.status_code

        response_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

        try:
            parsed_json = json.loads(content)
            record_count = len(parsed_json) if isinstance(parsed_json, list) else len(parsed_json.keys())
        except Exception:
            parsed_json = {}
            record_count = 0

        return RawFetchedDocument(
            source_id=self.connector_id,
            source_url=str(response.url),
            content=content,
            content_type="application/json",
            status_code=status_code,
            retrieval_timestamp=datetime.now(timezone.utc),
            extracted_metadata={"record_count": record_count},
            response_time_ms=response_time_ms,
        )

    async def extract_records(
        self,
        document: RawFetchedDocument,
        field_names: List[str]
    ) -> List[Dict[str, Any]]:
        try:
            data = json.loads(document.content)
        except Exception:
            return []

        items = data if isinstance(data, list) else data.get("items", data.get("results", data.get("data", [data])))
        if not isinstance(items, list):
            items = [items]

        extracted = []
        for raw_item in items[:50]:
            if not isinstance(raw_item, dict):
                continue
            rec = {
                "source": document.source_url,
                "snippet": f"Retrieved from JSON catalog: {document.source_url}",
            }
            for f in field_names:
                # Direct match or case-insensitive lookup
                val = raw_item.get(f)
                if val is None:
                    for k, v in raw_item.items():
                        if k.lower() == f.lower() or f.lower() in k.lower():
                            val = v
                            break
                rec[f] = str(val) if val is not None else ""
            extracted.append(rec)

        return extracted

    async def health_check(self) -> bool:
        return True
