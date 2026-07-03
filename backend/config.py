"""
Central configuration for the Smart Traffic Violation System.

Everything you might want to tune for a demo lives here: fines, the virtual
stop line, the traffic-signal behaviour, speed calibration and per-violation
toggles. Nothing else in the codebase hard-codes these values.
"""
from pathlib import Path

# ----------------------------------------------------------------------------
# Paths (all derived from the project root, so they work regardless of cwd)
# ----------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
VIDEO_DIR = DATA_DIR / "videos"
OUTPUT_DIR = DATA_DIR / "output"
SNAPSHOT_DIR = OUTPUT_DIR / "snapshots"
MODELS_DIR = ROOT / "models"
FRONTEND_DIR = ROOT / "frontend"

DB_PATH = OUTPUT_DIR / "traffic.db"
RESULTS_JSON = OUTPUT_DIR / "results.json"
ANNOTATED_VIDEO = OUTPUT_DIR / "annotated.mp4"

for _d in (DATA_DIR, VIDEO_DIR, OUTPUT_DIR, SNAPSHOT_DIR, MODELS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------------
# Models
# ----------------------------------------------------------------------------
# yolov8n auto-downloads on first use. Swap to yolov8s/m for higher accuracy.
VEHICLE_MODEL = str(MODELS_DIR / "yolov8n.pt")

# OPTIONAL drop-in helmet model. If a file exists here it is used for real
# helmet detection (classes should include 'helmet' / 'no-helmet' / 'head').
# See README for how to grab one from Roboflow Universe in 2 minutes.
HELMET_MODEL = str(MODELS_DIR / "helmet.pt")

# OPTIONAL dedicated licence-plate detector (YOLOv8). When present it localises
# the plate inside each vehicle BEFORE OCR — far better reads than OCR-ing the
# whole car. Drop a trained model here (see scripts/get_plate_model.py / README).
PLATE_MODEL = str(MODELS_DIR / "license_plate_detector.pt")

# "auto" picks the GPU if torch+CUDA are available, else CPU. Resolved lazily
# in detection.py so importing this module never requires torch.
DEVICE = "auto"

# Inference size. 960 finds small/distant vehicles far better than the 640
# default at ~2x the CPU cost — worth it for CCTV footage.
IMGSZ = 960

# Analyze every Nth frame (1 = every frame). The annotated video keeps every
# frame (skipped ones reuse the last overlay), so output length is unchanged
# while processing time drops ~Nx. 2 is visually seamless; 3 is fine at 25fps+.
# The dashboard's speed-mode selector overrides this per run.
PROCESS_EVERY = 2

# ----------------------------------------------------------------------------
# Confidence thresholds — the #1 defence against false positives
# ----------------------------------------------------------------------------
TRACK_CONF = 0.30        # min det confidence fed into ByteTrack
CONF = {
    "vehicle": 0.35,     # a vehicle counts toward violations at this conf
    "moto_rider": 0.45,  # motorcycle conf required before helmet analysis
    "person": 0.40,      # person conf required to count as a rider
    "light": 0.45,       # traffic-light conf required to read signal colour
    "no_helmet": 0.50,   # helmet-model 'Without Helmet' must be this sure
}

# ----------------------------------------------------------------------------
# Temporal persistence — a violation must be OBSERVED REPEATEDLY before it
# fires. Single-frame flickers (the classic demo-killer) never emit.
# ----------------------------------------------------------------------------
HELMET_MIN_HITS = 3      # no-helmet must be seen in >= N frames of a track
TRIPLE_MIN_HITS = 3      # 3+ riders must be seen in >= N frames
RED_MIN_STREAK = 3       # signal must read RED for N consecutive detections

# Rider analysis is skipped for motorcycles smaller than this fraction of the
# frame height — a 15-pixel bike is too small to judge helmets honestly.
MIN_MOTO_H_FRAC = 0.06

# A track must MOVE to violate (camera-motion compensated). Parked bikes and
# roadside scooters can never trigger helmet / triple-riding / red-light.
# Threshold: displacement per second as a fraction of frame height.
MIN_MOVE_FRAC = 0.02

# ----------------------------------------------------------------------------
# Continuous ANPR — plates are read for every tracked vehicle (not only
# violators), so the dashboard proves number-plate recognition on any clip.
# ----------------------------------------------------------------------------
ANPR_EVERY = 5           # try plate detection every N analyzed frames
ANPR_MIN_VEH_H = 48      # min vehicle box height in px (scaled up on >720p)
ANPR_MAX_PER_FRAME = 3   # OCR at most N vehicles per ANPR frame (CPU budget)
ANPR_GOOD_CONF = 0.80    # stop re-reading a track once this confident
ANPR_TRIES = 10          # max OCR attempts per track (detector runs are free)

# The annotated OUTPUT video is capped at this width (4K in = 1080p out).
# Snapshots stay full resolution for evidence; the dashboard player doesn't
# need 4K and the H.264 encode is ~4x faster this way.
OUTPUT_MAX_W = 1920

# A plate is CONFIRMED (shown on video/dashboard, written to DB, used on
# challans) only when reads agreeing on the same digit-tail were seen in at
# least this many different frames. One read is NEVER proof, however
# confident — a wrong number on a challan is worse than no number.
PLATE_CONFIRM_READS = 2

# ----------------------------------------------------------------------------
# Police alert emails — auto-send an e-challan with photo evidence when a
# violation is confirmed. Off until credentials are configured. For Gmail use
# an App Password (Google Account -> Security -> 2-Step -> App passwords).
# Credentials can also come from env vars SMTP_USER / SMTP_PASS.
# ----------------------------------------------------------------------------
ALERTS = {
    "enabled": False,             # master switch (True once configured)
    "auto_send": True,            # email immediately on each new violation
    "to": "traffic.police@example.lk",
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "user": "",                   # your.email@gmail.com
    "password": "",               # Gmail App Password (NOT your real password)
}

# Per-video speed calibration store (managed via the dashboard's Calibrate
# tool or by hand). Keys: video file basename, or "WIDTHxHEIGHT" to match any
# clip of that resolution. Values: {"points": [[x,y]*4], "target_m": [w, l]}.
CALIBRATION_FILE = DATA_DIR / "calibration.json"

# COCO class ids for the default YOLOv8 model
COCO = {
    "person": 0, "bicycle": 1, "car": 2, "motorcycle": 3,
    "bus": 5, "truck": 7, "traffic light": 9,
}
VEHICLE_CLASSES = {COCO["car"], COCO["motorcycle"], COCO["bus"],
                   COCO["truck"], COCO["bicycle"]}

# ----------------------------------------------------------------------------
# Which violations are active
# ----------------------------------------------------------------------------
ENABLE = {
    "no_helmet": True,
    "red_light": True,       # only fires when a real traffic light is detected
    "over_speed": True,      # only fires when speed is calibrated for the clip
    "wrong_way": True,       # only fires when a direction is calibrated (🎯 tool)
    "triple_riding": True,
}

# ----------------------------------------------------------------------------
# Fines in LKR (shown on the e-challan). Tweak freely.
# ----------------------------------------------------------------------------
FINES = {   # Sri Lankan spot-fine style amounts (LKR)
    "No Helmet": 1500,
    "Red Light Jump": 3000,
    "Over Speeding": 3000,
    "Wrong Way": 2000,
    "Triple Riding": 1500,
}

# Emoji / label metadata used by the pipeline + dashboard
VIOLATION_META = {
    "No Helmet":      {"emoji": "⛑",  "color": "#f59e0b"},
    "Red Light Jump": {"emoji": "🔴", "color": "#ef4444"},
    "Over Speeding":  {"emoji": "🏎", "color": "#a855f7"},
    "Wrong Way":      {"emoji": "↩",  "color": "#3b82f6"},
    "Triple Riding":  {"emoji": "👥", "color": "#14b8a6"},
}

# ----------------------------------------------------------------------------
# Red-light logic
# ----------------------------------------------------------------------------
# Virtual stop line as a fraction of frame height (0 = top, 1 = bottom).
# A vehicle whose centroid crosses this line downward while the signal is RED
# is flagged. Adjust to match where the stop line is in YOUR clip.
STOP_LINE_Y = 0.55

# Signal state source:
#   * None (default, HONEST) => state comes ONLY from a YOLO-detected traffic
#     light + HSV colour. Red-light detection runs only while a real signal is
#     visible, so signal-less clips (e.g. highways) never fake red-light events.
#   * A [(state, seconds), ...] cycle => deliberate demo override for a clip
#     whose signal genuinely can't be read by the model. Use sparingly.
FORCE_SIGNAL = None

# ----------------------------------------------------------------------------
# Speed estimation (approximate, pixel-based)
# ----------------------------------------------------------------------------
SPEED_LIMIT_KMPH = 60

# --- Accurate speed via perspective transform (Supervision-style, recommended) ---
# Four image points of a road quad — order: far-left, far-right, near-right,
# near-left — mapped onto a real-world rectangle SPEED_TARGET_M = (width_m,
# length_m). Vehicle bottom-centre points are projected to metres and speed is
# distance-travelled-per-second along the road. Only points INSIDE this quad are
# measured, so readings stay sane.
#
# Pre-calibrated for the 3840x2160 sample highway clip. Set SPEED_SOURCE = None
# to disable and use the pixel fallback below, or recalibrate for your footage.
# Calibration is PER-CAMERA. Speed is OFF (honest) until you set SPEED_SOURCE for
# YOUR clip. The example below is calibrated for the 3840x2160 sample highway —
# uncomment it (and comment `= None`) to re-enable speed on that clip.
# SPEED_SOURCE = [[1252, 787], [2298, 803], [5039, 2159], [-550, 2159]]
SPEED_SOURCE = None
SPEED_TARGET_M = (25, 250)   # (width metres, length metres) of the road region

# --- Fallback speed (used only when SPEED_SOURCE is None) ---
# How many image pixels represent 1 metre on the road plane.
PIXELS_PER_METER = 8.0

# ----------------------------------------------------------------------------
# Wrong-way detection
# ----------------------------------------------------------------------------
# Allowed direction of travel in image space (dx, dy). (0, 1) = downward.
ALLOWED_DIRECTION = (0, 1)
# Motion whose cosine-similarity with the allowed direction is below this is
# flagged as wrong-way (-1 = exact opposite).
WRONG_WAY_MIN_DOT = -0.5

# ----------------------------------------------------------------------------
# Meta shown on the dashboard / challans
# ----------------------------------------------------------------------------
CAMERA_LOCATION = "Galle Road, Colombo 03"
CURRENCY = "Rs. "
