<p align="center">
  <img src="docs/banner.svg" alt="AI Smart Traffic Intelligence Platform" width="100%"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/YOLOv8-Ultralytics-00BFFF?logo=pytorch&logoColor=white" alt="YOLOv8"/>
  <img src="https://img.shields.io/badge/ByteTrack-Tracking-6c5ce7" alt="ByteTrack"/>
  <img src="https://img.shields.io/badge/OpenCV-Vision-5C3EE8?logo=opencv&logoColor=white" alt="OpenCV"/>
  <img src="https://img.shields.io/badge/ANPR-EasyOCR-ff7675" alt="EasyOCR"/>
  <img src="https://img.shields.io/badge/tests-61%20passing-2ecc71" alt="Tests"/>
  <img src="https://img.shields.io/badge/license-MIT-blue" alt="License"/>
</p>

# 🚦 Smart Traffic Violation System 🇱🇰

AI that turns a **live camera feed** into **actionable enforcement**: it
detects and tracks vehicles in real time,
catches **no-helmet riders, red-light jumping, over-speeding, wrong-way driving,
triple-riding, no-seatbelt, no-rest-break (fatigue), wheelie/stunt riding and
mobile-phone use**, reads the number plate, and auto-generates an
**e-challan with photo evidence** — all shown on a live "traffic control centre"
dashboard. **Live only** — there is no file-upload / batch-analysis path.

<p align="center">
  <img src="docs/architecture.svg" alt="AI pipeline: live feed → YOLOv8 + ByteTrack → homography → violation engine → ANPR + evidence → e-challan + dashboard" width="100%"/>
</p>

## 📸 Screenshots

> Drop your own dashboard captures into `docs/screenshots/` and they'll show up
> here. Suggested shots: the live annotated feed, an open e-challan with stamped
> evidence, and the Vehicles·ANPR log.

| Live control-centre | e-Challan with evidence |
|---|---|
| ![Live dashboard](docs/screenshots/dashboard.png) | ![e-Challan](docs/screenshots/challan.png) |

---

## ⚡ Quick start (2 commands)

```powershell
pip install -r requirements.txt
./run.ps1
```

`run.ps1` opens <http://localhost:8000>. The dashboard starts **empty and
honest** — it only ever shows what the AI actually detected on a live feed.
There is no mock/demo data anywhere; each Go Live / Play Live session starts
from a clean slate and streams real detections.

> **Just want the dashboard right now, before the big ML install finishes?**
> The dashboard needs only the *core* deps:
> ```powershell
> pip install fastapi "uvicorn[standard]" python-multipart pillow
> python -m uvicorn main:app --app-dir backend --port 8000
> ```
> YOLO/OCR are only needed to actually go **Live**.

---

## 🔌 Connecting a live camera source

`Go Live` accepts anything OpenCV's `VideoCapture` can open, typed into the
camera-source box:

| Source | What to type |
|---|---|
| Laptop webcam | `0` (or `1`, `2`… for other attached cameras) |
| IP / CCTV camera | `rtsp://user:pass@camera-ip:554/stream` |
| An MJPEG HTTP stream | `http://host:port/stream.mjpg` |
| Any capture-card / HDMI-in video source | Plug it into this PC — it shows up as a normal webcam, so use its camera index (often `1`) |

### Streaming in from a phone or an external transmitter over RTMP

A lot of transmitters (including most drone controller apps) only *push*
video out over **RTMP** to a server — they don't expose a URL you can pull
from directly, which is what `Go Live` needs. RTMP is a push protocol; this
app is a pull client. The fix is a tiny local relay that receives the RTMP
push and re-serves it as a pull-able RTSP URL:

1. Download **[MediaMTX](https://github.com/bluenviron/mediamtx)** (a single
   portable exe, no install) and run it. By default it listens for RTMP
   pushes on port `1935` and re-exposes each one as RTSP on port `8554`.
2. On the transmitter's live-stream/broadcast setting, set the **custom RTMP
   URL** to `rtmp://<this-PC's-LAN-IP>:1935/live/cam1` (both devices must be
   on the same network).
3. In the dashboard's camera-source box, type `rtsp://127.0.0.1:8554/cam1`
   and hit **Go Live**.

If your phone/camera app can expose an RTSP or MJPEG URL directly (e.g.
Android's "IP Webcam" app), skip the relay entirely and paste that URL
straight into the camera-source box — it's a pull source already.

Once connected, pick a **speed mode** (🐢/⚡/🚀). On a CPU laptop the detector
is slower than playback, so the feed **drops frames it was too busy to analyse**
— exactly as a real camera does — and always plays at true speed instead of
crawling in slow motion. The speed mode sets the inference resolution
(960/640/480 px), which decides how many of those frames get analysed.

---

## 🧪 Will my clip actually demo well?

The system only reports what it can genuinely prove, so footage with no moving
traffic legitimately produces **no violations**. Vet a clip before you rely on
it:

```powershell
python scripts/check_clip.py data/videos/mine.mp4
```

It runs the real pipeline and prints what fired, what's blocked and how to
unblock it — e.g. *"Over Speeding OFF — no speed calibration for this clip"*.

---

## 🖥️ Using it

| Action | What happens |
|---|---|
| **📹 Go Live** | Stream from a camera (`rtsp://…`) / an MJPEG URL / a webcam index → real-time annotated feed with live violation logging, ANPR and e-challans as it happens. |
| **🎬 Play Live (sample)** | No live camera handy? Replay a bundled sample clip through the exact same live pipeline — detections, plates and violations land in real time as it plays. Plays **once** (no loop re-counting). |
| **Speed mode (🐢/⚡/🚀)** | Analyze every 1st/2nd/3rd frame so the live feed keeps up in real time on slower hardware. |
| **Vehicles · ANPR tab** | Best **confirmed** plate for every tracked vehicle. A number appears ONLY after two frames agree on it (digit-tail voting) — one garbled read can never show up. Click a row to see the captured plate photo. |
| **Click any violation** | Opens the **e-challan**: photo evidence with the **proof stamped on the image** (speed + limit, plate, vehicle #, zoom inset), plate crop, fine. Buttons: **📧 Send to Police**, **⬇ PDF Challan**, print. |
| **📍 ✎ location** | Set the camera location manually, or leave it to auto-detect from the video's GPS metadata (phone recordings) with reverse geocoding. |
| **🎯 Speed setup** | Click 4 road corners + enter real metres → speed + over-speeding activate for that clip (pre-done for sample.mp4). Also pick the **traffic direction** there → wrong-way detection activates. All violations then run simultaneously per vehicle. |
| **⬇ CSV** | Exports the current violations or ANPR log for the "police back-office" story. |
| **🗑 Clear** | Wipes the current results + evidence for a clean slate (a fresh Go Live / Play Live also auto-clears on start). |

**Police email alerts:** set `ALERTS` in `backend/config.py` (Gmail App
Password) → every confirmed violation is auto-emailed with the PDF challan,
evidence photo and plate crop. Credentials can also come from `SMTP_USER` /
`SMTP_PASS` env vars.

Put sample footage in `data/videos/` (used by 🎬 Play Live) or run
`python scripts/download_sample.py`.

---

## 🎬 The winning demo

**Read `DEMO_GUIDE.md`** — full pitch script, footage guide, judge Q&A and
fallback ladder. Short version:

1. **Hook (15s).** "Colombo already has 103 CCTV cameras watching its roads —
   we turn every one of them into an AI traffic officer, live."
2. **Prove it's real (3min).** **Go Live** from a camera (or **Play Live** on
   your best sample clip) → boxes, track IDs and plates land live; click a
   violation → e-challan with photo evidence, plate crop and LKR fine.
3. **Prove it's honest (1min).** Live-play the parked-bikes clip: **zero false
   violations**. "Ask any other team what their system does with a parked bike."
4. **Close.** AI Insights panel + hotspot map + CSV export: "an end-to-end
   live enforcement product, running on a laptop."

---

## 🧠 Why this wins (talking points)

- **Real tracking, not per-frame boxes.** ByteTrack gives every vehicle a persistent
  ID — that's what makes line-crossing, counting, dedup and speed possible.
- **Engineered against false positives.** Confidence gates + multi-frame
  persistence + camera-motion-compensated movement checks: parked bikes,
  pedestrians and one-frame flickers can never trigger a challan.
- **Honest by design.** No mock data exists — every row is a live detection; unreadable
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
back to the vehicle crop (lower accuracy). Plate cleanup is **country-agnostic**:
it shows exactly what was read (cleaned + spaced), never reformats to a
national grammar — a plate is only confirmed once two frames agree on it.

### 🔗 Seatbelt detection (optional)
Base YOLO has no seatbelt class, so this violation stays **off** until you
drop a trained model at `models/seatbelt.pt` (classes like `seatbelt` /
`no seatbelt` — Roboflow Universe has ready-made YOLOv8 seatbelt-detection
models). Unlike helmets there is no heuristic fallback — a wrong seatbelt
fine is worse than no detection — so without the file, "No Seatbelt" simply
never fires. Applies to cars/buses/trucks only, not motorcycles.

> 🇱🇰 **Localised for Sri Lanka:** fines in LKR, Colombo location.
> Change `FINES`, `CAMERA_LOCATION`, `CURRENCY` in `backend/config.py` to relocate.

---

## 📁 Structure

```
backend/    config, db, detection, ocr, violations, pipeline, live, main(API)
frontend/   index.html   (self-contained control-centre dashboard, no CDNs)
scripts/    download_sample.py
data/videos sample clips for 🎬 Play Live
data/output snapshots/ , traffic.db , results.json
models/     yolov8n.pt (auto) , helmet.pt (optional) , seatbelt.pt (optional)
```

## 🔌 API

`GET /api/stats` · `GET /api/violations` · `GET /api/violations/{id}` ·
`POST /api/violations/{id}/alert` (email police) · `GET /api/violations/{id}/pdf` ·
`GET /api/vehicles` (ANPR log) · `GET /api/samples` (sample clips for 🎬 Play Live) ·
`GET /api/frame?name=` · `GET|POST /api/calibration` (speed setup) ·
`POST /api/live/start` (`source`, `every` — camera/sample) ·
`POST /api/live/stop` · `GET /api/live/status` · `GET /api/live.mjpg` ·
`GET /api/live/frame` (raw frame for live calibration) ·
`POST /api/location` · `POST /api/reset`
