"""
POST /api/timer/start, POST /api/timer/stop,
GET /api/timer/state, GET /api/timer/history,
DELETE /api/timer/history/{id}, POST /api/timer/history/delete-batch.
"""
from fastapi import APIRouter, Depends, HTTPException
from backend.api.deps import get_timer_service
from backend.api.schemas import (
    TimerStartRequest, TimerStopResponse, TimerStateResponse, HistoryResponse
)

router = APIRouter(prefix="/api/timer", tags=["timer"])


@router.post("/start")
def timer_start(body: TimerStartRequest, svc=Depends(get_timer_service)):
    ok = svc.start_timer(body.user_name)
    if not ok:
        raise HTTPException(status_code=400, detail="failed to start timer")
    return {"success": True, "message": f"计时已开始: {body.user_name}"}


@router.post("/stop", response_model=TimerStopResponse)
def timer_stop(svc=Depends(get_timer_service)):
    if not svc.is_running:
        raise HTTPException(status_code=400, detail="timer is not running")
    result = svc.stop_timer()
    if result is None:
        raise HTTPException(status_code=400, detail="failed to stop timer")
    return {"success": True, **result}


@router.get("/state", response_model=TimerStateResponse)
def timer_state(svc=Depends(get_timer_service)):
    return svc.get_state()


@router.get("/history", response_model=HistoryResponse)
def timer_history(filter_mode: str = "all", search: str = "", svc=Depends(get_timer_service)):
    records = svc.get_history(filter_mode, search)
    return {"records": records}


@router.delete("/history/{record_id}")
def delete_history_record(record_id: int, svc=Depends(get_timer_service)):
    svc.delete_record(record_id)
    return {"success": True}


@router.post("/history/delete-batch")
def delete_history_batch(body: dict, svc=Depends(get_timer_service)):
    ids = body.get("ids", [])
    svc.delete_records(ids)
    return {"success": True, "deleted": len(ids)}
