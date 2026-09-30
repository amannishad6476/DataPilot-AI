import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import engine, Base, init_db
import app.models  # Ensure all SQLAlchemy models are registered
from app.api import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("datapilot")

# Ensure tables are created on startup
init_db()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database tables...")
    init_db()
    logger.info("Database initialized successfully.")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="DataPilot AI - Autonomous Natural Language to Actionable Data Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware - permits Next.js local dev, Vercel deployments, and configured origins
cors_origins = list(set(settings.CORS_ORIGINS + [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]))

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"^(https?://(localhost|127\.0\.0\.1)(:[0-9]+)?|https://.*\.vercel\.app)$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Mount API routers
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.middleware("http")
async def add_observability_middleware(request: Request, call_next):
    import time
    import uuid
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{duration_ms}ms"
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    from app.core.errors import AppException
    if isinstance(exc, AppException):
        return exc.to_response()

    logger.error(f"Unhandled server exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": str(exc),
                "retryable": False
            }
        }
    )



@app.get("/")
def root():
    return {
        "platform": settings.PROJECT_NAME,
        "tagline": "From Natural Language to Actionable Data",
        "docs_url": "/docs",
        "api_v1": settings.API_V1_STR,
        "status": "operational"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "provider": settings.LLM_PROVIDER}
