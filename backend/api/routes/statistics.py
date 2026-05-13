"""
GET /api/statistics/* — usage statistics data.
"""
from fastapi import APIRouter, Depends
from backend.api.deps import get_statistics_service

router = APIRouter(prefix="/api/statistics", tags=["statistics"])


@router.get("/users")
def statistics_users(filter_mode: str = "all", svc=Depends(get_statistics_service)):
    data = svc.get_user_stats(filter_mode)
    return {"users": data}


@router.get("/hourly")
def statistics_hourly(svc=Depends(get_statistics_service)):
    data = svc.get_hourly_stats()
    return {"hourly": data}


@router.get("/daily")
def statistics_daily(days: int = 30, svc=Depends(get_statistics_service)):
    data = svc.get_daily_stats(days)
    return {"daily": data}


@router.get("/distribution")
def statistics_distribution(filter_mode: str = "all", svc=Depends(get_statistics_service)):
    data = svc.get_user_distribution(filter_mode)
    return {"distribution": data}
