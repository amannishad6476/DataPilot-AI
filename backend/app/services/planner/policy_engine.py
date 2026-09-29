from typing import Tuple, List, Set, Dict
from app.schemas.planner import PlannerOutput
from app.services.connectors.ssrf_firewall import validate_url_security


APPROVED_ACTIONS: Set[str] = {
    "ingest_prompt_parameters",
    "formulate_search_strategy",
    "discover_public_endpoints",
    "extract_entity_records",
    "enrich_entity_details",
    "normalize_and_clean",
    "validate_record_fields",
    "fuzzy_deduplicate",
    "merge_and_attach_evidence",
    "deliver_final_dataset",
    "webhook_dispatch",
    "fetch_public_data",
    "parse_entities",
    "normalize_attributes",
    "validate_records",
    "deduplicate_entities",
    "merge_records"
}

APPROVED_STEP_TYPES: Set[str] = {
    "input",
    "ai_planning",
    "source_discovery",
    "source",
    "extraction",
    "transformation",
    "transform",
    "validation",
    "deduplication",
    "merge",
    "output"
}


FORBIDDEN_KEYWORDS: List[str] = [
    "__import__", "os.system", "subprocess", "eval(", "exec(", "<script>", "javascript:", "file://", "ftp://"
]


class PolicyEngine:
    """
    AI Safety and Policy Enforcement Engine.
    Treats the LLM as an untrusted planner. Enforces allowlisted capability boundaries,
    validates DAG acyclicity, checks SSRF rules, and rejects malicious or invalid workflow plans.
    """

    @classmethod
    def validate_plan(cls, plan: PlannerOutput) -> Tuple[bool, List[str]]:
        violations: List[str] = []

        # 1. Bounds & structural checks
        if not plan.steps:
            violations.append("Workflow plan must contain at least one execution step.")
        if not plan.fields:
            violations.append("Workflow plan must specify at least one target field.")

        if plan.target_record_count > 500:
            violations.append(f"Target record count {plan.target_record_count} exceeds maximum platform limit of 500.")

        # 2. Check for suspicious or injection payloads in goal/reasoning
        text_corpus = f"{plan.goal} {' '.join(plan.reasoning)} {' '.join(plan.entities)}"
        for bad_kw in FORBIDDEN_KEYWORDS:
            if bad_kw in text_corpus.lower():
                violations.append(f"Security policy violation: detected forbidden token '{bad_kw}'.")

        # 3. Action allowlisting & dependency integrity
        step_ids = {s.id for s in plan.steps}
        graph: Dict[str, List[str]] = {}

        for step in plan.steps:
            if step.action not in APPROVED_ACTIONS:
                violations.append(
                    f"Step '{step.id}' uses unapproved action '{step.action}'. Must be one of: {sorted(APPROVED_ACTIONS)}"
                )

            if step.type not in APPROVED_STEP_TYPES:
                violations.append(
                    f"Step '{step.id}' uses unapproved type '{step.type}'. Must be one of: {sorted(APPROVED_STEP_TYPES)}"
                )

            graph[step.id] = []
            for dep in step.depends_on:
                if dep not in step_ids:
                    violations.append(f"Step '{step.id}' depends on non-existent step '{dep}'.")
                else:
                    graph[step.id].append(dep)

        # 4. DAG Cycle Detection (DFS)
        visited = {}  # 0 = unvisited, 1 = visiting, 2 = visited

        def has_cycle(node: str) -> bool:
            visited[node] = 1
            for neighbor in graph.get(node, []):
                if visited.get(neighbor) == 1:
                    return True
                if visited.get(neighbor, 0) == 0:
                    if has_cycle(neighbor):
                        return True
            visited[node] = 2
            return False

        for sid in step_ids:
            if visited.get(sid, 0) == 0:
                if has_cycle(sid):
                    violations.append("Cyclic dependency detected in workflow steps. Workflows must be strict Directed Acyclic Graphs (DAG).")
                    break

        # 5. Source security check
        for src in plan.sources:
            if src.target_url:
                is_safe, reason = validate_url_security(src.target_url)
                if not is_safe:
                    violations.append(f"Source '{src.id}' target URL is forbidden: {reason}")

        return len(violations) == 0, violations


policy_engine = PolicyEngine()
