"""Run a still IMAGE through the real detection pipeline and save the
annotated result as demo evidence.

Public traffic photographs are often a better demo source than video: one
image can clearly show a helmet-less rider, a phone in a driver's hand or
three people on a motorcycle, with no privacy exposure from footage you shot
yourself.

    python scripts/detect_image.py photo.jpg --out docs/evidence/helmet

IMPORTANT — what a single image can and cannot show. Detection and per-vehicle
verdicts (NO HELMET / ON PHONE / seatbelt / plate reading) are per-frame and
appear on the annotation. Actual VIOLATIONS deliberately do not fire, because
the engine requires several frames of persistence and camera-motion-compensated
movement before it will accuse anyone. A still frame has neither, so this
prints detections, not challans — which is the honest thing for a photograph.
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))
os.chdir(ROOT)

import config      # noqa: E402
import pipeline    # noqa: E402
import db          # noqa: E402
from violations import ViolationEngine    # noqa: E402
from detection import resolve_device      # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--out", default="docs/evidence/images")
    ap.add_argument("--name", default=None)
    args = ap.parse_args()

    import cv2
    from ultralytics import YOLO

    path = args.image if os.path.isabs(args.image) else os.path.join(ROOT, args.image)
    frame = cv2.imread(path)
    if frame is None:
        print("cannot read image:", path)
        return 2

    # Upscale small photos: the helmet/seatbelt models need enough pixels on a
    # head or a windscreen to judge anything.
    h, w = frame.shape[:2]
    if w < 1100:
        s = 1100.0 / w
        frame = cv2.resize(frame, None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC)
        h, w = frame.shape[:2]

    model = YOLO(config.VEHICLE_MODEL)
    _, helmet_model = pipeline.load()
    seatbelt_model = pipeline.load_seatbelt()
    device = resolve_device()

    engine = ViolationEngine(w, h, 25.0)
    db.init_db()
    state = pipeline.new_run_state(25.0, seq_base=0, frame_w=w, every=1)
    state["location"] = "public dataset image"

    annotated = pipeline.process_frame(model, engine, frame, 0, device,
                                       helmet_model, state, seatbelt_model)

    os.makedirs(args.out, exist_ok=True)
    base = args.name or os.path.splitext(os.path.basename(path))[0]
    dst = os.path.join(args.out, f"{base}_detected.jpg")
    cv2.imwrite(dst, annotated, [cv2.IMWRITE_JPEG_QUALITY, 92])

    # report what the per-frame analysis actually concluded
    res = model.track(frame, persist=False, tracker="bytetrack.yaml",
                      classes=pipeline.TRACK_CLASSES, conf=config.TRACK_CONF,
                      imgsz=state.get("imgsz", config.IMGSZ), device=device,
                      verbose=False)[0]
    motos, persons, cars = [], [], []
    for b in (res.boxes or []):
        c, cf = int(b.cls[0]), float(b.conf[0])
        box = [float(x) for x in b.xyxy[0].tolist()]
        if c == config.COCO["motorcycle"] and cf >= config.CONF["moto_rider"]:
            motos.append({"track_id": None, "box": box})
        elif c == config.COCO["person"] and cf >= config.CONF["person"]:
            persons.append({"track_id": None, "box": box})
        elif c in config.SEATBELT_CLASSES and cf >= config.CONF["vehicle"]:
            cars.append({"track_id": None, "box": box})

    print(f"saved: {dst}")
    riders = pipeline.build_riders(frame, motos, persons, helmet_model)
    for r in riders:
        verdict = ("NO HELMET" if r["no_helmet"]
                   else ("helmet OK" if r["helmet_ok"] else "not judged"))
        print(f"   motorcycle: riders={r['riders']}  helmet -> {verdict}")
    belts = pipeline.build_seatbelt_status(frame, cars, seatbelt_model)
    for b in belts:
        print(f"   car: seatbelt -> "
              f"{'NO SEATBELT' if b.get('no_seatbelt') else 'belt seen / not judged'}")
    if not riders and not belts:
        print("   (no motorcycles or cars large enough to judge)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
