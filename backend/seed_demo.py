"""
Seed the database with realistic demo violations + generated evidence images.

THIS IS YOUR DEMO SAFETY NET. Run it (or hit POST /api/seed) and the dashboard
is instantly full of believable data — vehicles counted, violations of every
type, fines, evidence snapshots, a timeline — with zero ML dependencies and no
video. If anything goes wrong with live processing during the demo, the last
seeded/processed state is still on screen and looks great.

Usage:
    python backend/seed_demo.py            # fresh seed
    python backend/seed_demo.py --if-empty # only seed when DB has no rows
"""
import datetime
import json
import os
import random
import sys

# Make `import config` work when run directly as a script.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
import db
from challan import make_challan_id

# Sri Lankan plate parts: optional province code + 2-3 letters + 4 digits
_PROVINCES = ["WP", "CP", "SP", "NP", "EP", "NW", "NC", "UP", "SG"]
_LETTERS = "ABCDEFGHJKLMNPQRSTUVWXYZ"

_TYPE_WEIGHTS = [
    ("No Helmet", 0.34),
    ("Red Light Jump", 0.24),
    ("Over Speeding", 0.20),
    ("Triple Riding", 0.12),
    ("Wrong Way", 0.10),
]


def _plate():
    prov = (random.choice(_PROVINCES) + " ") if random.random() < 0.6 else ""
    letters = "".join(random.choice(_LETTERS) for _ in range(random.choice([2, 3])))
    return f"{prov}{letters}-{random.randint(1000, 9999)}"


def _weighted_type():
    r = random.random()
    acc = 0.0
    for t, w in _TYPE_WEIGHTS:
        acc += w
        if r <= acc:
            return t
    return _TYPE_WEIGHTS[0][0]


def _make_evidence(path, vtype, plate, ts):
    """Generate a plausible 'CCTV evidence' JPG with PIL. No-op if PIL missing."""
    try:
        from PIL import Image, ImageDraw
    except Exception:
        return False

    W, H = 640, 380
    img = Image.new("RGB", (W, H), (17, 24, 39))
    d = ImageDraw.Draw(img)

    # faux road + lane markings
    d.polygon([(120, H), (250, 150), (390, 150), (W - 60, H)], fill=(31, 41, 55))
    for i in range(150, H, 40):
        d.line([(W // 2, i), (W // 2, i + 20)], fill=(120, 120, 120), width=3)

    # the offending vehicle
    vx1, vy1, vx2, vy2 = 250, 200, 400, 320
    d.rectangle([vx1, vy1, vx2, vy2], fill=(55, 65, 81), outline=(148, 163, 184))
    # windshield + wheels for a car-ish silhouette
    d.rectangle([vx1 + 18, vy1 + 12, vx2 - 18, vy1 + 45], fill=(30, 41, 59))
    d.ellipse([vx1 + 12, vy2 - 18, vx1 + 42, vy2 + 12], fill=(10, 10, 10))
    d.ellipse([vx2 - 42, vy2 - 18, vx2 - 12, vy2 + 12], fill=(10, 10, 10))

    # red violation box
    d.rectangle([vx1 - 8, vy1 - 8, vx2 + 8, vy2 + 8], outline=(239, 68, 68), width=4)

    # plate chip
    d.rectangle([vx1 + 40, vy2 - 26, vx2 - 40, vy2 - 6], fill=(250, 250, 250))
    d.text((vx1 + 46, vy2 - 24), plate, fill=(0, 0, 0))

    # top evidence banner
    d.rectangle([0, 0, W, 30], fill=(0, 0, 0))
    d.text((8, 9), f"{vtype}  |  {ts}  |  {config.CAMERA_LOCATION}",
           fill=(255, 255, 255))
    d.text((W - 150, 9), "CAM-14 * REC", fill=(239, 68, 68))

    img.save(path, quality=85)
    return True


def _export_results_json():
    payload = {
        "stats": db.stats(),
        "violations": db.all_violations(limit=5000),
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    config.RESULTS_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def seed(n_violations=34, n_vehicles=1284):
    db.init_db()
    db.clear()

    now = datetime.datetime.now()
    for seq in range(1, n_violations + 1):
        vtype = _weighted_type()
        # spread events over the last ~55 minutes, newest last
        ts = (now - datetime.timedelta(
            minutes=random.randint(0, 55),
            seconds=random.randint(0, 59))).isoformat(timespec="seconds")
        plate = _plate()

        snap_name = f"snapshots/seed_{seq:04d}.jpg"
        made = _make_evidence(config.OUTPUT_DIR / snap_name, vtype, plate, ts)

        speed = None
        if vtype == "Over Speeding":
            speed = round(random.uniform(61, 118), 1)

        frame_index = random.randint(1, 4000)
        # plausible in-frame position for the hotspot map (1280x720 space)
        bx = random.uniform(120, 1000)
        by = random.uniform(300, 640)
        db.insert_violation({
            "challan_id": make_challan_id(seq),
            "track_id": random.randint(1, 400),
            "type": vtype,
            "plate": plate,
            "plate_conf": round(random.uniform(0.62, 0.97), 3),
            "speed_kmph": speed,
            "fine": config.FINES.get(vtype, 1000),
            "timestamp": ts,
            "frame_index": frame_index,
            "video_s": round(frame_index / 25.0, 2),
            "box": json.dumps([round(bx, 1), round(by, 1),
                               round(bx + 160, 1), round(by + 120, 1)]),
            "snapshot": snap_name if made else None,
            "location": config.CAMERA_LOCATION,
            "status": random.choices(["PENDING", "PAID"], weights=[0.75, 0.25])[0],
            "source": "demo",
        })

    # a small ANPR vehicle log so that panel demos too
    for tid in range(1, 29):
        has_plate = random.random() < 0.7
        seen = round(random.uniform(2, 160), 1)
        db.upsert_vehicle({
            "track_id": tid,
            "cls": random.choices(["Car", "Motorcycle", "Bus", "Truck"],
                                  weights=[0.5, 0.3, 0.1, 0.1])[0],
            "plate": _plate() if has_plate else None,
            "plate_conf": round(random.uniform(0.55, 0.97), 3) if has_plate else None,
            "plate_img": None,
            "first_seen": seen,
            "last_seen": seen + round(random.uniform(1, 8), 1),
            "source": "demo",
        })

    db.set_meta("vehicle_count", n_vehicles)
    db.set_meta("processed_at", now.isoformat(timespec="seconds"))
    db.set_meta("data_source", "demo")
    db.set_meta("frame_size", [1280, 720])
    _export_results_json()
    return n_violations


if __name__ == "__main__":
    if "--if-empty" in sys.argv and not db.is_empty():
        print("DB already has data — skipping seed.")
    else:
        count = seed()
        print(f"Seeded {count} demo violations + evidence images.")
