"""Demo-readiness checker: will THIS clip actually show violations?

Run a clip through the real pipeline and report what the system detects, what
fires, and — most usefully — WHY anything that can't fire is blocked. Use it to
vet footage before a demo instead of discovering on stage that a clip contains
nothing the AI can flag.

    python scripts/check_clip.py data/videos/mine.mp4
    python scripts/check_clip.py data/videos/mine.mp4 --frames 400 --every 2

Exit status is 0 if at least one violation fired, 1 otherwise, so it can be
used in a pre-demo check script.
"""
import argparse
import collections
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))
os.chdir(ROOT)

import config          # noqa: E402
import pipeline        # noqa: E402
import db              # noqa: E402
from violations import ViolationEngine   # noqa: E402
from detection import resolve_device     # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("clip", help="path to a video file")
    ap.add_argument("--frames", type=int, default=400,
                    help="how many source frames to scan (default 400)")
    ap.add_argument("--every", type=int, default=2,
                    help="analyse every Nth frame (default 2)")
    args = ap.parse_args()

    import cv2
    from ultralytics import YOLO

    path = args.clip if os.path.isabs(args.clip) else os.path.join(ROOT, args.clip)
    if not os.path.exists(path):
        print(f"!! no such file: {path}")
        return 2

    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        print(f"!! cannot open: {path}")
        return 2
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    src_w, src_h = W, H
    # Mirror live mode's downscaling, or these numbers wouldn't describe what
    # the dashboard will actually do with this clip.
    scale = 1.0
    if W > config.LIVE_MAX_W or H > config.LIVE_MAX_H:
        scale = min(config.LIVE_MAX_W / float(W), config.LIVE_MAX_H / float(H))
        W, H = int(round(W * scale)), int(round(H * scale))

    print("=" * 66)
    print(f"CLIP   {os.path.basename(path)}")
    print(f"       {src_w}x{src_h} @ {fps:.0f} fps, {total} frames "
          f"({total / max(fps, 1):.0f}s)"
          + (f"  -> analysed at {W}x{H}" if scale != 1.0 else ""))

    model = YOLO(config.VEHICLE_MODEL)
    _, helmet_model = pipeline.load()
    seatbelt_model = pipeline.load_seatbelt()
    device = resolve_device()
    cal_pts, cal_target, cal_dir = pipeline.load_calibration(path, src_w, src_h)
    if cal_pts and scale != 1.0:
        cal_pts = [[x * scale, y * scale] for x, y in cal_pts]

    print(f"MODEL  {os.path.basename(config.VEHICLE_MODEL)} on {device}")
    print(f"SETUP  speed calibration: {'YES' if cal_pts else 'NO'}   "
          f"direction: {'YES' if cal_dir else 'NO'}   "
          f"helmet model: {'YES' if helmet_model else 'no (heuristic)'}   "
          f"seatbelt model: {'YES' if seatbelt_model else 'NO'}")
    print("=" * 66)

    ppm = pipeline.load_pixels_per_meter(path, src_w, src_h)
    if ppm and scale != 1.0:
        ppm *= scale
    engine = ViolationEngine(
        W, H, fps,
        transform_fn=pipeline.make_transform_fn(cal_pts, cal_target),
        allowed_direction=cal_dir, ppm=ppm)
    sly = pipeline.load_stop_line_y(path, src_w, src_h)
    if sly:
        engine.stop_line_y = sly * H
    slx = pipeline.load_stop_line_x(path, src_w, src_h)
    if slx:
        engine.stop_line_x = slx * W
    roi, zone = pipeline.load_signal_setup(path, src_w, src_h)
    if zone:
        engine.red_light_zone = [[x * W, y * H] for x, y in zone]
    db.init_db()
    db.clear()
    state = pipeline.new_run_state(fps, seq_base=0, frame_w=W, every=args.every)
    state["speed_quad"] = cal_pts
    if roi:
        state["signal_roi"] = [roi[0] * W, roi[1] * H, roi[2] * W, roi[3] * H]
    state["location"] = "clip-check"

    seen = collections.Counter()
    speeds = {}
    signal_states = collections.Counter()
    t0 = time.time()
    fidx = 0
    analysed = 0
    while fidx < args.frames:
        ok, frame = cap.read()
        if not ok:
            break
        if fidx % args.every == 0:
            if scale != 1.0:
                frame = cv2.resize(frame, (W, H), interpolation=cv2.INTER_AREA)
            pipeline.process_frame(model, engine, frame, fidx, device,
                                   helmet_model, state, seatbelt_model)
            analysed += 1
            for tid in engine.tracks:
                s = engine.speed_of(tid)
                if s:
                    speeds[tid] = max(speeds.get(tid, 0), s)
        fidx += 1
    cap.release()

    for r in db.all_violations():
        seen[r.get("type", "?")] += 1

    dt = time.time() - t0
    print(f"\nscanned {fidx} frames ({analysed} analysed) in {dt:.0f}s "
          f"-> {analysed / max(dt, .01):.1f} analysed fps")
    print(f"vehicles tracked : {len(state['vehicle_ids'])}")
    print(f"with a speed     : {len(speeds)}"
          + (f"   max {max(speeds.values())} km/h" if speeds else ""))

    print("\nVIOLATIONS FIRED")
    if seen:
        for k, v in seen.most_common():
            print(f"   {config.VIOLATION_META.get(k, {}).get('emoji', ' ')} {k:<18} {v}")
    else:
        print("   none")

    # --- the useful part: what is blocked, and how to unblock it -----------
    print("\nRULE STATUS")
    blocked = []

    def row(name, ok, why, fix=None):
        mark = "OK  " if ok else "OFF "
        print(f"   {mark} {name:<18} {why}")
        if not ok and fix:
            blocked.append((name, fix))

    row("Over Speeding", bool(cal_pts),
        "calibrated" if cal_pts else "no speed calibration for this clip",
        "open the clip in the dashboard and use the 🎯 Speed setup tool "
        "(click 4 road corners + enter real metres)")
    row("Wrong Way", bool(cal_dir),
        "direction set" if cal_dir else "no travel direction calibrated",
        "pick the traffic direction in the 🎯 Speed setup tool")
    # "missing" was wrong and misleading: the file is present, it is REFUSED.
    # Saying "missing" sent us hunting for footage for weeks when the real
    # problem was the model itself.
    import os as _os
    _sb_present = _os.path.exists(config.SEATBELT_MODEL)
    row("No Seatbelt", seatbelt_model is not None,
        "model loaded" if seatbelt_model
        else ("models/seatbelt.pt REJECTED (classifier - cannot localise the "
              "belt, and fails to discriminate)" if _sb_present
              else "models/seatbelt.pt is missing"),
        "drop a seatbelt DETECTION model (not a classifier) at "
        "models/seatbelt.pt")
    row("No Helmet", helmet_model is not None,
        "model loaded" if helmet_model else "using the weak colour heuristic",
        "drop a YOLOv8 helmet model at models/helmet.pt")
    print("   --   Red Light Jump    needs a traffic light visible in frame")
    print("   --   Triple Riding     needs >=3 people on one moving motorcycle")
    print("   --   Wheelie Stunt     needs a real wheelie (front wheel lifted)")
    print("   --   Mobile Phone Use  needs a visible phone in a rider/driver's hand")
    print("   --   No Rest Break     needs one vehicle tracked continuously for "
          f"{config.MAX_CONTINUOUS_DRIVE_SECONDS}s")
    print("   --   Illegal Parking   needs a vehicle stationary for "
          f"{config.ILLEGAL_PARK_SECONDS}s (clip must be longer than that)")

    if blocked:
        print("\nTO UNBLOCK")
        for name, fix in blocked:
            print(f"   * {name}: {fix}")

    if not seen:
        print("\nVERDICT: this clip produced NO violations.")
        print("  That is not necessarily a bug — the system refuses to fine")
        print("  parked or stationary vehicles, and only reports what it can")
        print("  actually prove. For a demo you want footage with MOVING")
        print("  traffic that genuinely contains the offences you want to show.")
    else:
        print(f"\nVERDICT: usable — {sum(seen.values())} violation(s) across "
              f"{len(seen)} type(s).")
    return 0 if seen else 1


if __name__ == "__main__":
    sys.exit(main())
