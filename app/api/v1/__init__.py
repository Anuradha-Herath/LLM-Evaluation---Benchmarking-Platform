from fastapi import APIRouter
from app.api.v1.health import router as health_router

router_v1 = APIRouter(prefix="/v1")
router_v1.include_router(health_router, tags=["Health"])

__all__ = ["router_v1"]
