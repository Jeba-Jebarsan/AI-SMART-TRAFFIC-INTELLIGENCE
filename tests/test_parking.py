"""Unit tests for the Illegal Parking rule.

The hard part of this rule is what it must NOT do: a vehicle stopped at a red
light or crawling in a jam is behaving lawfully, and fining it would be exactly
the kind of false positive this system is built to avoid.
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

import config
from violations import ViolationEngine

W, H, FPS = 1000, 1000, 25
PASSED = []


def check(name, cond):
    PASSED.append((name, bool(cond)))
    print(("PASS" if cond else "FAIL"), "-", name)


def car(tid, cx, cy, conf=0.9):
    return {"track_id": tid, "cls": config.COCO["car"], "conf": conf,
            "box": [cx - 30, cy - 25, cx + 30, cy + 25]}


def run(eng, tid, frames, signal="UNKNOWN", move_px=0.0, x0=500, y0=500):
    """Drive a track for `frames` frames at `move_px` per frame."""
    events = []
    for f in range(frames):
        y = y0 + f * move_px
        events += eng.update(f, [car(tid, x0, y)], signal, [])
    return events


SECS = config.ILLEGAL_PARK_SECONDS
STOPPED_FRAMES = int((SECS + 3) * FPS)

# --- 1: a genuinely stationary vehicle IS eventually flagged, exactly once
eng = ViolationEngine(W, H, FPS)
ev = run(eng, 1, STOPPED_FRAMES)
parks = [e for e in ev if e["type"] == "Illegal Parking"]
check("stationary vehicle past the threshold fires Illegal Parking",
      len(parks) == 1)
check("the event records how long it was parked",
      parks and parks[0].get("parked_seconds", 0) >= SECS)

# --- 2: a vehicle stopped at a RED light is lawful -> never fires
eng = ViolationEngine(W, H, FPS)
ev = run(eng, 2, STOPPED_FRAMES, signal="RED")
check("vehicle stopped at a red light never fires Illegal Parking",
      not any(e["type"] == "Illegal Parking" for e in ev))

# --- 3: a MOVING vehicle never fires, however long it is tracked
eng = ViolationEngine(W, H, FPS)
ev = run(eng, 3, STOPPED_FRAMES, move_px=6.0)
check("moving vehicle never fires Illegal Parking",
      not any(e["type"] == "Illegal Parking" for e in ev))

# --- 4: stopping BRIEFLY (a queue) is not parking
eng = ViolationEngine(W, H, FPS)
ev = run(eng, 4, int(FPS * (SECS * 0.5)))
check("a short stop (traffic queue) does not fire",
      not any(e["type"] == "Illegal Parking" for e in ev))

# --- 5: moving again RESETS the clock, so a stop-start vehicle never trips it
eng = ViolationEngine(W, H, FPS)
events = []
f = 0
for _cycle in range(4):
    for _ in range(int(FPS * (SECS * 0.6))):        # stop for 60% of the limit
        events += eng.update(f, [car(5, 500, 500)], "UNKNOWN", [])
        f += 1
    for i in range(int(FPS * 2)):                   # then genuinely move off
        events += eng.update(f, [car(5, 500, 500 + i * 8)], "UNKNOWN", [])
        f += 1
check("stop-start driving never accumulates into Illegal Parking",
      not any(e["type"] == "Illegal Parking" for e in events))

# --- 6: the no-parking ZONE confines the rule to the configured area
config.NO_PARKING_ZONE = [[0, 0], [200, 0], [200, 200], [0, 200]]  # top-left only
try:
    eng = ViolationEngine(W, H, FPS)
    ev = run(eng, 6, STOPPED_FRAMES, x0=500, y0=500)               # outside it
    check("stationary vehicle OUTSIDE the no-parking zone does not fire",
          not any(e["type"] == "Illegal Parking" for e in ev))

    eng = ViolationEngine(W, H, FPS)
    ev = run(eng, 7, STOPPED_FRAMES, x0=100, y0=100)               # inside it
    check("stationary vehicle INSIDE the no-parking zone does fire",
          any(e["type"] == "Illegal Parking" for e in ev))
finally:
    config.NO_PARKING_ZONE = None

# --- 7: the rule can be switched off entirely
config.ENABLE["illegal_parking"] = False
try:
    eng = ViolationEngine(W, H, FPS)
    ev = run(eng, 8, STOPPED_FRAMES)
    check("disabling illegal_parking suppresses the rule",
          not any(e["type"] == "Illegal Parking" for e in ev))
finally:
    config.ENABLE["illegal_parking"] = True

n_fail = sum(1 for _, ok in PASSED if not ok)
print(f"\n{len(PASSED) - n_fail}/{len(PASSED)} passed")
sys.exit(1 if n_fail else 0)
