"""
GET/POST /api/settings — system settings management.
All infrastructure access goes through services, not direct imports.
"""
from fastapi import APIRouter, Depends, HTTPException
from backend.api.deps import get_config, get_password_manager, get_backup_service
from backend.api.schemas import (
    AdminPasswordRequest, WebPasswordRequest, SettingsResponse, BackupListResponse
)

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
def get_settings(cfg=Depends(get_config)):
    return {
        "web_server_port": cfg.get("web_server_port", 8080),
        "web_server_enabled": cfg.get("web_server_enabled", True),
        "tunnel_enabled": cfg.get("tunnel_enabled", True),
        "tunnel_mode": cfg.get("tunnel_mode", "cloudflared"),
        "auto_backup": cfg.get("auto_backup", True),
        "backup_retention_days": cfg.get("backup_retention_days", 30),
        "remote_monitor_enabled": cfg.get("remote_monitor_enabled", True),
    }


@router.post("/password/admin")
def change_admin_password(body: AdminPasswordRequest, pwd_mgr=Depends(get_password_manager)):
    if not pwd_mgr.change_admin_password(body.old_password, body.new_password):
        raise HTTPException(status_code=403, detail="current password is incorrect")
    return {"success": True}


@router.post("/password/web")
def change_web_password(body: WebPasswordRequest, cfg=Depends(get_config)):
    cfg.set("web_server_password", body.new_password)
    return {"success": True}


@router.post("/backup")
def create_backup(backup_svc=Depends(get_backup_service)):
    try:
        path = backup_svc.create_backup()
        return {"success": True, "path": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backups", response_model=BackupListResponse)
def list_backups(backup_svc=Depends(get_backup_service)):
    backups = backup_svc.get_backup_list()
    return {"backups": backups}
