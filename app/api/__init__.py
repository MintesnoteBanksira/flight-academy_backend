"""
API Routes
"""
from fastapi import APIRouter
from .auth import router as auth_router
from .users import router as users_router
from .videos import router as videos_router
from .categories import router as categories_router
from .admin import router as admin_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(videos_router)
api_router.include_router(categories_router)
api_router.include_router(admin_router)
