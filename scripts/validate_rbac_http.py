from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
OWNER = "http-owner"
OWNER_PASSWORD = "HttpOwnerPassword-2026!"
RESEARCHER_PASSWORD = "HttpResearcherPassword-2026!"


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="opportunity-radar-rbac-http-") as temp:
        db = Path(temp) / "rbac.db"
        env = os.environ.copy()
        env.update({
            "DATABASE_URL": f"sqlite:///{db}",
            "APP_ENV": "test",
            "AUTH_MODE": "rbac",
            "ALLOW_LEGACY_API_KEY": "false",
            "PYTHONPATH": str(BACKEND),
        })
        subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=BACKEND, env=env, check=True, stdout=subprocess.DEVNULL)
        subprocess.run([sys.executable, "-m", "app.admin_cli", "create-user", OWNER, "--role", "OWNER", "--password", OWNER_PASSWORD], cwd=BACKEND, env=env, check=True, stdout=subprocess.DEVNULL)
        port = free_port(); base = f"http://127.0.0.1:{port}"
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
            cwd=BACKEND, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, start_new_session=True,
        )
        try:
            deadline = time.time() + 15
            while time.time() < deadline:
                try:
                    if httpx.get(base + "/health", timeout=1).status_code == 200: break
                except Exception: pass
                time.sleep(0.15)
            else: raise RuntimeError("uvicorn did not start")

            with httpx.Client(base_url=base, timeout=10) as client:
                anonymous = client.get("/api/v1/dashboard")
                assert anonymous.status_code == 401
                login = client.post("/api/v1/auth/login", json={"username": OWNER, "password": OWNER_PASSWORD})
                assert login.status_code == 200
                assert client.cookies.get("or_session") and client.cookies.get("or_csrf")
                dashboard = client.get("/api/v1/dashboard")
                assert dashboard.status_code == 200
                assert "Content-Security-Policy" in dashboard.headers and dashboard.headers.get("X-Request-ID")
                blocked = client.post("/api/v1/watch-keywords", json={"keyword": "HTTP CSRF", "priority": 3})
                assert blocked.status_code == 403
                csrf = client.cookies.get("or_csrf")
                headers = {"X-CSRF-Token": csrf}
                created = client.post("/api/v1/watch-keywords", headers=headers, json={"keyword": "HTTP CSRF", "priority": 3})
                assert created.status_code == 200
                user = client.post("/api/v1/admin/users", headers=headers, json={"username": "http-researcher", "password": RESEARCHER_PASSWORD, "role": "RESEARCHER", "enabled": True})
                assert user.status_code == 200
                metrics = client.get("/metrics")
                assert metrics.status_code == 200
                assert "opportunity_radar_probe_tasks_active" in metrics.text

            with httpx.Client(base_url=base, timeout=10) as researcher:
                login = researcher.post("/api/v1/auth/login", json={"username": "http-researcher", "password": RESEARCHER_PASSWORD})
                assert login.status_code == 200
                csrf = researcher.cookies.get("or_csrf")
                headers = {"X-CSRF-Token": csrf}
                assert researcher.post("/api/v1/watch-keywords", headers=headers, json={"keyword": "researcher write", "priority": 2}).status_code == 200
                assert researcher.post("/api/v1/import", headers=headers, json={"records": []}).status_code == 403
                assert researcher.post("/api/v1/alerts/evaluate", headers=headers).status_code == 403
                assert researcher.post("/api/v1/alerts/run-pending", headers=headers).status_code == 403
                assert researcher.get("/api/v1/workers").status_code == 403
                assert researcher.get("/api/v1/probes/tasks").status_code == 403
                assert researcher.get("/api/v1/collection-runs").status_code == 403
                assert researcher.get("/api/v1/admin/users").status_code == 403
        finally:
            try: os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError: pass
            try: process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL); process.wait(timeout=5)
            if process.returncode not in {0, -signal.SIGTERM, -signal.SIGKILL}:
                stderr = process.stderr.read() if process.stderr else ""
                raise RuntimeError(f"uvicorn failed: {process.returncode}\n{stderr}")
    print("RBAC_HTTP_E2E_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
