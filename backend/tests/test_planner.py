import pytest
from app.services.planner.heuristic_planner import DynamicSemanticPlanner


@pytest.mark.asyncio
async def test_dynamic_sponsor_planner():
    planner = DynamicSemanticPlanner()
    prompt = "Find 30 potential sponsors for a college technical fest in Lucknow. Collect company name, industry, website, public business email, phone, location and source. Remove duplicates and validate the results."

    plan = await planner.generate_plan(prompt, target_count=30)

    assert plan.target_record_count == 30
    assert "sponsor" in plan.domain or "event" in plan.domain
    assert len(plan.fields) >= 5

    field_names = [f.name for f in plan.fields]
    assert "company_name" in field_names
    assert "website" in field_names
    assert "public_business_email" in field_names or "business_email" in field_names

    # Check DAG steps
    step_types = [s.type for s in plan.steps]
    assert "input" in step_types
    assert "source_discovery" in step_types
    assert "extraction" in step_types
    assert "validation" in step_types
    assert "deduplication" in step_types
    assert "merge" in step_types
    assert "output" in step_types

    # Verify depends_on forms a valid DAG
    step_ids = {s.id for s in plan.steps}
    for s in plan.steps:
        for dep in s.depends_on:
            assert dep in step_ids, f"Dependency {dep} in step {s.id} is invalid"


@pytest.mark.asyncio
async def test_dynamic_job_planner():
    planner = DynamicSemanticPlanner()
    prompt = "Collect 40 remote AI engineer jobs with salary, company name, apply link and source."

    plan = await planner.generate_plan(prompt, target_count=40)

    assert plan.target_record_count == 40
    assert "recruitment" in plan.domain or "job" in plan.domain

    field_names = [f.name for f in plan.fields]
    assert "job_title" in field_names or "company_name" in field_names
    assert "salary_range" in field_names or "apply_link" in field_names
