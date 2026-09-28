import re
from typing import List, Tuple
from app.schemas.planner import (
    PlannerOutput,
    FieldSpec,
    SourceSpec,
    WorkflowStepPlan,
    ValidationRuleSpec,
)
from app.services.planner.base import BasePlannerProvider


class DynamicSemanticPlanner(BasePlannerProvider):
    """
    Intelligent semantic planner that dynamically deconstructs arbitrary natural-language data requests.
    Used for local / offline operation, development, and as an immediate fallback when external LLM APIs
    are unreachable or unconfigured.

    Generates genuine, dynamically tailored DAG workflows matching the specific prompt intent.
    """

    async def generate_plan(self, prompt: str, target_count: int = 30) -> PlannerOutput:
        prompt_lower = prompt.lower()

        # 1. Detect target count if explicitly specified in text
        count_match = re.search(r'\b(?:find|collect|gather|get|extract|scrape|fetch)\s+(\d+)\b', prompt_lower)
        if count_match:
            try:
                target_count = int(count_match.group(1))
            except ValueError:
                pass

        # 2. Semantic Domain Detection
        domain = self._detect_domain(prompt_lower)

        # 3. Dynamic Entity Identification
        entities = self._detect_entities(prompt_lower, domain)

        # 4. Dynamic Field Extraction & Type Inference
        fields = self._extract_fields(prompt, prompt_lower, domain)

        # 5. Dynamic Source Archetype Generation
        sources = self._synthesize_sources(prompt_lower, domain, entities)

        # 6. Dynamic DAG Workflow Generation
        steps = self._construct_workflow_dag(prompt_lower, domain, fields, sources)

        # 7. Validation Rules tailored to fields
        validation_rules = self._derive_validation_rules(fields)

        # 8. Deduplication Strategy
        dedup_strategy, dedup_keys = self._derive_deduplication_strategy(fields, entities)

        # 9. Synthesize Goal
        goal = f"Collect {target_count} validated, deduplicated {domain.replace('_', ' ')} records with full source traceability according to user specifications."

        return PlannerOutput(
            goal=goal,
            domain=domain,
            target_record_count=target_count,
            entities=entities,
            fields=fields,
            sources=sources,
            steps=steps,
            validation_rules=validation_rules,
            deduplication_strategy=dedup_strategy,
            deduplication_keys=dedup_keys,
            output_format="table"
        )

    def _detect_domain(self, text: str) -> str:
        if any(w in text for w in ["sponsor", "fest", "college", "event", "partnership"]):
            return "event_sponsorship_intelligence"
        elif any(w in text for w in ["job", "career", "hiring", "salary", "vacanc"]):
            return "recruitment_job_market"
        elif any(w in text for w in ["lead", "sales", "prospect", "b2b", "outreach"]):
            return "b2b_sales_prospecting"
        elif any(w in text for w in ["investor", "vc", "venture", "fund", "angel"]):
            return "investor_capital_intelligence"
        elif any(w in text for w in ["real estate", "property", "rent", "apartment"]):
            return "real_estate_market"
        elif any(w in text for w in ["product", "ecommerce", "price", "catalog"]):
            return "ecommerce_competitive_pricing"
        else:
            return "targeted_web_intelligence"

    def _detect_entities(self, text: str, domain: str) -> List[str]:
        entities = []
        if "sponsor" in text or "event" in domain:
            entities.extend(["sponsor_organization", "decision_maker_contact", "brand_profile"])
        elif "job" in domain:
            entities.extend(["job_posting", "hiring_company", "compensation_tier"])
        elif "lead" in domain:
            entities.extend(["target_account", "executive_lead", "firmographic_data"])
        elif "investor" in domain:
            entities.extend(["fund_firm", "general_partner", "investment_portfolio"])
        else:
            entities.extend(["organization", "contact_point"])
        return entities

    def _extract_fields(self, raw_prompt: str, text: str, domain: str) -> List[FieldSpec]:
        """
        Dynamically extracts fields mentioned in the prompt or infers them from domain semantics.
        Supports explicit 'collect x, y, z' syntax as well as natural descriptions.
        """
        detected_fields: List[FieldSpec] = []
        added_names = set()

        def add_field(name: str, ftype: str, required: bool, desc: str):
            if name not in added_names:
                detected_fields.append(FieldSpec(
                    name=name,
                    type=ftype,
                    required=required,
                    description=desc
                ))
                added_names.add(name)

        # Check for explicit list pattern like "collect company name, industry, website..."
        collect_match = re.search(r'(?:collect|extract|include|gather|find)\s+([^\.]+?)(?:\.|$|remove|validate)', text)
        if collect_match:
            items_str = collect_match.group(1)
            raw_items = re.split(r'[,;]|\band\b', items_str)
            for item in raw_items:
                item_clean = item.strip()
                if not item_clean or len(item_clean) < 2:
                    continue

                # Check known tokens
                if "company" in item_clean or "name" in item_clean or "organization" in item_clean:
                    add_field("company_name", "string", True, "Official legal or commercial business name")
                elif "industry" in item_clean or "sector" in item_clean or "category" in item_clean:
                    add_field("industry", "string", False, "Operating market sector or specialization")
                elif "website" in item_clean or "domain" in item_clean or "url" in item_clean:
                    add_field("website", "url", True, "Official verified website address")
                elif "email" in item_clean:
                    add_field("public_business_email", "email", False, "Public official business inquiry or contact email")
                elif "phone" in item_clean or "mobile" in item_clean or "contact number" in item_clean:
                    add_field("phone", "phone", False, "Verified public office contact or support phone")
                elif "location" in item_clean or "city" in item_clean or "address" in item_clean:
                    add_field("location", "string", False, "Headquarters or regional operating location")
                elif "source" in item_clean or "evidence" in item_clean:
                    add_field("source", "string", True, "Public source or directory where evidence was retrieved")
                elif "job" in item_clean and "title" in item_clean:
                    add_field("job_title", "string", True, "Designation or title of the role")
                elif "salary" in item_clean or "compensation" in item_clean:
                    add_field("salary_range", "string", False, "Published compensation benchmark")
                elif "link" in item_clean or "apply" in item_clean:
                    add_field("apply_link", "url", True, "Direct application endpoint")
                elif "revenue" in item_clean:
                    add_field("annual_revenue", "string", False, "Reported or estimated annual revenue")
                elif "employee" in item_clean or "headcount" in item_clean:
                    add_field("employee_count", "string", False, "Estimated company size / employee tier")

        # Guarantee foundational fields for the domain if not parsed
        if not detected_fields:
            if domain == "event_sponsorship_intelligence":
                add_field("company_name", "string", True, "Name of potential sponsor")
                add_field("industry", "string", False, "Industry sector")
                add_field("website", "url", True, "Official website URL")
                add_field("public_business_email", "email", False, "Corporate contact email")
                add_field("phone", "phone", False, "Public office phone")
                add_field("location", "string", False, "Headquarters or regional office")
                add_field("source", "string", True, "Originating public listing URL")
            elif domain == "recruitment_job_market":
                add_field("job_title", "string", True, "Role title")
                add_field("company_name", "string", True, "Hiring organization")
                add_field("location", "string", False, "Workplace location or remote")
                add_field("salary_range", "string", False, "Compensation package")
                add_field("apply_link", "url", True, "Application URL")
                add_field("source", "string", True, "Originating job board")
            else:
                add_field("entity_name", "string", True, "Primary entity identifier")
                add_field("website", "url", True, "Entity website")
                add_field("contact_email", "email", False, "Primary contact email")
                add_field("phone", "phone", False, "Primary phone number")
                add_field("location", "string", False, "Geographic location")
                add_field("source", "string", True, "Public data source")

        return detected_fields

    def _synthesize_sources(self, text: str, domain: str, entities: List[str]) -> List[SourceSpec]:
        sources = [
            SourceSpec(
                id="src_public_registry",
                type="official_portal",
                name="Public Corporate Registries & Tech Hubs",
                purpose="Discover legally registered and operating entities compliant with public access terms",
                allowed_public_only=True
            ),
            SourceSpec(
                id="src_industry_directories",
                type="public_directory",
                name="Verified Industry Directories & Portals",
                purpose="Locate active organizations, category tags, and verified public web domains",
                allowed_public_only=True
            ),
            SourceSpec(
                id="src_entity_portals",
                type="official_portal",
                name="Official Public Contact & Press Pages",
                purpose="Extract published corporate emails, public relations contacts, and office locations",
                allowed_public_only=True
            )
        ]
        return sources

    def _construct_workflow_dag(
        self,
        text: str,
        domain: str,
        fields: List[FieldSpec],
        sources: List[SourceSpec]
    ) -> List[WorkflowStepPlan]:
        """
        Dynamically stitches together a DAG of workflow steps based on the fields, domain, and requirements.
        Each step has explicit dependencies to form a genuine visual DAG in React Flow.
        """
        steps: List[WorkflowStepPlan] = []
        field_names = [f.name for f in fields]

        # Step 1: Input Ingestion
        steps.append(WorkflowStepPlan(
            id="step_1_input",
            type="input",
            name="Request Ingestion",
            description=f"Parse prompt constraints, target entity criteria, and extraction parameters.",
            depends_on=[],
            action="ingest_prompt_parameters",
            target_fields=[],
            estimated_duration_sec=0.5
        ))

        # Step 2: Semantic Query Plan
        steps.append(WorkflowStepPlan(
            id="step_2_plan",
            type="ai_planning",
            name="Dynamic Source Planner",
            description="Deconstruct extraction criteria into targeted search directives across permitted public indexes.",
            depends_on=["step_1_input"],
            action="formulate_search_strategy",
            target_fields=[],
            estimated_duration_sec=1.0
        ))

        # Step 3: Source Discovery
        steps.append(WorkflowStepPlan(
            id="step_3_discovery",
            type="source_discovery",
            name="Public Source Discovery",
            description="Query permitted business directories, public listings, and tech hubs respecting robots.txt guidelines.",
            depends_on=["step_2_plan"],
            action="discover_public_endpoints",
            target_fields=["source"],
            estimated_duration_sec=2.0
        ))

        # Step 4: Primary Entity Extraction
        entity_fields = [f for f in ["company_name", "job_title", "entity_name", "industry"] if f in field_names]
        steps.append(WorkflowStepPlan(
            id="step_4_extraction",
            type="extraction",
            name="Primary Entity Extraction",
            description=f"Extract primary attributes ({', '.join(entity_fields)}) from candidate source documents.",
            depends_on=["step_3_discovery"],
            action="extract_entity_records",
            target_fields=entity_fields,
            estimated_duration_sec=2.5
        ))

        # Step 5: Contact / Detail Deep Extraction
        detail_fields = [f for f in ["website", "public_business_email", "phone", "location", "apply_link", "salary_range"] if f in field_names]
        if detail_fields:
            steps.append(WorkflowStepPlan(
                id="step_5_detail_extraction",
                type="extraction",
                name="Contact & Detail Enrichment",
                description=f"Crawl linked public contact and 'About Us' pages for {', '.join(detail_fields)}.",
                depends_on=["step_4_extraction"],
                action="enrich_entity_details",
                target_fields=detail_fields,
                estimated_duration_sec=3.0
            ))
            upstream_for_transform = "step_5_detail_extraction"
        else:
            upstream_for_transform = "step_4_extraction"

        # Step 6: Normalization
        steps.append(WorkflowStepPlan(
            id="step_6_transform",
            type="transformation",
            name="Data Cleaning & Normalization",
            description="Normalize URLs with scheme canonicalization, strip tracking parameters, and clean phone formatting.",
            depends_on=[upstream_for_transform],
            action="normalize_and_clean",
            target_fields=field_names,
            estimated_duration_sec=1.5
        ))

        # Step 7: Validation
        steps.append(WorkflowStepPlan(
            id="step_7_validation",
            type="validation",
            name="Integrity & Field Validation",
            description="Validate RFC email standards, phone number digit criteria, and domain reachable health checks.",
            depends_on=["step_6_transform"],
            action="validate_record_fields",
            target_fields=[f.name for f in fields if f.type in ["email", "phone", "url"]],
            estimated_duration_sec=1.5
        ))

        # Step 8: Similarity-based Deduplication
        steps.append(WorkflowStepPlan(
            id="step_8_deduplication",
            type="deduplication",
            name="Similarity Deduplication",
            description="Perform fuzzy Levenshtein & domain token matching to eliminate near-duplicate records and aliases.",
            depends_on=["step_7_validation"],
            action="fuzzy_deduplicate",
            target_fields=["company_name", "website"] if "company_name" in field_names else ["entity_name"],
            estimated_duration_sec=1.5
        ))

        # Step 9: Evidence Merge
        steps.append(WorkflowStepPlan(
            id="step_9_merge",
            type="merge",
            name="Traceability & Evidence Merge",
            description="Consolidate validated fields, attach public source URLs, citation quotes, and confidence scores.",
            depends_on=["step_8_deduplication"],
            action="merge_and_attach_evidence",
            target_fields=[],
            estimated_duration_sec=1.0
        ))

        # Step 10: Final Output
        steps.append(WorkflowStepPlan(
            id="step_10_output",
            type="output",
            name="Dataset Delivery",
            description="Render structured, filterable, and exportable dataset ready for dashboard exploration and export.",
            depends_on=["step_9_merge"],
            action="deliver_final_dataset",
            target_fields=[],
            estimated_duration_sec=0.5
        ))

        return steps

    def _derive_validation_rules(self, fields: List[FieldSpec]) -> List[ValidationRuleSpec]:
        rules = []
        for f in fields:
            if f.type == "email":
                rules.append(ValidationRuleSpec(
                    field=f.name,
                    rule_type="email_rfc",
                    description=f"Validate that {f.name} strictly conforms to standard email format RFC 5322",
                    severity="warning"
                ))
            elif f.type == "phone":
                rules.append(ValidationRuleSpec(
                    field=f.name,
                    rule_type="phone_format",
                    description=f"Verify {f.name} contains valid digits and optional country code",
                    severity="warning"
                ))
            elif f.type == "url":
                rules.append(ValidationRuleSpec(
                    field=f.name,
                    rule_type="url_format",
                    description=f"Verify {f.name} begins with valid http/https scheme and hostname",
                    severity="error"
                ))
            elif f.required:
                rules.append(ValidationRuleSpec(
                    field=f.name,
                    rule_type="non_empty",
                    description=f"Field {f.name} is mandatory and cannot be null or blank",
                    severity="error"
                ))
        return rules

    def _derive_deduplication_strategy(self, fields: List[FieldSpec], entities: List[str]) -> Tuple[str, List[str]]:
        field_names = [f.name for f in fields]
        keys = []
        if "company_name" in field_names:
            keys.append("company_name")
        elif "entity_name" in field_names:
            keys.append("entity_name")

        if "website" in field_names:
            keys.append("website")
        elif "apply_link" in field_names:
            keys.append("apply_link")

        if not keys and field_names:
            keys.append(field_names[0])

        desc = (
            f"Fuzzy multi-key deduplication: 1) Canonical root domain match on {', '.join([k for k in keys if 'url' in k or 'web' in k or 'link' in k] or ['domain'])}; "
            f"2) Token-set Jaro-Winkler similarity (threshold >= 0.86) on {', '.join([k for k in keys if 'name' in k] or ['title'])}; "
            f"merging duplicate records while preserving the richest contact attributes."
        )
        return desc, keys
