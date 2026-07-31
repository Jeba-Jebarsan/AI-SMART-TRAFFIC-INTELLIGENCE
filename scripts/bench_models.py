"""Benchmark candidate detectors on OUR footage, not on COCO leaderboards.

The metric that matters here is not mAP. Most rules need a RIDER associated
with a motorcycle (helmet, triple riding, phone), so the question is: how many
bikes does this model find, and on how many of them can we actually resolve
the rider? A model with better mAP that runs at a third of the speed may
analyse so few frames on a CPU that it finds fewer violations in practice.

    python scripts/bench_models.py --clip data/videos/IMG_6992.MOV --frames 300

Models are downloaded on first use by ultralytics. Anything that fails to
download is reported and skipped, so this is safe to run offline.
"""
import argparse
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))
os.chdir(ROOT)

import config      # noqa: E402

CANDIDATES = ["yolov8n.pt", "yolov8s.pt", "yolov8m.pt",
              "yolo11s.pt", "yolo11m.pt"]


def bench(name, frames, clip, every, imgsz):
    import cv2
    from ultralytics import YOLO

    from detection import load, resolve_device
    from pipeline import build_riders

    _, helmet_model = load()
    device = resolve_device()
    local = os.path.join(config.MODELS_DIR, name)
    try:
        model = YOLO(local if os.path.exists(local) else name)
    except Exception as e:
        return {"model": name, "error": str(e)[:90]}

    cap = cv2.VideoCapture(clip)
    if not cap.isOpened():
        return {"model": name, "error": "cannot open clip"}

    motos = persons = riders_assoc = riders_3 = no_helmet = 0
    infer_s = 0.0
    n = fidx = 0
    while fidx < frames:
        ok, frame = cap.read()
        if not ok:
            break
        if fidx % every == 0:
            h, w = frame.shape[:2]
            if w > config.LIVE_MAX_W:
                s = config.LIVE_MAX_W / float(w)
                frame = cv2.resize(frame, (int(w * s), int(h * s)),
                                   interpolation=cv2.INTER_AREA)
            t0 = time.perf_counter()
            res = model.predict(frame, conf=config.TRACK_CONF, imgsz=imgsz,
                                device=device, verbose=False)[0]
            infer_s += time.perf_counter() - t0
            n += 1
            m_boxes, p_boxes = [], []
            for i, b in enumerate(res.boxes or []):
                cls, conf = int(b.cls[0]), float(b.conf[0])
                box = [float(x) for x in b.xyxy[0].tolist()]
                if (cls == config.COCO["motorcycle"]
                        and conf >= config.CONF["moto_rider"]):
                    m_boxes.append({"track_id": i + 1, "box": box})
                elif (cls == config.COCO["person"]
                        and conf >= config.CONF["rider_person"]):
                    p_boxes.append({"track_id": i + 1, "box": box})
            motos += len(m_boxes)
            persons += len(p_boxes)
            for r in build_riders(frame, m_boxes, p_boxes, helmet_model):
                if r["riders"] >= 1:
                    riders_assoc += 1
                if r["riders"] >= 3:
                    riders_3 += 1
                if r["no_helmet"]:
                    no_helmet += 1
        fidx += 1
    cap.release()
    return {"model": name, "frames": n, "motorcycles": motos, "persons": persons,
            "with_rider": riders_assoc, "three_up": riders_3,
            "no_helmet": no_helmet,
            "fps": round(n / infer_s, 2) if infer_s else 0.0,
            "ms_per_frame": round(1000 * infer_s / n, 1) if n else 0.0}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clip", default="data/videos/IMG_6992.MOV")
    ap.add_argument("--frames", type=int, default=300)
    ap.add_argument("--every", type=int, default=3)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--models", default=",".join(CANDIDATES))
    args = ap.parse_args()

    rows = []
    for name in args.models.split(","):
        name = name.strip()
        if not name:
            continue
        print(f"--- {name}", flush=True)
        r = bench(name, args.frames, args.clip, args.every, args.imgsz)
        rows.append(r)
        print("   ", r, flush=True)

    print(f"\n{'model':14s} {'fps':>6s} {'ms/f':>7s} {'bikes':>7s} "
          f"{'w/rider':>8s} {'3-up':>6s} {'noHelm':>7s}")
    for r in rows:
        if r.get("error"):
            print(f"{r['model']:14s}  ERROR: {r['error']}")
            continue
        print(f"{r['model']:14s} {r['fps']:6.2f} {r['ms_per_frame']:7.1f} "
              f"{r['motorcycles']:7d} {r['with_rider']:8d} {r['three_up']:6d} "
              f"{r['no_helmet']:7d}")
    print(f"\nclip={args.clip}  imgsz={args.imgsz}  device=CPU"
          "\nwith_rider is the number that matters: no rider, no helmet rule.")


if __name__ == "__main__":
    main()
