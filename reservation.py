"""
Compatibility re-export — delegates to frames.reservation_frame.
TODO Phase 5: remove this file; all imports should use the frames module directly.
"""
from app.presentation.desktop.frames.reservation_frame import ReservationFrame

__all__ = ["ReservationFrame"]
