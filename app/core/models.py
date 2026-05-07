"""
Core domain models as dataclasses.
Used by services and repositories to pass typed data instead of raw dicts.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class UsageRecord:
    id: Optional[int] = None
    user_name: str = ""
    start_time: str = ""
    end_time: str = ""
    duration_seconds: int = 0
    created_at: str = ""


@dataclass
class Reservation:
    id: Optional[int] = None
    user_name: str = ""
    date: str = ""
    start_hour: int = 0
    end_hour: int = 0
    created_at: str = ""
    status: str = "active"


@dataclass
class RemoteSession:
    id: Optional[int] = None
    remote_type: str = ""
    start_time: str = ""
    end_time: Optional[str] = None
    duration_seconds: int = 0
    is_active: bool = True
    created_at: str = ""


@dataclass
class AppStatus:
    """Aggregated application status for GUI and Web consumption."""
    computer_status: str = "idle"  # idle | in_use | remote_controlled
    current_user: Optional[str] = None
    timer_start_time: Optional[str] = None
    timer_elapsed_seconds: int = 0
    timer_elapsed_formatted: str = "00:00:00"
    remote_is_active: bool = False
    remote_type: Optional[str] = None
    remote_start_time: Optional[str] = None
    remote_elapsed_seconds: int = 0
    remote_elapsed_formatted: str = "00:00:00"
    today_records: list = field(default_factory=list)
    today_reservations: list = field(default_factory=list)
    timestamp: str = ""
