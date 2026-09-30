from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.app.config import get_settings, Settings
from backend.app.db.session import get_db
from backend.app.schemas import HealthResponse

router = APIRouter(prefix="", tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="System Health & Status Check",
    description="Verifies API responsiveness, database connectivity, and configuration metadata.",
)
def check_health(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "degraded",
                "version": settings.app_version,
                "database": db_status,
                "environment": settings.app_env,
                "llm_provider": settings.llm_provider,
            },
        )

    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        database=db_status,
        environment=settings.app_env,
        llm_provider=settings.llm_provider,
    )
