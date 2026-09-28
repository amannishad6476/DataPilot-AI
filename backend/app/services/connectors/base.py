from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
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

    def is_domain_permitted(self, url: str) -> bool:
        """
        Validates that the target URL complies with the allowed domains list.
        If allowed_domains is empty or contains '*', all publicly accessible HTTP(S) domains are permitted.
        """
        if not url:
            return False
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ["http", "https"]:
                return False

            host = parsed.netloc.lower().split(":")[0]
            if not host:
                return False

            # Disallow private/internal IPs to prevent SSRF
            if host in ["localhost", "127.0.0.1", "0.0.0.0"] or host.startswith("192.168.") or host.startswith("10."):
                return False

            if not self.allowed_domains or "*" in self.allowed_domains:
                return True

            for allowed in self.allowed_domains:
                allowed_clean = allowed.lower().lstrip(".")
                if host == allowed_clean or host.endswith(f".{allowed_clean}"):
                    return True
            return False
        except Exception:
            return False

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
        )
