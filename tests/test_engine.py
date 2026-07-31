"""Unit tests for the false-positive defences in ViolationEngine + ocr.normalize_plate."""
import os
import random
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

import config
from violations import ViolationEngine

W, H, FPS = 1280, 720, 25
PASSED = []
random.seed(42)


def check(name, cond):
    PASSED.append((name, bool(cond)))
    print(("PASS" if cond else "FAIL"), "-", name)


def moto(tid, x, y, w=120, h=90, conf=0.9):
    return {"track_id": tid, "cls": 3, "conf": conf, "box": [x, y, x + w, y + h]}


def rider(tid, box, no_helmet=True, helmet_ok=False, n=1):
    return {"track_id": tid, "box": box, "no_helmet": no_helmet,
            "helmet_ok": helmet_ok, "riders": n}


# --- A: parked moto flagged no-helmet every frame -> must NEVER fire
eng = ViolationEngine(W, H, FPS)
events = []
for f in range(60):
    v = moto(1, 400, 500)                     # stationary
    events += eng.update(f, [v], "UNKNOWN", [rider(1, v["box"])])
check("A parked bike never fires no-helmet", len(events) == 0)

# --- B: moving moto, bare head each frame -> exactly ONE event after persistence
eng = ViolationEngine(W, H, FPS)
events = []
for f in range(60):
    v = moto(2, 100 + f * 6, 400)             # moving right 6px/frame
    events += eng.update(f, [v], "UNKNOWN", [rider(2, v["box"])])
check("B moving bare-head rider fires exactly once",
      len(events) == 1 and events[0]["type"] == "No Helmet")

# --- C: moving moto with helmet -> never fires
eng = ViolationEngine(W, H, FPS)
events = []
for f in range(60):
    v = moto(3, 100 + f * 6, 400)
    events += eng.update(f, [v], "UNKNOWN",
                         [rider(3, v["box"], no_helmet=False, helmet_ok=True)])
check("C helmeted rider never fires", len(events) == 0)

# --- C2: flicker (1 bad frame among good) -> never fires
eng = ViolationEngine(W, H, FPS)
events = []
for f in range(60):
    v = moto(4, 100 + f * 6, 400)
    bad = (f == 20)                           # single-frame false detection
    events += eng.update(f, [v], "UNKNOWN",
                         [rider(4, v["box"], no_helmet=bad, helmet_ok=not bad)])
check("C2 one-frame flicker suppressed", len(events) == 0)

# --- D: camera pan — 6 parked bikes all shift together, all flagged bare
eng = ViolationEngine(W, H, FPS)
events = []
for f in range(60):
    vs = [moto(10 + i, 100 + i * 150 + f * 8, 500) for i in range(6)]  # global +8px
    rs = [rider(10 + i, vs[i]["box"]) for i in range(6)]
    events += eng.update(f, vs, "UNKNOWN", rs)
check("D camera pan over parked bikes never fires", len(events) == 0)

# --- D2: pan + ONE genuinely moving rider among 6 -> exactly that one fires
eng = ViolationEngine(W, H, FPS)
events = []
for f in range(60):
    vs = [moto(20 + i, 100 + i * 150 + f * 8, 500) for i in range(5)]
    vs.append(moto(29, 100 + f * 16, 300))    # moves 8px/frame relative to pan
    rs = [rider(v["track_id"], v["box"]) for v in vs]
    events += eng.update(f, vs, "UNKNOWN", rs)
check("D2 pan: only the truly moving rider fires",
      len(events) == 1 and events[0]["track_id"] == 29)

# --- E: triple riding needs persistence + motion
eng = ViolationEngine(W, H, FPS)
events = []
for f in range(60):
    v = moto(5, 100 + f * 6, 400)
    events += eng.update(f, [v], "UNKNOWN",
                         [rider(5, v["box"], no_helmet=False, n=3)])
check("E moving triple-riding fires once",
      len(events) == 1 and events[0]["type"] == "Triple Riding")

eng = ViolationEngine(W, H, FPS)
events = []
for f in range(60):
    v = moto(6, 400, 500)                     # parked
    events += eng.update(f, [v], "UNKNOWN",
                         [rider(6, v["box"], no_helmet=False, n=3)])
check("E2 parked 'triple' (mannequins) never fires", len(events) == 0)

# --- F: red-light needs RED streak + moving vehicle crossing line
# (car tracked for ~2/3s before reaching the line, like real approaches)
# The stop line is per-camera calibration, not a global default, so set it
# here exactly as pipeline.load_stop_line_y does for a real deployment.
STOP_LINE_FRAC = 0.55
eng = ViolationEngine(W, H, FPS)
eng.stop_line_y = STOP_LINE_FRAC * H
events = []
y0 = STOP_LINE_FRAC * H - 160
for f in range(40):
    car = {"track_id": 7, "cls": 2, "conf": 0.9,
           "box": [600, y0 + f * 8, 720, y0 + f * 8 + 90]}
    sig = eng.signal_state(f, "RED")          # detected red every frame
    events += eng.update(f, [car], sig, [])
check("F red-light jump fires once with streak+motion",
      len(events) == 1 and events[0]["type"] == "Red Light Jump")

# F1b: an UNCALIBRATED camera has no stop line, so nothing can cross it.
# Guessing the line's position fined vehicles mid-junction; refusing is right.
eng = ViolationEngine(W, H, FPS)
assert eng.stop_line_y is None, "engine must start with no stop line"
events = []
for f in range(40):
    car = {"track_id": 71, "cls": 2, "conf": 0.9,
           "box": [600, y0 + f * 8, 720, y0 + f * 8 + 90]}
    sig = eng.signal_state(f, "RED")
    events += eng.update(f, [car], sig, [])
check("F1b uncalibrated camera never fires Red Light Jump", len(events) == 0)

# F2: single-frame red flicker -> not armed -> no event
eng = ViolationEngine(W, H, FPS)
eng.stop_line_y = STOP_LINE_FRAC * H
events = []
for f in range(40):
    car = {"track_id": 8, "cls": 2, "conf": 0.9,
           "box": [600, y0 + f * 8, 720, y0 + f * 8 + 90]}
    det = "RED" if f == 18 else "GREEN"       # red only one frame
    sig = eng.signal_state(f, det)
    events += eng.update(f, [car], sig, [])
check("F2 one-frame red flicker never fires", len(events) == 0)

# G: low-confidence vehicle never triggers red-light
eng = ViolationEngine(W, H, FPS)
events = []
for f in range(40):
    car = {"track_id": 9, "cls": 2, "conf": 0.20,   # below CONF['vehicle']
           "box": [600, y0 + f * 8, 720, y0 + f * 8 + 90]}
    sig = eng.signal_state(f, "RED")
    events += eng.update(f, [car], sig, [])
check("G low-conf vehicle suppressed", len(events) == 0)

# --- A2: parked bike WITH REALISTIC BOX JITTER (the real-world killer)
eng = ViolationEngine(W, H, FPS)
events = []
for f in range(90):
    jx, jy = random.uniform(-2.5, 2.5), random.uniform(-2.5, 2.5)
    v = moto(31, 400 + jx, 500 + jy)          # parked, tracker box wobbling
    events += eng.update(f, [v], "UNKNOWN", [rider(31, v["box"])])
check("A2 jittering parked bike never fires", len(events) == 0)

# A3: 360p case (small frame => small thresholds) with jitter
eng = ViolationEngine(640, 360, 30)
events = []
for f in range(90):
    jx, jy = random.uniform(-2.0, 2.0), random.uniform(-2.0, 2.0)
    v = moto(32, 300 + jx, 250 + jy, w=70, h=60)
    events += eng.update(f, [v], "UNKNOWN", [rider(32, v["box"])])
check("A3 jittering parked bike (360p) never fires", len(events) == 0)

# A4: genuinely moving rider WITH jitter still fires exactly once
eng = ViolationEngine(W, H, FPS)
events = []
for f in range(60):
    jx, jy = random.uniform(-2.5, 2.5), random.uniform(-2.5, 2.5)
    v = moto(33, 100 + f * 6 + jx, 400 + jy)
    events += eng.update(f, [v], "UNKNOWN", [rider(33, v["box"])])
check("A4 moving rider with jitter fires exactly once",
      len(events) == 1 and events[0]["type"] == "No Helmet")

# --- H: plate cleanup — COUNTRY-AGNOSTIC, shows exactly what was read
import ocr
cases = [
    ("KA02MH7256", "KA 02 MH 7256", True),    # Indian: as-is, just spaced
    ("XA02MH7256", "XA 02 MH 7256", True),    # misread stays visible — no fake 'repair'
    ("WPCAB1234", "WPCAB 1234", True),        # Sri Lankan
    ("wp ka - 4821", "WPKA 4821", True),
    ("GX15OGJ", "GX 15 OGJ", True),           # UK
    ("2501234", "2501234", True),             # numeric series ok (6-8 digits)
    ("XYZ", "XYZ", False),                    # no digits -> implausible
    ("7256", "7256", False),                  # fragment -> implausible
    ("X", "X", False),
]
ok = True
for raw, want, wantm in cases:
    got, m = ocr.normalize_plate(raw)
    if got != want or m != wantm:
        ok = False
        print("   normalize_plate", repr(raw), "->", got, m, "wanted", want, wantm)
check("H SL plate normalisation", ok)

# --- I: digit-bucket voting — garbled letters, same digits => same plate
from pipeline import _record_read
plates = {}
_record_read(plates, 9, "KA 02 IH 7256", 0.45, None)  # frame 1: M read as I
p = plates[9]
check("I1 single mid-conf read NOT confirmed", not p["confirmed"])
_record_read(plates, 8, "WPCAB 4821", 0.95, None)     # one read, very confident
check("I1b even a 0.95 single read NOT confirmed", not plates[8]["confirmed"])
_record_read(plates, 9, "0217256", 0.40, None)        # frame 2: letters lost
check("I1c two agreeing reads still NOT confirmed (needs three)",
      not plates[9]["confirmed"])
_record_read(plates, 9, "KA 02 IH 7256", 0.45, None)  # frame 3: same tail again
p = plates[9]
check("I2 same digit-tail pools votes -> confirmed",
      p["confirmed"] and p["hits"] == 3)
check("I3 representative is the letter-bearing text",
      p["text"] == "KA 02 IH 7256")
_record_read(plates, 9, "KA 02 MH 7256", 0.50, None)  # frame 3: clean read
_record_read(plates, 9, "KA 02 MH 7256", 0.55, None)  # frame 4: again
p = plates[9]
check("I4 repeated clean read becomes the representative",
      p["text"] == "KA 02 MH 7256" and p["hits"] == 5)

fails = [n for n, c in PASSED if not c]
print(f"\n{len(PASSED) - len(fails)}/{len(PASSED)} passed")
sys.exit(1 if fails else 0)
