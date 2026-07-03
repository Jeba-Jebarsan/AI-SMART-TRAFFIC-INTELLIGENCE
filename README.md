# 🚦 Smart Traffic Violation System 🇱🇰

AI that turns any CCTV / traffic clip into **actionable enforcement**: it detects
and tracks vehicles, catches **no-helmet riders, red-light jumping, over-speeding,
wrong-way driving and triple-riding**, reads the number plate, and auto-generates
an **e-challan with photo evidence** — all shown on a live "traffic control centre"
dashboard.

```
 VIDEO ─▶ YOLOv8 + ByteTrack ─▶ Signal state ─▶ Violation engine
       ─▶ Plate OCR ─▶ e-challan ─▶ SQLite/JSON ─▶ Control-centre dashboard
```

---

## ⚡ Quick start (2 commands)

```powershell
pip install -r requirements.txt
./run.ps1
```

`run.ps1` opens <http://localhost:8000>. The dashboard starts **empty and
honest** — it only ever shows what the AI actually detected. The header badge
tells everyone whether they're looking at `REAL AI RESULTS` or clearly-marked
`SIMULATED DEMO DATA`.

> **Just want the dashboard right now, before the big ML install finishes?**
> The dashboard needs only the *core* deps:
> ```powershell
> pip install fastapi "uvicorn[standard]" python-multipart pillow
> python -m uvicorn main:app --app-dir backend --port 8000
> ```
> YOLO/OCR are only needed to **Analyze** a real video.

---

## 🖥️ Using it

| Action | What happens |
|---|---|
| **Analyze Video / Run Sample** | Real YOLO+ByteTrack runs in the background — and the video panel switches to a **live AI view** (MJPEG) so you watch boxes/plates/violations land in real time while it processes. Annotated video loads when done. |
| **Speed mode (🐢/⚡/🚀)** | Analyze every 1st/2nd/3rd frame — output video stays full length, processing is ~1×/2×/3× faster. |
| **🎬 Play Live** | Play any sample clip like a live CCTV feed — detections, plates and violations land in real time as it plays. Plays **once** (no loop re-counting). |
| **Analyze URL** | Paste a YouTube / direct video URL → fetched with `yt-dlp` at up to **1080p** and analyzed. |
| **Go Live** | Stream from a webcam (`0`), an IP/CCTV camera (`rtsp://…`) or a local file → real-time annotated MJPEG feed with live violation logging. |
| **Vehicles · ANPR tab** | Best **confirmed** plate for every tracked vehicle. A number appears ONLY after two frames agree on it (digit-tail voting) — one garbled read can never show up. Click a row to see the captured plate photo. |
| **Click any violation** | Opens the **e-challan**: photo evidence with the **proof stamped on the image** (speed + limit, plate, vehicle #, zoom inset), plate crop, fine. Buttons: **📧 Send to Police**, **⬇ PDF Challan**, print. |
| **📍 ✎ location** | Set the camera location manually, or leave it to auto-detect from the video's GPS metadata (phone recordings) with reverse geocoding. |
| **🎯 Speed setup** | Click 4 road corners + enter real metres → speed + over-speeding activate for that clip (pre-done for sample.mp4). Also pick the **traffic direction** there → wrong-way detection activates. All five violations then run simultaneously per vehicle. |
| **⬇ CSV** | Exports the current violations or ANPR log for the "police back-office" story. |
| **Demo data (simulated)** | Presentation fallback only — 34 fake violations, **badged SIMULATED in the header** so it can never pass as real. |

**Police email alerts:** set `ALERTS` in `backend/config.py` (Gmail App
Password) → every confirmed violation is auto-emailed with the PDF challan,
evidence photo and plate crop. Credentials can also come from `SMTP_USER` /
`SMTP_PASS` env vars.

Put test footage in `data/videos/` or run `python scripts/download_sample.py`.

---

## 🎬 The winning demo

**Read `DEMO_GUIDE.md`** — full pitch script, footage guide, judge Q&A and
fallback ladder. Short version:

1. **Hook (15s).** "Colombo already has 103 CCTV cameras watching its roads —
   humans review the footage. We turn every one into an AI traffic officer."
2. **Prove it's real (3min).** **Run Sample** on your best clip → boxes, track
   IDs and plates land live; click a violation → e-challan with photo evidence,
   plate crop and LKR fine.
3. **Prove it's honest (1min).** Run the parked-bikes clip: **zero false
   violations**. "Ask any other team what their system does with a parked bike."
4. **Close.** AI Insights panel + hotspot map + CSV export: "an end-to-end
   enforcement product, offline, on a laptop."

---

## 🧠 Why this wins (talking points)

- **Real tracking, not per-frame boxes.** ByteTrack gives every vehicle a persistent
  ID — that's what makes line-crossing, counting, dedup and speed possible.
- **Engineered against false positives.** Confidence gates + multi-frame
  persistence + camera-motion-compensated movement checks: parked bikes,
  pedestrians and one-frame flickers can never trigger a challan.
- **Honest by design.** Real vs simulated data is badged in the UI; unreadable
  plates say UNREADABLE; signal-less roads show "no signal in view" instead of
  an invented red light.
- **Actionable output.** Auto e-challans with photo evidence + plate crop + fine,
  plus a full ANPR log of every tracked vehicle.
- **Analytics anyone understands.** Plain-language AI insights, violation mix,
  timeline, in-frame hotspot map, CSV export.

---

## 🎯 Tuning for YOUR clip (`backend/config.py`)

| Setting | Meaning |
|---|---|
| `STOP_LINE_Y` | Height (0–1) of the virtual stop line for red-light detection. |
| `FORCE_SIGNAL` | Deterministic signal cycle (demo-safe). Set `None` to auto-detect the light colour from the video. |
| `SPEED_LIMIT_KMPH` | Over-speed threshold (km/h). |
| `SPEED_SOURCE` / `SPEED_TARGET_M` | Perspective speed calibration — a road quad (4 image points) mapped to real-world `(width_m, length_m)`. Pre-set for the sample clip; `None` uses the `PIXELS_PER_METER` fallback. |
| `ALLOWED_DIRECTION` | Correct travel direction; opposite motion = wrong-way. |
| `FINES` | Fine amount per violation type. |
| `ENABLE` | Turn individual violations on/off. |

### 🪖 Real helmet detection (optional, ~2 min)
Base YOLO has **no** helmet class, so without a model helmet uses a rough head-region
heuristic. For accuracy, drop a trained model at `models/helmet.pt`:
- Grab one from **Roboflow Universe** (search "helmet detection", export as YOLOv8),
  or train `yolo detect train data=helmet.yaml model=yolov8n.pt` on a helmet dataset.
The pipeline auto-detects the file and switches to it — no code change.

### 🔢 Accurate number plates (optional, recommended)
OCR reads far better when the plate is localised first. Drop a YOLOv8 plate
detector at `models/license_plate_detector.pt` (`python scripts/get_plate_model.py`,
or export one from Roboflow Universe). The pipeline then runs **two-stage ANPR**
— detect plate → crop → threshold → OCR — automatically. Without it, OCR falls
back to the vehicle crop (lower accuracy). Plate cleanup is tuned for **Sri Lankan**
formats (province code + letters + 4 digits).

> 🇱🇰 **Localised for Sri Lanka:** fines in LKR, Colombo location, Sri Lankan plates.
> Change `FINES`, `CAMERA_LOCATION`, `CURRENCY` in `backend/config.py` to relocate.

---

## 📁 Structure

```
backend/    config, db, detection, ocr, violations, pipeline, main(API), seed_demo
frontend/   index.html   (self-contained control-centre dashboard, no CDNs)
scripts/    download_sample.py
data/output snapshots/ , annotated.mp4 , traffic.db , results.json
models/     yolov8n.pt (auto) , helmet.pt (optional)
```

## 🔌 API

`GET /api/stats` · `GET /api/violations` · `GET /api/violations/{id}` ·
`POST /api/violations/{id}/alert` (email police) · `GET /api/violations/{id}/pdf` ·
`GET /api/vehicles` (ANPR log) · `GET /api/samples` · `GET /api/frame?name=` ·
`GET|POST /api/calibration` (speed setup) · `POST /api/process` (upload, `every`) ·
`POST /api/process_local` · `POST /api/process_url` · `GET /api/process/{job}` ·
`POST /api/live/start|stop` · `GET /api/live.mjpg` ·
`POST /api/seed` (simulated, badged) · `POST /api/reset`
