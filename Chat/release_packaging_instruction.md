# Release Packaging Verification Instruction for DeepSeek

## Stage

Release Packaging Verification

## Goal

Verify that the current React + FastAPI + WebView2 desktop shell can be packaged and launched as a Windows `.exe`.

This stage is about packaging, runtime paths, bundled assets, and launch verification. Do **not** add new features. Do **not** redesign UI. Do **not** refactor architecture unless a packaging blocker requires a minimal fix.

## Required Checks

### 1. Frontend production build

Run:

```bash
cd frontend
npm run build
```

Verify:

- `frontend/dist/index.html` exists.
- `frontend/dist/assets/` exists.
- The built app is the current polished UI.

### 2. Python dependency check

Verify the active environment has at least:

- `fastapi`
- `uvicorn`
- `pydantic`
- `webview2`
- `pywin32`
- `customtkinter`
- `pystray`
- `matplotlib`
- `pillow`
- `bcrypt`

If dependency checks fail, document exact missing packages and the install command. Do not silently ignore missing dependencies.

### 3. PyInstaller spec review

Inspect:

- `MonitorApp.spec`
- `build_exe.py`
- `environment.yml`

Verify the packaged app includes required runtime files:

- `frontend/dist`
- `web`
- `config.json`
- any required static assets
- required Python modules for FastAPI/uvicorn/webview2/pywin32

Pay special attention to hidden imports for:

- `uvicorn`
- `uvicorn.logging`
- `uvicorn.loops`
- `uvicorn.loops.auto`
- `uvicorn.protocols`
- `uvicorn.protocols.http`
- `uvicorn.protocols.http.auto`
- `uvicorn.protocols.websockets`
- `fastapi`
- `pydantic`
- `webview2`
- `win32gui`
- `win32con`

### 4. Build exe

Use the existing project build mechanism if possible:

```bash
python build_exe.py
```

or the documented PyInstaller command if `build_exe.py` delegates to it.

Verify:

- Build finishes without errors.
- `dist/` contains the expected `.exe` or app folder.
- Build output is not accidentally using stale files.

### 5. Runtime verification

Launch the generated executable.

Verify:

- App opens the WebView2 desktop shell.
- No immediate crash.
- Frontend loads from bundled `frontend/dist`.
- FastAPI starts internally.
- TitleBar appears in desktop shell.
- Minimize / maximize / close work.
- Drag title area works.
- Double-click title area toggles maximize/restore.
- Close performs cleanup.
- Reopening the exe does not fail due to stale `monitor.lock`.

### 6. Path/data verification

Verify packaged runtime handles:

- `monitor.db`
- `config.json`
- backup folder
- WebView2 cache folder
- log file
- `cloudflared.exe` missing case should remain a non-fatal warning unless existing behavior requires otherwise.

If the executable writes runtime data into the unpacked temp directory or a read-only package path, identify it clearly and propose a minimal path fix.

## Output Files To Update

Update:

- `Chat/deepseek_report.md`
- `Chat/current_decision.md`
- `Chat/open_issues.md` if packaging creates or resolves issues

When done:

- Set `Chat/current_decision.md` to `WAITING_FOR_REVIEW`.
- Include exact build command used.
- Include generated exe path.
- Include any runtime errors or warnings.

## Report Format

Write `Chat/deepseek_report.md` with:

1. Build command used
2. Files changed, if any
3. Frontend build result
4. Python dependency check result
5. PyInstaller/spec review result
6. Exe output path
7. Runtime verification result
8. Remaining packaging risks
9. Whether this stage is ready for Codex review

