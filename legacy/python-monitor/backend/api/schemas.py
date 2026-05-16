"""
Pydantic schemas — aligned with actual service return structures.
Field names and types match timer_service / status_service / statistics_service exactly.
"""
from pydantic import BaseModel
from typing import Optional, List, Any


# ---- Timer ----

class TimerStartRequest(BaseModel):
    user_name: str


class TimerStopResponse(BaseModel):
    success: bool = True
    user_name: str
    duration_seconds: int
    duration_formatted: str
    elapsed_formatted: str


class TimerStateResponse(BaseModel):
    is_running: bool
    current_user: Optional[str] = None
    start_time: Optional[str] = None
    elapsed_seconds: int = 0
    elapsed_formatted: str = "00:00:00"


# ---- History ----

class HistoryRecord(BaseModel):
    id: int
    user_name: str
    start_time: str
    end_time: str
    duration_seconds: int
    created_at: Optional[str] = ""


class HistoryResponse(BaseModel):
    records: list = []


# ---- Statistics ----

class UserStatItem(BaseModel):
    user_name: str
    total_seconds: float
    last_seen: Optional[str] = None


class UserStatsResponse(BaseModel):
    users: list = []


# ---- Status ----

class RemoteControlState(BaseModel):
    """Matches remote_monitor.get_status() exactly."""
    is_remote: bool = False
    remote_type: Optional[str] = None
    start_time: Optional[str] = None
    elapsed_seconds: int = 0
    elapsed_formatted: str = "00:00:00"


class LocalUseState(BaseModel):
    """Matches timer_service.get_state() exactly."""
    current_user: Optional[str] = None
    start_time: Optional[str] = None
    elapsed_seconds: int = 0
    elapsed_formatted: str = "00:00:00"


class StatusResponse(BaseModel):
    """Matches status_service.get_full_status() exactly."""
    timestamp: str
    computer_status: str
    local_use: dict
    remote_control: dict
    today_records: list = []
    today_reservations: list = []


# ---- Reservation ----

class ReservationCreateRequest(BaseModel):
    user_name: str
    date: str
    start_hour: int
    end_hour: int


class ReservationItem(BaseModel):
    id: int
    user_name: str
    date: str
    start_hour: int
    end_hour: int
    status: str


class ReservationListResponse(BaseModel):
    reservations: list = []


# ---- Settings ----

class AdminPasswordRequest(BaseModel):
    old_password: str = ""
    new_password: str


class WebPasswordRequest(BaseModel):
    new_password: str


class SettingsResponse(BaseModel):
    web_server_port: int = 8080
    web_server_enabled: bool = True
    tunnel_enabled: bool = True
    tunnel_mode: str = "cloudflared"
    auto_backup: bool = True
    backup_retention_days: int = 30
    remote_monitor_enabled: bool = True


class BackupItem(BaseModel):
    name: str
    path: str
    size: int
    created: str
    is_manual: bool = False


class BackupListResponse(BaseModel):
    backups: list = []
