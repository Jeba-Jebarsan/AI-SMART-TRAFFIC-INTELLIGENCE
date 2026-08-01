"""
FastAPI app: serves the dashboard + a small JSON API.

Crucially, importing this module pulls in NONE of the ML stack. The server
and the dashboard run with just fastapi + uvicorn installed. Only live mode
(backed by live.py) imports the heavy pipeline, and it does so lazily inside
a background thread. The primary mode is LIVE (IP camera, RTSP/HTTP stream or
webcam); /api/analyze-image additionally judges a single still against the
appearance-based rules only, and also imports the pipeline lazily.
"""
import os
import time
from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import alerts
import config
import db
import live as live_mod


class LiveIn(BaseModel):
    source: str = "0"
    every: int = 0            # 0 = use config.PROCESS_EVERY


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

# Serve evidence snapshots under /media
app.mount("/media", StaticFiles(directory=str(config.OUTPUT_DIR)), name="media")


@app.get("/", response_class=HTMLResponse)
def index():
    html = config.FRONTEND_DIR / "index.html"
    if not html.exists():
        return HTMLResponse("<h1>Frontend not found</h1>", status_code=500)
    return html.read_text(encoding="utf-8")


@app.get("/api/stats")
def api_stats():
    s = db.stats()
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
                   plate: Optional[str] = None,
                   status: Optional[str] = None):
    rows = db.all_violations(limit=limit, vtype=type, plate=plate,
                             status=status)
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
    """Bundled clips in data/videos — picked from the 🎬 Play Live selector.

    Phone footage arrives as .MOV/.mov (iPhone) or .mkv/.webm as often as .mp4,
    so match any container OpenCV can open rather than mp4 alone — otherwise a
    clip you dropped in simply never appears in the selector.
    """
    exts = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm"}
    vids = sorted((p for p in config.VIDEO_DIR.iterdir()
                   if p.is_file() and p.suffix.lower() in exts),
                  key=lambda p: p.name.lower())
    return [v.name for v in vids if v.name != "annotated.mp4"]


# ----------------------------------------------------------- alerts + challans
def _find_violation(vid: int):
    for r in db.all_violations(limit=100000):
        if r["id"] == vid:
            return r
    raise HTTPException(status_code=404, detail="not found")


def _require_approved(row: dict):
    """The AI proposes; an officer decides. Enforce that here, not in the UI.

    A challan the system generated on its own must not be able to leave the
    building as a PDF or an email — otherwise "a human approved this" is a
    claim about the interface rather than about the system, and hiding the
    button would be the only thing standing between a detection and a fine.
    """
    status = (row.get("status") or "PENDING").upper()
    if status != "APPROVED":
        raise HTTPException(
            status_code=409,
            detail=f"challan {row.get('challan_id') or row.get('id')} is "
                   f"{status}. An officer must approve it before it can be "
                   f"issued.")
    return row


class ReviewIn(BaseModel):
    action: str = "approve"          # approve | reject | reopen
    officer: str = ""
    note: str = ""


@app.post("/api/violations/{vid}/review")
def api_review(vid: int, body: ReviewIn):
    """Record an officer's decision on one proposed violation."""
    try:
        row = db.review_violation(vid, body.action, body.officer, body.note)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    # Approval is the moment a proposal becomes a challan, so this is where
    # the police notification belongs - not at detection time.
    if row.get("status") == "APPROVED":
        alerts.notify_async(row)
    return {"ok": True, "violation": row}


@app.get("/api/audit")
def api_audit(limit: int = 200, violation_id: int = None):
    """The append-only review trail: who decided what, and when."""
    return {"entries": db.audit_log(limit=limit, violation_id=violation_id)}


@app.post("/api/violations/{vid}/alert")
def api_send_alert(vid: int):
    """Manually email this violation (evidence + PDF challan) to the police."""
    ok, msg = alerts.send_alert(_require_approved(_find_violation(vid)))
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"ok": True, "detail": msg}


@app.get("/api/violations/{vid}/pdf")
def api_challan_pdf(vid: int):
    """Download the print-ready PDF e-challan for an APPROVED violation."""
    pdf = alerts.make_challan_pdf(_require_approved(_find_violation(vid)))
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


@app.get("/api/live/frame")
def api_live_frame():
    """Latest RAW (un-annotated) frame of the running live stream — lets the
    calibration tool work on the live camera, not just sample clips."""
    jpg = live_mod.LIVE.raw_jpg()
    if jpg is None:
        raise HTTPException(status_code=404,
                            detail="live stream not running / no frame yet")
    return Response(content=jpg, media_type="image/jpeg")


@app.get("/api/calibration")
def api_calibration_list():
    import json as _json
    try:
        return _json.loads(config.CALIBRATION_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


@app.post("/api/calibration")
def api_calibration_save(body: CalibIn):
    """Save per-source calibration: a 4-point road quad + real-world size
    (enables speed + over-speeding) and/or an allowed travel direction
    (enables wrong-way).

    video = a sample-clip basename, or the literal "live" to calibrate the
    CURRENTLY RUNNING live stream — stored under its WxH resolution key (so
    the same camera picks it up next session too) and hot-applied to the
    running session immediately, no restart needed."""
    has_quad = len(body.points) == 4 and len(body.target_m) == 2
    has_dir = len(body.direction) == 2 and any(body.direction)
    if not (has_quad or has_dir):
        raise HTTPException(status_code=400,
                            detail="need 4 points + [w, l] metres and/or a direction")

    points = ([[float(x), float(y)] for x, y in body.points]
              if has_quad else None)
    target = ([float(body.target_m[0]), float(body.target_m[1])]
              if has_quad else None)
    direction = ([float(body.direction[0]), float(body.direction[1])]
                 if has_dir else None)

    if body.video.strip().lower() == "live":
        if not (live_mod.LIVE.running and live_mod.LIVE.frame_w):
            raise HTTPException(status_code=409,
                                detail="live stream is not running")
        key = f"{live_mod.LIVE.frame_w}x{live_mod.LIVE.frame_h}"
    else:
        key = os.path.basename(body.video)

    from pipeline import save_calibration
    save_calibration(key, points, target, direction=direction)

    applied = False
    if body.video.strip().lower() == "live":
        applied = live_mod.LIVE.apply_calibration(points, target, direction)
    return {"ok": True, "video": key, "applied": applied}


@app.get("/api/violations/{vid}")
def api_violation(vid: int):
    for r in db.all_violations(limit=100000):
        if r["id"] == vid:
            r["snapshot_url"] = f"/media/{r['snapshot']}" if r.get("snapshot") else None
            return r
    raise HTTPException(status_code=404, detail="not found")


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
    started = live_mod.LIVE.start(body.source or "0", every=body.every)
    return {"started": started, **live_mod.LIVE.state_dict()}


@app.post("/api/live/stop")
def api_live_stop():
    live_mod.LIVE.stop()
    return {"stopped": True, **live_mod.LIVE.state_dict()}


@app.get("/api/live/status")
def api_live_status():
    return live_mod.LIVE.state_dict()


@app.post("/api/analyze-image")
async def api_analyze_image(file: UploadFile = File(...)):
    """Analyse ONE uploaded photograph and log the violations it shows.

    Only appearance-based rules are applied (helmet, three-up riding,
    seatbelt, phone) — a still cannot establish speed, red-light running or
    parking duration. Results are stored with source "image" so they stay
    distinguishable from live camera detections.
    """
    import cv2
    import numpy as np
    import pipeline            # lazy: keeps the ML stack out of module import

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="empty file")
    img = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        # OpenCV only decodes a handful of formats. Pillow covers the rest —
        # and HEIC (every modern iPhone photo) needs pillow-heif on top. Fall
        # back rather than telling the user their own photo is "not an image".
        try:
            import io

            from PIL import Image as PILImage
            try:
                import pillow_heif
                pillow_heif.register_heif_opener()
            except ImportError:
                pass
            pil = PILImage.open(io.BytesIO(raw)).convert("RGB")
            img = np.array(pil)[:, :, ::-1].copy()      # RGB -> BGR
        except Exception:
            img = None
    if img is None:
        raise HTTPException(
            status_code=400,
            detail=f"could not read '{file.filename}'. Use JPG, PNG or WEBP "
                   f"(HEIC needs: pip install pillow-heif)")

    db.init_db()
    seq = db.violation_count()
    annotated, rows = pipeline.analyse_image(img, seq_base=seq)
    name = f"image_{seq + 1}.jpg"
    out = config.SNAPSHOT_DIR / name
    cv2.imwrite(str(out), annotated, [cv2.IMWRITE_JPEG_QUALITY, 90])
    db.set_meta("data_source", "ai")
    return {"violations": [{"type": r["type"], "challan_id": r["challan_id"],
                            "plate": r["plate"], "fine": r["fine"]}
                           for r in rows],
            "count": len(rows),
            "annotated": f"/media/snapshots/{name}"}


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
