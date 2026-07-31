import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

import config
from violations import ViolationEngine
from pipeline import build_seatbelt_status

W, H, FPS = 1280, 720, 25
PASSED = []


def check(name, cond):
    PASSED.append((name, bool(cond)))
    print(("PASS" if cond else "FAIL"), "-", name)


def car(tid, x, y, w=160, h=110, conf=0.9):
    return {"track_id": tid, "cls": config.COCO["car"], "conf": conf,
            "box": [x, y, x + w, y + h]}


def belt(tid, box, no_seatbelt=True, seatbelt_ok=False):
    return {"track_id": tid, "box": box, "no_seatbelt": no_seatbelt,
            "seatbelt_ok": seatbelt_ok}


# --- moving car, no seatbelt every frame -> exactly ONE event after persistence
eng = ViolationEngine(W, H, FPS)
events = []
for f in range(60):
    v = car(1, 100 + f * 6, 400)
    events += eng.update(f, [v], "UNKNOWN", [], [belt(1, v["box"])])
check("moving no-seatbelt car fires exactly once",
      len(events) == 1 and events[0]["type"] == "No Seatbelt")

# --- moving car, belted -> never fires
eng = ViolationEngine(W, H, FPS)
events = []
for f in range(60):
    v = car(2, 100 + f * 6, 400)
    events += eng.update(f, [v], "UNKNOWN", [],
                         [belt(2, v["box"], no_seatbelt=False, seatbelt_ok=True)])
check("belted car never fires", len(events) == 0)

# --- parked car flagged every frame -> must NEVER fire (motion gate)
eng = ViolationEngine(W, H, FPS)
events = []
for f in range(60):
    v = car(3, 400, 500)          # stationary
    events += eng.update(f, [v], "UNKNOWN", [], [belt(3, v["box"])])
check("parked car never fires no-seatbelt", len(events) == 0)

# --- single-frame flicker among belted frames -> never fires
eng = ViolationEngine(W, H, FPS)
events = []
for f in range(60):
    v = car(4, 100 + f * 6, 400)
    bad = (f == 20)
    events += eng.update(f, [v], "UNKNOWN", [],
                         [belt(4, v["box"], no_seatbelt=bad, seatbelt_ok=not bad)])
check("one-frame no-seatbelt flicker suppressed", len(events) == 0)

# --- no belts data at all (model absent) -> engine call with belts=None is safe
eng = ViolationEngine(W, H, FPS)
events = []
for f in range(60):
    v = car(5, 100 + f * 6, 400)
    events += eng.update(f, [v], "UNKNOWN", [])   # no belts arg at all
check("belts=None (model absent) never fires, no crash", len(events) == 0)

# --- build_seatbelt_status returns [] when the model isn't installed
out = build_seatbelt_status(None, [car(6, 0, 0)["__dict__"] if False else
                                   {"track_id": 6, "box": [0, 0, 100, 100]}], None)
check("build_seatbelt_status([], model=None) returns []", out == [])


# --- seatbelt_verdict must read CLASSIFICATION models, not only detectors.
# The shipped models/seatbelt.pt is a classify-task model; the pipeline read
# only .boxes, which is always None for a classifier, so No Seatbelt could
# never fire on any footage. Both result shapes must be understood.
from detection import _seatbelt_model_is_sane, seatbelt_verdict   # noqa: E402


class _Probs:
    def __init__(self, top1, conf):
        self.top1, self.top1conf = top1, conf


class _Box:
    def __init__(self, cls, conf):
        self.cls, self.conf = [cls], [conf]


class _Res:
    def __init__(self, names, probs=None, boxes=None):
        self.names, self.probs, self.boxes = names, probs, boxes


NAMES = {0: "no_seatbelt", 1: "seat_belt"}
check("verdict reads a CLASSIFICATION result",
      seatbelt_verdict(_Res(NAMES, probs=_Probs(0, 0.91))) == ("no_seatbelt", 0.91))
check("verdict reads a DETECTION result",
      seatbelt_verdict(_Res(NAMES, boxes=[_Box(1, 0.4), _Box(0, 0.8)]))
      == ("no_seatbelt", 0.8))
check("verdict on an empty detection result is (None, 0)",
      seatbelt_verdict(_Res(NAMES, boxes=[])) == (None, 0.0))


# --- a whole-crop CLASSIFIER must be refused: it cannot localise the belt,
# so it can produce no evidence, and the shipped one does not discriminate at
# all. Fixing the classifier bug WITHOUT this gate made No Seatbelt fire on 6
# of 18 sampled frames of a driver who is visibly wearing a belt.
class _Model:
    def __init__(self, task):
        self.task = task
        self.names = NAMES

    def predict(self, img, **kw):
        return [_Res(NAMES, probs=_Probs(0, 1.0))]


check("a classification seatbelt model is refused",
      _seatbelt_model_is_sane(_Model("classify")) is False)
check("a detection seatbelt model is accepted",
      _seatbelt_model_is_sane(_Model("detect")) is True)

n_fail = sum(1 for _, ok in PASSED if not ok)
print(f"\n{len(PASSED)-n_fail}/{len(PASSED)} passed")
sys.exit(1 if n_fail else 0)
