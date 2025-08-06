from fastapi import APIRouter
from .endpoints import history, auth


api_router = APIRouter()
api_router.include_router(history.router, prefix="/history", tags=["history"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

