"""
POST /api/window/* — desktop window controls.
Token-authenticated: every action endpoint verifies the per-session token.
A browser cannot guess the token, so direct POST calls are rejected.
"""
import queue
from fastapi import APIRouter, Query, HTTPException

router = APIRouter(prefix="/api/window", tags=["window"])

_action_queue = None
_desktop_token = ""


def register_window_routes(app):
    global _action_queue, _desktop_token
    import desktop.shell as _shell
    _action_queue = _shell._window_actions
    _desktop_token = _shell._desktop_token
    app.include_router(router)


def _verify(token: str):
    if token != _desktop_token:
        raise HTTPException(status_code=403, detail="invalid desktop token")


def _push(action: str):
    if _action_queue is not None:
        _action_queue.put(action)


@router.post("/minimize")
def minimize(token: str = Query("")):
    _verify(token)
    _push("minimize")
    return {"ok": True}


@router.post("/maximize")
def maximize(token: str = Query("")):
    _verify(token)
    _push("maximize")
    return {"ok": True}


@router.post("/close")
def close_window(token: str = Query("")):
    _verify(token)
    _push("close")
    return {"ok": True}


@router.post("/toggle-maximize")
def toggle_maximize(token: str = Query("")):
    _verify(token)
    _push("toggle_maximize")
    return {"ok": True}


@router.post("/drag")
def begin_drag(token: str = Query("")):
    _verify(token)
    _push("drag")
    return {"ok": True}


@router.get("/mode")
def window_mode(token: str = Query("")):
    return {"desktop": bool(token) and token == _desktop_token}
