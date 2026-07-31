"""Sweep a clip as SINGLE STILLS through the appearance-rule analyser.

make_evidence.py runs a clip as a temporal stream, which is right for speed,
parking and red light. But the appearance rules (helmet, triple riding,
seatbelt, phone) need only one good frame, and a stream run can miss them
because the persistence gate needs the same subject held across frames while
the subject is only briefly well-resolved.

This walks a clip at a coarse stride, runs each frame through
pipeline.analyse_image (upscaling small frames), and reports which frames
produced which violations - so we can find a genuine evidence frame instead of
staging one.

    python scripts/scan_stills.py "data/videos/_unused/seatbelit.webm" --stride 25
"""
import argparse
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))
os.chdir(ROOT)

import config      # noqa: E402
import db          # noqa: E402

OUT_DIR = os.path.join(ROOT, "docs", "screenshots")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("clip")
    ap.add_argument("--stride", type=int, default=25)
    ap.add_argument("--max", type=int, default=4000)
    ap.add_argument("--prefix", default=None)
    args = ap.parse_args()

    import cv2
    import pipeline

    os.makedirs(OUT_DIR, exist_ok=True)
    path = args.clip if os.path.isabs(args.clip) else os.path.join(ROOT, args.clip)
    prefix = args.prefix or os.path.splitext(os.path.basename(path))[0].lower()
    prefix = prefix.replace(" ", "_")

    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        print("cannot open", path)
        return 2

    db.init_db()
    db.clear()
    for snap in config.SNAPSHOT_DIR.glob("*.jpg"):
        try:
            snap.unlink()
        except OSError:
            pass

    hits = {}
    fidx = saved = 0
    while fidx < args.max:
        ok, frame = cap.read()
        if not ok:
            break
        if fidx % args.stride == 0:
            annotated, rows = pipeline.analyse_image(frame, seq_base=0)
            if rows:
                kinds = sorted({r["type"] for r in rows})
                key = "+".join(kinds)
                hits[key] = hits.get(key, 0) + 1
                # keep at most 3 frames per distinct violation combination
                n = sum(1 for f in os.listdir(OUT_DIR)
                        if f.startswith(f"{prefix}_still_"))
                if n < 12:
                    fn = os.path.join(
                        OUT_DIR,
                        f"{prefix}_still_{saved}_{key.replace(' ', '')}.jpg")
                    cv2.imwrite(fn, annotated, [cv2.IMWRITE_JPEG_QUALITY, 92])
                    print(f"frame {fidx}: {key}  ->  {os.path.basename(fn)}")
                    saved += 1
            # analyse_image writes its own evidence crops; clear between frames
            for snap in config.SNAPSHOT_DIR.glob("*.jpg"):
                try:
                    snap.unlink()
                except OSError:
                    pass
            db.clear()
        fidx += 1
    cap.release()

    print(f"\nscanned {fidx} frames at stride {args.stride}")
    if hits:
        for k, v in sorted(hits.items(), key=lambda x: -x[1]):
            print(f"   {v:4d} frames -> {k}")
    else:
        print("   no appearance-based violations found in this clip")
    return 0


if __name__ == "__main__":
    sys.exit(main())
