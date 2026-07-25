"""Unit tests for Wrong Way driving.

The dangerous failure here is the opposite of a miss: on a two-way road the
oncoming carriageway is lawfully travelling against the policed direction, so
an unzoned rule would fine every legitimate vehicle in view. These tests pin
down both that the rule fires on a genuine wrong-way driver and that it stays
silent on lawful opposing traffic.
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


def drive(eng, tid, x, y0, dy, frames=30):
    """Drive a track vertically at dy px/frame; return the events."""
    events = []
    for f in range(frames):
        events += eng.update(f, [car(tid, x, y0 + f * dy)], "UNKNOWN", [])
    return events


def wrongs(events):
    return [e for e in events if e["type"] == "Wrong Way"]


DOWN = (0, 1)      # allowed direction: travelling DOWN the image

# --- 1: no direction calibrated -> rule is off entirely (honest default)
eng = ViolationEngine(W, H, FPS)
ev = drive(eng, 1, 500, 800, -12)          # driving UP, against nothing
check("no calibrated direction -> Wrong Way never fires",
      not wrongs(ev))

# --- 2: calibrated, vehicle travelling the ALLOWED way -> no event
eng = ViolationEngine(W, H, FPS, allowed_direction=DOWN)
ev = drive(eng, 2, 500, 200, 12)           # going down = correct
check("vehicle travelling the allowed direction never fires",
      not wrongs(ev))

# --- 3: calibrated, vehicle travelling AGAINST it -> fires exactly once
eng = ViolationEngine(W, H, FPS, allowed_direction=DOWN)
ev = drive(eng, 3, 500, 800, -12)          # going up = wrong way
check("genuine wrong-way driver fires exactly once", len(wrongs(ev)) == 1)

# --- 4: a STATIONARY vehicle never fires (motion gate), however long it sits
eng = ViolationEngine(W, H, FPS, allowed_direction=DOWN)
ev = drive(eng, 4, 500, 500, 0, frames=60)
check("parked vehicle never fires Wrong Way", not wrongs(ev))

# --- 5: THE ZONE TEST — on a two-way road, opposing traffic outside the
# policed lane must stay clean while a wrong-way driver inside it is caught.
config.WRONG_WAY_ZONE = [[0, 0], [500, 0], [500, 1000], [0, 1000]]  # left half
try:
    eng = ViolationEngine(W, H, FPS, allowed_direction=DOWN)
    ev = drive(eng, 5, 800, 800, -12)      # oncoming traffic, RIGHT half
    check("lawful opposing traffic outside the policed lane never fires",
          not wrongs(ev))

    eng = ViolationEngine(W, H, FPS, allowed_direction=DOWN)
    ev = drive(eng, 6, 200, 800, -12)      # wrong way INSIDE the policed lane
    check("wrong-way driver inside the policed lane still fires",
          len(wrongs(ev)) == 1)
finally:
    config.WRONG_WAY_ZONE = None

# --- 6: a low-confidence detection is never enough to fine someone
eng = ViolationEngine(W, H, FPS, allowed_direction=DOWN)
ev = []
for f in range(30):
    ev += eng.update(f, [car(7, 500, 800 - f * 12, conf=0.20)], "UNKNOWN", [])
check("low-confidence vehicle never fires Wrong Way", not wrongs(ev))

# --- 7: the rule can be switched off
config.ENABLE["wrong_way"] = False
try:
    eng = ViolationEngine(W, H, FPS, allowed_direction=DOWN)
    ev = drive(eng, 8, 500, 800, -12)
    check("disabling wrong_way suppresses the rule", not wrongs(ev))
finally:
    config.ENABLE["wrong_way"] = True

n_fail = sum(1 for _, ok in PASSED if not ok)
print(f"\n{len(PASSED) - n_fail}/{len(PASSED)} passed")
sys.exit(1 if n_fail else 0)
