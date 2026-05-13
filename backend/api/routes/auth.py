"""
POST /api/auth — web dashboard authentication.
"""
from fastapi import APIRouter, Depends, HTTPException
from backend.api.deps import get_config

router = APIRouter(prefix="/api", tags=["auth"])


@router.post("/auth")
def authenticate(body: dict, cfg=Depends(get_config)):
    password = body.get("password", "")
    stored = cfg.get("web_server_password", "123456")
    if password == stored:
        return {"success": True, "token": "desktop-session"}
    raise HTTPException(status_code=401, detail="密码错误")
