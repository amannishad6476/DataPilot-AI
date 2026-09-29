import logging
from sqlalchemy.orm import Session
from app.config import settings
from app.models.workflow import Workflow
from app.schemas.planner import PlannerOutput
from app.services.planner.openai_provider import OpenAIPlannerProvider
from app.services.planner.gemini_provider import GeminiPlannerProvider
from app.services.planner.heuristic_planner import DynamicSemanticPlanner

logger = logging.getLogger(__name__)


class PlannerService:
    def __init__(self):
        self.heuristic_planner = DynamicSemanticPlanner()

    async def generate_plan(self, prompt: str, target_count: int = 30) -> PlannerOutput:
        provider_name = settings.LLM_PROVIDER.lower()

        # 1. Attempt OpenAI if configured or requested
        if (provider_name in ["openai", "auto"]) and settings.OPENAI_API_KEY:
            try:
                logger.info("Generating workflow plan via OpenAI provider...")
                provider = OpenAIPlannerProvider()
                return await provider.generate_plan(prompt, target_count)
            except Exception as e:
                logger.warning(f"OpenAI provider failed, falling back to dynamic semantic planner: {e}")

        # 2. Attempt Gemini if configured or requested
        if (provider_name in ["gemini", "auto"]) and settings.GEMINI_API_KEY:
            try:
                logger.info("Generating workflow plan via Gemini provider...")
                provider = GeminiPlannerProvider()
                return await provider.generate_plan(prompt, target_count)
            except Exception as e:
                logger.warning(f"Gemini provider failed, falling back to dynamic semantic planner: {e}")

        # 3. Dynamic Semantic Planner (Offline / Zero-Config / Instant)
        logger.info("Generating workflow plan via Dynamic Semantic Planner...")
        return await self.heuristic_planner.generate_plan(prompt, target_count)

    async def create_and_save_workflow(
        self,
        prompt: str,
        target_count: int,
        db: Session,
        tenant_id: str = "tenant_default",
        user_id: str = "usr_local_owner"
    ) -> Workflow:
        from app.services.planner.policy_engine import policy_engine
        from app.core.errors import PolicyViolationError

        plan: PlannerOutput = await self.generate_plan(prompt, target_count)

        # Policy & Safety Validation (Untrusted LLM Boundary)
        is_valid, violations = policy_engine.validate_plan(plan)
        if not is_valid:
            logger.error(f"PolicyEngine rejected generated workflow plan: {violations}")
            raise PolicyViolationError(
                message="AI-generated workflow plan was rejected by the security policy engine.",
                violations=violations
            )

        # Persist to database with audit and ownership boundary
        workflow = Workflow(
            prompt=prompt,
            goal=plan.goal,
            domain=plan.domain,
            entities=plan.entities,
            fields_spec=[f.model_dump() for f in plan.fields],
            sources_spec=[s.model_dump() for s in plan.sources],
            steps_spec=[s.model_dump() for s in plan.steps],
            validation_rules=[r.model_dump() for r in plan.validation_rules],
            deduplication_strategy=plan.deduplication_strategy,
            output_format=plan.output_format,
            reasoning=plan.reasoning,
            tenant_id=tenant_id,
            user_id=user_id,
            workflow_version=1,
            planner_version="2.0.0",
            policy_status="APPROVED"
        )
        db.add(workflow)
        db.commit()
        db.refresh(workflow)
        return workflow


planner_service = PlannerService()
