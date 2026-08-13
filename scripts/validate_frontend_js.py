from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
html_path = ROOT / "backend" / "app" / "static" / "index.html"
html = html_path.read_text(encoding="utf-8")

# Product CSP deliberately forbids inline JavaScript. Keep that contract testable.
inline = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", html, flags=re.I | re.S)
if any(chunk.strip() for chunk in inline):
    raise SystemExit("inline executable JavaScript is forbidden by product CSP")
if re.search(r"\sonclick\s*=", html, flags=re.I):
    raise SystemExit("inline onclick handler is forbidden by product CSP")
if "localStorage" in html:
    raise SystemExit("browser credential state must not use localStorage")

files = [ROOT / "backend" / "app" / "static" / "js" / "main.js", ROOT / "backend" / "app" / "static" / "js" / "client.js"]
for path in files:
    if not path.exists():
        raise SystemExit(f"compiled frontend module missing: {path}")
    subprocess.run(["node", "--check", str(path)], check=True)
    text = path.read_text(encoding="utf-8")
    if "X-Opportunity-Radar-Key" in text or "localStorage" in text:
        raise SystemExit(f"legacy browser API-key storage/header found in {path}")
print("FRONTEND_JS_PASS modules=2 csp_inline_handlers=0 local_storage_credentials=0")
