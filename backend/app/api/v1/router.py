"""
API v1 router — aggregates all endpoint sub-routers.
"""

from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.books import router as books_router
from app.api.v1.endpoints.chat import router as chat_router
from app.api.v1.endpoints.libraries import router as libraries_router
from app.api.v1.endpoints.shelves import router as shelves_router

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(auth_router)
v1_router.include_router(libraries_router)
v1_router.include_router(shelves_router)
v1_router.include_router(books_router)
v1_router.include_router(chat_router)
