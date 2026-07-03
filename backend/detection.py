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
_device = None


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
