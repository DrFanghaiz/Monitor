# Open Issues

## Desktop Shell

1. **Edge resize not supported** — `webview2.Window` has no runtime resize API. Would need Win32 `SetWindowPos` + `WM_SIZING`, high complexity. Not planned.

2. **Restore button not exposed** — `webview2` does not report current maximized state. Only toggle-maximize (double-click) is available. No standalone restore button in TitleBar.

3. **Window state tracking cannot sync system-level changes** — Win+Up, taskbar menu, and snap layouts change window state without updating `_window_maximized`. Calling maximize on already-maximized window is a no-op, so drift is harmless.

4. **`webview2` package maturity** — `webview2==0.0.4` is community-maintained. `pywebview` would be preferable but requires `pythonnet` which needs C++ build tools.

## Legacy Path

5. **`BackupService` not in unified ServiceContainer** — Route dependency removed, but service is created ad-hoc in `deps.py`. Low priority.

6. **`database.py` still exists as facade** — All access goes through repositories, but facade marked `TODO remove`. Can be cleaned up when legacy customtkinter UI is fully retired.

## Resolved

- Double-click drag conflict — fixed with mousemove-threshold (4px)
- `_window_maximized` drift from app's maximize button — fixed with `global` keyword
