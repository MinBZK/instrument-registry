from fastapi import APIRouter
from task_registry.api.routes import health, instruments, urns

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(instruments.router, prefix="/instruments", tags=["instruments"])
api_router.include_router(urns.router, prefix="/urns", tags=["urns"])
