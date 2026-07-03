"""
FastAPI app: serves the dashboard + a small JSON API.

Crucially, importing this module pulls in NONE of the ML stack. The server,
the dashboard and the seed data all run with just fastapi + uvicorn installed.
Only POST /api/process imports the heavy pipeline, and it does so lazily inside
a background thread.
"""
import glob
import os
import shutil
import threading
import time
import uuid
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import alerts
import config
import db
import live as live_mod


class UrlIn(BaseModel):
    url: str
    every: int = 0            # 0 = use config.PROCESS_EVERY


class LiveIn(BaseModel):
    source: str = "0"


class CalibIn(BaseModel):
    video: str                # basename or "WIDTHxHEIGHT"
    points: list = []         # [[x,y] * 4] far-left, far-right, near-right, near-left
    target_m: list = []       # [width_m, length_m]
    direction: list = []      # allowed travel [dx, dy] for wrong-way (optional)

app = FastAPI(title="AI Smart Traffic Intelligence Platform")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"],
    allow_methods=["*"], allow_headers=["*"],
)

db.init_db()

# Serve evidence snapshots + the annotated video under /media
app.mount("/media", StaticFiles(directory=str(config.OUTPUT_DIR)), name="media")

# In-memory job registry for the "processing…" progress bar
JOBS: dict = {}


@app.get("/", response_class=HTMLResponse)
def index():
    html = config.FRONTEND_DIR / "index.html"
    if not html.exists():
        return HTMLResponse("<h1>Frontend not found</h1>", status_code=500)
    return html.read_text(encoding="utf-8")


@app.get("/api/stats")
def api_stats():
    s = db.stats()
    s["annotated_video"] = ("/media/annotated.mp4"
                            if config.ANNOTATED_VIDEO.exists() else None)
    s["helmet_model"] = os.path.exists(config.HELMET_MODEL)
    s["plate_model"] = os.path.exists(config.PLATE_MODEL)
    s["fines"] = config.FINES
    s["violation_meta"] = config.VIOLATION_META
    s["currency"] = config.CURRENCY
    s["speed_limit"] = config.SPEED_LIMIT_KMPH
    s["alerts_enabled"] = alerts.alerts_ready()
    s["alerts_to"] = config.ALERTS.get("to") if alerts.alerts_ready() else None
    return s


@app.get("/api/violations")
def api_violations(limit: int = 200, type: Optional[str] = None,
                   plate: Optional[str] = None):
    rows = db.all_violations(limit=limit, vtype=type, plate=plate)
    for r in rows:
        r["snapshot_url"] = f"/media/{r['snapshot']}" if r.get("snapshot") else None
        r["plate_img_url"] = f"/media/{r['plate_img']}" if r.get("plate_img") else None
    return rows


@app.get("/api/vehicles")
def api_vehicles(limit: int = 300):
    """Every tracked vehicle with its best plate read — the live ANPR log."""
    rows = db.all_vehicles(limit=limit)
    for r in rows:
        r["plate_img_url"] = f"/media/{r['plate_img']}" if r.get("plate_img") else None
    return rows


@app.post("/api/reset")
def api_reset():
    """Wipe all data (and old evidence files) for a clean-slate demo."""
    db.clear()
    for f in config.SNAPSHOT_DIR.glob("*.jpg"):
        try:
            f.unlink()
        except OSError:
            pass
    try:
        config.ANNOTATED_VIDEO.unlink()
    except OSError:
        pass
    return {"ok": True}


@app.get("/api/samples")
def api_samples():
    """Bundled clips in data/videos — one-click demo material."""
    vids = sorted(config.VIDEO_DIR.glob("*.mp4"))
    return [v.name for v in vids if v.name != "annotated.mp4"]


class LocalIn(BaseModel):
    name: str
    every: int = 0


@app.post("/api/process_local")
def api_process_local(body: LocalIn):
    """Analyze a clip already in data/videos (picked from /api/samples)."""
    path = (config.VIDEO_DIR / os.path.basename(body.name)).resolve()
    if not path.exists() or path.suffix.lower() != ".mp4":
        raise HTTPException(status_code=404, detail="sample not found")
    job_id = uuid.uuid4().hex[:8]
    JOBS[job_id] = {"status": "queued", "progress": 0}
    threading.Thread(target=_run_job, args=(job_id, str(path), body.every),
                     daemon=True).start()
    return {"job_id": job_id}


# ----------------------------------------------------------- alerts + challans
def _find_violation(vid: int):
    for r in db.all_violations(limit=100000):
        if r["id"] == vid:
            return r
    raise HTTPException(status_code=404, detail="not found")


@app.post("/api/violations/{vid}/alert")
def api_send_alert(vid: int):
    """Manually email this violation (evidence + PDF challan) to the police."""
    ok, msg = alerts.send_alert(_find_violation(vid))
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"ok": True, "detail": msg}


@app.get("/api/violations/{vid}/pdf")
def api_challan_pdf(vid: int):
    """Download the print-ready PDF e-challan for a violation."""
    pdf = alerts.make_challan_pdf(_find_violation(vid))
    return FileResponse(str(pdf), media_type="application/pdf",
                        filename=pdf.name)


# ------------------------------------------------------- speed calibration
@app.get("/api/frame")
def api_frame(name: str):
    """First frame of a sample clip as JPEG — used by the calibration tool."""
    path = (config.VIDEO_DIR / os.path.basename(name)).resolve()
    if not path.exists():
        raise HTTPException(status_code=404, detail="video not found")
    import cv2
    cap = cv2.VideoCapture(str(path))
    ok, frame = cap.read()
    cap.release()
    if not ok:
        raise HTTPException(status_code=500, detail="could not read frame")
    ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return Response(content=buf.tobytes(), media_type="image/jpeg")


@app.get("/api/calibration")
def api_calibration_list():
    import json as _json
    try:
        return _json.loads(config.CALIBRATION_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


@app.post("/api/calibration")
def api_calibration_save(body: CalibIn):
    """Save per-clip calibration: a 4-point road quad + real-world size
    (enables speed + over-speeding) and/or an allowed travel direction
    (enables wrong-way). Applies the next time that clip is analyzed."""
    has_quad = len(body.points) == 4 and len(body.target_m) == 2
    has_dir = len(body.direction) == 2 and any(body.direction)
    if not (has_quad or has_dir):
        raise HTTPException(status_code=400,
                            detail="need 4 points + [w, l] metres and/or a direction")
    from pipeline import save_calibration
    save_calibration(
        os.path.basename(body.video),
        [[float(x), float(y)] for x, y in body.points] if has_quad else None,
        [float(body.target_m[0]), float(body.target_m[1])] if has_quad else None,
        direction=[float(body.direction[0]), float(body.direction[1])]
        if has_dir else None)
    return {"ok": True, "video": os.path.basename(body.video)}


@app.get("/api/violations/{vid}")
def api_violation(vid: int):
    for r in db.all_violations(limit=100000):
        if r["id"] == vid:
            r["snapshot_url"] = f"/media/{r['snapshot']}" if r.get("snapshot") else None
            return r
    raise HTTPException(status_code=404, detail="not found")


def _run_job(job_id: str, path: str, every: int = 0):
    try:
        JOBS[job_id].update(status="processing")
        from pipeline import process_video  # heavy import, deferred

        def cb(cur, total):
            JOBS[job_id].update(
                progress=round(cur / total * 100, 1) if total else 0,
                current=cur, total=total)

        summary = process_video(path, progress_cb=cb, every=every or None)
        JOBS[job_id].update(status="done", progress=100, summary=summary)
    except Exception as e:  # surface the error to the UI instead of dying silently
        JOBS[job_id].update(status="error", error=str(e))


@app.post("/api/process")
async def api_process(file: UploadFile = File(...), every: int = Form(0)):
    dest = config.VIDEO_DIR / (file.filename or "upload.mp4")
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    job_id = uuid.uuid4().hex[:8]
    JOBS[job_id] = {"status": "queued", "progress": 0}
    threading.Thread(target=_run_job, args=(job_id, str(dest), every),
                     daemon=True).start()
    return {"job_id": job_id}


@app.get("/api/process/{job_id}")
def api_job(job_id: str):
    return JOBS.get(job_id, {"status": "unknown"})


@app.post("/api/seed")
def api_seed():
    """Reset the DB to a rich set of realistic demo violations."""
    import seed_demo
    n = seed_demo.seed()
    return {"ok": True, "violations": n}


# --------------------------------------------------------------------- URL / YouTube
def _download_url(url: str) -> str:
    import yt_dlp

    for f in glob.glob(str(config.VIDEO_DIR / "stream.*")):
        try:
            os.remove(f)
        except OSError:
            pass
    # NOTE: YouTube only offers ~360p as a single progressive MP4 — useless
    # for plate reading. Prefer the video-only DASH stream up to 1080p (no
    # audio merge needed, so ffmpeg is optional but wired up just in case).
    opts = {
        "format": ("bestvideo[ext=mp4][height<=1080]/bestvideo[height<=1080]"
                   "/best[ext=mp4]/best"),
        "outtmpl": str(config.VIDEO_DIR / "stream.%(ext)s"),
        "quiet": True, "no_warnings": True, "noplaylist": True,
    }
    try:
        import imageio_ffmpeg
        opts["ffmpeg_location"] = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])
    files = glob.glob(str(config.VIDEO_DIR / "stream.*"))
    if not files:
        raise RuntimeError("download produced no file")
    return files[0]


def _run_url_job(job_id: str, url: str, every: int = 0):
    try:
        JOBS[job_id].update(status="downloading")
        path = _download_url(url)
        JOBS[job_id].update(status="processing")
        from pipeline import process_video

        def cb(cur, total):
            JOBS[job_id].update(
                progress=round(cur / total * 100, 1) if total else 0,
                current=cur, total=total)

        summary = process_video(path, progress_cb=cb, every=every or None)
        JOBS[job_id].update(status="done", progress=100, summary=summary)
    except Exception as e:
        JOBS[job_id].update(status="error", error=str(e))


@app.post("/api/process_url")
def api_process_url(body: UrlIn):
    job_id = uuid.uuid4().hex[:8]
    JOBS[job_id] = {"status": "queued", "progress": 0}
    threading.Thread(target=_run_url_job, args=(job_id, body.url, body.every),
                     daemon=True).start()
    return {"job_id": job_id}


# -------------------------------------------------------- live analysis preview
@app.get("/api/preview.mjpg")
def api_preview_mjpg():
    """MJPEG stream of annotated frames WHILE a video is being analyzed —
    the dashboard shows the AI working live instead of waiting for the file."""
    import pipeline

    def _job_running():
        return any(j.get("status") in ("queued", "downloading", "processing")
                   for j in JOBS.values())

    def gen():
        import time as _t
        # wait through upload/download/model-load — up to 3 minutes as long
        # as a job is actually alive
        deadline = _t.time() + 180
        while not pipeline.preview_active() and _t.time() < deadline:
            if not _job_running():
                deadline = min(deadline, _t.time() + 5)
            _t.sleep(0.15)
        while pipeline.preview_active():
            jpg = pipeline.preview_jpg()
            if jpg:
                yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"
                       + jpg + b"\r\n")
            _t.sleep(0.08)

    return StreamingResponse(
        gen(), media_type="multipart/x-mixed-replace; boundary=frame")


class LocationIn(BaseModel):
    location: str = ""


@app.post("/api/location")
def api_set_location(body: LocationIn):
    """Manually set the camera location (empty string clears the override
    and returns to auto-detection from video GPS metadata)."""
    loc = body.location.strip()
    if loc:
        db.set_meta("location_override", loc)
        db.set_meta("location", loc)
    else:
        db.set_meta("location_override", None)
    return {"ok": True, "location": loc or None}


# --------------------------------------------------------------------- Live camera
@app.post("/api/live/start")
def api_live_start(body: LiveIn):
    started = live_mod.LIVE.start(body.source or "0")
    return {"started": started, **live_mod.LIVE.state_dict()}


@app.post("/api/live/stop")
def api_live_stop():
    live_mod.LIVE.stop()
    return {"stopped": True, **live_mod.LIVE.state_dict()}


@app.get("/api/live/status")
def api_live_status():
    return live_mod.LIVE.state_dict()


@app.get("/api/live.mjpg")
def api_live_mjpg():
    def gen():
        while live_mod.LIVE.running:
            jpg = live_mod.LIVE.get_jpg()
            if jpg:
                yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"
                       + jpg + b"\r\n")
            time.sleep(0.05)

    return StreamingResponse(
        gen(), media_type="multipart/x-mixed-replace; boundary=frame")
