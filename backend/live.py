"""
Live mode: process a webcam / CCTV (RTSP/HTTP) / video-file stream in real time,
detect violations, and expose the latest annotated frame as JPEG for an MJPEG
feed on the dashboard.

Source values:
    "0" (or "webcam" / "")   -> default webcam
    "1", "2", ...            -> other camera indices
    "rtsp://..."             -> IP / CCTV camera
    "http://.../stream.mjpg" -> network stream (phone / IP-camera app, RTMP bridge, etc.)
    a local file path        -> plays once (sample-clip live replay)
"""
import datetime
import threading
import time

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
        self.every = 1
        self.frame_w = None
        self.frame_h = None
        self._frame_jpg = None
        self._last_raw = None         # latest RAW frame (for calibration tool)
        self._engine = None           # live ViolationEngine (for hot-apply)
        self._state = None            # live run state (for hot-apply)
        self._lock = threading.Lock()
        self.stats = {"frames": 0, "vehicles": 0, "violations": 0}

    # ------------------------------------------------------------------ control
    def start(self, source, every=None):
        if self.running:
            return False
        self.source = source
        self.every = max(1, int(every or config.PROCESS_EVERY))
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
                "error": self.error, "frame_w": self.frame_w,
                "frame_h": self.frame_h, **self.stats}

    def raw_jpg(self):
        """Latest UN-annotated frame, full resolution — the calibration tool
        needs clean pixels to click road corners on."""
        import cv2
        with self._lock:
            frame = self._last_raw
        if frame is None:
            return None
        ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        return buf.tobytes() if ok else None

    def apply_calibration(self, points, target_m, direction):
        """Hot-apply a speed/direction calibration to the RUNNING live session
        (also persisted by the caller for future sessions). Speed labels and
        over-speed / wrong-way checks activate within ~1 s — no restart, no
        loss of tracking state."""
        engine, state = self._engine, self._state
        if not self.running or engine is None:
            return False
        if points:
            engine.set_transform_fn(pipeline.make_transform_fn(points, target_m))
            if state is not None:
                state["speed_quad"] = points
            db.set_meta("speed_calibrated", True)
        if direction:
            engine.allowed_dir = tuple(direction)
        return True

    def _publish(self, frame_bgr):
        """Encode + downscale for streaming (bandwidth/encode-time friendly —
        detection still runs at full/imgsz resolution; only the JPEG we ship
        to the browser is shrunk, same trick as the batch-analysis preview)."""
        import cv2
        h, w = frame_bgr.shape[:2]
        if w > 1280:
            frame_bgr = cv2.resize(frame_bgr, (1280, int(h * 1280 / w)))
        ok, buf = cv2.imencode(".jpg", frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 72])
        if ok:
            with self._lock:
                self._frame_jpg = buf.tobytes()

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
            self.frame_w, self.frame_h = W, H

            # Live gets its OWN model instance so its ByteTrack state never
            # collides with a file-processing run.
            model = YOLO(config.VEHICLE_MODEL)
            _, helmet_model = pipeline.load()
            seatbelt_model = pipeline.load_seatbelt()
            device = resolve_device()
            cal_pts, cal_target, cal_dir = pipeline.load_calibration(
                self.source if self.is_file else None, W, H)
            engine = ViolationEngine(
                W, H, fps,
                transform_fn=pipeline.make_transform_fn(cal_pts, cal_target),
                allowed_direction=cal_dir)
            self._engine = engine

            db.init_db()
            # A fresh live session starts CLEAN: wipe the previous run's
            # violations, vehicles and evidence so the dashboard only ever
            # shows what THIS live camera is seeing right now — no stale rows
            # from an earlier session bleeding through.
            db.clear()
            for snap in config.SNAPSHOT_DIR.glob("*.jpg"):
                try:
                    snap.unlink()
                except OSError:
                    pass
            db.set_meta("data_source", "ai")
            db.set_meta("frame_size", [W, H])
            db.set_meta("video_fps", round(float(fps), 2))
            db.set_meta("device", "GPU" if device != "cpu" else "CPU")
            db.set_meta("speed_calibrated", bool(cal_pts))
            state = pipeline.new_run_state(fps, seq_base=0, frame_w=W)
            state["speed_quad"] = cal_pts
            self._state = state
            from location import resolve_location
            state["location"] = resolve_location(
                self.source if self.is_file else None)
            db.set_meta("location", state["location"])
            fidx = 0
            t0 = time.monotonic()          # wall-clock origin for live-camera speed
            self.status = "live"

            # instant feedback: publish a warm-up frame + pre-warm EasyOCR
            # before the loop, same fix as the batch-analysis preview — the
            # first real frame on CPU (model load + first inference) can take
            # 15-30+ seconds on 1080p+/4K footage, otherwise the stream just
            # looks frozen/broken for that whole time.
            ok0, f0 = cap.read()
            if ok0:
                with self._lock:
                    self._last_raw = f0
                warm = f0.copy()
                cv2.rectangle(warm, (0, H // 2 - 30), (W, H // 2 + 18),
                              (10, 10, 10), -1)
                cv2.putText(warm, "AI WARMING UP - loading detection + OCR models...",
                            (24, H // 2 + 4), cv2.FONT_HERSHEY_SIMPLEX,
                            max(0.6, W / 1600), (80, 255, 255), 2, cv2.LINE_AA)
                self._publish(warm)
                if self.is_file:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            try:
                import ocr
                ocr._get_reader()
            except Exception:
                pass

            while self.running:
                ok, frame = cap.read()
                if not ok:
                    # File sources play ONCE — looping would re-count every
                    # vehicle and re-issue every violation on each pass.
                    break
                with self._lock:
                    self._last_raw = frame

                # Frame-skip speed mode (same lever as batch analysis): on
                # heavy footage, processing every single frame on CPU can
                # never keep up with "live" — skipping frames is what makes
                # this feel live instead of stuck.
                if fidx % self.every == 0:
                    # A live CAMERA delivers frames at a real (fluctuating) rate,
                    # so measure speed against the wall clock. A FILE replay has
                    # exact per-frame timing, so let it use frame_idx/fps (None).
                    ftime = None if self.is_file else (time.monotonic() - t0)
                    annotated = pipeline.process_frame(
                        model, engine, frame, fidx, device, helmet_model,
                        state, seatbelt_model, ftime)
                    self._publish(annotated)

                fidx += 1
                self.stats = {"frames": fidx,
                              "vehicles": len(state["vehicle_ids"]),
                              "violations": len(engine.events)}
                if fidx % 15 == 0:
                    db.set_meta("vehicle_count", len(state["vehicle_ids"]))

            cap.release()
            pipeline.final_plate_sweep(state)   # slow-motion pass on unread plates
            pipeline.flush_vehicles(state)
            db.set_meta("vehicle_count", len(state["vehicle_ids"]))
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
            self._engine = None
            self._state = None


# module-level singleton used by the API
LIVE = LiveProcessor()
