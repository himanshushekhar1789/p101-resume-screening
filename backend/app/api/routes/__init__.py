from fastapi import APIRouter
from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.resumes import router as resumes_router
from backend.app.api.routes.jobs import router as jobs_router
from backend.app.api.routes.skills import router as skills_router
from backend.app.api.routes.matching import router as matching_router
from backend.app.api.routes.scoring import router as scoring_router
from backend.app.api.routes.gaps import router as gaps_router
from backend.app.api.routes.explanations import router as explanations_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(resumes_router)
api_router.include_router(jobs_router)
api_router.include_router(skills_router)
api_router.include_router(matching_router)
api_router.include_router(scoring_router)
api_router.include_router(gaps_router)
api_router.include_router(explanations_router)

__all__ = ["api_router"]


