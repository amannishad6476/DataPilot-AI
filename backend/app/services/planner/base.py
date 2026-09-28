from abc import ABC, abstractmethod
from app.schemas.planner import PlannerOutput


class BasePlannerProvider(ABC):
    @abstractmethod
    async def generate_plan(self, prompt: str, target_count: int = 30) -> PlannerOutput:
        """Takes a natural language prompt and produces a validated PlannerOutput."""
        pass
