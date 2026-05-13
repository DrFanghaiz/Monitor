# Next Instruction for DeepSeek

## Stage

Desktop Shell Final Polish

## Goal

Finish the desktop-shell user experience so the app feels like a normal Windows desktop application.

This stage is a polish/verification stage. Do **not** redesign business pages. Do **not** modify data/repository/service business logic. Do **not** implement edge resize or deep Win32 frameless-window reconstruction.

## Scope

### 1. Fix visible TitleBar text

Files to inspect:

- `frontend/src/components/ui/TitleBar.tsx`
- `desktop/shell.py`

Requirements:

- The title bar should display normal text, for example: `Monitor · 公用机管理系统`.
- Button titles should be normal Chinese:
  - `最小化`
  - `最大化`
  - `关闭`
- Do not leave mojibake/garbled text in visible UI strings.
- If PowerShell displays UTF-8 text incorrectly but the source/browser is correct, document the verification method clearly in `Chat/deepseek_report.md`.

### 2. Verify close cleanup

Files to inspect:

- `frontend/src/components/ui/TitleBar.tsx`
- `frontend/src/hooks/useDesktop.ts`
- `backend/api/routes/window.py`
- `desktop/shell.py`

Requirements:

- Clicking the close button should close the WebView2 window.
- `desktop/shell.py` must execute its `finally` cleanup path:
  - `services.tunnel.stop()`
  - `services.remote_monitor.stop()`
  - `services.web_server.stop()`
  - `app_logger.app_exit()`
  - `release_instance()`
- Do not add force-kill logic.
- After close, starting `python main.py` again should not be blocked by stale `monitor.lock`.

### 3. Verify browser fallback behavior

Files to inspect:

- `desktop/shell.py`
- `frontend/src/hooks/useDesktop.ts`
- `backend/api/routes/window.py`

Requirements:

- Normal browser access to `http://127.0.0.1:8000` should not show the desktop TitleBar.
- Browser access with fake `?desktop=1` should not show a persistent TitleBar and must not be able to control the desktop window.
- Window-control endpoints must remain token-protected.
- If WebView2 fallback opens a browser, document whether it should show the desktop TitleBar or not. Prefer not showing it unless there is a strong reason.

### 4. Improve startup blank-screen experience if simple

Files to inspect:

- `desktop/shell.py`
- `frontend/src/layout/AppShell.tsx`
- global frontend styles if needed

Requirements:

- Avoid long pure-gray/pure-black empty window on startup if a small fix is possible.
- A lightweight loading/splash state is acceptable.
- Do not introduce a large loading framework or redesign the app shell.

### 5. Update status files

Update:

- `Chat/deepseek_report.md`
- `Chat/current_decision.md`
- `Chat/open_issues.md`

Requirements:

- Set `Chat/current_decision.md` status to `WAITING_FOR_REVIEW` when done.
- Remove or mark resolved stale issues from `Chat/open_issues.md`, especially:
  - double-click drag conflict
  - `_window_maximized` drift from the app's maximize button
- Keep genuinely unresolved issues, such as edge resize and webview2 package maturity.

## Verification Checklist

Run or verify:

- `npm run build` from `frontend/`
- Python compile for modified Python files
- `python main.py` opens the shell
- TitleBar text is readable
- Minimize works
- Maximize works
- Close works and cleanup runs
- Drag title area works
- Double-click title area toggles maximize/restore
- Closing and reopening does not fail due to stale single-instance lock

## Report Format

When finished, write `Chat/deepseek_report.md` with:

1. Files modified
2. What was fixed
3. What was verified
4. Remaining known limitations
5. Why this stage is ready for Codex review

