"""Unit tests for the AI speed-estimation module (backend/speed.py) as wired
into the ViolationEngine: perspective transform + multi-frame regression +
outlier rejection + confidence gating + over-speed enforcement.

A clean full-frame calibration quad is used so image-Y maps LINEARLY to road
metres, giving a known ground-truth speed we can assert against.
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

import config
from violations import ViolationEngine
from pipeline import make_transform_fn

W, H, FPS = 1000, 1000, 25
TARGET_M = (10, 100)                 # 10 m wide, 100 m long road region
# full-frame quad (far-left, far-right, near-right, near-left) => road_y = y*99/1000
QUAD = [[0, 0], [W, 0], [W, H], [0, H]]
PASSED = []


def check(name, cond):
    PASSED.append((name, bool(cond)))
    print(("PASS" if cond else "FAIL"), "-", name)


def car(tid, cx, y2, conf=0.9):
    """A car whose bottom-centre is (cx, y2)."""
    return {"track_id": tid, "cls": config.COCO["car"], "conf": conf,
            "box": [cx - 20, y2 - 40, cx + 20, y2]}


def new_engine(calibrated=True):
    fn = make_transform_fn(QUAD, TARGET_M) if calibrated else None
    return ViolationEngine(W, H, FPS, transform_fn=fn)


def run(eng, tid, step_px, frames, y0=300, outlier_at=None, outlier_px=300):
    """Drive one track downward at `step_px`/frame; return all events."""
    events = []
    for f in range(frames):
        y2 = y0 + f * step_px
        if outlier_at is not None and f == outlier_at:
            y2 += outlier_px            # single bad tracker frame
        events += eng.update(f, [car(tid, 500, y2)], "UNKNOWN", [])
    return events


# --- 0a: DEFAULT (SPEED_APPROX off) -> uncalibrated camera shows NO speed
# (exact-only, so no "random" numbers)
config.SPEED_APPROX = False
eng = new_engine(calibrated=False)
run(eng, 2, step_px=8.1, frames=40)
check("default (approx off) -> uncalibrated moving vehicle shows no speed",
      eng.speed_of(2) is None)

# --- 0b: opt-in approx (SPEED_APPROX on) -> a rough number, never a fine
config.SPEED_APPROX = True
eng = new_engine(calibrated=False)
ev = run(eng, 1, step_px=8.1, frames=40)
check("approx on -> uncalibrated moving vehicle shows a ~number",
      isinstance(eng.speed_of(1), int) and eng.speed_of(1) > 0)
check("approx on -> estimator is NOT confident (no fine basis)",
      not eng.speed_est.confident(1))
check("approx on -> no Over Speeding fired (approx never fines)",
      not any(e["type"] == "Over Speeding" for e in ev))
# a PARKED vehicle whose tracker box jitters shows NO speed (motion gate) —
# this is the "parked bike shows 10 km/h" bug. Tested with realistic jitter.
import random as _r
_r.seed(1)
eng = new_engine(calibrated=False)          # approx mode
for f in range(60):
    jx, jy = _r.uniform(-6, 6), _r.uniform(-6, 6)
    eng.update(f, [car(7, 500 + jx, 300 + jy)], "UNKNOWN", [])
check("no calibration -> jittering PARKED bike shows no speed",
      eng.speed_of(7) is None)
eng = new_engine()                           # calibrated mode, same parked jitter
for f in range(60):
    jx, jy = _r.uniform(-6, 6), _r.uniform(-6, 6)
    eng.update(f, [car(8, 500 + jx, 300 + jy)], "UNKNOWN", [])
check("calibrated -> jittering PARKED bike shows no speed",
      eng.speed_of(8) is None)

# --- 1: calibrated + genuinely fast (~72 km/h) -> confident, fires exactly once
eng = new_engine()
ev = run(eng, 2, step_px=8.1, frames=40)     # 8.1px/f * 0.099 m/px / 0.04s ~= 72 km/h
speeders = [e for e in ev if e["type"] == "Over Speeding"]
check("fast vehicle: confident speed estimate",
      eng.speed_est.confident(2))
check("fast vehicle: Over Speeding fires exactly once",
      len(speeders) == 1)
check("fast vehicle: reported speed is in a sane ~72 km/h band",
      speeders and 60 < speeders[0]["speed_kmph"] < 90)
check("fast vehicle: speed_of returns a rounded km/h int > limit",
      isinstance(eng.speed_of(2), int) and eng.speed_of(2) > config.SPEED_LIMIT_KMPH)
check("fast vehicle: top_speed recorded",
      eng.speed_est.top_speed(2) > config.SPEED_LIMIT_KMPH)

# --- 2: calibrated + slow (~18 km/h) -> confident but UNDER the limit, no fire
eng = new_engine()
ev = run(eng, 3, step_px=2.0, frames=40)      # ~18 km/h
check("slow vehicle: confident", eng.speed_est.confident(3))
check("slow vehicle: speed_of in a sane low band",
      8 < eng.speed_of(3) < 30)
check("slow vehicle: never fires Over Speeding",
      not any(e["type"] == "Over Speeding" for e in ev))

# --- 3: too-short track -> NOT confident -> can never issue a fine
eng = new_engine()
ev = run(eng, 4, step_px=8.1, frames=4)       # only 4 samples
check("short track: not confident", not eng.speed_est.confident(4))
check("short track: no Over Speeding",
      not any(e["type"] == "Over Speeding" for e in ev))

# --- 4: OUTLIER REJECTION — one wild tracker jump must not spike the speed or
#        manufacture a speeding fine on a genuinely ~50 km/h (under-limit) car
eng_clean = new_engine()
run(eng_clean, 5, step_px=5.6, frames=40)     # ~50 km/h, clean
clean_spd = eng_clean.speed_of(5)

eng_out = new_engine()
ev_out = run(eng_out, 6, step_px=5.6, frames=40, outlier_at=20, outlier_px=350)
out_spd = eng_out.speed_of(6)
check("outlier: clean run is confident and under the limit",
      eng_clean.speed_est.confident(5) and clean_spd <= config.SPEED_LIMIT_KMPH)
check("outlier: one bad frame stays within ~12 km/h of the clean estimate",
      out_spd is not None and abs(out_spd - clean_spd) <= 12)
check("outlier: no false Over Speeding fine from the spike",
      not any(e["type"] == "Over Speeding" for e in ev_out))

# --- 5: wall-clock timestamps override frame_idx/fps (live-camera accuracy).
# Same pixel motion, but we tell the engine only HALF the time elapsed per frame
# (camera actually running ~2x the assumed fps) -> measured speed must ~double.
eng_ts = new_engine()
for f in range(40):
    y2 = 300 + f * 8.1
    t = (f / FPS) / 2.0                       # real elapsed = half of frame/fps
    eng_ts.update(f, [car(20, 500, y2)], "UNKNOWN", [], [], None, t)
eng_base = new_engine()
for f in range(40):
    eng_base.update(f, [car(21, 500, 300 + f * 8.1)], "UNKNOWN", [])
check("wall-clock timestamp is used (half the time -> ~2x the speed)",
      eng_ts.speed_of(20) is not None and eng_base.speed_of(21) is not None
      and eng_ts.speed_of(20) > eng_base.speed_of(21) * 1.6)

n_fail = sum(1 for _, ok in PASSED if not ok)
print(f"\n{len(PASSED) - n_fail}/{len(PASSED)} passed")
sys.exit(1 if n_fail else 0)
