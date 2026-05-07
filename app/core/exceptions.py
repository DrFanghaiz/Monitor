"""
Business exceptions for the Monitor application.
"""


class MonitorError(Exception):
    """Base exception for all Monitor application errors."""


class ReservationConflictError(MonitorError):
    """Raised when a reservation time slot conflicts with an existing one."""


class AuthenticationError(MonitorError):
    """Raised when password verification fails."""


class ConfigError(MonitorError):
    """Raised when configuration is invalid or missing."""
