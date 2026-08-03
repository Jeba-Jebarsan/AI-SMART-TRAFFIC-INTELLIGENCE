# Smart Traffic Violation System

AI that turns a live camera feed into actionable traffic enforcement. It
detects and tracks vehicles in real time, catches violations — no-helmet
riders, red-light jumping, over-speeding, wrong-way driving, triple-riding,
no-seatbelt, no-rest-break (fatigue), wheelie/stunt riding, mobile-phone use —
reads the number plate, and generates an e-challan with photo evidence, all
shown on a live control-centre dashboard.

**Live only.** There is no file-upload or batch-analysis path — every result
on the dashboard came from a camera or a replayed clip running through the
real-time pipeline, and every session starts empty.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-00BFFF)](https://github.com/ultralytics/ultralytics)
[![OpenCV](https://img.shields.io/badge/OpenCV-Vision-5C3EE8?logo=opencv&logoColor=white)](https://opencv.org/)
[![Tests](https://img.shields.io/badge/tests-61%20passing-2ecc71)](tests/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

## How detection becomes a fine

The AI never issues a fine on its own. Every violation it detects lands in a
review queue as `PENDING`; a human officer has to open it, look at the
evidence, and approve it before a PDF challan or police email is ever
generated. Reject and reopen are both logged too, and every decision is
written to an append-only audit table — nothing is ever deleted or silently
overwritten, even a full data reset.

This is enforced twice: once in the API route, and again inside the email
function itself, so nothing can bypass the human step by calling the
internals directly.

## Quick start

```powershell
pip install -r requirements.txt
./run.ps1
```

This opens `http://localhost:8000`. There is no mock or demo data — each
"Go Live" / "Play Live" session starts from a clean slate and streams real
detections.

Just want the dashboard running before the full ML install finishes? It
only needs the core deps:

```powershell
pip install fastapi "uvicorn[standard]" python-multipart pillow
python -m uvicorn main:app --app-dir backend --port 8000
```

YOLO and OCR are only needed to actually go live.

## Connecting a live camera source

`Go Live` accepts anything OpenCV's `VideoCapture` can open, typed into the
camera-source box:

| Source | What to type |
|---|---|
| Laptop webcam | `0` (or `1`, `2`… for other attached cameras) |
| IP / CCTV camera | `rtsp://user:pass@camera-ip:554/stream` |
| MJPEG HTTP stream | `http://host:port/stream.mjpg` |
| Capture-card / HDMI-in source | Plug it into this PC — it shows up as a normal webcam, use its camera index |

### Streaming from a phone or transmitter over RTMP

Most drone controller apps and phone broadcast tools only *push* video out
over RTMP — they don't expose a URL that `Go Live` can pull from. The fix is
a small local relay:

1. Download [MediaMTX](https://github.com/bluenviron/mediamtx) (a single
   portable executable) and run it. It listens for RTMP pushes on port
   `1935` and re-exposes each as RTSP on port `8554`.
2. On the transmitter, set the custom RTMP URL to
   `rtmp://<this-PC's-LAN-IP>:1935/live/cam1` (same network as this PC).
3. In the camera-source box, type `rtsp://127.0.0.1:8554/cam1` and hit
   **Go Live**.

If your phone/camera app can already expose an RTSP or MJPEG URL directly
(e.g. Android's "IP Webcam" app), skip the relay and paste that URL straight
in.

Once connected, pick a speed mode (slow / balanced / fast). On a CPU laptop
the detector is slower than playback, so the feed drops frames it didn't
have time to analyse — the same way a real camera-plus-DVR setup behaves —
and always plays at true speed instead of crawling in slow motion.

Capture and analysis run on separate threads: a webcam produces ~30 fps
while CPU detection manages ~2-3 fps, so a reader thread keeps the newest
frame flowing to the browser (~7-8 fps published) and stamps the latest
detection overlay onto it. Inference threads are capped at roughly two
thirds of your CPU cores (`config.TORCH_THREADS`) so capture is never
starved.

## Will my clip actually demo well?

The system only reports what it can prove, so footage with no moving
traffic legitimately produces zero violations. Check a clip before relying
on it:

```powershell
python scripts/check_clip.py data/videos/mine.mp4
```

This runs the real pipeline and prints what fired, what's blocked, and how
to unblock it — e.g. *"Over Speeding OFF — no speed calibration for this
clip"*.

## Using it

| Action | What happens |
|---|---|
| **Go Live** | Stream from a camera / MJPEG URL / webcam index → real-time annotated feed with live violation logging, ANPR and e-challans as it happens. |
| **Play Live (sample)** | No live camera handy? Replay a bundled sample clip through the same live pipeline — detections, plates and violations land in real time as it plays. Plays once, no loop re-counting. |
| **Speed mode** | Analyse every 1st/2nd/3rd frame so the live feed keeps up in real time on slower hardware. |
| **Vehicles · ANPR tab** | Best confirmed plate for every tracked vehicle. A number only appears once two frames agree on it (digit-tail voting) — one garbled read can't show up. |
| **Review queue** | Every violation opens as an e-challan: photo evidence, plate crop, fine, a **PENDING / APPROVED / REJECTED** stamp, and Approve / Reject / Reopen buttons for the reviewing officer. Send-to-police and PDF export are disabled until it's approved. |
| **Location** | Set the camera location manually, or auto-detect from the video's GPS metadata with reverse geocoding. |
| **Speed setup** | Click 4 road corners, enter the real-world distance → speed and over-speeding activate for that clip. Also sets the traffic direction, which activates wrong-way detection. |
| **CSV export** | Exports the current violations or ANPR log. |
| **Clear** | Wipes the current session's results and evidence (a fresh Go Live / Play Live also clears automatically). |

**Police email alerts:** set `ALERTS` in `backend/config.py` (or the
`SMTP_USER` / `SMTP_PASS` env vars). Emails only ever go out for an
**approved** violation, complete with the PDF challan, evidence photo and
plate crop.

Put sample footage in `data/videos/` (used by Play Live) or run
`python scripts/download_sample.py`.

## Design choices worth knowing about

- **Real tracking, not per-frame boxes.** ByteTrack gives every vehicle a
  persistent ID, which is what makes line-crossing, counting, dedup and
  speed measurement possible at all.
- **Engineered against false positives.** Confidence gates, multi-frame
  persistence, and camera-motion-compensated movement checks mean a parked
  bike, a pedestrian, or a one-frame flicker can't trigger a challan.
- **Human approval is not optional.** See "How detection becomes a fine"
  above — this is the part of the system we'd want audited first.
- **No invented data.** Unreadable plates say `UNREADABLE`. A signal-less
  road shows "no signal in view" instead of guessing a light colour. Every
  row on the dashboard traces back to an actual detection.

## Tuning for your own footage (`backend/config.py`)

| Setting | Meaning |
|---|---|
| `STOP_LINE_Y` | Height (0-1) of the virtual stop line for red-light detection. |
| `FORCE_SIGNAL` | Deterministic signal cycle for demos. Set to `None` to auto-detect the light colour from the video. |
| `SPEED_LIMIT_KMPH` | Over-speed threshold in km/h. |
| `SPEED_SOURCE` / `SPEED_TARGET_M` | Perspective speed calibration — a road quad (4 image points) mapped to a real-world `(width_m, length_m)`. `None` falls back to `PIXELS_PER_METER`. |
| `ALLOWED_DIRECTION` | Correct travel direction; opposite motion is flagged wrong-way. |
| `FINES` | Fine amount per violation type. |
| `ENABLE` | Turn individual violation types on or off. |

### Real helmet detection (optional)

Base YOLO has no helmet class, so without a trained model, helmet detection
falls back to a rough head-region heuristic. For real accuracy, drop a
trained model at `models/helmet.pt` — search "helmet detection" on Roboflow
Universe and export as YOLOv8, or train your own with
`yolo detect train data=helmet.yaml model=yolov8n.pt`. The pipeline picks up
the file automatically.

### Accurate number plates (optional, recommended)

OCR reads far better once the plate is localised first. Drop a YOLOv8 plate
detector at `models/license_plate_detector.pt`
(`python scripts/get_plate_model.py`, or export one from Roboflow
Universe). The pipeline then runs two-stage ANPR — detect plate, crop,
threshold, OCR — automatically; without it, OCR falls back to the full
vehicle crop at lower accuracy. Plate cleanup is country-agnostic: it shows
exactly what was read, never reformats to a national plate grammar, and a
plate is only confirmed once two frames agree on it.

### Seatbelt detection (optional)

Base YOLO has no seatbelt class, so this violation stays off until a
trained model is present at `models/seatbelt.pt` (classes like `seatbelt` /
`no seatbelt` — Roboflow Universe has ready-made YOLOv8 seatbelt models).
Unlike helmets, there's no heuristic fallback here on purpose — a wrong
seatbelt fine is worse than no detection — so without the file, "No
Seatbelt" simply never fires. Applies to cars/buses/trucks, not
motorcycles.

Localised for Sri Lanka by default: fines in LKR, Colombo as the default
location. Change `FINES`, `CAMERA_LOCATION`, `CURRENCY` in
`backend/config.py` to relocate.

## Project structure

```
backend/    config, db, detection, ocr, violations, pipeline, live, main (API)
frontend/   index.html — self-contained control-centre dashboard, no CDNs
scripts/    download_sample.py, check_clip.py, and doc/deck generators
tests/      unit test suites + run_all.py
data/videos     sample clips for Play Live
data/output     snapshots/, traffic.db, results.json
models/     yolov8n.pt (auto-downloaded), helmet.pt / seatbelt.pt (optional)
```

## API

`GET /api/stats` · `GET /api/violations` (`?status=PENDING|APPROVED|REJECTED`) ·
`GET /api/violations/{id}` · `POST /api/violations/{id}/review` (approve /
reject / reopen) · `GET /api/audit` · `POST /api/violations/{id}/alert`
(email police, approved only) · `GET /api/violations/{id}/pdf` (approved
only) · `GET /api/vehicles` (ANPR log) · `GET /api/samples` ·
`GET /api/frame?name=` · `GET|POST /api/calibration` ·
`POST /api/live/start` (`source`, `every`) · `POST /api/live/stop` ·
`GET /api/live/status` · `GET /api/live.mjpg` · `GET /api/live/frame` ·
`POST /api/location` · `POST /api/reset`

## Testing

```powershell
python tests/run_all.py
```

Runs every suite (detection engine, each violation type, the review/audit
workflow) and reports a combined pass/fail.

## License

[MIT](LICENSE)
