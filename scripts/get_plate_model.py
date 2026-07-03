"""
Fetch a YOLOv8 licence-plate detector into models/license_plate_detector.pt.

Public weights move around, so this tries a few mirrors and otherwise prints
clear manual options. Once the file exists, the pipeline uses it automatically
(two-stage ANPR: detect plate -> crop -> OCR) — no code change needed.

Usage:  python scripts/get_plate_model.py
"""
import os
import sys
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))
import config  # noqa: E402

DEST = config.MODELS_DIR / "license_plate_detector.pt"

# Community mirrors of the well-known ANPR plate detector (YOLOv8). May rot.
CANDIDATES = [
    "https://huggingface.co/Koushim/yolov8-license-plate-detection/resolve/main/best.pt",
    "https://huggingface.co/ml-debi/yolov8-license-plate-detection/resolve/main/best.pt",
]


def main():
    if DEST.exists() and DEST.stat().st_size > 100_000:
        print(f"Already present: {DEST}")
        return
    for url in CANDIDATES:
        try:
            print(f"Trying {url} ...")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=45) as r, open(DEST, "wb") as f:
                f.write(r.read())
            if DEST.stat().st_size > 100_000:
                print(f"Saved -> {DEST}")
                return
        except Exception as e:
            print(f"  failed: {e}")
    try:
        if DEST.exists():
            DEST.unlink()
    except OSError:
        pass
    print("\nCouldn't fetch automatically. Get one manually (2 min):")
    print("  1) Roboflow Universe -> search 'license plate recognition' ->")
    print("     Download dataset/model as 'YOLOv8' -> save the .pt here:")
    print(f"       {DEST}")
    print("  2) Or train: yolo detect train data=plates.yaml model=yolov8n.pt")
    print("\nWithout it, OCR still runs on the vehicle crop (lower accuracy).")


if __name__ == "__main__":
    main()
