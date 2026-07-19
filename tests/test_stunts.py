"""Unit tests for the two new illegal-behaviour rules:
  * Wheelie / stunt riding  (relative bounding-box aspect-ratio spike)
  * Mobile phone use        (COCO cell-phone associated to a moving occupant)

Same false-positive discipline as every other rule: motion gate + multi-frame
persistence, and — for the wheelie — a per-bike baseline so a normally tall
rear-view rider is NOT mistaken for a stunt.
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

import config
from violations import ViolationEngine
from pipeline import build_phone_status

W, H, FPS = 1280, 720, 25
PASSED = []


def check(name, cond):
    PASSED.append((name, bool(cond)))
    print(("PASS" if cond else "FAIL"), "-", name)


def moto(tid, box, conf=0.9):
    return {"track_id": tid, "cls": config.COCO["motorcycle"], "conf": conf, "box": box}


def rider(tid, box, n=1):
    return {"track_id": tid, "box": box, "no_helmet": False,
            "helmet_ok": False, "riders": n}


def car(tid, x, y, w=160, h=110, conf=0.9):
    return {"track_id": tid, "cls": config.COCO["car"], "conf": conf,
            "box": [x, y, x + w, y + h]}


# ===================== WHEELIE / STUNT =====================

# --- moving bike whose box aspect SPIKES (front lifts) -> fires exactly once
eng = ViolationEngine(W, H, FPS)
events = []
x = 100
for f in range(70):
    x += 6                                   # moving
    if f < 24:
        box = [x, 400, x + 120, 520]         # aspect 1.0 (normal baseline)
    else:
        box = [x, 250, x + 90, 520]          # aspect 3.0 (wheelie spike)
    events += eng.update(f, [moto(1, box)], "UNKNOWN", [rider(1, box)])
wheelies = [e for e in events if e["type"] == "Wheelie Stunt"]
check("wheelie: aspect spike on a moving bike fires exactly once",
      len(wheelies) == 1)

# --- normal moving bike (constant ~1.0 aspect) -> never fires
eng = ViolationEngine(W, H, FPS)
events = []
x = 100
for f in range(70):
    x += 6
    box = [x, 400, x + 120, 520]
    events += eng.update(f, [moto(2, box)], "UNKNOWN", [rider(2, box)])
check("wheelie: normal-aspect moving bike never fires",
      not any(e["type"] == "Wheelie Stunt" for e in events))

# --- consistently TALL rear-view rider (aspect ~2.4 the whole time) -> never
# fires (relative-to-own-baseline logic, not an absolute threshold)
eng = ViolationEngine(W, H, FPS)
events = []
x = 100
for f in range(70):
    x += 6
    box = [x, 300, x + 100, 540]             # aspect 2.4, constant
    events += eng.update(f, [moto(3, box)], "UNKNOWN", [rider(3, box)])
check("wheelie: consistently tall rear-view rider never fires",
      not any(e["type"] == "Wheelie Stunt" for e in events))

# --- parked bike with a tall box -> motion gate blocks it -> never fires
eng = ViolationEngine(W, H, FPS)
events = []
for f in range(70):
    box = [400, 250, 490, 520]               # tall but stationary
    events += eng.update(f, [moto(4, box)], "UNKNOWN", [rider(4, box)])
check("wheelie: parked tall bike never fires (motion gate)",
      not any(e["type"] == "Wheelie Stunt" for e in events))

# ===================== MOBILE PHONE USE =====================

# --- moving vehicle, phone in hand every frame -> fires exactly once
eng = ViolationEngine(W, H, FPS)
events = []
x = 100
for f in range(60):
    x += 6
    v = car(1, x, 400)
    ph = [{"track_id": 1, "box": v["box"], "phone": True}]
    events += eng.update(f, [v], "UNKNOWN", [], [], ph)
check("phone: moving driver on a phone fires exactly once",
      len([e for e in events if e["type"] == "Mobile Phone Use"]) == 1)

# --- moving vehicle, no phone -> never fires
eng = ViolationEngine(W, H, FPS)
events = []
x = 100
for f in range(60):
    x += 6
    v = car(2, x, 400)
    ph = [{"track_id": 2, "box": v["box"], "phone": False}]
    events += eng.update(f, [v], "UNKNOWN", [], [], ph)
check("phone: no phone never fires",
      not any(e["type"] == "Mobile Phone Use" for e in events))

# --- single-frame phone flicker -> persistence suppresses it
eng = ViolationEngine(W, H, FPS)
events = []
x = 100
for f in range(60):
    x += 6
    v = car(3, x, 400)
    ph = [{"track_id": 3, "box": v["box"], "phone": (f == 30)}]
    events += eng.update(f, [v], "UNKNOWN", [], [], ph)
check("phone: one-frame flicker suppressed",
      not any(e["type"] == "Mobile Phone Use" for e in events))

# --- parked vehicle on a phone -> motion gate blocks it
eng = ViolationEngine(W, H, FPS)
events = []
for f in range(60):
    v = car(4, 400, 400)                     # stationary
    ph = [{"track_id": 4, "box": v["box"], "phone": True}]
    events += eng.update(f, [v], "UNKNOWN", [], [], ph)
check("phone: parked vehicle never fires (motion gate)",
      not any(e["type"] == "Mobile Phone Use" for e in events))

# --- association helper: a phone over a moto rider is attributed to the bike
moto_box = [100, 300, 220, 470]
person_box = [120, 300, 200, 430]            # rider sitting on the bike
phone_box = [150, 360, 175, 395]             # small phone inside the rider box
out = build_phone_status([{"track_id": 1, "box": moto_box}], [],
                         [{"track_id": 9, "box": person_box}], [phone_box])
check("phone: build_phone_status attributes a phone to the moto rider",
      bool(out) and out[0]["phone"] is True)
out2 = build_phone_status([{"track_id": 1, "box": moto_box}], [],
                          [{"track_id": 9, "box": person_box}], [])
check("phone: no phones -> phone False (and vehicle still reported for decay)",
      bool(out2) and out2[0]["phone"] is False)

n_fail = sum(1 for _, ok in PASSED if not ok)
print(f"\n{len(PASSED) - n_fail}/{len(PASSED)} passed")
sys.exit(1 if n_fail else 0)
