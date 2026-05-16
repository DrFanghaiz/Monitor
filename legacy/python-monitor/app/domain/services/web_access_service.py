"""
Web access service — handles authentication, token management.
Decoupled from HTTP handler details.
"""
import uuid
from datetime import datetime


class WebAccessService:
    """Manages web dashboard authentication and token lifecycle."""

    def __init__(self, config):
        self._config = config
        self._active_tokens = {}

    def authenticate(self, password: str) -> str | None:
        """Verify password and return a new token, or None if wrong password."""
        stored = self._config.get("web_server_password", "123456")
        if password == stored:
            token = str(uuid.uuid4())
            self._active_tokens[token] = datetime.now()
            return token
        return None

    def validate_token(self, token: str) -> bool:
        """Check if a token is still valid."""
        return token in self._active_tokens

    def revoke_token(self, token: str):
        """Revoke a token."""
        self._active_tokens.pop(token, None)
