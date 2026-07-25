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


def has_seatbelt_model():
    return os.path.exists(config.SEATBELT_MODEL)


def load_seatbelt():
    """Load (and cache) the optional seatbelt model, or return None (feature
    stays off — no heuristic fallback, unlike helmets)."""
    global _seatbelt
    if _seatbelt is None and has_seatbelt_model():
        from ultralytics import YOLO
        _seatbelt = YOLO(config.SEATBELT_MODEL)
    return _seatbelt
