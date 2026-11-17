import hmac
import logging
import os
import time
import uuid
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from . import copyleaks
from .report import build_pdf

logger = logging.getLogger(__name__)
app = FastAPI(docs_url=None, redoc_url=None)
WEB = Path(__file__).parent.parent / "web"
MAX_BYTES = 10 * 1024 * 1024
TTL = 2 * 3600
jobs: dict = {}  # RAM-only; use one worker, and expect jobs to be lost on restart.
basic_auth = HTTPBasic(auto_error=False)


def require_basic_auth(credentials: HTTPBasicCredentials | None = Depends(basic_auth)):
    username = os.getenv("APP_USERNAME", "")
    password = os.getenv("APP_PASSWORD", "")
    if not username or not password:
        raise HTTPException(503, "Login belum dikonfigurasi oleh pemilik aplikasi")
    if credentials is None:
        raise HTTPException(
            401,
            "Login diperlukan",
            headers={"WWW-Authenticate": 'Basic realm="Cek Plagiarisme"'},
        )
    user_ok = hmac.compare_digest(credentials.username.encode(), username.encode())
    pass_ok = hmac.compare_digest(credentials.password.encode(), password.encode())
    if not (user_ok and pass_ok):
        raise HTTPException(
            401,
            "Username atau password salah",
            headers={"WWW-Authenticate": 'Basic realm="Cek Plagiarisme"'},
        )


def purge():
    now = time.time()
    for key in [key for key, job in jobs.items() if now - job["t"] > TTL]:
        del jobs[key]


@app.get("/healthz")
def healthz():
    # Public endpoint for the host's health checker; it reveals no credentials.
    return {"ok": True}


@app.post("/api/cek", dependencies=[Depends(require_basic_auth)])
async def cek(file: UploadFile = File(...)):
    purge()
    name = file.filename or ""
    if not name.lower().endswith((".docx", ".pdf")):
        raise HTTPException(400, "Hanya .docx atau .pdf")
    data = await file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "Maksimal 10 MB")
    if not data:
        raise HTTPException(400, "File kosong")

    job_id = uuid.uuid4().hex
    jobs[job_id] = {"status": "processing", "filename": name, "t": time.time()}
    try:
        await copyleaks.submit(job_id, name, data)
    except Exception:
        jobs.pop(job_id, None)
        logger.exception("Pengiriman scan ke Copyleaks gagal")
        raise HTTPException(
            502,
            "Gagal mengirim scan. Periksa konfigurasi Copyleaks dan log server.",
        )
    return {"id": job_id}


@app.post("/webhook/{secret}/{status}")
async def webhook(secret: str, status: str, request: Request):
    if not copyleaks.SECRET or not hmac.compare_digest(secret, copyleaks.SECRET):
        raise HTTPException(404)
    if status not in {"completed", "error"}:
        return {"ok": True}
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(400, "Payload webhook tidak valid")
    if not isinstance(payload, dict):
        raise HTTPException(400, "Payload webhook tidak valid")

    doc = payload.get("scannedDocument") or {}
    job_id = payload.get("developerPayload") or doc.get("scanId") or payload.get("scanId")
    job = jobs.get(job_id)
    if not job:
        # Copyleaks can retry a callback after the in-memory job has expired/restarted.
        return {"ok": True}
    if status == "completed":
        try:
            summary = copyleaks.summarize(payload)
            job["pdf"] = await run_in_threadpool(
                build_pdf, job["filename"], summary, copyleaks.SANDBOX
            )
            job["status"] = "done"
        except Exception as exc:
            logger.exception("Pembuatan PDF dari webhook gagal")
            job.update(status="error", error=f"Gagal membuat PDF: {exc}")
    else:
        msg = (payload.get("error") or {}).get("message") or "Scan gagal di Copyleaks"
        job.update(status="error", error=msg)
    return {"ok": True}


@app.get("/api/status/{job_id}", dependencies=[Depends(require_basic_auth)])
def status(job_id: str):
    purge()
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job tidak ditemukan / kedaluwarsa")
    return {"status": job["status"], "progress": None, "error": job.get("error")}


@app.get("/api/hasil/{job_id}", dependencies=[Depends(require_basic_auth)])
def hasil(job_id: str):
    job = jobs.get(job_id)
    if not job or job["status"] != "done":
        raise HTTPException(404, "Hasil belum tersedia atau job kedaluwarsa")
    pdf = job["pdf"]
    del jobs[job_id]
    return Response(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="laporan-plagiarisme.pdf"'},
    )


@app.get("/", dependencies=[Depends(require_basic_auth)])
def index():
    return FileResponse(WEB / "index.html")
