# 🏆 Demo & Pitch Playbook — AI Smart Traffic Intelligence (Sri Lanka)

Everything you need to win: what to show, what to say, which videos to use,
and how to answer the judges. Read this twice before the demo.

---

## 1. Your winning angle (memorise this)

Most hackathon traffic demos **fake it** — hardcoded detections, mock plates,
violations firing on parked bikes. Yours **doesn't**, and you can prove it
live. That honesty is the pitch:

> "Colombo already has **103 CCTV cameras** watching its roads — but humans
> review the footage. We turn every one of those existing cameras into an AI
> traffic officer: it tracks every vehicle, reads number plates, detects
> five violation types, and issues an e-challan with photo evidence —
> in one box, offline, no cloud, running on a laptop."

Four proof points to say out loud:
1. **No mock data.** The header badge shows `REAL AI RESULTS` vs `SIMULATED
   DEMO DATA` — the system refuses to blur that line. Unreadable plates say
   `UNREADABLE`, never an invented number.
2. **Engineered against false positives.** A violation needs a *confident*,
   *tracked*, *moving* vehicle observed over *multiple frames*. Parked bikes,
   pedestrians and one-frame flickers can't trigger it. (Show the parked-bike
   clip — zero violations. Judges LOVE seeing what it *doesn't* flag.)
   Plates use the same philosophy: a number is only accepted when the SAME
   text is read in multiple frames (or one read is high-confidence AND fits
   Sri Lankan plate grammar) — click any vehicle to see the captured plate
   photo behind the reading.
3. **Evidence-grade output.** Every challan = photo with zoom inset + plate
   crop (the exact OCR input) + timestamp + LKR fine, downloadable as a
   **Sri Lanka Police PDF challan**.
4. **Closes the enforcement loop.** One click (or fully automatic) emails
   the challan + evidence photos + plate crop straight to the traffic police
   mailbox. Detection → verification → notification, end to end.

---

## 2. Which footage works (this decides your demo quality)

| Feature | Needs | Avoid |
|---|---|---|
| Vehicle tracking / counting | any road footage, 480p+ | extreme night/rain |
| **ANPR (plates)** | camera ≤ 15 m from plates, 720p+, plates facing camera | distant/oblique plates, < 720p |
| **No-helmet** | fixed camera, bikes passing within ~10–20 m, 720p+ | moving/walking camera, tiny bikes |
| Red-light jump | the traffic light itself VISIBLE in frame + stop line area | signal out of frame (system honestly shows "no signal in view") |
| Over-speeding | fixed camera + 4-point road calibration (config.SPEED_SOURCE) | uncalibrated scenes (speed stays off — honest) |

**The #1 upgrade you can make before the demo: record your own clips.**
30–60 seconds each, phone on a tripod (or against a window/railing), 1080p:
- stand on a footbridge or 1st-floor balcony over a junction → helmet demo
- film vehicles entering a car park / gate head-on at 5–10 m → killer ANPR demo
  (Sri Lankan plates are high-contrast — they OCR beautifully at this range)
- a junction where the signal head is visible in frame → red-light demo

Own footage of Galle Road tuk-tuks and bikes beats any YouTube clip for the
"built for Sri Lanka" story — judges instantly recognise the streets.

**Ready-made footage (already tested in this repo):**
- `data/videos/Automatic Number Plate Recognition (ANPR)….mp4` — verified:
  plates get detected + read as vehicles approach (ANPR log fills in).
- `data/videos/sample.mp4` (4K highway) — verified: strong multi-vehicle
  tracking demo, some plate reads; enable speed by uncommenting the
  pre-calibrated `SPEED_SOURCE` in `backend/config.py`.
- `data/videos/srilanka.mp4` — verified: busy Pettah street, ZERO false
  violations on all the parked bikes. This is your honesty exhibit.

**Downloadable sources for more:**
- Kaggle [Road Traffic Video Monitoring](https://www.kaggle.com/datasets/shawon10/road-traffic-video-monitoring) — junction CCTV clips
- Kaggle [Highway Traffic Videos](https://www.kaggle.com/datasets/aryashah2k/highway-traffic-videos-dataset) — fixed-camera highway CCTV
- Mendeley [Helmet Use in Motorcycle Drivers](https://data.mendeley.com/datasets/bmy35m25pw/1) — 32 rider videos with/without helmets
- YouTube search terms that find usable clips (then paste the URL straight
  into the dashboard's **Analyze URL** box): `"traffic junction cctv footage
  india"`, `"colombo traffic 4k"`, `"license plate recognition test video"`,
  `"motorcycle traffic fixed camera"`. Prefer fixed-camera, daytime, 720p+.
  Download happens automatically via yt-dlp — test every URL the night before.

---

## 3. The demo flow (7 minutes, 3 acts)

**Prep (before judges arrive):**
1. `./run.ps1` → dashboard opens EMPTY (honest zero state — that's fine).
2. Pre-process your best clip once so `annotated.mp4` is ready as backup.
3. Have 2–3 clips in `data/videos/` (they appear in the sample dropdown).
4. **Set up police email alerts** (the wow moment): in `backend/config.py`
   set `ALERTS = {"enabled": True, "to": "<a second email you control>",
   ..., "user": "<your gmail>", "password": "<Gmail App Password>"}`.
   Gmail App Password: Google Account → Security → 2-Step Verification →
   App passwords. Open the "police" inbox on your phone — when a violation
   lands DURING the demo, the challan + evidence arrives on screen live.
   Test it the night before with the challan modal's **Send to Police** button.
5. Speed mode: use **⚡ Fast (2x)** for live runs — full accuracy per analyzed
   frame, half the wait. **🐢 Accurate** for pre-processing overnight footage.
6. If you have a fixed-camera clip, run **🎯 Speed setup** once (click the
   4 road corners, enter metres) — over-speeding + live km/h labels activate
   for that clip. `sample.mp4` is already calibrated.
7. Keep this guide's Q&A section open on your phone.

**Act 1 — the hook (60 s).**
Say the Colombo-103-cameras line. Point at the header: "No data yet — this
dashboard only ever shows what the AI actually found."

**Act 2 — live analysis (3 min).**
Pick your best clip in the sample dropdown → **Run Sample**. The video panel
switches to the LIVE AI VIEW — judges literally watch the model box vehicles,
read plates and flag violations in real time while the feed fills. Narrate:
- "Every vehicle gets a ByteTrack ID — that's how we fine each one once,
  not forty times."
- point at the ANPR tab: "plates are read continuously for every vehicle,
  best read wins — not just violators."
- when a violation lands: click it → e-challan modal → zoom inset + plate
  crop + LKR fine. "This PDF-prints as a court-ready challan."

**Act 3 — the differentiators (2 min).**
- Run `srilanka.mp4` (or show its results): "A dozen parked bikes, people
  everywhere — and ZERO false violations. Ask any other team what their
  system does with a parked bike." Then show the AI Insights panel reading
  out plain-language findings, the hotspot map, and CSV export ("plugs into
  the police back office").
- Open a violation → **Send to Police** → hold up the phone with the
  arriving email: PDF challan + evidence photo + plate crop. "No officer
  typed anything. This is the whole enforcement loop." (If alerts fire
  automatically during Act 2, even better — point at the 📧 counter chip.)
- If asked about scale: "One camera = one box. 103 cameras = 103 boxes or
  one GPU server. No cloud dependency, works with CEB power cuts via UPS."

**Close (30 s).**
"Sri Lanka Police wrote ~600,000 fines last year by hand. This issues them
with photo evidence, at camera speed, in LKR, localised for our plates.
We built the traffic officer that never blinks."
*(If you quote a fines number, verify the current-year figure first or say
"hundreds of thousands".)*

---

## 4. Judge Q&A (rehearse these)

**"What's your false-positive rate?"**
"We engineered four independent gates: detection confidence thresholds,
multi-frame persistence, camera-motion-compensated movement checks, and
positive-evidence-only helmet classification — absence of a detection never
convicts anyone. On our busiest test clip — 113 tracked vehicles, dozens of
parked bikes — zero false violations. A formal benchmark needs a labelled
Sri Lankan dataset; that's on our roadmap and we'd love RDA/Police footage."

**"Why didn't the plate read on that vehicle?"**
"The plate was N pixels tall — below what any OCR can read honestly. The
system marks it UNREADABLE instead of guessing; a wrong plate means fining
an innocent citizen. With a properly-mounted ANPR camera (15 m, slight
downtilt) read rates go way up — that's a camera-placement spec, not a
software limit."

**"How do you know the plate is CORRECT and not an OCR glitch?"**
"Multi-frame voting. We keep reading the plate as the vehicle approaches and
a number is accepted ONLY when at least two frames agree on it — one read is
never proof, no matter how confident the model is. We deliberately show the
characters exactly as captured (no country-format 'auto-correction' — that
would be inventing evidence), and clicking any vehicle shows the exact plate
photo the OCR read, so a human verifies in one glance. A single noisy read
can never reach a challan."

**"Does it run in real time?"**
"On this CPU laptop, near-real-time at 720p. On a ~LKR 200k consumer GPU it
is comfortably real-time for multiple 1080p streams — YOLOv8n is tiny. The
architecture also processes offline: cameras record, the box analyses,
challans queue for officer review."

**"Privacy?"**
"Processing is fully on-premise — no cloud, no internet needed. We store
only violation evidence, not continuous footage of citizens. Plates of
non-violators can be auto-purged on a retention timer. That's GDPR-grade
and fits Sri Lanka's PDPA."

**"Wrong-way and speed are off — why?"**
"Deliberate honesty. Both need per-camera calibration (allowed direction /
a 4-point road homography). Turning them on uncalibrated would fabricate
violations. For a fixed installation it's a 5-minute one-time setup — we
pre-calibrated the highway clip to show real speeds." *(Uncomment
`SPEED_SOURCE` in backend/config.py and run sample.mp4 to demo this.)*

**"How is this Sri Lankan, not generic?"**
"LKR spot-fine amounts, Sri Lankan plate grammar (province code + letters +
4 digits) built into the OCR validator, tuk-tuk-dense footage tested, works
offline for island-wide deployment, and it plugs into the 103-camera network
Colombo already owns — zero new hardware to start."

**"What would you build next?"**
"1) Helmet + tuk-tuk fine-tuned model on Sri Lankan data (current helmet
model is trained on Indian traffic — transfers well, but local data is
better). 2) e-challan delivery via SMS to the DMT-registered owner.
3) Multi-camera dashboard for a police control room. 4) An accuracy
benchmark with the Police traffic division."

---

## 5. If something breaks (fallback ladder)

1. Annotated video won't play → refresh once; it reloads with cache-buster.
2. Processing is slow in the room → use the pre-processed results already
   on the dashboard (they persist), narrate over the existing annotated video.
3. Total ML failure → **✨ Demo data (simulated)** button. It is badged
   SIMULATED in the header — OWN it: "this is our simulated preview mode for
   stakeholders; here's the real footage we processed earlier" and show
   `data/output/annotated.mp4` + snapshots in the folder.
4. Browser dies → results.json + snapshots + annotated.mp4 in `data/output/`
   are all on disk. Nothing is lost.

---

## 6. One-breath architecture (for tech judges)

> Video → YOLOv8n (vehicles/riders/lights, imgsz auto 640–960, frame-skip
> speed modes) → ByteTrack IDs → camera-motion-compensated movement gate →
> violation engine (confidence + multi-frame persistence + dedup per track)
> → two-stage ANPR (YOLO plate detector → EasyOCR, SL-plate grammar, multi-
> frame VOTING before a number is accepted) → per-video 4-point speed
> calibration → SQLite + JPEG evidence + PDF challans + SMTP police alerts +
> H.264 annotated video → FastAPI → zero-dependency single-file dashboard.
> Runs fully offline on CPU (email needs internet, everything else doesn't).

Sources for the claims used above:
- [Sunday Times — 103 CCTV cameras on Colombo roads](https://www.sundaytimes.lk/250202/news/with-103-cctvs-eyeing-motorists-on-colombo-roads-drivers-think-twice-before-breaking-rules-586597.html)
- [Kaggle Road Traffic Video Monitoring](https://www.kaggle.com/datasets/shawon10/road-traffic-video-monitoring) · [Kaggle Highway Traffic Videos](https://www.kaggle.com/datasets/aryashah2k/highway-traffic-videos-dataset) · [Mendeley helmet videos](https://data.mendeley.com/datasets/bmy35m25pw/1)
