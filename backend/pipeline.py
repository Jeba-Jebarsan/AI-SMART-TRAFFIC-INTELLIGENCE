"""
Shared frame-processing pipeline: detection -> tracking -> signal state ->
rider/seatbelt association -> continuous ANPR -> ViolationEngine -> evidence
+ e-challan -> SQLite + results.json.

LIVE ONLY: this platform has no file-upload / batch-analysis path. The single
per-frame entry point (process_frame) is driven by live.py against an IP
camera, RTSP/HTTP stream, webcam, or a sample-clip live replay.

Honesty rules baked in:
  * a violation needs a CONFIDENT, TRACKED, MOVING subject seen over several
    frames — parked bikes / pedestrians / one-frame flickers never fire
  * helmet/seatbelt status is only judged from a POSITIVE model detection —
    absence of a detection never convicts anyone
  * plates come from real OCR; unconfirmed reads stay off the dashboard —
    never invented
"""
import datetime
import json

import alerts
import config
import db
import ocr
from challan import make_challan_id
from detection import load, load_seatbelt, load_threewheeler, resolve_device
from location import resolve_location
from violations import ViolationEngine, centroid


# --------------------------------------------------------------------- helpers
def _clip(v, lo, hi):
    return max(lo, min(hi, v))


def _overlap_ratio(person, moto):
    """Fraction of the person box that lies inside the motorcycle box."""
    px1, py1, px2, py2 = person
    mx1, my1, mx2, my2 = moto
    ix1, iy1 = max(px1, mx1), max(py1, my1)
    ix2, iy2 = min(px2, mx2), min(py2, my2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    parea = max(1.0, (px2 - px1) * (py2 - py1))
    return inter / parea


def _on_board(pbox, mbox):
    """Strict person<->motorcycle association: is this person RIDING the bike?

    A pedestrian walking past overlaps a parked bike easily; a rider sits ON
    it. So we require substantial overlap, the person's centre over the bike,
    and the person's feet near/above the bike's bottom edge.

    The overlap floor is 0.20, not 0.30: a rider's person-box extends well
    ABOVE the motorcycle box (head and torso clear the bike), so only ~20-35%
    of a genuine rider's box falls inside it. Measured on real footage, 0.30
    rejected a third of true riders that 0.20 keeps. The three geometric gates
    below — plus the engine's motion gate and multi-frame persistence — are
    what actually exclude pedestrians, not this ratio alone.
    """
    if _overlap_ratio(pbox, mbox) < 0.20:
        return False
    px1, py1, px2, py2 = pbox
    mx1, my1, mx2, my2 = mbox
    mw, mh = mx2 - mx1, my2 - my1
    pcx = (px1 + px2) / 2.0
    if not (mx1 - 0.15 * mw <= pcx <= mx2 + 0.15 * mw):
        return False
    if py2 > my2 + 0.15 * mh:      # feet clearly below the bike -> walking past
        return False
    if py2 < my1:                  # entirely above the bike -> unrelated
        return False
    return True


def load_calibration(video_path=None, frame_w=None, frame_h=None):
    """Find a calibration for this clip in data/calibration.json.

    Lookup order: exact video basename -> "WIDTHxHEIGHT" resolution key ->
    config.SPEED_SOURCE fallback. Returns (points, target_m, direction);
    direction is the allowed travel vector for wrong-way (or None = off).
    """
    entries = {}
    try:
        entries = json.loads(config.CALIBRATION_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    keys = []
    if video_path:
        import os
        keys.append(os.path.basename(str(video_path)))
    if frame_w and frame_h:
        keys.append(f"{int(frame_w)}x{int(frame_h)}")
    for k in keys:
        e = entries.get(k)
        if e and (e.get("points") or e.get("direction")):
            pts = e.get("points") if e.get("points") and len(e["points"]) == 4 else None
            direction = tuple(e["direction"]) if e.get("direction") else None
            return (pts, tuple(e.get("target_m") or config.SPEED_TARGET_M),
                    direction)
    if config.SPEED_SOURCE:
        return config.SPEED_SOURCE, config.SPEED_TARGET_M, None
    return None, None, None


def save_calibration(key, points, target_m, direction=None):
    """Persist a per-video calibration (used by /api/calibration)."""
    entries = {}
    try:
        entries = json.loads(config.CALIBRATION_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    entry = {}
    if points:
        entry["points"] = points
        entry["target_m"] = list(target_m)
    if direction:
        entry["direction"] = list(direction)
    entries[key] = entry
    config.CALIBRATION_FILE.write_text(json.dumps(entries, indent=2),
                                       encoding="utf-8")


def load_stop_line_y(video_path=None, frame_w=None, frame_h=None):
    """Per-camera virtual stop line (0-1 of frame height), or None.

    Read from a "stop_line_y" key in the same calibration.json entry. Where
    the stop line falls in frame depends entirely on how the camera is aimed,
    so a single global default is right for no one: on junction CCTV the line
    sits near the bottom of frame, while a high mast view puts it mid-frame.
    """
    entries = {}
    try:
        entries = json.loads(config.CALIBRATION_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None
    keys = []
    if video_path:
        import os
        keys.append(os.path.basename(str(video_path)))
    if frame_w and frame_h:
        keys.append(f"{int(frame_w)}x{int(frame_h)}")
    for k in keys:
        e = entries.get(k) or {}
        if e.get("stop_line_y"):
            return float(e["stop_line_y"])
    return None


def load_pixels_per_meter(video_path=None, frame_w=None, frame_h=None):
    """Per-camera pixels-per-metre for APPROX (uncalibrated) speed, or None.

    Read from the same calibration.json entry as the quad, via a
    "pixels_per_meter" key. Approx speed is lens- and mounting-dependent, so
    one global constant reads sensibly on a distant highway view and wildly
    wrong on close roadside phone footage.
    """
    entries = {}
    try:
        entries = json.loads(config.CALIBRATION_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None
    keys = []
    if video_path:
        import os
        keys.append(os.path.basename(str(video_path)))
    if frame_w and frame_h:
        keys.append(f"{int(frame_w)}x{int(frame_h)}")
    for k in keys:
        e = entries.get(k) or {}
        if e.get("pixels_per_meter"):
            return float(e["pixels_per_meter"])
    return None


def make_transform_fn(points=None, target_m=None):
    """Build an image->road-metres transform from a calibration quad.

    Returns a function mapping an image point to its distance (metres) along the
    road, or None for points outside the calibrated quad. Returns None entirely
    when no calibration is configured (caller then uses the pixel fallback).
    """
    points = points if points is not None else config.SPEED_SOURCE
    target_m = target_m or config.SPEED_TARGET_M
    if not points:
        return None
    import cv2
    import numpy as np

    src = np.array(points, dtype=np.float32)
    w, l = target_m
    dst = np.array([[0, 0], [w - 1, 0], [w - 1, l - 1], [0, l - 1]],
                   dtype=np.float32)
    M = cv2.getPerspectiveTransform(src, dst)
    poly = np.array(points, dtype=np.int32)

    def fn(pt):
        if cv2.pointPolygonTest(poly, (float(pt[0]), float(pt[1])), False) < 0:
            return None
        p = np.array([[[float(pt[0]), float(pt[1])]]], dtype=np.float32)
        out = cv2.perspectiveTransform(p, M)
        return float(out[0, 0, 1])

    return fn


def detect_signal_color(frame, light_boxes):
    """Classify the dominant colour of detected traffic-light boxes via HSV."""
    import cv2

    best_state, best_score = None, 0
    for (x1, y1, x2, y2) in light_boxes:
        h, w = frame.shape[:2]
        x1, y1 = int(_clip(x1, 0, w - 1)), int(_clip(y1, 0, h - 1))
        x2, y2 = int(_clip(x2, 0, w)), int(_clip(y2, 0, h))
        roi = frame[y1:y2, x1:x2]
        if roi.size == 0:
            continue
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        red = (cv2.inRange(hsv, (0, 90, 90), (10, 255, 255)) +
               cv2.inRange(hsv, (160, 90, 90), (180, 255, 255)))
        yellow = cv2.inRange(hsv, (18, 90, 90), (35, 255, 255))
        green = cv2.inRange(hsv, (40, 60, 60), (90, 255, 255))
        counts = {"RED": int(red.sum()), "YELLOW": int(yellow.sum()),
                  "GREEN": int(green.sum())}
        state = max(counts, key=counts.get)
        if counts[state] > best_score:
            best_score, best_state = counts[state], state
    return best_state


def _is_no_helmet(label):
    l = label.lower()
    return ("without" in l or "no_helmet" in l or "no-helmet" in l
            or "nohelmet" in l or "no helmet" in l or l == "head")


def _is_helmet(label):
    l = label.lower()
    return "helmet" in l and not _is_no_helmet(l)


def build_riders(frame, motos, persons, helmet_model):
    """Associate persons with motorcycles and judge helmet / rider-count.

    Only motorcycles that are big enough to see AND have at least one
    strictly-associated rider are analysed. no_helmet requires the helmet
    model to POSITIVELY detect a bare head — absence of detections proves
    nothing and never flags anyone.
    """
    import cv2

    H, W = frame.shape[:2]
    riders = []
    for m in motos:
        mx1, my1, mx2, my2 = m["box"]
        onboard = [p for p in persons if _on_board(p["box"], m["box"])]
        n = len(onboard)

        no_helmet = False
        helmet_ok = False
        big_enough = (my2 - my1) >= config.MIN_MOTO_PX

        if n >= 1 and big_enough and helmet_model is not None:
            # Judge each ASSOCIATED RIDER's own head region, not one wide crop
            # around the motorcycle. In dense traffic a bike-sized crop sweeps
            # in the riders of neighbouring bikes and pedestrians, so a bare
            # head anywhere nearby flagged THIS rider — observed falsely
            # accusing a helmeted pair because another rider sat just behind
            # them. Cropping per rider keeps the verdict about that person.
            for p in onboard:
                px1, py1, px2, py2 = p["box"]
                pw, ph = px2 - px1, py2 - py1
                # head-and-shoulders: top third of the person, padded, since
                # the person box can start at the chin on a leaning rider.
                hx1 = _clip(px1 - pw * 0.25, 0, W)
                hx2 = _clip(px2 + pw * 0.25, 0, W)
                hy1 = _clip(py1 - ph * 0.25, 0, H)
                hy2 = _clip(py1 + ph * 0.45, 0, H)
                crop = frame[int(hy1):int(hy2), int(hx1):int(hx2)]
                if crop.size == 0 or min(crop.shape[:2]) < 12:
                    continue
                r = helmet_model.predict(crop, verbose=False, conf=0.30,
                                         device=resolve_device())[0]
                names = r.names
                if r.boxes is None:
                    continue
                for b in r.boxes:
                    label = names[int(b.cls[0])]
                    conf = float(b.conf[0])
                    if _is_no_helmet(label) and conf >= config.CONF["no_helmet"]:
                        no_helmet = True
                    elif _is_helmet(label) and conf >= 0.35:
                        helmet_ok = True
            if helmet_ok and no_helmet:
                # Two riders disagreeing (pillion bare, rider helmeted) is a
                # real violation, so no_helmet wins.
                helmet_ok = False
        elif n >= 1 and big_enough:
            # Heuristic fallback (no helmet model installed): a helmet is a
            # large uniform saturated patch at the rider's head. Conservative;
            # the engine still demands multi-frame persistence + motion.
            for p in onboard:
                px1, py1, px2, py2 = p["box"]
                head_h = (py2 - py1) * 0.28
                hx1, hy1 = int(_clip(px1, 0, W)), int(_clip(py1, 0, H))
                hx2, hy2 = int(_clip(px2, 0, W)), int(_clip(py1 + head_h, 0, H))
                head = frame[hy1:hy2, hx1:hx2]
                if head.size == 0:
                    continue
                hsv = cv2.cvtColor(head, cv2.COLOR_BGR2HSV)
                if float(hsv[..., 1].mean()) < 45:
                    no_helmet = True
                    break

        riders.append({
            "track_id": m.get("track_id"),
            "box": m["box"],
            "no_helmet": bool(no_helmet),
            "helmet_ok": bool(helmet_ok),
            "riders": n,
        })
    return riders


def _is_no_seatbelt(label):
    l = label.lower()
    return "belt" in l and ("no" in l or "without" in l or "un" in l)


def _is_seatbelt(label):
    l = label.lower()
    return "belt" in l and not _is_no_seatbelt(l)


def build_seatbelt_status(frame, cars, seatbelt_model):
    """Judge front-seat seatbelt use for cars/buses/trucks via the OPTIONAL
    drop-in model (models/seatbelt.pt). Returns [] when the model isn't
    installed — there is no colour/shape heuristic fallback here (unlike the
    helmet heuristic) because a wrong seatbelt fine is worse than none.

    Only a POSITIVE 'no seatbelt' detection ever counts against a driver —
    absence of any detection proves nothing, same rule as helmets.
    """
    if seatbelt_model is None or not cars:
        return []
    H, W = frame.shape[:2]
    out = []
    for c in cars:
        x1, y1, x2, y2 = c["box"]
        mh, mw = y2 - y1, x2 - x1
        if mh < config.MIN_CAR_H_FRAC * H:
            continue
        # windshield / driver area: upper ~55% of the vehicle box, trimmed
        # in from the side mirrors
        wx1 = int(_clip(x1 + 0.08 * mw, 0, W))
        wx2 = int(_clip(x2 - 0.08 * mw, 0, W))
        wy1 = int(_clip(y1, 0, H))
        wy2 = int(_clip(y1 + 0.55 * mh, 0, H))
        crop = frame[wy1:wy2, wx1:wx2]
        if crop.size == 0:
            continue
        r = seatbelt_model.predict(crop, verbose=False, conf=0.30,
                                   device=resolve_device())[0]
        no_belt, belt_ok = False, False
        names = r.names
        if r.boxes is not None:
            for b in r.boxes:
                label = names[int(b.cls[0])]
                conf = float(b.conf[0])
                if _is_no_seatbelt(label) and conf >= config.CONF["no_seatbelt"]:
                    no_belt = True
                elif _is_seatbelt(label) and conf >= 0.35:
                    belt_ok = True
        if belt_ok and no_belt:
            belt_ok = False        # conservative: trust the violation signal
        out.append({"track_id": c["track_id"], "box": c["box"],
                    "no_seatbelt": no_belt, "seatbelt_ok": belt_ok})
    return out


def build_phone_status(motos, cars, persons, phones):
    """Associate detected phones (COCO 'cell phone') with the rider/driver of a
    vehicle. Returns [{track_id, box, phone}] for every analysed motorcycle and
    car — phone=True when a phone overlaps this vehicle's occupant THIS frame.

    Every analysed vehicle is reported (even with phone=False) so the engine
    can DECAY a phone streak when the phone drops out of view — a phone must be
    seen across several frames (config.PHONE_MIN_HITS) before it convicts, so a
    one-frame stray detection never issues a fine. Same honesty rule as the
    other detectors: only a POSITIVE association counts.
    """
    out = []
    for m in motos:
        onboard = [p for p in persons if _on_board(p["box"], m["box"])]
        use = any(_overlap_ratio(ph, p["box"]) >= 0.20
                  for p in onboard for ph in phones) if phones else False
        out.append({"track_id": m["track_id"], "box": m["box"], "phone": use})
    for c in cars:
        x1, y1, x2, y2 = c["box"]
        mh, mw = y2 - y1, x2 - x1
        # driver area: upper 60% of the car box, trimmed in from the mirrors
        region = [x1 + 0.06 * mw, y1, x2 - 0.06 * mw, y1 + 0.60 * mh]
        use = any(_overlap_ratio(ph, region) >= 0.40
                  for ph in phones) if phones else False
        out.append({"track_id": c["track_id"], "box": c["box"], "phone": use})
    return out


# ------------------------------------------------------------------------ ANPR
def _anpr_step(frame, vehicles, state, engine, fidx):
    """Continuous plate reading: keep the BEST read per track over time.

    Runs every config.ANPR_EVERY frames. Strategy tuned on real footage:
      * moving vehicles first (they leave the scene; parked ones can wait)
      * a cheap plate-DETECTOR pass decides who is worth OCR — tiny plates
        are skipped without cost and retried when the vehicle gets closer
      * tracks whose crops repeatedly show no plate at all go on cooldown
      * the per-track OCR budget only counts real OCR runs
    """
    import cv2

    plates = state["plates"]
    tries = state["ocr_tries"]
    miss = state["ocr_miss"]
    cool = state["ocr_cool"]

    min_h = max(config.ANPR_MIN_VEH_H, 0.07 * frame.shape[0])
    cands = []
    for v in vehicles:
        tid = v["track_id"]
        if tid is None:
            continue
        h = v["box"][3] - v["box"][1]
        if h < min_h:
            continue
        cur = plates.get(tid)
        if cur and cur["conf"] >= config.ANPR_GOOD_CONF:
            continue
        if cur and cur.get("confirmed") and (cur["conf"] >= 0.55
                                             or cur["hits"] >= 3):
            continue                             # good enough — stop paying OCR
        if tries.get(tid, 0) >= config.ANPR_TRIES:
            continue
        if cool.get(tid, 0) > fidx:              # detector kept missing
            continue
        moving = 1 if engine.is_moving(tid) else 0
        cands.append((moving, h, tid, v))
    cands.sort(key=lambda c: (-c[0], -c[1]))     # moving first, then biggest

    ocr_runs = 0
    for _, _, tid, v in cands[:4]:               # detector pass on up to 4
        if ocr_runs >= config.ANPR_MAX_PER_FRAME:
            break
        text, conf, crop, ocr_ran = ocr.read_plate_and_crop(
            frame, v["box"], min_ocr_h=12)

        if crop is None:                          # no plate seen in this crop
            miss[tid] = miss.get(tid, 0) + 1
            if miss[tid] >= 5:                    # stop hammering this track
                cool[tid] = fidx + 90
                miss[tid] = 0
            continue
        miss[tid] = 0
        if not ocr_ran:                           # plate too small — wait
            continue

        ocr_runs += 1
        tries[tid] = tries.get(tid, 0) + 1
        if text == "UNKNOWN" or conf <= 0:
            continue
        _record_read(plates, tid, text, conf, crop)


def _plate_digit_key(text):
    """The trailing 4-digit block — the most reliably-OCR'd part of a plate.
    Reads that agree on it are treated as sightings of the SAME plate even
    when a stylised letter was garbled differently in each frame."""
    import re
    m = re.search(r"(\d{4})\s*$", text.replace("-", "").replace(" ", ""))
    return m.group(1) if m else text


def _record_read(plates, tid, text, conf, crop):
    """Vote a new OCR read into the track's candidate table.

    Votes are pooled per digit-tail bucket (see _plate_digit_key), and the
    bucket's best-formed text represents it. A plate is CONFIRMED only when
    its bucket was read in multiple frames, or one read cleared the high bar
    AND matches a known plate grammar. Everything downstream — overlay,
    dashboard, challans, police emails — shows confirmed plates only, so a
    single garbled read can never become someone's fine.
    """
    import cv2

    entry = plates.setdefault(
        tid, {"text": None, "conf": 0.0, "img": None, "hits": 0,
              "confirmed": False, "crop_img": None, "cands": {}})
    cnt, best = entry["cands"].get(text, (0, 0.0))
    entry["cands"][text] = (cnt + 1, max(best, conf))

    # pool candidate texts into digit-tail buckets
    buckets = {}
    for t, (c, cf) in entry["cands"].items():
        b = buckets.setdefault(_plate_digit_key(t), {"n": 0, "texts": []})
        b["n"] += c
        b["texts"].append((t, c, cf))
    key, bucket = max(buckets.items(), key=lambda kv: kv[1]["n"])
    # bucket representative: prefer reads that carry letters (fragments are
    # usually digits-only), then most-seen, then longest, then confidence
    win_text, win_cnt, win_conf = max(
        bucket["texts"],
        key=lambda x: (any(c.isalpha() for c in x[0]), x[1],
                       len(x[0].replace(" ", "")), x[2]))
    hits = bucket["n"]
    entry.update(text=win_text, conf=win_conf, hits=hits)
    # ONE read is never proof, however confident — the same plate (same
    # digit-tail) must be seen in at least two different frames. This is
    # what keeps a single garbled read off someone's challan.
    entry["confirmed"] = hits >= config.PLATE_CONFIRM_READS

    if _plate_digit_key(text) == key and crop is not None and crop.size:
        img_name = f"snapshots/plate_{tid}.jpg"
        ch, cw = crop.shape[:2]
        if ch < 60:                               # store a readable-size crop
            crop = cv2.resize(crop, (int(cw * 60 / ch), 60),
                              interpolation=cv2.INTER_CUBIC)
        cv2.imwrite(str(config.OUTPUT_DIR / img_name), crop)
        entry["img"] = img_name
        # small in-memory copy for the video overlay banner
        bh = 28
        entry["crop_img"] = cv2.resize(
            crop, (max(1, int(crop.shape[1] * bh / crop.shape[0])), bh))


def _best_plate(state, tid, frame=None, box=None):
    """Best CONFIRMED plate for a track; tries once more at violation time."""
    cached = state["plates"].get(tid)
    if frame is not None and box is not None and (
            cached is None or not cached["confirmed"]):
        text, conf, crop, _ = ocr.read_plate_and_crop(frame, box)
        if text != "UNKNOWN":
            _record_read(state["plates"], tid, text, conf, crop)
            cached = state["plates"].get(tid)
    if cached is None or not cached["confirmed"]:
        return "UNKNOWN", 0.0, None
    return cached["text"], cached["conf"], cached["img"]


# ----------------------------------------------------------------- annotation
_PALETTE = {
    2: (80, 200, 120), 3: (255, 170, 40), 5: (0, 180, 255),
    7: (0, 140, 255), 1: (200, 200, 60),
}
_CLS_NAMES = {1: "Bicycle", 2: "Car", 3: "Motorcycle", 5: "Bus", 7: "Truck"}


def apply_threewheeler_labels(frame, vehicles):
    """Relabel vehicles the optional three-wheeler model recognises.

    COCO has no three-wheeler class, so tuk-tuks arrive labelled 'Truck'. When
    models/threewheeler.pt is installed, any vehicle box that substantially
    overlaps a three-wheeler detection is renamed. A no-op when the model is
    absent, which is the default.
    """
    model = load_threewheeler()
    if model is None or not vehicles:
        return {}
    r = model.predict(frame, verbose=False, conf=0.35,
                      device=resolve_device())[0]
    if r.boxes is None or not len(r.boxes):
        return {}
    dets = [[float(x) for x in b.xyxy[0].tolist()] for b in r.boxes]
    out = {}
    for v in vehicles:
        tid = v.get("track_id")
        if tid is None:
            continue
        for d in dets:
            # IoU-style overlap of the detection against the vehicle box
            ix1, iy1 = max(d[0], v["box"][0]), max(d[1], v["box"][1])
            ix2, iy2 = min(d[2], v["box"][2]), min(d[3], v["box"][3])
            inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
            area = max(1.0, (d[2] - d[0]) * (d[3] - d[1]))
            if inter / area >= 0.55:
                out[tid] = "Three Wheeler"
                break
    return out


def _put_tag(out, text, x, y, color, scale=0.5, thick=1):
    """Text with a dark backing strip so labels stay readable on any footage."""
    import cv2
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, thick)
    cv2.rectangle(out, (x - 2, y - th - 6), (x + tw + 4, y + 2), (10, 10, 10), -1)
    cv2.putText(out, text, (x, y - 3), cv2.FONT_HERSHEY_SIMPLEX, scale,
                color, thick, cv2.LINE_AA)


def _corner_box(out, box, color, thickness=2):
    """ANPR-style corner brackets instead of a full rectangle."""
    import cv2
    x1, y1, x2, y2 = [int(c) for c in box]
    ll = max(8, int(min(x2 - x1, y2 - y1) * 0.25))
    for (cx, cy, dx, dy) in ((x1, y1, 1, 1), (x2, y1, -1, 1),
                             (x1, y2, 1, -1), (x2, y2, -1, -1)):
        cv2.line(out, (cx, cy), (cx + dx * ll, cy), color, thickness, cv2.LINE_AA)
        cv2.line(out, (cx, cy), (cx, cy + dy * ll), color, thickness, cv2.LINE_AA)


def _plate_banner(out, box, entry, sc, lift=0):
    """Paste the captured plate crop + its number in a white banner above the
    vehicle — the classic ANPR showcase look. Confirmed reads only."""
    import cv2

    h, w = out.shape[:2]
    x1, y1, x2, _ = [int(c) for c in box]
    text = entry["text"]
    fscale = max(0.55, 0.8 * sc)
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, fscale, 2)
    crop = entry.get("crop_img")
    ch = crop.shape[0] if crop is not None else 0
    cw = crop.shape[1] if crop is not None else 0
    bw = max(tw + 16, cw + 8)
    bh = th + 14 + (ch + 6 if crop is not None else 0)

    cx = max(2, min((x1 + x2) // 2 - bw // 2, w - bw - 2))
    ty = y1 - 8 - bh - lift
    if ty < int(34 * sc) + 14:                    # would collide with HUD
        ty = y1 + 8
    if ty + bh >= h:
        return

    cv2.rectangle(out, (cx, ty), (cx + bw, ty + bh), (255, 255, 255), -1)
    cv2.rectangle(out, (cx, ty), (cx + bw, ty + bh), (30, 30, 30), 1)
    cv2.putText(out, text, (cx + (bw - tw) // 2, ty + th + 7),
                cv2.FONT_HERSHEY_SIMPLEX, fscale, (10, 10, 10), 2, cv2.LINE_AA)
    if crop is not None:
        ox = cx + (bw - cw) // 2
        oy = ty + th + 12
        if oy + ch < h and ox + cw < w:
            out[oy:oy + ch, ox:ox + cw] = crop


def _draw(frame, vehicles, riders, light_boxes, signal, engine, active_ids,
          state, fidx, speeds=None, belts=None, phones=None):
    import cv2
    import numpy as np

    out = frame.copy()
    h, w = out.shape[:2]
    sc = max(0.5, min(1.0, w / 1280))            # scale UI with resolution

    # speed-measurement zone (perspective-calibrated region)
    if state.get("speed_quad"):
        pts = np.array(state["speed_quad"], dtype=np.int32).reshape(-1, 1, 2)
        cv2.polylines(out, [pts], True, (255, 200, 0), 2, cv2.LINE_AA)
        _put_tag(out, "SPEED ZONE (calibrated)", int(pts[0][0][0]),
                 max(14, int(pts[0][0][1]) - 6), (255, 200, 0), 0.5 * sc + 0.1)

    has_signal = signal in ("RED", "YELLOW", "GREEN")

    # Stop line + signal are drawn ONLY when a real traffic light is detected —
    # never invented on a road that has no signal.
    if has_signal:
        y = int(engine.stop_line_y)
        cv2.line(out, (0, y), (w, y), (0, 0, 255), 2, cv2.LINE_AA)
        _put_tag(out, "STOP LINE", 10, y - 4, (0, 0, 255), 0.5 * sc + 0.2)
        scol = {"RED": (0, 0, 255), "YELLOW": (0, 210, 255),
                "GREEN": (0, 200, 0)}[signal]
        cv2.circle(out, (w - 30, 34), 12, scol, -1)
        _put_tag(out, f"SIGNAL: {signal}", w - 200, 42, scol, 0.6 * sc + 0.2, 2)

    for b in light_boxes:                       # outline any detected lights
        x1, y1, x2, y2 = [int(v) for v in b]
        cv2.rectangle(out, (x1, y1), (x2, y2), (0, 210, 255), 1)

    rider_ids = {r["track_id"]: r for r in riders}
    belt_ids = {b["track_id"]: b for b in (belts or [])}
    phone_ids = {p["track_id"]: p for p in (phones or [])}
    for v in vehicles:
        x1, y1, x2, y2 = [int(c) for c in v["box"]]
        col = _PALETTE.get(v["cls"], (180, 180, 180))
        tid = v["track_id"]
        r = rider_ids.get(tid) if v["cls"] == config.COCO["motorcycle"] else None
        bstat = belt_ids.get(tid) if v["cls"] in config.SEATBELT_CLASSES else None
        flagged = (r and r["no_helmet"] and r["riders"] >= 1) or \
                  (bstat and bstat["no_seatbelt"])
        _corner_box(out, v["box"], (0, 0, 255) if flagged else col,
                    3 if flagged else 2)

        spd = speeds.get(tid) if speeds else None
        approx = engine.transform_fn is None

        # Speed rides INLINE with the ID so every measured vehicle shows its
        # km/h continuously — not only at the instant it violates something.
        name = (state.get("threewheelers", {}).get(tid)
                or _CLS_NAMES.get(v["cls"], "Vehicle"))
        label = f"{name} #{tid}" if tid is not None else name
        if spd:
            label += f"  {'~' if approx else ''}{spd} km/h"
        _put_tag(out, label, x1, max(y1, 14), col, 0.5 * sc + 0.15)

        # Big SPEED chip above the vehicle, reserved for OVER-LIMIT vehicles so
        # a violation still pops; ordinary speeds read fine inline above.
        lift = 0
        if spd and (not approx) and spd > config.SPEED_LIMIT_KMPH:
            stext = f"{spd} km/h"
            fs = 0.6 * sc + 0.2
            (tw2, th2), _ = cv2.getTextSize(stext, cv2.FONT_HERSHEY_SIMPLEX,
                                            fs, 2)
            scx = max(2, min((x1 + x2) // 2 - tw2 // 2 - 6, w - tw2 - 14))
            scy = max(int(34 * sc) + 16, y1 - 8 - th2 - 10)
            cv2.rectangle(out, (scx, scy), (scx + tw2 + 12, scy + th2 + 10),
                          (0, 0, 200), -1)
            cv2.putText(out, stext, (scx + 6, scy + th2 + 3),
                        cv2.FONT_HERSHEY_SIMPLEX, fs, (255, 255, 255), 2,
                        cv2.LINE_AA)
            lift = th2 + 22                     # keep the plate banner clear

        # CONFIRMED plate: white banner + the captured crop above the vehicle
        p = state["plates"].get(tid)
        if p and p.get("confirmed"):
            _plate_banner(out, v["box"], p, sc, lift=lift)

        # rider status chip for motorcycles with riders
        if r and r["riders"] >= 1:
            if r["no_helmet"]:
                _put_tag(out, "NO HELMET", x1, min(y2 + int(38 * sc) + 8, h - 4),
                         (0, 0, 255), 0.6 * sc + 0.15, 2)
            elif r["helmet_ok"]:
                _put_tag(out, "HELMET OK", x1, min(y2 + int(38 * sc) + 8, h - 4),
                         (0, 200, 0), 0.5 * sc + 0.15)
            if r["riders"] >= 3:
                _put_tag(out, f"{r['riders']} RIDERS", x2 - int(80 * sc), y1 + 16,
                         (0, 120, 255), 0.5 * sc + 0.15, 2)

        # seatbelt status chip for cars/buses/trucks (only when the optional
        # seatbelt model is installed and produced a reading for this track)
        if bstat:
            if bstat["no_seatbelt"]:
                _put_tag(out, "NO SEATBELT", x1, min(y2 + int(38 * sc) + 8, h - 4),
                         (0, 0, 255), 0.6 * sc + 0.15, 2)
            elif bstat["seatbelt_ok"]:
                _put_tag(out, "SEATBELT OK", x1, min(y2 + int(38 * sc) + 8, h - 4),
                         (0, 200, 0), 0.5 * sc + 0.15)

        # stunt (wheelie) + phone-use chips, driven by the engine's per-track
        # state (so they reflect the SAME persistence-gated logic that fires
        # the violation, not a raw one-frame guess)
        stt = engine.tracks.get(tid)
        if stt and ("wheelie" in stt["emitted"] or stt.get("wheelie_hits", 0) >= 2):
            _put_tag(out, "WHEELIE / STUNT", x1,
                     min(y2 + int(58 * sc) + 8, h - 4), (200, 0, 255),
                     0.6 * sc + 0.15, 2)
        pstat = phone_ids.get(tid)
        if pstat and (pstat.get("phone") or (stt and "phone" in stt["emitted"])):
            _put_tag(out, "ON PHONE", x1, min(y2 + int(78 * sc) + 8, h - 4),
                     (0, 200, 255), 0.6 * sc + 0.15, 2)

    # --- HUD (top-left): counters everyone in the room can read
    n_veh = len(state["vehicle_ids"])
    n_vio = state["violations"]
    hud = f"VEHICLES {n_veh}   VIOLATIONS {n_vio}   SIGNAL {signal}"
    cv2.rectangle(out, (0, 0), (w, int(30 * sc) + 12), (12, 12, 12), -1)
    cv2.putText(out, "AI TRAFFIC INTELLIGENCE  |  " + hud, (10, int(22 * sc) + 6),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55 * sc + 0.2, (255, 255, 255), 2,
                cv2.LINE_AA)

    # --- event banners: recent violations flash a strip for ~2.5 s
    state["banners"] = [b for b in state["banners"] if b[1] > fidx]
    by = int(30 * sc) + 18
    for text, _ in state["banners"][-3:]:
        (tw, _), _2 = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX,
                                      0.7 * sc + 0.2, 2)
        cv2.rectangle(out, (0, by), (tw + 26, by + int(30 * sc) + 6),
                      (0, 0, 200), -1)
        cv2.putText(out, text, (12, by + int(22 * sc) + 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7 * sc + 0.2,
                    (255, 255, 255), 2, cv2.LINE_AA)
        by += int(34 * sc) + 8

    if active_ids:
        cv2.rectangle(out, (0, 0), (w, 4), (0, 0, 255), -1)  # red flash bar
    return out


def _save_snapshot(frame, event, seq, plate=None, location=None):
    """Full-frame evidence: offender boxed + zoomed inset + a banner carrying
    the PROOF for this violation type (speed for over-speeding, plate when
    confirmed, vehicle track id) stamped onto the image itself."""
    import cv2

    out = frame.copy()
    H, W = out.shape[:2]
    x1, y1, x2, y2 = [int(_clip(c, 0, m)) for c, m in
                      zip(event["box"], (W - 1, H - 1, W - 1, H - 1))]
    cv2.rectangle(out, (x1, y1), (x2, y2), (0, 0, 255), 3)

    speed = event.get("speed_kmph")
    drive_secs = event.get("drive_seconds")
    tid = event.get("track_id")

    # zoomed inset of the offender (bottom-right) so judges see the subject
    crop = frame[y1:y2, x1:x2]
    if crop.size and (y2 - y1) > 10:
        zh = max(1, int(H * 0.35))
        zw = max(1, int(crop.shape[1] * zh / crop.shape[0]))
        if zw > int(W * 0.45):
            zw = int(W * 0.45)
            zh = max(1, int(crop.shape[0] * zw / crop.shape[1]))
        zoom = cv2.resize(crop, (zw, zh), interpolation=cv2.INTER_CUBIC)
        ox, oy = W - zw - 12, H - zh - 12
        out[oy:oy + zh, ox:ox + zw] = zoom
        cv2.rectangle(out, (ox, oy), (ox + zw, oy + zh), (0, 0, 255), 2)
        cv2.putText(out, "EVIDENCE ZOOM", (ox, oy - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2, cv2.LINE_AA)
        # the measured proof, stamped INSIDE the zoom for over-speeding /
        # continuous-driving events
        stamp = None
        if speed:
            stamp = f"{speed} km/h  (limit {config.SPEED_LIMIT_KMPH})"
        elif drive_secs:
            stamp = (f"{drive_secs/60:.0f} min non-stop "
                     f"(limit {config.MAX_CONTINUOUS_DRIVE_SECONDS/60:.0f} min)")
        if stamp:
            cv2.rectangle(out, (ox, oy + zh - 30), (ox + zw, oy + zh),
                          (0, 0, 180), -1)
            cv2.putText(out, stamp, (ox + 8, oy + zh - 9),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2,
                        cv2.LINE_AA)

    parts = [event["type"]]
    if speed:
        parts.append(f"{speed} km/h in {config.SPEED_LIMIT_KMPH} zone")
    if drive_secs:
        parts.append(f"{drive_secs/60:.0f} min continuous driving")
    if plate and plate != "UNKNOWN":
        parts.append(f"PLATE {plate}")
    if tid is not None:
        parts.append(f"VEHICLE #{tid}")
    parts += [event["timestamp"], location or config.CAMERA_LOCATION]
    banner = "  |  ".join(str(p) for p in parts)
    scale = 0.55 if len(banner) < 110 else 0.45
    cv2.rectangle(out, (0, 0), (W, 28), (0, 0, 0), -1)
    cv2.putText(out, banner, (8, 19), cv2.FONT_HERSHEY_SIMPLEX, scale,
                (255, 255, 255), 1, cv2.LINE_AA)
    name = f"snapshots/{seq:04d}_{event['type'].replace(' ', '_')}.jpg"
    cv2.imwrite(str(config.OUTPUT_DIR / name), out)
    return name


TRACK_CLASSES = list(config.VEHICLE_CLASSES |
                     {config.COCO["person"], config.COCO["traffic light"],
                      config.COCO["cell phone"]})


def new_run_state(fps, seq_base=0, frame_w=None, every=1):
    """Mutable per-run state shared by file processing and live mode."""
    # Don't upscale small footage: a 640px clip gains nothing at imgsz 960
    # but costs 2x CPU. Large footage is capped at config.IMGSZ.
    imgsz = config.IMGSZ
    if frame_w:
        imgsz = min(config.IMGSZ, max(640, ((int(frame_w) + 31) // 32) * 32))
    # The dashboard's speed selector (🐢/⚡/🚀) also drops INFERENCE RESOLUTION,
    # which is where the CPU time actually goes: measured on this laptop,
    # yolov8s runs 2.49 fps at imgsz 960 but 5.72 fps at 480. Since live replay
    # now drops frames to stay real-time, a lower imgsz doesn't speed the video
    # up — it means MORE of the frames get analysed, so violations that need
    # several hits are far more likely to accumulate.
    imgsz = min(imgsz, {1: 960, 2: 640}.get(int(every or 1), 480))
    return {
        "vehicle_ids": set(), "seq": seq_base, "violations": 0,
        "imgsz": imgsz, "speed_quad": None,
        "fps": max(float(fps or 25.0), 1.0),
        "plates": {},          # track_id -> {text, conf, img}
        "ocr_tries": {},       # track_id -> OCR attempts (budgeted)
        "ocr_miss": {},        # track_id -> consecutive detector misses
        "ocr_cool": {},        # track_id -> skip ANPR until this frame
        "best_crop": {},       # track_id -> (box_h, vehicle_crop) for the sweep
        "veh_meta": {},        # track_id -> {cls, first_seen, last_seen}
        # per-vehicle COMPLIANCE (the "normal / OK" states, not just violations):
        # helmet/seatbelt -> "ok" | "bad" | None(not assessed); top_speed km/h.
        "compliance": {},      # track_id -> {helmet, seatbelt, top_speed, over}
        "banners": [],         # [(text, expire_frame)]
        "dirty_vehicles": set(),
    }


def _update_compliance(state, riders, belts, speeds, calibrated=False):
    """Record each vehicle's OK / violation status per category so the
    dashboard can show COMPLIANT vehicles too, not only offenders. A
    positive violation is sticky (once bad, stays bad); an 'ok' is only set
    from a genuine positive detection (helmet/seatbelt actually seen) — never
    assumed from absence, same honesty rule as the violation engine.

    top_speed is recorded for every moving vehicle (accurate when calibrated,
    approximate otherwise). The 'over the limit' flag is only set when the
    camera is CALIBRATED — an approximate speed is shown but never asserts a
    limit breach (that would be a guess against a driver)."""
    comp = state["compliance"]

    def slot(tid):
        return comp.setdefault(tid, {"helmet": None, "seatbelt": None,
                                     "top_speed": None, "over": False})

    for r in riders:
        tid = r.get("track_id")
        if tid is None:
            continue
        s = slot(tid)
        if r.get("no_helmet"):
            s["helmet"] = "bad"
        elif r.get("helmet_ok") and s["helmet"] != "bad":
            s["helmet"] = "ok"

    for b in (belts or []):
        tid = b.get("track_id")
        if tid is None:
            continue
        s = slot(tid)
        if b.get("no_seatbelt"):
            s["seatbelt"] = "bad"
        elif b.get("seatbelt_ok") and s["seatbelt"] != "bad":
            s["seatbelt"] = "ok"

    for tid, spd in (speeds or {}).items():
        if tid is None or not spd:
            continue
        s = slot(tid)
        if s["top_speed"] is None or spd > s["top_speed"]:
            s["top_speed"] = spd
        if calibrated and spd > config.SPEED_LIMIT_KMPH:
            s["over"] = True
        state["dirty_vehicles"].add(tid)


def _plate_note(state, tid):
    """Human-readable reason why a vehicle has no confirmed plate yet."""
    p = state["plates"].get(tid)
    if p and not p.get("confirmed"):
        return f"unconfirmed ({p['hits']}/{config.PLATE_CONFIRM_READS} reads)"
    if state["ocr_tries"].get(tid, 0) > 0:
        return "plate unreadable"
    if tid in state["ocr_cool"] or state["ocr_miss"].get(tid, 0) > 0:
        return "no plate visible"
    bc = state["best_crop"].get(tid)
    if bc is None:
        return "too far / too small"
    return "not scanned yet"


def flush_vehicles(state):
    """Write tracked-vehicle rows to the DB. CONFIRMED plates only — an
    unconfirmed OCR guess never reaches the dashboard or a challan; the
    plate_note column explains WHY a plate is missing instead."""
    for tid in list(state["dirty_vehicles"]):
        meta = state["veh_meta"].get(tid)
        if not meta:
            continue
        p = state["plates"].get(tid)
        ok = bool(p and p.get("confirmed"))
        c = state["compliance"].get(tid, {})
        db.upsert_vehicle({
            "track_id": tid,
            "cls": meta["cls"],
            "plate": p["text"] if ok else None,
            "plate_conf": round(p["conf"], 3) if ok else None,
            "plate_img": p["img"] if ok else None,
            "plate_hits": p["hits"] if ok else 0,
            "plate_note": None if ok else _plate_note(state, tid),
            "helmet_status": c.get("helmet"),
            "seatbelt_status": c.get("seatbelt"),
            "top_speed": round(c["top_speed"], 1) if c.get("top_speed") else None,
            "over_speed": 1 if c.get("over") else 0,
            "first_seen": meta["first_seen"],
            "last_seen": meta["last_seen"],
            "source": "ai",
        })
    state["dirty_vehicles"].clear()


def final_plate_sweep(state):
    """Second pass for vehicles whose plate never confirmed: re-examine each
    track's BIGGEST captured appearance (the frame-by-frame / slow-motion
    idea) with a fresh OCR attempt. If the new read agrees with an earlier
    one, the plate confirms; a lone read still stays unconfirmed — honesty
    rules are never relaxed, we just look harder."""
    for tid, (bh, crop) in list(state["best_crop"].items()):
        p = state["plates"].get(tid)
        if p and p.get("confirmed"):
            continue
        box = [0, 0, crop.shape[1], crop.shape[0]]
        try:
            text, conf, pcrop, ran = ocr.read_plate_and_crop(crop, box,
                                                             min_ocr_h=8)
        except Exception:
            continue
        if ran and text != "UNKNOWN" and conf > 0:
            _record_read(state["plates"], tid, text, conf, pcrop)
            state["dirty_vehicles"].add(tid)


def process_frame(model, engine, frame, fidx, device, helmet_model, state,
                  seatbelt_model=None, frame_time=None):
    """Detection -> tracking -> ANPR -> violations for ONE frame.

    Logs any new violations to the DB, mutates `state` (see new_run_state)
    and returns the annotated BGR frame. Shared by file processing and live
    mode so all paths behave identically.

    frame_time: real wall-clock time (seconds) of THIS frame, for accurate
    live-camera speed; None -> frame_idx/fps (exact for video files).
    """
    res = model.track(frame, persist=True, tracker="bytetrack.yaml",
                      classes=TRACK_CLASSES, conf=config.TRACK_CONF,
                      imgsz=state.get("imgsz", config.IMGSZ),
                      device=device, verbose=False)[0]

    video_s = round(fidx / state["fps"], 2)
    vehicles, persons, motos, cars, lights, phones = [], [], [], [], [], []
    if res.boxes is not None:
        for b in res.boxes:
            cls = int(b.cls[0])
            conf = float(b.conf[0])
            box = [float(x) for x in b.xyxy[0].tolist()]
            tid = int(b.id[0]) if b.id is not None else None
            if cls in config.VEHICLE_CLASSES:
                vehicles.append({"track_id": tid, "cls": cls,
                                 "conf": conf, "box": box})
                if tid is not None:
                    state["vehicle_ids"].add(tid)
                    m = state["veh_meta"].setdefault(
                        tid, {"cls": _CLS_NAMES.get(cls, "Vehicle"),
                              "first_seen": video_s, "last_seen": video_s})
                    m["last_seen"] = video_s
                    m["cls"] = _CLS_NAMES.get(cls, "Vehicle")
                    state["dirty_vehicles"].add(tid)
                    v3 = state.get("threewheelers")
                    if v3 and tid in v3:
                        m["cls"] = v3[tid]
                if (cls == config.COCO["motorcycle"]
                        and conf >= config.CONF["moto_rider"]):
                    motos.append({"track_id": tid, "box": box})
                elif (cls in config.SEATBELT_CLASSES
                        and conf >= config.CONF["vehicle"]):
                    cars.append({"track_id": tid, "box": box})
            elif cls == config.COCO["person"]:
                if conf >= config.CONF["person"]:
                    persons.append({"track_id": tid, "box": box})
            elif cls == config.COCO["traffic light"]:
                if conf >= config.CONF["light"]:
                    lights.append(box)
            elif cls == config.COCO["cell phone"]:
                if conf >= config.CONF["phone"]:
                    phones.append(box)

    detected = detect_signal_color(frame, lights) if lights else None
    signal = engine.signal_state(fidx, detected)
    riders = build_riders(frame, motos, persons, helmet_model)
    belts = build_seatbelt_status(frame, cars, seatbelt_model)
    phone_status = build_phone_status(motos, cars, persons, phones)
    # Three-wheeler relabelling, when the optional model is installed. Labels
    # persist per track, so this needn't run on every analysed frame.
    if fidx % 5 == 0:
        found = apply_threewheeler_labels(frame, vehicles)
        if found:
            state.setdefault("threewheelers", {}).update(found)

    # remember each track's biggest (closest) appearance for the final
    # slow-motion plate sweep — like scrubbing the video frame by frame
    if fidx % 5 == 0:
        H = frame.shape[0]
        for v in vehicles:
            tid = v["track_id"]
            if tid is None:
                continue
            x1, y1, x2, y2 = [int(_clip(c, 0, m)) for c, m in
                              zip(v["box"], (frame.shape[1], H,
                                             frame.shape[1], H))]
            bh = y2 - y1
            prev = state["best_crop"].get(tid)
            if bh >= config.ANPR_MIN_VEH_H and (prev is None or bh > prev[0]):
                crop = frame[y1:y2, x1:x2].copy()
                if crop.size:
                    state["best_crop"][tid] = (bh, crop)

    if fidx % config.ANPR_EVERY == 0:
        _anpr_step(frame, vehicles, state, engine, fidx)

    new_events = engine.update(fidx, vehicles, signal, riders, belts,
                               phone_status, frame_time)

    # per-vehicle compliance (OK + violation states) for the dashboard's
    # Vehicles tab — needs speeds, so compute them once here and reuse for
    # both compliance and the on-screen overlay.
    speeds = {v["track_id"]: engine.speed_of(v["track_id"]) for v in vehicles}
    _update_compliance(state, riders, belts, speeds,
                       calibrated=engine.transform_fn is not None)

    active_ids = []
    for ev in new_events:
        state["seq"] += 1
        state["violations"] += 1
        # plate first, so the evidence image can carry it as proof
        plate, pconf, pimg = _best_plate(state, ev["track_id"],
                                         frame, ev["box"])
        snap = _save_snapshot(frame, ev, state["seq"], plate=plate,
                              location=state.get("location"))
        row = {
            "challan_id": make_challan_id(state["seq"]),
            "track_id": ev["track_id"],
            "type": ev["type"],
            "plate": plate,
            "plate_conf": round(pconf, 3),
            "plate_img": pimg,
            "speed_kmph": ev.get("speed_kmph"),
            "drive_seconds": ev.get("drive_seconds"),
            "fine": ev["fine"],
            "timestamp": ev["timestamp"],
            "frame_index": fidx,
            "video_s": video_s,
            "box": json.dumps([round(c, 1) for c in ev["box"]]),
            "snapshot": snap,
            "location": state.get("location") or config.CAMERA_LOCATION,
            "status": "PENDING",
            "source": "ai",
        }
        db.insert_violation(row)
        alerts.notify_async(row)      # email the police (if configured)
        active_ids.append(ev["track_id"])
        vm = state["veh_meta"].get(ev["track_id"]) or {}
        state["banners"].append(
            (f"{ev['type'].upper()}  -  {vm.get('cls', 'Vehicle')} #{ev['track_id']}",
             fidx + int(state["fps"] * 2.5)))

    if fidx % 30 == 0:
        flush_vehicles(state)

    return _draw(frame, vehicles, riders, lights, signal, engine, active_ids,
                 state, fidx, speeds, belts, phone_status)


def export_results_json():
    """Static backup of everything the dashboard needs."""
    payload = {
        "stats": db.stats(),
        "violations": db.all_violations(limit=5000),
        "vehicles": db.all_vehicles(limit=1000),
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    config.RESULTS_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
