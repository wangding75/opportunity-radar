from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
PASSWORD = "ReviewE2E-Password-2026!"
USERNAME = "review-owner"


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_health(url: str, timeout: float = 15.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.15)
    raise RuntimeError("uvicorn did not become healthy")


def run_checked(args: list[str], env: dict[str, str]) -> None:
    subprocess.run(args, cwd=BACKEND, env=env, check=True, stdout=subprocess.DEVNULL)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="opportunity-radar-browser-") as temp:
        db_path = Path(temp) / "browser.db"
        env = os.environ.copy()
        env.update({
            "DATABASE_URL": f"sqlite:///{db_path}",
            "APP_ENV": "test",
            "AUTH_MODE": "rbac",
            "ALLOW_LEGACY_API_KEY": "false",
            "PYTHONPATH": str(BACKEND),
        })
        run_checked([sys.executable, "-m", "alembic", "upgrade", "head"], env)
        run_checked([sys.executable, "-m", "app.admin_cli", "create-user", USERNAME, "--role", "OWNER", "--password", PASSWORD], env)

        port = free_port()
        health_base = f"http://127.0.0.1:{port}"
        base = f"http://opportunity-radar.test:{port}"
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
            cwd=BACKEND,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        try:
            wait_health(health_base + "/health")
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True, executable_path="/usr/bin/chromium", args=["--no-sandbox", "--host-resolver-rules=MAP opportunity-radar.test 127.0.0.1", "--no-proxy-server"])
                context = browser.new_context()
                page = context.new_page()
                page_errors: list[str] = []
                console_errors: list[str] = []
                page.on("pageerror", lambda exc: page_errors.append(str(exc)))
                page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

                response = page.goto(base + "/", wait_until="networkidle")
                assert response and response.ok
                page.get_by_test_id("login-panel").wait_for(state="visible")
                assert page.evaluate("localStorage.length") == 0

                page.get_by_test_id("login-username").fill(USERNAME)
                page.get_by_test_id("login-password").fill(PASSWORD)
                page.get_by_test_id("login-submit").click()
                page.locator("#appViews").wait_for(state="visible")
                page.locator("#currentUser").wait_for(state="visible")
                assert USERNAME in page.locator("#currentUser").inner_text()
                assert page.evaluate("localStorage.length") == 0

                cookies = {item["name"]: item for item in context.cookies()}
                assert cookies["or_session"]["httpOnly"] is True
                assert cookies["or_csrf"]["httpOnly"] is False
                assert cookies["or_session"]["sameSite"] == "Strict"

                page.get_by_role("button", name="关注词").click()
                watch_input = page.get_by_placeholder("新增长期关注关键词，例如：AI短剧、短剧出海")
                watch_input.fill("AI视频自动化 E2E")
                page.get_by_role("button", name="加入监控").click()
                page.locator("#watchRows").get_by_text("AI视频自动化 E2E", exact=True).wait_for()

                # OWNER should see admin-only operations; session logout must remove it.
                assert page.get_by_role("button", name="运行").is_visible()
                page.get_by_test_id("logout").click()
                page.get_by_test_id("login-panel").wait_for(state="visible")
                cookies = {item["name"]: item for item in context.cookies()}
                assert "or_session" not in cookies

                browser.close()
                assert not page_errors, f"page errors: {page_errors}"
                # Chromium may emit a network error for the expected unauthenticated /me
                # during logout/bootstrap; JS/CSP errors are not allowed.
                unsafe = [e for e in console_errors if "Content Security Policy" in e or "Uncaught" in e]
                assert not unsafe, f"browser console errors: {unsafe}"
        finally:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
            if process.returncode not in {0, -signal.SIGTERM, -signal.SIGKILL}:
                stderr = process.stderr.read() if process.stderr else ""
                raise RuntimeError(f"uvicorn exited unexpectedly: {process.returncode}\n{stderr}")
    print("BROWSER_RBAC_E2E_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
