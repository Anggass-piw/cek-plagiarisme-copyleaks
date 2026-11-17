import base64
import os
import time

import httpx

EMAIL = os.getenv("COPYLEAKS_EMAIL", "")
KEY = os.getenv("COPYLEAKS_KEY", "")
# Render provides an HTTPS service URL at runtime; local Docker can set PUBLIC_URL.
PUBLIC_URL = (os.getenv("PUBLIC_URL") or os.getenv("RENDER_EXTERNAL_URL") or "").rstrip("/")
SECRET = os.getenv("WEBHOOK_SECRET", "")
SANDBOX = os.getenv("COPYLEAKS_SANDBOX", "true").lower() != "false"

_tok = {"v": None, "exp": 0.0}


def _check_config():
    missing = []
    if not EMAIL:
        missing.append("COPYLEAKS_EMAIL")
    if not KEY:
        missing.append("COPYLEAKS_KEY")
    if not PUBLIC_URL:
        missing.append("PUBLIC_URL atau RENDER_EXTERNAL_URL")
    if not SECRET:
        missing.append("WEBHOOK_SECRET")
    if missing:
        raise RuntimeError("Konfigurasi belum lengkap: " + ", ".join(missing))


async def _token(c: httpx.AsyncClient) -> str:
    if _tok["v"] and time.time() < _tok["exp"]:
        return _tok["v"]
    r = await c.post(
        "https://id.copyleaks.com/v3/account/login/api",
        json={"email": EMAIL, "key": KEY},
    )
    r.raise_for_status()
    _tok["v"] = r.json()["access_token"]
    _tok["exp"] = time.time() + 3000  # cache ~50 menit
    return _tok["v"]


async def submit(scan_id: str, filename: str, data: bytes):
    _check_config()
    body = {
        "base64": base64.b64encode(data).decode(),
        "filename": filename,
        "properties": {
            "webhooks": {"status": f"{PUBLIC_URL}/webhook/{SECRET}/{{STATUS}}"},
            "sandbox": SANDBOX,
            "expiration": 1,
            "developerPayload": scan_id,
            "scanning": {"internet": True},
        },
    }
    async with httpx.AsyncClient(timeout=60) as c:
        t = await _token(c)
        r = await c.put(
            f"https://api.copyleaks.com/v3/scans/submit/file/{scan_id}",
            json=body,
            headers={"Authorization": f"Bearer {t}"},
        )
        r.raise_for_status()


def summarize(payload: dict) -> dict:
    """Ringkas payload webhook 'completed'. Nama field perlu dicek ke payload sandbox."""
    doc = payload.get("scannedDocument") or {}
    total = doc.get("totalWords") or 0
    res = payload.get("results") or {}
    sources = []
    for kind in ("internet", "database", "batch", "repositories"):
        for it in res.get(kind) or []:
            words = it.get("matchedWords") or 0
            sources.append({
                "kind": kind,
                "title": it.get("title") or "(tanpa judul)",
                "url": it.get("url") or "",
                "words": words,
                "pct": round(words / total * 100, 1) if total else 0,
            })
    sources.sort(key=lambda s: s["words"], reverse=True)
    score = (res.get("score") or {}).get("aggregatedScore")
    if score is None:
        score = min(100, sum(s["pct"] for s in sources))
    return {"total": total, "score": round(float(score), 1), "sources": sources}
