# Monitor — 公用机管理系统

Shared/public computer time management with remote control detection.

## Quick Start

```bash
# 1. Install Python dependencies
conda env create -f environment.yml
conda activate monitor

# 2. Build frontend
cd frontend && npm install && npm run build && cd ..

# 3. Start (default: new React UI in native window)
python main.py
```

## Startup Modes

| Command | Mode | UI | Description |
|---------|------|-----|-------------|
| `python main.py` | **production** | React in WebView2 window | Default main path. API on :8000, static files served. |
| `python main.py --dev` | **development** | React in WebView2 window | Loads from Vite dev server (:5173). Hot reload. |
| `python main.py --legacy` | **legacy** | customtkinter desktop | Original desktop UI. Full feature parity. |
| `python timer.py` | **legacy standalone** | customtkinter desktop | Same as `--legacy`, independent entry point. |

### Development Mode

```bash
# Terminal 1: start Vite dev server
cd frontend && npm run dev

# Terminal 2: start desktop shell
python main.py --dev
```

## Prerequisites

- Python 3.10+
- Node.js 18+
- Microsoft Edge WebView2 Runtime (included in Windows 10/11)
- conda (recommended) or pip

### Missing `frontend/dist`?

```
ERROR: frontend build not found.
Run:  cd frontend && npm run build
Then retry:  python main.py
Or use dev mode:  python main.py --dev
```

### WebView2 not available?

The shell falls back to opening the frontend in your default browser.

## Architecture

```
python main.py
  └── bootstrap()
        ├── ConnectionManager + migration
        ├── ServiceContainer (shared by desktop + API)
        │     ├── timer_service, reservation_service, statistics_service
        │     ├── status_service (unified state aggregator)
        │     ├── remote_monitor_service, tunnel_service
        │     └── web_server (legacy dashboard, port 8080)
        └── desktop.shell.launch()
              ├── FastAPI (port 8000)
              │     ├── /api/status, /api/timer/*, /api/statistics/*
              │     ├── /api/reservations/*, /api/settings/*
              │     └── StaticFiles: frontend/dist (production)
              └── WebView2 window → React SPA
```

```
frontend/src/
  ├── pages/        Dashboard, Timer, History, Statistics, Reservation, Settings
  ├── layout/       AppShell (3 layout modes), Sidebar
  ├── components/   ui/ (Card, Button, StatusBadge), charts/ (ECharts theme), timer/
  ├── services/     API client → /api/*
  ├── hooks/        React Query wrappers
  └── theme/        Design tokens (CSS vars), Framer Motion variants
```

## Legacy Modules

These modules are retained for backward compatibility. New code should use the service layer.

| Module | Status | Replacement |
|--------|--------|-------------|
| `database.py` | Facade over repositories | `app/domain/repositories/` |
| `remote_monitor.py` | Wrapped by service | `app/domain/services/remote_monitor_service.py` |
| `tunnel.py` | Wrapped by service | `app/domain/services/tunnel_service.py` |
| `web_server.py` | Compatibility proxy | `app/presentation/web/server.py` |
| `timer.py` | Legacy entry point | `main.py` |
| `reservation.py` | Re-export wrapper | `app/presentation/desktop/frames/` |
| `password_manager.py` | Wrapped in container | `app/infrastructure/security/` |
| `app/presentation/desktop/` | Legacy customtkinter UI | React frontend |
