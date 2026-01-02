"""
API v1 router - aggregates all endpoint routers.
"""

from fastapi import APIRouter

from .auth import router as auth_router
from .cases import router as cases_router
from .submissions import router as submissions_router
from .admin import router as admin_router
from .unlock import router as unlock_router
from .challenges import router as challenges_router


api_router = APIRouter()

# Include all routers
api_router.include_router(auth_router)
api_router.include_router(cases_router)
api_router.include_router(submissions_router)
api_router.include_router(admin_router)
api_router.include_router(unlock_router)
api_router.include_router(challenges_router)
