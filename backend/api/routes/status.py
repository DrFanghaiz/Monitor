"""
GET /api/status — aggregated system status.
"""
from fastapi import APIRouter, Depends
from backend.api.deps import get_status_service
from backend.api.schemas import StatusResponse

router = APIRouter(prefix="/api", tags=["status"])


@router.get("/status", response_model=StatusResponse)
def get_status(svc=Depends(get_status_service)):
    return svc.get_full_status()
