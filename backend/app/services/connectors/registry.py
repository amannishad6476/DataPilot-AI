import logging
from typing import Dict, List, Optional
from app.services.connectors.base import (
    BaseSourceConnector,
    ConnectorDescriptor,
    ConnectorCapability,
    SourceType,
)

logger = logging.getLogger(__name__)


class ConnectorRegistry:
    """
    Central registry of approved and permitted data connectors.
    Ensures the AI planner only assigns workflows to validated, policy-compliant execution endpoints.
    """

    def __init__(self):
        self._connectors: Dict[str, BaseSourceConnector] = {}

    def register(self, connector: BaseSourceConnector) -> None:
        self._connectors[connector.connector_id] = connector
        logger.info(f"Registered connector: {connector.connector_id} ({connector.name})")

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
