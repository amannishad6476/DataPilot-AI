from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
import ipaddress
from pydantic import BaseModel, Field


class SourceType(str, Enum):
    REST_API = "REST_API"
    JSON_FEED = "JSON_FEED"
    RSS = "RSS"
    PUBLIC_WEBPAGE = "PUBLIC_WEBPAGE"
    DEMO = "DEMO"
    N8N_WEBHOOK = "N8N_WEBHOOK"


class ConnectorCapability(str, Enum):
    SEARCH = "search"
    FETCH = "fetch"
    STRUCTURED_DATA = "structured_data"
    STREAMING = "streaming"


class ConnectorStatus(str, Enum):
    ACTIVE = "active"
    DEGRADED = "degraded"
    OFFLINE = "offline"


class FetchRequest(BaseModel):
    url: Optional[str] = None
    query: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict)
    headers: Dict[str, str] = Field(default_factory=dict)
    timeout_sec: float = 12.0


class RawFetchedDocument(BaseModel):
    source_id: str
    source_url: str
    content: str
    content_type: str = "text/html"
    status_code: int = 200
    retrieval_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    extracted_metadata: Dict[str, Any] = Field(default_factory=dict)
    response_time_ms: float = 0.0


class ConnectorDescriptor(BaseModel):
    connector_id: str
    name: str
    description: str
    source_type: SourceType
    capabilities: List[ConnectorCapability]
    allowed_domains: List[str]
    rate_limit_per_minute: int
    supports_search: bool
    supports_fetch: bool
    supports_structured_data: bool
    health_status: ConnectorStatus
    authentication_type: str = "NONE"
    timeout_sec: float = 12.0
    last_success: Optional[str] = None
    last_failure: Optional[str] = None
    supported_operations: List[str] = Field(default_factory=lambda: ["fetch", "search", "extract"])


class BaseSourceConnector(ABC):
    connector_id: str
    name: str
    description: str
    source_type: SourceType
    capabilities: List[ConnectorCapability]
    allowed_domains: List[str] = []
    rate_limit_per_minute: int = 60
    supports_search: bool = True
    supports_fetch: bool = True
    supports_structured_data: bool = True
    health_status: ConnectorStatus = ConnectorStatus.ACTIVE
    authentication_type: str = "NONE"
    timeout_sec: float = 12.0
    last_success: Optional[str] = None
    last_failure: Optional[str] = None
    supported_operations: List[str] = ["fetch", "search", "extract"]

    def is_domain_permitted(self, url: str) -> bool:
        """
        Validates target URL against SSRF safety rules, disallowing loopback,
        private RFC 1918 subnets, and cloud metadata IPs.
        """
        from app.services.connectors.ssrf_firewall import validate_url_security
        is_safe, _ = validate_url_security(url, self.allowed_domains)
        return is_safe

    @abstractmethod
    async def fetch(self, request: FetchRequest) -> RawFetchedDocument:
        """Fetches raw content from the source conforming to rate limits and timeouts."""
        pass

    @abstractmethod
    async def extract_records(
        self,
        document: RawFetchedDocument,
        field_names: List[str]
    ) -> List[Dict[str, Any]]:
        """Parses raw content into structured entity records according to requested field names."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Checks if the external source / service is responsive."""
        pass

    def to_descriptor(self) -> ConnectorDescriptor:
        return ConnectorDescriptor(
            connector_id=self.connector_id,
            name=self.name,
            description=self.description,
            source_type=self.source_type,
            capabilities=self.capabilities,
            allowed_domains=self.allowed_domains,
            rate_limit_per_minute=self.rate_limit_per_minute,
            supports_search=self.supports_search,
            supports_fetch=self.supports_fetch,
            supports_structured_data=self.supports_structured_data,
            health_status=self.health_status,
            authentication_type=self.authentication_type,
            timeout_sec=self.timeout_sec,
            last_success=self.last_success,
            last_failure=self.last_failure,
            supported_operations=self.supported_operations,
        )
