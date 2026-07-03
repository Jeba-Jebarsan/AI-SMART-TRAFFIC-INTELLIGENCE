"""
Live mode: process a webcam / CCTV (RTSP/HTTP) / video-file stream in real time,
detect violations, and expose the latest annotated frame as JPEG for an MJPEG
feed on the dashboard.

Source values:
    "0" (or "webcam" / "")   -> default webcam
    "1", "2", ...            -> other camera indices
    "rtsp://..."             -> IP / CCTV camera
    "http://.../stream.mjpg" -> network stream
    a local file path        -> loops the file (handy for a repeatable demo)
"""
import datetime
import threading

import config
import db
import pipeline
from detection import resolve_device
from violations import ViolationEngine


class LiveProcessor:
    def __init__(self):
        self.thread = None
        self.running = False
        self.status = "idle"          # idle | starting | live | stopped | error
        self.error = None
        self.source = None
        self.is_file = False
        self._frame_jpg = None
        self._lock = threading.Lock()
        self.stats = {"frames": 0, "vehicles": 0, "violations": 0}

    # ------------------------------------------------------------------ control
    def start(self, source):
        if self.running:
            return False
        self.source = source
        self.running = True
        self.status = "starting"
        self.error = None
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        return True

    def stop(self):
        self.running = False
        self.status = "stopped"

    def get_jpg(self):
        with self._lock:
            return self._frame_jpg

    def state_dict(self):
        return {"status": self.status, "source": str(self.source),
                "error": self.error, **self.stats}

    # ------------------------------------------------------------------ worker
    def _open(self):
        import cv2
        s = str(self.source).strip()
        low = s.lower()
        if low in ("", "0", "webcam"):
            src, self.is_file = 0, False
        elif low.isdigit():
            src, self.is_file = int(low), False
        elif low.startswith(("rtsp://", "http://", "https://")):
            src, self.is_file = self.source, False
        elif low.startswith("sample:"):              # dashboard sample clips
            self.source = str(config.VIDEO_DIR / s.split(":", 1)[1])
            src, self.is_file = self.source, True
        else:
            src, self.is_file = self.source, True    # local file (played once)
        return cv2.VideoCapture(src)

    def _loop(self):
        import cv2
        from ultralytics import YOLO

        try:
            cap = self._open()
            if not cap.isOpened():
                raise RuntimeError(f"Cannot open source: {self.source}")

            fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
            W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1280
            H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 720

            # Live gets its OWN model instance so its ByteTrack state never
            # collides with a file-processing run.
            model = YOLO(config.VEHICLE_MODEL)
            _, helmet_model = pipeline.load()
            device = resolve_device()
            cal_pts, cal_target, cal_dir = pipeline.load_calibration(
                self.source if self.is_file else None, W, H)
            engine = ViolationEngine(
                W, H, fps,
                transform_fn=pipeline.make_transform_fn(cal_pts, cal_target),
                allowed_direction=cal_dir)

            db.init_db()
            # Live APPENDS to whatever is on the dashboard (no wipe); challan
            # numbering continues from the existing rows so ids never collide.
            base_vehicles = db.get_meta("vehicle_count", 0) or 0
            db.set_meta("data_source", "ai")
            db.set_meta("frame_size", [W, H])
            db.set_meta("video_fps", round(float(fps), 2))
            db.set_meta("device", "GPU" if device != "cpu" else "CPU")
            db.set_meta("speed_calibrated", bool(cal_pts))
            state = pipeline.new_run_state(fps, seq_base=db.violation_count(),
                                           frame_w=W)
            state["speed_quad"] = cal_pts
            from location import resolve_location
            state["location"] = resolve_location(
                self.source if self.is_file else None)
            db.set_meta("location", state["location"])
            fidx = 0
            self.status = "live"

            while self.running:
                ok, frame = cap.read()
                if not ok:
                    # File sources play ONCE — looping would re-count every
                    # vehicle and re-issue every violation on each pass.
                    break

                annotated = pipeline.process_frame(
                    model, engine, frame, fidx, device, helmet_model, state)

                ok2, buf = cv2.imencode(
                    ".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 72])
                if ok2:
                    with self._lock:
                        self._frame_jpg = buf.tobytes()

                fidx += 1
                self.stats = {"frames": fidx,
                              "vehicles": len(state["vehicle_ids"]),
                              "violations": len(engine.events)}
                if fidx % 15 == 0:
                    db.set_meta("vehicle_count",
                                base_vehicles + len(state["vehicle_ids"]))

            cap.release()
            pipeline.flush_vehicles(state)
            db.set_meta("vehicle_count", base_vehicles + len(state["vehicle_ids"]))
            db.set_meta("processed_at",
                        datetime.datetime.now().isoformat(timespec="seconds"))
            pipeline.export_results_json()
            if self.status != "error":
                self.status = "stopped"
        except Exception as e:
            self.error = str(e)
            self.status = "error"
        finally:
            self.running = False


# module-level singleton used by the API
LIVE = LiveProcessor()
