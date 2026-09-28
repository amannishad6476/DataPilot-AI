from fastapi import APIRouter
from app.api.workflows import router as workflows_router
from app.api.execution import router as execution_router
from app.api.datasets import router as datasets_router
from app.api.connectors import router as connectors_router

api_router = APIRouter()
api_router.include_router(workflows_router)
api_router.include_router(execution_router)
api_router.include_router(datasets_router)
api_router.include_router(connectors_router)
