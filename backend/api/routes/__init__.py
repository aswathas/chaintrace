"""Aggregate all sub-routers into a single APIRouter."""
from fastapi import APIRouter

from .cluster import router as cluster_router
from .labels import router as labels_router
from .monitor import router as monitor_router
from .profile import router as profile_router
from .report import router as report_router
from .trace import router as trace_router

router = APIRouter()
router.include_router(trace_router)
router.include_router(profile_router)
router.include_router(cluster_router)
router.include_router(monitor_router)
router.include_router(report_router)
router.include_router(labels_router)

__all__ = ["router"]
