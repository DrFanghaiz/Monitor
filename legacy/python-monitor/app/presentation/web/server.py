"""
Web server — HTTP API and static dashboard.
Uses injected services (status_service, web_access_service, config) only.
No direct dependency on config/db/remote_monitor/callback modules.
"""
import http.server
import json
import threading
import os
from urllib.parse import urlparse, parse_qs
from pathlib import Path

WEB_DIR = Path(__file__).parent.parent.parent.parent / "web"


def _make_handler(web_access_svc, status_svc):
    """Create a request handler class configured with services."""

    class _StatusAPIHandler(http.server.BaseHTTPRequestHandler):
        """HTTP request handler — all data comes from injected services."""

        def log_message(self, format, *args):
            pass  # silent logging

        def _check_auth(self) -> bool:
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            token = params.get("token", [None])[0]
            return web_access_svc.validate_token(token) if token else False

        def _send_json(self, data, status=200):
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

        def _serve_static(self, filepath: Path, content_type: str):
            if filepath.exists():
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.end_headers()
                with open(filepath, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404)

        def do_GET(self):
            parsed = urlparse(self.path)
            path = parsed.path.rstrip("/") or "/"

            if path in ("/", ""):
                self._serve_static(WEB_DIR / "index.html", "text/html; charset=utf-8")
                return

            if path == "/api/status":
                if not self._check_auth():
                    self._send_json({"error": "未授权"}, 401)
                    return

                data = status_svc.get_full_status()
                self._send_json(data)
                return

            self.send_error(404)

        def do_POST(self):
            parsed = urlparse(self.path)
            path = parsed.path.rstrip("/") or "/"

            if path == "/api/auth":
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length)
                try:
                    req = json.loads(body)
                    password = req.get("password", "")
                except json.JSONDecodeError:
                    self._send_json({"success": False, "message": "无效请求"}, 400)
                    return

                token = web_access_svc.authenticate(password)
                if token:
                    self._send_json({"success": True, "token": token})
                else:
                    self._send_json({"success": False, "message": "密码错误"}, 401)
                return

            self.send_error(404)

        def do_OPTIONS(self):
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()

    return _StatusAPIHandler


class WebServer:
    """Web server manager — uses injected services, no legacy module imports."""

    def __init__(self, config, web_access_svc, status_svc):
        self._config = config
        self._web_access = web_access_svc
        self._status = status_svc
        self._server = None
        self._thread = None
        self._running = False

    def start(self):
        if self._running:
            return
        if not self._config.get("web_server_enabled", True):
            return

        port = self._config.get("web_server_port", 8080)
        handler_class = _make_handler(self._web_access, self._status)
        self._running = True
        self._thread = threading.Thread(
            target=self._run_server, args=(port, handler_class), daemon=True
        )
        self._thread.start()

    def stop(self):
        self._running = False
        if self._server:
            try:
                self._server.shutdown()
            except Exception:
                pass

    def _run_server(self, port, handler_class):
        try:
            self._server = http.server.HTTPServer(("0.0.0.0", port), handler_class)
            self._server.serve_forever()
        except OSError as e:
            self._running = False
        except Exception as e:
            self._running = False

    def get_port(self) -> int:
        return self._config.get("web_server_port", 8080)
