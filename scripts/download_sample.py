"""
Best-effort downloader for a sample traffic clip so you can test the pipeline
without hunting for footage. Public URLs rot, so if this fails just drop ANY
traffic .mp4 into data/videos/ and analyze it from the dashboard.

Usage:  python scripts/download_sample.py
"""
import os
import sys
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))
import config  # noqa: E402

# A few public sample videos (traffic / vehicles). Tried in order.
CANDIDATES = [
    "https://media.roboflow.com/supervision/video-examples/vehicles.mp4",
    "https://github.com/intel-iot-devkit/sample-videos/raw/master/car-detection.mp4",
    "https://github.com/intel-iot-devkit/sample-videos/raw/master/person-bicycle-car-detection.mp4",
]

DEST = config.VIDEO_DIR / "sample.mp4"


def main():
    for url in CANDIDATES:
        try:
            print(f"Downloading {url} ...")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r, open(DEST, "wb") as f:
                f.write(r.read())
            if DEST.stat().st_size > 10_000:
                print(f"Saved sample -> {DEST}")
                return
        except Exception as e:
            print(f"  failed: {e}")
    print("\nCould not fetch a sample automatically.")
    print(f"Drop any traffic .mp4 into: {config.VIDEO_DIR}")


if __name__ == "__main__":
    main()
