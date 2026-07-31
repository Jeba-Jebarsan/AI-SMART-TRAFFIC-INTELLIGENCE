"""Explain, frame by frame, why Illegal Parking did or did not fire on a clip.

The rule has several independent gates and check_clip only reports the final
answer, so a clip that "should obviously" fire gives no clue which gate
stopped it. This prints the state of every gate for every tracked vehicle.

    python scripts/diag_parking.py data/videos/illegal_parking_sl.mp4
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
    ap.add_argument("clip")
    ap.add_argument("--every", type=int, default=2)
    ap.add_argument("--frames", type=int, default=100000)
    args = ap.parse_args()

    import cv2
    from ultralytics import YOLO

    import pipeline
    from detection import resolve_device
    from violations import ViolationEngine

    path = args.clip
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    sw = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    sh = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    scale = 1.0
    W, H = sw, sh
    if W > config.LIVE_MAX_W or H > config.LIVE_MAX_H:
        scale = min(config.LIVE_MAX_W / float(W), config.LIVE_MAX_H / float(H))
        W, H = int(round(W * scale)), int(round(H * scale))
    print(f"clip {os.path.basename(path)}  {sw}x{sh} -> {W}x{H}  {fps:.1f} fps")
    print(f"gates: ILLEGAL_PARK_SECONDS={config.ILLEGAL_PARK_SECONDS}  "
          f"PARK_MIN_OBSERVATIONS={config.PARK_MIN_OBSERVATIONS}  "
          f"enabled={config.ENABLE['illegal_parking']}")

    model = YOLO(config.VEHICLE_MODEL)
    device = resolve_device()
    engine = ViolationEngine(W, H, fps)
    state = pipeline.new_run_state(fps, frame_w=W, every=args.every)

    fidx = 0
    seen = {}
    while fidx < args.frames:
        ok, frame = cap.read()
        if not ok:
            break
        if fidx % args.every == 0:
            if scale != 1.0:
                frame = cv2.resize(frame, (W, H), interpolation=cv2.INTER_AREA)
            res = model.track(frame, persist=True, conf=config.TRACK_CONF,
                              classes=list(config.VEHICLE_CLASSES),
                              imgsz=state["imgsz"], device=device,
                              tracker="bytetrack.yaml", verbose=False)[0]
            vehicles = []
            for b in (res.boxes or []):
                if b.id is None:
                    continue
                vehicles.append({"track_id": int(b.id[0]), "cls": int(b.cls[0]),
                                 "conf": float(b.conf[0]),
                                 "box": [float(x) for x in b.xyxy[0].tolist()]})
            engine.update(fidx, vehicles, "UNKNOWN", [])
            for v in vehicles:
                tid = v["track_id"]
                st = engine.tracks.get(tid)
                if not st:
                    continue
                secs = (fidx - st["park_start"]) / fps if st.get("park_start") else 0.0
                d = seen.setdefault(tid, {"cls": v["cls"], "obs": 0, "max_park": 0.0,
                                          "ever_moved": False, "first": fidx})
                d["obs"] += 1
                d["last"] = fidx
                d["max_park"] = max(d["max_park"], secs)
                d["ever_moved"] = d["ever_moved"] or bool(st.get("ever_moved"))
        fidx += 1
    cap.release()

    names = {1: "bicycle", 2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}
    print(f"\nscanned {fidx} frames ({fidx // args.every} analysed)\n")
    print(f"{'id':>4} {'class':<11} {'obs':>4} {'seen s':>7} {'max still s':>12} "
          f"{'ever_moved':>11}  verdict")
    for tid, d in sorted(seen.items(), key=lambda x: -x[1]["max_park"])[:12]:
        span = (d["last"] - d["first"]) / fps
        if d["ever_moved"]:
            verdict = "MOVED -> exempt (traffic, not parked)"
        elif d["obs"] < config.PARK_MIN_OBSERVATIONS:
            verdict = f"too few observations (<{config.PARK_MIN_OBSERVATIONS})"
        elif d["max_park"] < config.ILLEGAL_PARK_SECONDS:
            verdict = (f"still only {d['max_park']:.1f}s of "
                       f"{config.ILLEGAL_PARK_SECONDS}s needed")
        else:
            verdict = "*** WOULD FIRE ***"
        print(f"{tid:>4} {names.get(d['cls'], d['cls']):<11} {d['obs']:>4} "
              f"{span:>7.1f} {d['max_park']:>12.1f} {str(d['ever_moved']):>11}  "
              f"{verdict}")
    ev = [e for e in engine.events if e["type"] == "Illegal Parking"]
    print(f"\nIllegal Parking events: {len(ev)}")


if __name__ == "__main__":
    main()
