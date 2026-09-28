import logging
from typing import Dict, List, Optional
from app.services.connectors.base import (
    BaseSourceConnector,
    ConnectorDescriptor,
    ConnectorCapability,
    SourceType,
)

from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class ConnectorRegistry:
    """
    Central registry of approved and permitted data connectors.
    Ensures the AI planner only assigns workflows to validated, policy-compliant execution endpoints.
    Tracks real execution metrics to power the Source Health Dashboard.
    """

    def __init__(self):
        self._connectors: Dict[str, BaseSourceConnector] = {}
        self._metrics: Dict[str, Dict[str, Any]] = {}

    def register(self, connector: BaseSourceConnector) -> None:
        self._connectors[connector.connector_id] = connector
        if connector.connector_id not in self._metrics:
            self._metrics[connector.connector_id] = {
                "total_requests": 0,
                "success_count": 0,
                "error_count": 0,
                "latencies": [],
                "last_attempt_at": None,
                "last_status_code": 200,
                "last_error": None
            }
        logger.info(f"Registered connector: {connector.connector_id} ({connector.name})")

    def record_call(
        self,
        connector_id: str,
        success: bool,
        latency_ms: float,
        status_code: Optional[int] = None,
        error: Optional[str] = None
    ) -> None:
        if connector_id not in self._metrics:
            self._metrics[connector_id] = {
                "total_requests": 0,
                "success_count": 0,
                "error_count": 0,
                "latencies": [],
                "last_attempt_at": None,
                "last_status_code": status_code or 200,
                "last_error": None
            }
        m = self._metrics[connector_id]
        m["total_requests"] += 1
        if success:
            m["success_count"] += 1
        else:
            m["error_count"] += 1
        m["latencies"].append(latency_ms)
        m["latencies"] = m["latencies"][-20:]
        m["last_attempt_at"] = datetime.now(timezone.utc).isoformat()
        m["last_status_code"] = status_code
        m["last_error"] = error

    def get_health_report(self) -> Dict[str, Any]:
        items = []
        overall = "HEALTHY"
        for cid, conn in self._connectors.items():
            m = self._metrics.get(cid, {
                "total_requests": 0,
                "success_count": 0,
                "error_count": 0,
                "latencies": [],
                "last_attempt_at": None,
                "last_status_code": 200,
                "last_error": None
            })
            total = m["total_requests"]
            successes = m["success_count"]
            errors = m["error_count"]
            latencies = m["latencies"]
            avg_lat = round(sum(latencies) / len(latencies), 1) if latencies else 0.0

            if total == 0:
                c_status = "HEALTHY"
                details = "Configured and operational (awaiting live requests)"
            else:
                err_rate = errors / total
                if err_rate == 0:
                    c_status = "HEALTHY"
                    details = f"All {total} requests succeeded with avg latency {avg_lat}ms"
                elif err_rate < 0.35:
                    c_status = "DEGRADED"
                    overall = "DEGRADED"
                    details = f"{errors}/{total} requests encountered retries or timeouts"
                else:
                    c_status = "UNAVAILABLE"
                    overall = "DEGRADED"
                    details = f"High error rate ({int(err_rate*100)}%): {m.get('last_error') or 'Endpoint unreachable'}"

            items.append({
                "connector_id": cid,
                "name": conn.name,
                "source_type": conn.source_type.value,
                "status": c_status,
                "total_requests": total,
                "success_count": successes,
                "error_count": errors,
                "avg_latency_ms": avg_lat,
                "last_attempt_at": m["last_attempt_at"],
                "last_status_code": m["last_status_code"],
                "details": details
            })

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_status": overall,
            "connectors": items
        }

    def get(self, connector_id: str) -> Optional[BaseSourceConnector]:
        return self._connectors.get(connector_id)

    def list_all(self) -> List[ConnectorDescriptor]:
        return [c.to_descriptor() for c in self._connectors.values()]

    def find_by_capability(self, capability: ConnectorCapability) -> List[BaseSourceConnector]:
        return [c for c in self._connectors.values() if capability in c.capabilities]

    def find_by_type(self, source_type: SourceType) -> List[BaseSourceConnector]:
        return [c for c in self._connectors.values() if c.source_type == source_type]

    def select_best_connector(
        self,
        domain: str,
        source_type_hint: Optional[str] = None
    ) -> BaseSourceConnector:
        """
        Dynamically recommends the best permitted connector for a given data extraction domain.
        """
        if source_type_hint:
            for c in self._connectors.values():
                if c.source_type.value.lower() == source_type_hint.lower():
                    return c

        if "api" in domain.lower() or "feed" in domain.lower():
            json_conn = self.get("json_feed")
            if json_conn:
                return json_conn

        if "webhook" in domain.lower() or "n8n" in domain.lower():
            n8n_conn = self.get("n8n_webhook")
            if n8n_conn:
                return n8n_conn

        # Default preferred real connector is public_webpage
        web_conn = self.get("public_webpage")
        if web_conn:
            return web_conn

        # Fallback to first available connector
        return next(iter(self._connectors.values()))


connector_registry = ConnectorRegistry()
