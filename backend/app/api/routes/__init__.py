from fastapi import APIRouter
from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.resumes import router as resumes_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(resumes_router)

__all__ = ["api_router"]
