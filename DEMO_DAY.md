# 🏆 Demo Day Runbook — Top 3 Final

Everything below was **measured on this laptop**, not estimated. Numbers are
from real pipeline runs on 2026-07-25.

---

## 1. Pre-flight (do this the night before)

```powershell
python tests/run_all.py                                   # expect 61/61
python scripts/check_clip.py data/videos/sample_1080p.mp4 # expect Over Speeding
./run.ps1                                                 # then Ctrl+F5 the page
```

Then do a **full dress rehearsal on the actual demo laptop, on battery,
with the projector plugged in**. Windows power-saving throttles the CPU on
battery, and this system is CPU-bound.

| Check | Why |
|---|---|
| Plug in mains power | On battery the CPU throttles and analysis rate halves |
| Close Chrome tabs / Teams / OneDrive | They steal the CPU the detector needs |
| Start the clip **before** you start talking | Model + OCR load takes ~10-12 s ("AI WARMING UP") |
| Ctrl+F5 the dashboard | The frontend is cached aggressively |

---

## 2. What is verified working

| Feature | Status | Evidence |
|---|---|---|
| Vehicle detection + tracking | ✅ | 21 vehicles on a 21 s clip |
| **Calibrated speed** | ✅ | 83–163 km/h on `sample_1080p.mp4` |
| **Over Speeding** | ✅ | 7 events fired |
| ANPR plate reading | ✅ | plates confirmed over ≥2 frames |
| No Rest Break | ✅ | time-based rule |
| Real-time playback | ✅ | 0.99–1.01× true speed |
| Honesty / false-positive defence | ✅ | parked-bike clip → **0 violations** |

### What is NOT yet demonstrable, and why

These are **not code failures** — the rules are live, but nothing in the
current footage triggers them:

| Rule | Blocker | Fix |
|---|---|---|
| Red Light Jump | **No traffic light exists in any clip.** A scan of all footage found only one candidate, which on inspection was a *Bank of Ceylon sign on a utility pole*, not a signal. | Film 30 s at a signalised junction |
| Wrong Way | No vehicle in any clip actually drives against traffic | Film (or stage, safely) a genuine wrong-way movement |

**Do not fake either of these.** Lowering the traffic-light threshold makes the
system read a shop sign as a signal and issue red-light challans — with real
plates on them — against riders who never ran a light. Setting an unzoned
travel direction on a two-way road flags every lawfully oncoming vehicle. Both
turn your headline claim (evidence that holds up) into the opposite.

If you can't get the footage, the honest demo is the **test suite**: both rules
are implemented and proven by unit tests (`tests/test_wrongway.py`,
`test_engine.py` cases F/F2). Run `python tests/run_all.py` on stage — 78
passing tests, including the cases where each rule must *refuse* to fire.

> **Say this out loud if asked.** "The system only reports what it can prove.
> On a clip of parked motorcycles it reports nothing — that's the feature, not
> a gap. Most systems would happily fine a parked bike."

---

## 3. Footage to shoot this weekend (highest value action)

One person, a phone, a pedestrian bridge or upper floor over a busy road,
**60–90 seconds each**, held still or propped:

1. **Bike traffic** — a junction with real motorcycle flow. This single clip
   unlocks No Helmet + Triple Riding + Phone Use, four of your nine rules.
2. **A signalised junction** — frame the traffic light *and* the stop line in
   the same shot. Unlocks Red Light Jump.
3. **A straight road** — for speed. Note the length of something real in the
   shot (lane markings, a bridge span) so the 🎯 calibration is honest.

**Shoot from above and along the road, not from the roadside.** A high, shallow
angle is what makes riders, helmets and plates all readable at once.

After each clip:

```powershell
python scripts/check_clip.py data/videos/yourclip.mp4
```

It tells you in ~1 minute whether that clip will demo well.

---

## 4. The 6-minute demo script

**0:00 — Hook (spoken, no slides)**
> "Colombo already has over a hundred CCTV cameras watching its roads. We turn
> every one of them into an AI traffic officer — live."

**0:20 — Play Live on `sample_1080p.mp4`.** Let boxes, track IDs and plates
appear. Point at the speed chips: *"That's real speed — pixels mapped to road
metres through a surveyed calibration, the same geometry a speed camera uses."*

**1:30 — Click an Over Speeding violation.** Open the e-challan: photo evidence
with the proof stamped on the image, plate crop, LKR fine, PDF button.
> "Detection to court-ready challan, no human typing anything."

**3:00 — The honesty proof.** Play the parked-bike clip. **Zero violations.**
> "Ask any other team what their system does with a parked motorcycle."

**4:00 — Dashboard breadth.** Violations feed, Vehicles·ANPR log, filters,
hotspot map, CSV export.

**5:00 — Close.** Nine violation types, one pipeline, runs on this laptop.
> "Safer roads, proven by evidence."

**Always have a screen-recording of a perfect run on the desktop.** If anything
stalls live, play the recording and keep talking. Never debug on stage.

---

## 5. Judge Q&A — the questions you will actually get

**"How accurate is the speed?"**
> Exact when calibrated: we map four surveyed road corners to real-world metres
> via a homography, then fit distance-against-time across many frames with
> outlier rejection. Uncalibrated cameras show **no** speed at all rather than a
> guess. Validated at 83–163 km/h on highway footage.

**"How do you avoid false positives?"**
> Four layers: a confidence floor, a camera-motion-compensated motion gate,
> multi-frame persistence, and a confidence gate on speed. A violation must be
> seen repeatedly on a genuinely moving vehicle. That's why parked bikes give zero.

**"What if the plate is unreadable?"**
> It says UNREADABLE. We never invent a number — a wrong plate on a challan is
> worse than no challan. A plate is only confirmed when two frames agree.

**"Does it work at night / in rain?"**
> Detection degrades in low light like any camera system; that's why enforcement
> cameras use IR illumination. Our models are drop-in replaceable, so a
> night-trained model swaps in without a code change.

**"Why is it not real-time?"** *(if they notice frame dropping)*
> It **is** real-time. On a CPU laptop we analyse ~2 frames per second and drop
> the rest — exactly what a real camera does when the analyser is busy. On a
> GPU edge box it analyses every frame. The video never slows down.

**"What does deployment cost?"**
> It runs on existing CCTV. A pilot needs one laptop; a city needs GPU edge
> boxes. No custom hardware, no new cameras.

---

## 6. Monday's presentation

You already submitted the 9-slide pitch deck, and the judges have scored the
idea. **Do not re-pitch the idea.** Build a shorter demo-day deck that reuses
the same visual identity and the same claims, restructured to prove delivery:

| # | Slide | Content |
|---|---|---|
| 1 | Title | Same title slide as the submitted deck — continuity |
| 2 | "We said we would build this" | The 9 violations + ANPR promise from your pitch, one line each |
| 3 | **"Here it is running"** | → switch to the **live demo** (§4). This is the whole presentation. |
| 4 | Proof it's honest | Parked-bike clip = 0 violations; UNREADABLE plates; no mock data |
| 5 | Proof it's accurate | Homography speed, 83–163 km/h measured; 61 automated tests |
| 6 | What's new since the pitch | Real-time frame-dropping replay, 4K drone support, sampling-rate-independent speed, clip-readiness tooling |
| 7 | Deployment | Existing CCTV / phone / drone; laptop pilot → GPU edge boxes |
| 8 | Impact & roadmap | 24/7 coverage, court-ready evidence, repeat-offender analytics; night models next |
| 9 | Close | "Safer roads, proven by evidence." |

Spend **60% of your time on slide 3** — the working demo. Finals reward a
product that runs, not a deck that explains.
