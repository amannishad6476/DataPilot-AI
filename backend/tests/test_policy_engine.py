import pytest
from app.services.planner.policy_engine import policy_engine
from app.schemas.planner import PlannerOutput, WorkflowStepPlan, FieldSpec, SourceSpec


def make_plan(**kwargs):
    defaults = {
        "goal": "Collect public tech companies",
        "domain": "tech",
        "target_record_count": 25,
        "entities": ["company"],
        "fields": [
            FieldSpec(name="company_name", type="string", required=True),
            FieldSpec(name="website", type="url", required=True),
        ],
        "deduplication_strategy": "fuzzy_match_name_and_domain",
        "sources": [],
        "steps": [
            WorkflowStepPlan(
                id="step_1",
                name="Input Parameters",
                type="input",
                action="ingest_prompt_parameters",
                description="Ingest prompt",
                depends_on=[]
            ),
            WorkflowStepPlan(
                id="step_2",
                name="Extract Entities",
                type="extraction",
                action="extract_entity_records",
                description="Extract records",
                depends_on=["step_1"]
            )
        ]
    }
    defaults.update(kwargs)
    return PlannerOutput(**defaults)


def test_valid_plan_policy():
    plan = make_plan()
    is_valid, violations = policy_engine.validate_plan(plan)
    assert is_valid is True
    assert len(violations) == 0


def test_plan_with_dag_cycle():
    plan = make_plan(
        steps=[
            WorkflowStepPlan(
                id="step_1",
                name="Step 1",
                type="transformation",
                action="normalize_and_clean",
                description="Step 1",
                depends_on=["step_2"]
            ),
            WorkflowStepPlan(
                id="step_2",
                name="Step 2",
                type="transformation",
                action="normalize_and_clean",
                description="Step 2",
                depends_on=["step_1"]
            )
        ]
    )
    is_valid, violations = policy_engine.validate_plan(plan)
    assert is_valid is False
    assert any("cyclic" in v.lower() or "dag" in v.lower() for v in violations)


def test_plan_with_unapproved_action():
    plan = make_plan(
        steps=[
            WorkflowStepPlan(
                id="step_1",
                name="Run Shell",
                type="extraction",
                action="unapproved_shell_exec",
                description="Execute malicious shell",
                depends_on=[]
            )
        ]
    )
    is_valid, violations = policy_engine.validate_plan(plan)
    assert is_valid is False
    assert any("unapproved action" in v.lower() for v in violations)


def test_plan_exceeding_max_records():
    plan = make_plan(target_record_count=1000)
    is_valid, violations = policy_engine.validate_plan(plan)
    assert is_valid is False
    assert any("exceeds maximum platform limit" in v.lower() for v in violations)


def test_plan_with_ssrf_source_url():
    plan = make_plan(
        sources=[
            SourceSpec(
                id="src_1",
                type="public_directory",
                name="Metadata Service",
                purpose="test",
                target_url="http://169.254.169.254/latest/meta-data/"
            )
        ]
    )
    is_valid, violations = policy_engine.validate_plan(plan)
    assert is_valid is False
    assert any("forbidden" in v.lower() for v in violations)


def test_plan_with_forbidden_code_injection():
    plan = make_plan(
        goal="Injecting eval() in prompt",
        reasoning=["We will run eval('import os; os.system()')"]
    )
    is_valid, violations = policy_engine.validate_plan(plan)
    assert is_valid is False
    assert any("forbidden token" in v.lower() for v in violations)
