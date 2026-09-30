import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import get_settings
from backend.app.db.session import init_db
from backend.app.api.routes import api_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event handler: initializes DB and local directories on startup."""
    # Ensure uploads directory exists
    os.makedirs(settings.upload_dir, exist_ok=True)
    # Initialize DB tables
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "P_101: LLM-Based Resume Screening System — An AI-assisted decision-support "
        "platform featuring hybrid multi-layer scoring, verifiable evidence citations, "
        "skill-gap analysis, and bias-reduction masked screening."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
def root():
    """Root endpoint welcoming clients and directing to documentation."""
    return {
        "project": settings.app_name,
        "version": settings.app_version,
        "docs_url": "/docs",
        "api_v1_prefix": "/api/v1",
        "health_check": "/api/v1/health",
    }
