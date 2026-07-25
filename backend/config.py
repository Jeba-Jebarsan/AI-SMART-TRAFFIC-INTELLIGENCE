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
# Vehicle/person detector. Prefers the strongest model actually present.
#
# WHY yolov8s IS THE DEFAULT: on real 640x360 Sri Lankan traffic footage,
# yolov8n detected only 64 motorcycles and could associate a RIDER with just 12
# of them — the rider simply wasn't detected as a person, so helmet / triple-
# riding / phone analysis was skipped for ~81% of bikes. yolov8s found 108
# motorcycles and 41 rider associations on the identical clip. Rider recall is
# the bottleneck for most violations, so the bigger model is worth its cost.
# yolov8n stays as an automatic fallback for low-end machines.
def _pick_vehicle_model():
    for _name in ("yolov8s.pt", "yolov8n.pt"):
        if (MODELS_DIR / _name).exists():
            return str(MODELS_DIR / _name)
    return str(MODELS_DIR / "yolov8s.pt")   # auto-downloads on first use


VEHICLE_MODEL = _pick_vehicle_model()

# OPTIONAL drop-in helmet model. If a file exists here it is used for real
# helmet detection (classes should include 'helmet' / 'no-helmet' / 'head').
# See README for how to grab one from Roboflow Universe in 2 minutes.
HELMET_MODEL = str(MODELS_DIR / "helmet.pt")

# OPTIONAL dedicated licence-plate detector (YOLOv8). When present it localises
# the plate inside each vehicle BEFORE OCR — far better reads than OCR-ing the
# whole car. Drop a trained model here (see scripts/get_plate_model.py / README).
PLATE_MODEL = str(MODELS_DIR / "license_plate_detector.pt")

# OPTIONAL drop-in seatbelt model (cars/buses/trucks only — not motorcycles).
# Classes should include something like 'seatbelt' / 'no seatbelt'. Same rule
# as the helmet model: if the file is absent the feature stays OFF — there is
# no colour/shape heuristic fallback because a wrong seatbelt fine is worse
# than no detection at all (Roboflow Universe has ready-made "seatbelt
# detection" YOLOv8 models you can drop in here).
SEATBELT_MODEL = str(MODELS_DIR / "seatbelt.pt")

# "auto" picks the GPU if torch+CUDA are available, else CPU. Resolved lazily
# in detection.py so importing this module never requires torch.
DEVICE = "auto"

# CPU threads for inference. None = auto (~2/3 of cores), which deliberately
# leaves headroom so the live capture thread can keep the video smooth — see
# detection._tune_cpu_threads(). Set an integer to override.
TORCH_THREADS = None

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
    "no_seatbelt": 0.50, # seatbelt-model 'No Seatbelt' must be this sure
    "phone": 0.35,       # COCO 'cell phone' conf required to count as phone-use
}

# ----------------------------------------------------------------------------
# Temporal persistence — a violation must be OBSERVED REPEATEDLY before it
# fires. Single-frame flickers (the classic demo-killer) never emit.
# ----------------------------------------------------------------------------
HELMET_MIN_HITS = 3      # no-helmet must be seen in >= N frames of a track
TRIPLE_MIN_HITS = 3      # 3+ riders must be seen in >= N frames
RED_MIN_STREAK = 3       # signal must read RED for N consecutive detections
SEATBELT_MIN_HITS = 3    # no-seatbelt must be seen in >= N frames of a track
PHONE_MIN_HITS = 4       # phone-in-hand must be seen in >= N frames of a track

# --- Wheelie / stunt riding (heuristic — no dedicated model needed) ---------
# A wheelie lifts the front wheel, so the motorcycle's bounding box suddenly
# becomes much TALLER relative to how that same bike normally looks. We detect
# a RELATIVE spike against each bike's own baseline aspect (height/width),
# never an absolute value — a tall rear-view rider has a high aspect too, so an
# absolute threshold alone would false-positive. Requires motion + persistence.
WHEELIE_MIN_HISTORY = 10   # frames of aspect history needed before judging (baseline)
WHEELIE_MIN_ASPECT = 1.8   # absolute floor: box must be at least this tall/wide
WHEELIE_RISE_RATIO = 1.45  # AND at least this much taller than the bike's baseline
WHEELIE_MIN_HITS = 4       # the spike must persist >= N frames

# Rider analysis is skipped for motorcycles smaller than this fraction of the
# frame height — a 15-pixel bike is too small to judge helmets honestly.
MIN_MOTO_H_FRAC = 0.06

# Seatbelt analysis is skipped for cars/buses/trucks smaller than this
# fraction of the frame height — the windshield is unreadable otherwise.
MIN_CAR_H_FRAC = 0.10

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

# Live/replay frames wider than this are downscaled BEFORE analysis. A 4K
# drone or CCTV feed costs ~4x the decode and inference time of 1080p for
# almost no detection benefit (the detector runs at IMGSZ anyway), and on a
# CPU laptop that is the difference between analysing 5% and 25% of the
# frames. Speed calibration quads are scaled by the same factor, so metric
# speed is unaffected. Raise it if you need maximum plate-OCR detail.
LIVE_MAX_W = 1920

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
    "bus": 5, "truck": 7, "traffic light": 9, "cell phone": 67,
}
VEHICLE_CLASSES = {COCO["car"], COCO["motorcycle"], COCO["bus"],
                   COCO["truck"], COCO["bicycle"]}
SEATBELT_CLASSES = {COCO["car"], COCO["bus"], COCO["truck"]}

# ----------------------------------------------------------------------------
# Which violations are active
# ----------------------------------------------------------------------------
ENABLE = {
    "no_helmet": True,
    "red_light": True,       # only fires when a real traffic light is detected
    "over_speed": True,      # only fires when speed is calibrated for the clip
    "wrong_way": True,       # only fires when a direction is calibrated (🎯 tool)
    "triple_riding": True,
    "no_seatbelt": True,     # only fires when models/seatbelt.pt is present
    "no_rest_break": True,   # continuous-driving / fatigue rule
    "wheelie": True,         # motorcycle wheelie / stunt riding (heuristic)
    "phone_use": True,       # rider/driver on a phone (COCO cell-phone detection)
}

# ----------------------------------------------------------------------------
# Continuous-driving / rest-break rule — flags a vehicle that this camera has
# watched drive CONTINUOUSLY (no qualifying stop) for too long, e.g. a
# fatigued commercial driver skipping mandatory rest breaks.
#
# Real transport-authority driving-hour rules work in HOURS (Sri Lanka's
# public/commercial transport rules and the EU's ~4.5h AETR limit are both
# this order of magnitude) — a live camera session is usually minutes,
# so the default below is a DEMO-SCALE value that can actually be observed
# live. Set MAX_CONTINUOUS_DRIVE_SECONDS to the real legal limit (in seconds)
# for an actual deployment.
MAX_CONTINUOUS_DRIVE_SECONDS = 240   # demo default: 4 minutes
BREAK_MIN_STOP_SECONDS = 15          # shorter stops (traffic lights, jams) don't count as a break

# ----------------------------------------------------------------------------
# Fines in LKR (shown on the e-challan). Tweak freely.
# ----------------------------------------------------------------------------
FINES = {   # Sri Lankan spot-fine style amounts (LKR)
    "No Helmet": 1500,
    "Red Light Jump": 3000,
    "Over Speeding": 3000,
    "Wrong Way": 2000,
    "Triple Riding": 1500,
    "No Seatbelt": 1500,
    "No Rest Break": 2000,
    "Wheelie Stunt": 5000,       # dangerous stunt riding — heaviest spot fine
    "Mobile Phone Use": 2000,
}

# Emoji / label metadata used by the pipeline + dashboard
VIOLATION_META = {
    "No Helmet":       {"emoji": "⛑",  "color": "#f59e0b"},
    "Red Light Jump":  {"emoji": "🔴", "color": "#ef4444"},
    "Over Speeding":   {"emoji": "🏎", "color": "#a855f7"},
    "Wrong Way":       {"emoji": "↩",  "color": "#3b82f6"},
    "Triple Riding":   {"emoji": "👥", "color": "#14b8a6"},
    "No Seatbelt":     {"emoji": "🔗", "color": "#eab308"},
    "No Rest Break":   {"emoji": "⏱",  "color": "#f97316"},
    "Wheelie Stunt":   {"emoji": "🛞", "color": "#ec4899"},
    "Mobile Phone Use":{"emoji": "📱", "color": "#06b6d4"},
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

# --- Speed-filtering knobs (the SpeedEstimator module, backend/speed.py) ---
# Speed is estimated over a MULTI-FRAME sliding window (never a single-frame
# pixel delta): least-squares regression of road-metres vs time, with outlier
# rejection, EMA smoothing and a confidence gate. These tune that filter.
# Show a ROUGH pixel-based speed for vehicles when the camera is NOT calibrated?
# Default OFF: exact speed needs a perspective calibration (the 🎯 tool / a
# calibration.json entry), so an uncalibrated camera shows NO speed rather than
# a misleading/"random" number. Set True to display approximate (~) speeds.
SPEED_APPROX = False
SPEED_EMA_ALPHA = 0.4        # weight on the newest reading when smoothing (0..1)
SPEED_MIN_R2 = 0.55          # min linearity (R^2) of motion required to TRUST a speed
SPEED_OUTLIER_SIGMA = 2.0    # drop position samples > N*std off the fitted line
# Readings above this km/h are rejected as tracker noise. No road vehicle on a
# Sri Lankan road legitimately exceeds this, so a higher reading is always a
# tracking artefact rather than a real (and enormous) speeding offence.
SPEED_SANITY_MAX = 180.0
# Max RMS distance (metres) the observed positions may sit off the fitted
# straight line before the speed is distrusted. Far from the camera one pixel
# of box jitter is worth several metres, so this — not R^2 — is what rejects
# noisy far-field tracks.
SPEED_MAX_RESIDUAL_M = 2.5
# A track must be watched this long before its speed is trusted. Measured over
# a third of a second the estimate is dominated by bounding-box jitter, which
# is what produced a spurious 180 km/h first reading on a car actually doing
# 144 — every track's opening estimate was too hot, then converged. One second
# of observation removes the transient.
SPEED_MIN_SECONDS = 1.0
# Length of the trailing measurement window, in SECONDS (not frames) — live
# replay drops frames, so the analysis rate varies and a frame-count window
# would mean wildly different durations on different hardware.
SPEED_WINDOW_SECONDS = 2.5

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
