import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

import config
from violations import ViolationEngine

W, H, FPS = 1280, 720, 25
PASSED = []


def check(name, cond):
    PASSED.append((name, bool(cond)))
    print(("PASS" if cond else "FAIL"), "-", name)


def car(tid, x, y, w=160, h=110, conf=0.9):
    return {"track_id": tid, "cls": config.COCO["car"], "conf": conf,
            "box": [x, y, x + w, y + h]}


THRESH_FRAMES = int(config.MAX_CONTINUOUS_DRIVE_SECONDS * FPS) + 60  # + is_moving warmup margin

# --- continuously moving car exceeds the threshold -> fires exactly once
eng = ViolationEngine(W, H, FPS)
events = []
x = 100
for f in range(THRESH_FRAMES):
    x += 6
    v = car(1, x, 400)
    events += eng.update(f, [v], "UNKNOWN", [])
fired = [e for e in events if e["type"] == "No Rest Break"]
check("continuous driver fires exactly once past the threshold",
      len(fired) == 1 and fired[0]["drive_seconds"] >= config.MAX_CONTINUOUS_DRIVE_SECONDS)

# --- short stop (traffic light, < BREAK_MIN_STOP_SECONDS) does NOT reset the clock
eng = ViolationEngine(W, H, FPS)
events = []
x = 100
half = THRESH_FRAMES // 2
for f in range(half):
    x += 6
    events += eng.update(f, [car(2, x, 400)], "UNKNOWN", [])
stop_frames = int((config.BREAK_MIN_STOP_SECONDS - 1) * FPS)   # shorter than the break rule
for f in range(half, half + stop_frames):
    events += eng.update(f, [car(2, x, 400)], "UNKNOWN", [])   # not moving
for f in range(half + stop_frames, THRESH_FRAMES + stop_frames):
    x += 6
    events += eng.update(f, [car(2, x, 400)], "UNKNOWN", [])
fired2 = [e for e in events if e["type"] == "No Rest Break"]
check("short traffic-light stop does not reset the continuous-drive clock",
      len(fired2) == 1)

# --- a genuine break (>= BREAK_MIN_STOP_SECONDS) resets the clock: no fire within a
# fresh short drive afterwards, and the rule re-arms for a second long stretch
eng = ViolationEngine(W, H, FPS)
events = []
x = 100
for f in range(half):
    x += 6
    events += eng.update(f, [car(3, x, 400)], "UNKNOWN", [])
long_stop = int((config.BREAK_MIN_STOP_SECONDS + 2) * FPS)
for f in range(half, half + long_stop):
    events += eng.update(f, [car(3, x, 400)], "UNKNOWN", [])   # genuine break
check("no violation yet right after a genuine break (clock reset)",
      len([e for e in events if e["type"] == "No Rest Break"]) == 0)
for f in range(half + long_stop, half + long_stop + THRESH_FRAMES):
    x += 6
    events += eng.update(f, [car(3, x, 400)], "UNKNOWN", [])
check("rule re-arms and fires again after a genuine break + a new long stretch",
      len([e for e in events if e["type"] == "No Rest Break"]) == 1)

# --- parked car (never moving) never fires
eng = ViolationEngine(W, H, FPS)
events = []
for f in range(THRESH_FRAMES):
    events += eng.update(f, [car(4, 400, 500)], "UNKNOWN", [])
check("parked car never fires no-rest-break",
      len([e for e in events if e["type"] == "No Rest Break"]) == 0)

n_fail = sum(1 for _, ok in PASSED if not ok)
print(f"\n{len(PASSED)-n_fail}/{len(PASSED)} passed")
sys.exit(1 if n_fail else 0)
