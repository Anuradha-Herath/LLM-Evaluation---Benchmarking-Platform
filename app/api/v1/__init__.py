from fastapi import APIRouter

from app.api.v1.benchmarks import router as benchmarks_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.evaluations import router as evaluations_router
from app.api.v1.health import router as health_router
from app.api.v1.regression_tests import router as regression_router

router_v1 = APIRouter(prefix="/v1")
router_v1.include_router(health_router, tags=["Health"])
router_v1.include_router(evaluations_router)
router_v1.include_router(benchmarks_router)
router_v1.include_router(regression_router)
router_v1.include_router(dashboard_router)

__all__ = ["router_v1"]
