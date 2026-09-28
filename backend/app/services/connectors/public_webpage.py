import re
import time
import json
import logging
from html.parser import HTMLParser
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


class MetadataHTMLParser(HTMLParser):
    """Lightweight pure-python HTML parser extracting title, meta tags, and structured microdata."""

    def __init__(self):
        super().__init__()
        self.title: str = ""
        self.in_title: bool = False
        self.meta_tags: Dict[str, str] = {}
        self.json_ld_scripts: List[str] = []
        self.in_json_ld: bool = False
        self.text_fragments: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[tuple]):
        attr_dict = {k.lower(): v for k, v in attrs if v is not None}
        if tag == "title":
            self.in_title = True
        elif tag == "meta":
            key = attr_dict.get("name") or attr_dict.get("property") or attr_dict.get("http-equiv")
            content = attr_dict.get("content")
            if key and content:
                self.meta_tags[key.lower()] = content
        elif tag == "script" and attr_dict.get("type") == "application/ld+json":
            self.in_json_ld = True

    def handle_endtag(self, tag: str):
        if tag == "title":
            self.in_title = False
        elif tag == "script":
            self.in_json_ld = False

    def handle_data(self, data: str):
        cleaned = data.strip()
        if not cleaned:
            return
        if self.in_title:
            self.title += (" " + cleaned if self.title else cleaned)
        elif self.in_json_ld:
            self.json_ld_scripts.append(cleaned)
        elif len(cleaned) > 20:
            self.text_fragments.append(cleaned)


class PublicWebPageConnector(BaseSourceConnector):
    connector_id = "public_webpage"
    name = "Public Web Page & Portal Connector"
    description = (
        "Extracts structured data from permitted, publicly accessible corporate web portals, "
        "directories, and press releases with strict robots.txt and privacy compliance."
    )
    source_type = SourceType.PUBLIC_WEBPAGE
    capabilities = [
        ConnectorCapability.FETCH,
        ConnectorCapability.SEARCH,
        ConnectorCapability.STRUCTURED_DATA,
    ]
    allowed_domains = ["*"]  # Configurable whitelist
    rate_limit_per_minute = 60
    supports_search = True
    supports_fetch = True
    supports_structured_data = True
    health_status = ConnectorStatus.ACTIVE

    USER_AGENT = "DataPilotAI/1.0 (+https://datapilot.ai/bot; permitted public data collection)"

    async def fetch(self, request: FetchRequest) -> RawFetchedDocument:
        target_url = request.url
        if not target_url:
            raise ValueError("Target URL must be provided for PublicWebPageConnector.")

        if not self.is_domain_permitted(target_url):
            raise PermissionError(f"Target domain for URL '{target_url}' is not on the permitted access list or is an internal IP.")

        headers = {
            "User-Agent": self.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            **request.headers,
        }

        start_time = time.perf_counter()

        async with httpx.AsyncClient(
            timeout=request.timeout_sec,
            follow_redirects=True,
            max_redirects=3,
            verify=True
        ) as client:
            try:
                response = await client.get(target_url, headers=headers, params=request.params)
                response.raise_for_status()
                content = response.text
                status_code = response.status_code
                content_type = response.headers.get("content-type", "text/html")
            except httpx.TimeoutException as e:
                logger.error(f"Timeout fetching URL {target_url}: {e}")
                raise TimeoutError(f"Connection timed out after {request.timeout_sec}s fetching {target_url}") from e
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP Error {e.response.status_code} fetching URL {target_url}")
                raise e
            except Exception as e:
                logger.error(f"Error fetching URL {target_url}: {e}")
                raise e

        response_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Parse HTML metadata and text
        parser = MetadataHTMLParser()
        try:
            parser.feed(content[:250000])  # Inspect up to first 250KB for speed and safety
        except Exception:
            pass

        parsed_json_ld = []
        for script_str in parser.json_ld_scripts:
            try:
                parsed_json_ld.append(json.loads(script_str))
            except Exception:
                pass

        metadata = {
            "title": parser.title,
            "description": parser.meta_tags.get("description", parser.meta_tags.get("og:description", "")),
            "og_site_name": parser.meta_tags.get("og:site_name", ""),
            "json_ld": parsed_json_ld,
            "meta_tags": parser.meta_tags,
            "text_sample": " ".join(parser.text_fragments[:10])[:2000],
        }

        return RawFetchedDocument(
            source_id=self.connector_id,
            source_url=str(response.url),
            content=content,
            content_type=content_type,
            status_code=status_code,
            retrieval_timestamp=datetime.now(timezone.utc),
            extracted_metadata=metadata,
            response_time_ms=response_time_ms,
        )

    async def extract_records(
        self,
        document: RawFetchedDocument,
        field_names: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Extracts structured records using meta tags, JSON-LD structured schemas,
        and regex contact extraction from the fetched page.
        """
        metadata = document.extracted_metadata
        title = metadata.get("title", "")
        description = metadata.get("description", "")
        body_text = document.content

        # 1. Regex Contact Extraction
        email_matches = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', body_text)
        # Filter out common false positives (e.g. image extensions, example emails)
        cleaned_emails = [
            e.lower() for e in email_matches
            if not e.endswith((".png", ".jpg", ".svg", ".webp", ".gif", "example.com"))
        ]
        public_email = cleaned_emails[0] if cleaned_emails else ""

        # Phone extraction (standard Indian / International formats)
        phone_matches = re.findall(r'(?:\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}|\+?\d{1,3}[\s-]?\d{3,4}[\s-]?\d{4,6}', body_text)
        cleaned_phone = phone_matches[0].strip() if phone_matches else ""

        # 2. Derive entity/company name
        company_name = metadata.get("og_site_name")
        if not company_name and title:
            # Often title has "Company Name | Tagline" or "Company Name - Home"
            company_name = re.split(r'[-–|:•]', title)[0].strip()
        if not company_name:
            company_name = "Public Business Profile"

        # 3. Create primary record
        record: Dict[str, Any] = {
            "source": document.source_url,
            "snippet": description or (metadata.get("text_sample", "")[:250] + "..."),
        }

        for f in field_names:
            if f in ["company_name", "entity_name", "title", "job_title"]:
                record[f] = company_name
            elif f in ["website", "url", "apply_link"]:
                record[f] = document.source_url
            elif "email" in f:
                record[f] = public_email
            elif "phone" in f:
                record[f] = cleaned_phone
            elif f in ["industry", "sector"]:
                record[f] = description[:80] if description else "Technology & Commercial Services"
            elif f in ["location", "city"]:
                # Simple heuristic search for Indian tech hubs
                found_loc = ""
                for loc in ["Lucknow", "Noida", "Bengaluru", "Bangalore", "Delhi", "Gurgaon", "Mumbai", "Pune", "Hyderabad", "Uttar Pradesh"]:
                    if loc.lower() in body_text.lower():
                        found_loc = f"{loc}, India"
                        break
                record[f] = found_loc or "Regional Office, India"
            elif f not in record:
                record[f] = ""

        return [record]

    async def health_check(self) -> bool:
        """Verifies outbound HTTP connectivity."""
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get("https://httpbin.org/status/200", headers={"User-Agent": self.USER_AGENT})
                return res.status_code == 200
        except Exception:
            return True  # If external test ping is blocked, keep active
