import json
import logging
from typing import Optional
import httpx
from app.config import settings
from app.schemas.planner import PlannerOutput
from app.services.planner.base import BasePlannerProvider

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are DataPilot AI, an autonomous data workflow planner.
Your job is to convert any natural language data extraction request into a robust, executable Directed Acyclic Graph (DAG) pipeline.

Respond ONLY with a valid JSON object matching the following structure:
{
  "goal": "Clear operational objective of the workflow",
  "domain": "Domain identifier, e.g. college_fest_sponsorship, tech_recruiting, b2b_leads, ecommerce_intel",
  "target_record_count": 30,
  "entities": ["company", "contact"],
  "fields": [
    {"name": "company_name", "type": "string", "required": true, "description": "Legal or brand name"},
    {"name": "industry", "type": "string", "required": false, "description": "Operating sector"},
    {"name": "website", "type": "url", "required": true, "description": "Official company website"},
    {"name": "business_email", "type": "email", "required": false, "description": "Public business contact email"},
    {"name": "phone", "type": "phone", "required": false, "description": "Public office or support phone"},
    {"name": "location", "type": "string", "required": false, "description": "Operating headquarters or local office"}
  ],
  "sources": [
    {
      "id": "src_1",
      "type": "official_portal",
      "name": "Public Business Registries & Portals",
      "purpose": "Discover permitted listings and official profiles",
      "allowed_public_only": true
    }
  ],
  "steps": [
    {
      "id": "step_1_input",
      "type": "input",
      "name": "Query Ingestion",
      "description": "Parse natural language parameters and constraints",
      "depends_on": [],
      "action": "ingest_user_query",
      "target_fields": [],
      "estimated_duration_sec": 0.5
    },
    {
      "id": "step_2_plan",
      "type": "ai_planning",
      "name": "Semantic Query Expansion",
      "description": "Formulate targeted search queries and source ranking criteria",
      "depends_on": ["step_1_input"],
      "action": "expand_search_queries",
      "target_fields": [],
      "estimated_duration_sec": 1.0
    },
    {
      "id": "step_3_discovery",
      "type": "source_discovery",
      "name": "Public Source Discovery",
      "description": "Identify accessible public directories, tech hubs, and corporate portals",
      "depends_on": ["step_2_plan"],
      "action": "discover_public_sources",
      "target_fields": ["source_url"],
      "estimated_duration_sec": 2.5
    },
    {
      "id": "step_4_extraction",
      "type": "extraction",
      "name": "Entity & Data Extraction",
      "description": "Extract raw company names, industries, and candidate domains from discovered sources",
      "depends_on": ["step_3_discovery"],
      "action": "extract_raw_entities",
      "target_fields": ["company_name", "industry", "website"],
      "estimated_duration_sec": 3.0
    },
    {
      "id": "step_5_contact",
      "type": "extraction",
      "name": "Public Contact Intelligence",
      "description": "Retrieve official public contact endpoints (email, phone, location) from public pages",
      "depends_on": ["step_4_extraction"],
      "action": "extract_contact_info",
      "target_fields": ["business_email", "phone", "location"],
      "estimated_duration_sec": 2.5
    },
    {
      "id": "step_6_transform",
      "type": "transformation",
      "name": "Field Normalization",
      "description": "Standardize URL schemes, format phone numbers into E.164 standard, and clean emails",
      "depends_on": ["step_5_contact"],
      "action": "normalize_records",
      "target_fields": ["website", "business_email", "phone"],
      "estimated_duration_sec": 1.5
    },
    {
      "id": "step_7_validation",
      "type": "validation",
      "name": "Data Quality & RFC Validation",
      "description": "Verify RFC email syntax, DNS validity, phone number length, and reachable website URLs",
      "depends_on": ["step_6_transform"],
      "action": "validate_fields",
      "target_fields": ["business_email", "phone", "website"],
      "estimated_duration_sec": 1.5
    },
    {
      "id": "step_8_dedup",
      "type": "deduplication",
      "name": "Fuzzy Entity Deduplication",
      "description": "Apply fuzzy Levenshtein and token-sort similarity to merge duplicate or near-duplicate records",
      "depends_on": ["step_7_validation"],
      "action": "deduplicate_records",
      "target_fields": ["company_name", "website"],
      "estimated_duration_sec": 1.5
    },
    {
      "id": "step_9_merge",
      "type": "merge",
      "name": "Dataset Synthesis & Evidence Linking",
      "description": "Consolidate clean attributes and attach source URL evidence with confidence scoring",
      "depends_on": ["step_8_dedup"],
      "action": "merge_and_link_evidence",
      "target_fields": [],
      "estimated_duration_sec": 1.0
    },
    {
      "id": "step_10_output",
      "type": "output",
      "name": "Dataset Delivery",
      "description": "Format dataset into structured table with search, filter, and export readiness",
      "depends_on": ["step_9_merge"],
      "action": "finalize_output_dataset",
      "target_fields": [],
      "estimated_duration_sec": 0.5
    }
  ],
  "validation_rules": [
    {"field": "business_email", "rule_type": "email_rfc", "description": "Standard RFC 5322 email syntax", "severity": "warning", "params": {}},
    {"field": "website", "rule_type": "url_format", "description": "Valid HTTP/HTTPS canonical URL format", "severity": "error", "params": {}},
    {"field": "company_name", "rule_type": "non_empty", "description": "Company name must not be blank", "severity": "error", "params": {}}
  ],
  "deduplication_strategy": "Multi-key hybrid deduplication: canonical website domain matching + Jaro-Winkler string similarity (threshold 0.88) on entity names",
  "deduplication_keys": ["company_name", "website"],
  "output_format": "table"
}

Ensure the steps form a connected DAG. Do NOT hardcode responses for a single domain; dynamically generate steps and fields appropriate to what the user requested."""


class OpenAIPlannerProvider(BasePlannerProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL
        self.base_url = settings.OPENAI_BASE_URL or "https://api.openai.com/v1"

    async def generate_plan(self, prompt: str, target_count: int = 30) -> PlannerOutput:
        if not self.api_key:
            raise ValueError("OpenAI API key is not configured.")

        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        user_message = f"User Request: {prompt}\nTarget Record Count: {target_count}\nGenerate the complete structured data collection workflow JSON."
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            parsed_json = json.loads(content)
            return PlannerOutput.model_validate(parsed_json)
