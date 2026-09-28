from abc import ABC, abstractmethod
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.workflow import Workflow, WorkflowRun


class BaseWorkflowExecutor(ABC):
    @abstractmethod
    async def execute(self, workflow: Workflow, run: WorkflowRun, db: Session):
        """Executes the workflow steps and stores resulting records and evidence."""
        pass
