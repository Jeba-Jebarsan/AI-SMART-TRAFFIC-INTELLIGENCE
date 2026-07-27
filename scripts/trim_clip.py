"""Cut a short, demo-sized clip out of a longer video.

Long source videos are unusable on stage: a 12-minute recording buries the one
moment that matters. This writes just the seconds you want, re-encoded so the
result seeks cleanly in the dashboard player.

    python scripts/trim_clip.py src.mp4 --start 95 --dur 20 --name red_light_jump
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--start", type=float, required=True, help="start second")
    ap.add_argument("--dur", type=float, default=20.0, help="clip length in seconds")
    ap.add_argument("--name", required=True, help="output basename (no extension)")
    ap.add_argument("--outdir", default="data/videos")
    args = ap.parse_args()

    import cv2

    src = args.src if os.path.isabs(args.src) else os.path.join(ROOT, args.src)
    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        print("cannot open:", src)
        return 2
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    first = int(args.start * fps)
    last = min(total, int((args.start + args.dur) * fps))
    if first >= total:
        print(f"start {args.start}s is past the end of a {total/fps:.0f}s video")
        return 2

    os.makedirs(args.outdir, exist_ok=True)
    dst = os.path.join(args.outdir, args.name + ".mp4")
    vw = cv2.VideoWriter(dst, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    cap.set(cv2.CAP_PROP_POS_FRAMES, first)
    n = 0
    while n < (last - first):
        ok, frame = cap.read()
        if not ok:
            break
        vw.write(frame)
        n += 1
    cap.release()
    vw.release()
    print(f"{dst}  {w}x{h} @ {fps:.0f}fps  {n} frames = {n/fps:.1f}s "
          f"(from {args.start:.0f}s of a {total/fps:.0f}s source)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
