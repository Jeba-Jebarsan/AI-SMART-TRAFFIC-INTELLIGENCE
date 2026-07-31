"""YOLO model loading + device resolution.

Heavy imports (ultralytics / torch) happen lazily inside _load() so that the
FastAPI app, the dashboard and the seed-data path all work with none of the ML
stack installed. Only actual video processing needs these libraries.
"""
import os

import config

_vehicle = None
_helmet = None
_plate = None
_seatbelt = None
# The sanity probe costs three inferences, so run it once per process even
# when it fails (otherwise every frame would re-probe a rejected model).
_seatbelt_checked = False
_threewheeler = None
_device = None


def _tune_cpu_threads():
    """Cap inference threads so frame capture isn't starved.

    torch grabs nearly every core for inference (10 of 12 by default). During
    live capture that leaves nothing to schedule the reader thread on, and the
    on-screen video stutters. Measured on this 12-core laptop, capping
    inference at ~2/3 of the cores raised the published video rate from 6.8 to
    7.9 fps AND raised the number of frames actually analysed from 43 to 56 —
    saturating every core made both jobs slower, not faster.
    """
    try:
        import os
        import torch
        n = config.TORCH_THREADS or max(2, int((os.cpu_count() or 4) * 0.67))
        torch.set_num_threads(int(n))
    except Exception:
        pass


def resolve_device():
    """Return the best available device: GPU index 0 if CUDA is up, else 'cpu'."""
    global _device
    if _device is not None:
        return _device
    if config.DEVICE != "auto":
        _device = config.DEVICE
        return _device
    try:
        import torch
        _device = 0 if torch.cuda.is_available() else "cpu"
    except Exception:
        _device = "cpu"
    if _device == "cpu":
        _tune_cpu_threads()
    return _device


def has_helmet_model():
    return os.path.exists(config.HELMET_MODEL)


def load():
    """Load (and cache) the vehicle model and, if present, the helmet model."""
    global _vehicle, _helmet
    if _vehicle is None:
        from ultralytics import YOLO
        _vehicle = YOLO(config.VEHICLE_MODEL)
        if has_helmet_model():
            _helmet = YOLO(config.HELMET_MODEL)
    return _vehicle, _helmet


def has_plate_model():
    return os.path.exists(config.PLATE_MODEL)


def load_plate():
    """Load (and cache) the optional licence-plate detector, or return None."""
    global _plate
    if _plate is None and has_plate_model():
        from ultralytics import YOLO
        _plate = YOLO(config.PLATE_MODEL)
    return _plate


def has_threewheeler_model():
    return os.path.exists(config.THREEWHEELER_MODEL)


def load_threewheeler():
    """Load (and cache) the optional three-wheeler detector, or return None.

    Without it, tuk-tuks keep whatever COCO class the base detector picked
    (usually 'truck'), which is a labelling inaccuracy only — no violation
    rule depends on the distinction.
    """
    global _threewheeler
    if _threewheeler is None and has_threewheeler_model():
        from ultralytics import YOLO
        _threewheeler = YOLO(config.THREEWHEELER_MODEL)
    return _threewheeler


def has_seatbelt_model():
    return os.path.exists(config.SEATBELT_MODEL)


def _seatbelt_model_is_sane(model):
    """Decide whether a drop-in seatbelt model may be trusted to accuse drivers.

    Requirement: it must be a DETECTION model, i.e. it must localise the belt
    (or its absence) to a box. Two independent reasons, both hard:

    1. Evidence. Every challan this system issues points at the thing it is
       accusing — a rider's head, a vehicle's box. A whole-windscreen
       classifier returns one label for a crop that may contain a driver, a
       front passenger and part of the back seat, so there is nothing to draw
       on the evidence photo and nothing for a human reviewer to check.
    2. Measured failure. The model shipped in models/seatbelt.pt is a
       classify-task model, and it does not discriminate: it returns
       'no_seatbelt' at confidence 1.000 for a motorway scene AND for a driver
       plainly wearing a belt, while calling random noise 'seat_belt'. Wired
       up as a classifier it fired No Seatbelt on 6 of 18 sampled frames of
       footage whose driver is wearing a belt.

    A blank-image probe does NOT catch this (that model happens to call blanks
    'seat_belt'), which is why the check is structural rather than empirical.
    Set config.SEATBELT_ALLOW_CLASSIFIER = True to override, knowing the above.
    """
    task = getattr(model, "task", None)
    if task == "classify" and not getattr(config, "SEATBELT_ALLOW_CLASSIFIER", False):
        return False
    return True


def seatbelt_verdict(result):
    """(label, confidence) from either a DETECTION or a CLASSIFICATION model.

    Ultralytics returns boxes for detect-task weights and probs for
    classify-task weights. The pipeline only ever read .boxes, so a
    classification model silently produced nothing at all and the seatbelt
    rule could never fire on any footage — it looked like a footage problem
    for weeks. Handle both shapes.
    """
    probs = getattr(result, "probs", None)
    if probs is not None:
        return result.names[int(probs.top1)], float(probs.top1conf)
    best, best_conf = None, 0.0
    for b in (getattr(result, "boxes", None) or []):
        conf = float(b.conf[0])
        if conf > best_conf:
            best, best_conf = result.names[int(b.cls[0])], conf
    return best, best_conf


def load_seatbelt():
    """Load (and cache) the optional seatbelt model, or return None (feature
    stays off — no heuristic fallback, unlike helmets).

    A model that fails the sanity probe is treated as absent.
    """
    global _seatbelt, _seatbelt_checked
    if _seatbelt is None and not _seatbelt_checked and has_seatbelt_model():
        _seatbelt_checked = True
        from ultralytics import YOLO
        model = YOLO(config.SEATBELT_MODEL)
        if _seatbelt_model_is_sane(model):
            _seatbelt = model
        else:
            print("WARNING: models/seatbelt.pt is a classification model, not a "
                  "detector. It cannot localise the belt, so it cannot produce "
                  "evidence — and this particular one reports 'no seatbelt' on "
                  "belted drivers and on empty road scenes alike. No Seatbelt "
                  "is DISABLED. Drop in a seatbelt DETECTION model to enable it.")
    return _seatbelt
