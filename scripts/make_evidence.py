"""Capture demo evidence: annotated frames + the system's own challan snapshots.

Runs a clip through the real pipeline, saves the most interesting annotated
frames (ones where a violation fired, plus frames rich in detections), and
copies the evidence snapshots the violation engine itself produced. Output
lands in docs/screenshots/ for the README and the pitch deck.

    python scripts/make_evidence.py data/videos/IMG_6992.MOV --frames 1200
"""
import argparse
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))
os.chdir(ROOT)

import config      # noqa: E402
import pipeline    # noqa: E402
import db          # noqa: E402
from violations import ViolationEngine    # noqa: E402
from detection import resolve_device      # noqa: E402

OUT_DIR = os.path.join(ROOT, "docs", "screenshots")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("clip")
    ap.add_argument("--frames", type=int, default=1200)
    ap.add_argument("--every", type=int, default=3)
    ap.add_argument("--prefix", default=None)
    args = ap.parse_args()

    import cv2
    from ultralytics import YOLO

    os.makedirs(OUT_DIR, exist_ok=True)
    path = args.clip if os.path.isabs(args.clip) else os.path.join(ROOT, args.clip)
    prefix = args.prefix or os.path.splitext(os.path.basename(path))[0].lower()

    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        print("cannot open", path)
        return 2
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    sw = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    sh = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    scale = 1.0
    W, H = sw, sh
    if W > config.LIVE_MAX_W or H > config.LIVE_MAX_H:
        scale = min(config.LIVE_MAX_W / float(W), config.LIVE_MAX_H / float(H))
        W, H = int(round(W * scale)), int(round(H * scale))

    model = YOLO(config.VEHICLE_MODEL)
    _, helmet_model = pipeline.load()
    seatbelt_model = pipeline.load_seatbelt()
    device = resolve_device()
    cal_pts, cal_target, cal_dir = pipeline.load_calibration(path, sw, sh)
    if cal_pts and scale != 1.0:
        cal_pts = [[x * scale, y * scale] for x, y in cal_pts]
    ppm = pipeline.load_pixels_per_meter(path, sw, sh)
    if ppm and scale != 1.0:
        ppm *= scale

    engine = ViolationEngine(
        W, H, fps, transform_fn=pipeline.make_transform_fn(cal_pts, cal_target),
        allowed_direction=cal_dir, ppm=ppm)
    db.init_db()
    db.clear()
    for snap in config.SNAPSHOT_DIR.glob("*.jpg"):
        try:
            snap.unlink()
        except OSError:
            pass
    state = pipeline.new_run_state(fps, seq_base=0, frame_w=W, every=args.every)
    state["speed_quad"] = cal_pts
    state["location"] = config.CAMERA_LOCATION

    saved = 0
    best = []            # (score, frame_idx, image) for the richest frames
    prev_viol = 0
    fidx = 0
    while fidx < args.frames:
        ok, frame = cap.read()
        if not ok:
            break
        if fidx % args.every == 0:
            if scale != 1.0:
                frame = cv2.resize(frame, (W, H), interpolation=cv2.INTER_AREA)
            annotated = pipeline.process_frame(model, engine, frame, fidx, device,
                                               helmet_model, state, seatbelt_model)
            n_viol = len(engine.events)
            # a frame where a violation just fired is the money shot
            if n_viol > prev_viol:
                fn = os.path.join(OUT_DIR, f"{prefix}_violation_{saved}.jpg")
                cv2.imwrite(fn, annotated, [cv2.IMWRITE_JPEG_QUALITY, 92])
                print("violation frame ->", os.path.basename(fn))
                saved += 1
                prev_viol = n_viol
            # keep the busiest frames as general "system working" shots
            speeds = sum(1 for t in engine.tracks if engine.speed_of(t))
            best.append((speeds, fidx, annotated.copy()))
            best.sort(key=lambda x: -x[0])
            best = best[:3]
        fidx += 1
    cap.release()

    for i, (score, f, img) in enumerate(best):
        fn = os.path.join(OUT_DIR, f"{prefix}_live_{i}.jpg")
        cv2.imwrite(fn, img, [cv2.IMWRITE_JPEG_QUALITY, 92])
        print(f"live frame -> {os.path.basename(fn)} ({score} vehicles with speed)")

    # the engine's own evidence snapshots (what a challan shows)
    snaps = sorted(config.SNAPSHOT_DIR.glob("*.jpg"))
    for i, s in enumerate(snaps[:6]):
        dst = os.path.join(OUT_DIR, f"{prefix}_evidence_{i}.jpg")
        shutil.copy(str(s), dst)
        print("evidence   ->", os.path.basename(dst))

    rows = db.all_violations()
    print(f"\n{len(rows)} violation(s); {len(snaps)} evidence snapshot(s)")
    for r in rows[:10]:
        print(f"   {r.get('type')}  vehicle #{r.get('track_id')}  "
              f"plate={r.get('plate') or '-'}")
    print("output:", OUT_DIR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
