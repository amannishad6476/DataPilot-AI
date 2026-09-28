from app.services.connectors.base import (
    BaseSourceConnector,
    SourceType,
    ConnectorCapability,
    ConnectorStatus,
    FetchRequest,
    RawFetchedDocument,
    ConnectorDescriptor,
)
from app.services.connectors.registry import ConnectorRegistry, connector_registry
from app.services.connectors.public_webpage import PublicWebPageConnector
from app.services.connectors.json_feed import JsonFeedConnector
from app.services.connectors.n8n_connector import N8nWebhookConnector

# Register default permitted source connectors
connector_registry.register(PublicWebPageConnector())
connector_registry.register(JsonFeedConnector())
connector_registry.register(N8nWebhookConnector())

__all__ = [
    "BaseSourceConnector",
    "SourceType",
    "ConnectorCapability",
    "ConnectorStatus",
    "FetchRequest",
    "RawFetchedDocument",
    "ConnectorDescriptor",
    "ConnectorRegistry",
    "connector_registry",
    "PublicWebPageConnector",
    "JsonFeedConnector",
    "N8nWebhookConnector",
]
