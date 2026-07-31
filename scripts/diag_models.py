"""Diagnose WHY a rule did not fire on a given image.

Runs the raw models on one image and prints every detection with its class and
confidence, plus the exact gates the pipeline applies. Use this instead of
guessing at thresholds.

    python scripts/diag_models.py docs/screenshots/seatbelit_live_1.jpg
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))
os.chdir(ROOT)

import config      # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--upscale", type=int, default=1100)
    args = ap.parse_args()

    import cv2
    from detection import load, load_seatbelt, resolve_device

    frame = cv2.imread(args.image)
    if frame is None:
        print("cannot read", args.image)
        return 2
    h, w = frame.shape[:2]
    if w < args.upscale:
        s = args.upscale / float(w)
        frame = cv2.resize(frame, None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC)
        h, w = frame.shape[:2]
    print(f"image {os.path.basename(args.image)}  {w}x{h}")

    model, helmet_model = load()
    seatbelt_model = load_seatbelt()
    device = resolve_device()
    print("seatbelt model loaded:", seatbelt_model is not None)

    # ---- COCO pass, unfiltered, so we see what was ALMOST detected
    res = model.predict(frame, conf=0.10, imgsz=960, device=device,
                        verbose=False)[0]
    names = res.names
    print("\nCOCO detections at conf>=0.10:")
    cars = []
    for b in res.boxes or []:
        cls, conf = int(b.cls[0]), float(b.conf[0])
        box = [round(float(x), 1) for x in b.xyxy[0].tolist()]
        label = names[cls]
        gate = ""
        if cls in config.SEATBELT_CLASSES:
            gate = f"(car gate {config.CONF['vehicle']})"
            if conf >= config.CONF["vehicle"]:
                cars.append(box)
        elif cls == config.COCO["cell phone"]:
            gate = f"(phone gate {config.CONF['phone']})"
        elif cls == config.COCO["person"]:
            gate = f"(rider gate {config.CONF['rider_person']})"
        print(f"   {label:14s} {conf:.3f}  {box}  {gate}")

    # ---- seatbelt model on the windscreen crop the pipeline actually uses
    if seatbelt_model is None:
        print("\nseatbelt model NOT loaded - rule can never fire")
        return 0
    print(f"\nseatbelt model classes: {seatbelt_model.names}")
    if not cars:
        print("no car passed the vehicle gate -> seatbelt crop never built")
    for i, box in enumerate(cars):
        x1, y1, x2, y2 = box
        mh, mw = y2 - y1, x2 - x1
        if mh < config.MIN_CAR_H_FRAC * h:
            print(f"car {i}: too small ({mh:.0f}px < "
                  f"{config.MIN_CAR_H_FRAC * h:.0f}px) -> skipped")
            continue
        wx1, wx2 = int(x1 + 0.08 * mw), int(x2 - 0.08 * mw)
        wy1, wy2 = int(y1), int(y1 + 0.55 * mh)
        crop = frame[max(0, wy1):min(h, wy2), max(0, wx1):min(w, wx2)]
        print(f"car {i}: box {box} -> windscreen crop {crop.shape[1]}x{crop.shape[0]}")
        if crop.size == 0:
            continue
        from detection import seatbelt_verdict
        r = seatbelt_model.predict(crop, verbose=False, conf=0.05,
                                   device=device)[0]
        label, conf = seatbelt_verdict(r)
        print(f"      verdict: {label} {conf:.3f}"
              f"   (accuse gate {config.CONF['no_seatbelt']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
