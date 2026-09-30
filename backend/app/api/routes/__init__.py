from fastapi import APIRouter
from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.resumes import router as resumes_router
from backend.app.api.routes.jobs import router as jobs_router
from backend.app.api.routes.skills import router as skills_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(resumes_router)
api_router.include_router(jobs_router)
api_router.include_router(skills_router)

__all__ = ["api_router"]
