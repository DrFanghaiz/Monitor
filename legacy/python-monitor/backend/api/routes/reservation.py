"""
GET/POST /api/reservations — reservation management.
"""
from fastapi import APIRouter, Depends, HTTPException
from backend.api.deps import get_reservation_service
from backend.api.schemas import ReservationCreateRequest, ReservationListResponse

router = APIRouter(prefix="/api/reservations", tags=["reservations"])


@router.get("", response_model=ReservationListResponse)
def list_reservations(date: str = None, svc=Depends(get_reservation_service)):
    data = svc.get_reservations(date)
    return {"reservations": data}


@router.post("")
def create_reservation(body: ReservationCreateRequest, svc=Depends(get_reservation_service)):
    ok, msg, rid = svc.create_reservation(body.user_name, body.date, body.start_hour, body.end_hour)
    if not ok:
        raise HTTPException(status_code=409, detail=msg)
    return {"success": True, "message": msg, "id": rid}


@router.post("/{reservation_id}/cancel")
def cancel_reservation(reservation_id: int, svc=Depends(get_reservation_service)):
    svc.cancel_reservation(reservation_id)
    return {"success": True}
