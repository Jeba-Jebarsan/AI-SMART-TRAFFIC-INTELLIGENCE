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
        # --- live-camera capture/analysis decoupling -----------------------
        # A camera produces ~30 fps; CPU detection manages ~2 fps. Reading and
        # analysing in one thread therefore throttles capture to the analysis
        # rate and the picture crawls. A reader thread keeps the newest frame
        # here so display stays at camera rate while analysis runs behind it.
        self._latest = None           # newest camera frame (reader thread)
        self._latest_seq = 0          # bumped per captured frame
        self._ov_img = None           # last ANNOTATED frame (overlay source)
        self._ov_mask = None          # pixels the annotation painted
        self._ov_lock = threading.Lock()

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

    def _set_overlay(self, raw, annotated):
        """Remember what the annotator PAINTED onto this frame.

        Detection runs far slower than the camera, so between analyses we
        still want boxes, plate banners and speed chips on screen instead of
        a bare picture that flickers annotations on and off. Rather than
        rebuilding that artwork (which lives inside pipeline._draw), we diff
        the annotated frame against the raw one it came from and keep the
        painted pixels as a stencil to stamp onto later frames.
        """
        import cv2
        if raw is None or annotated is None or raw.shape != annotated.shape:
            return
        diff = cv2.absdiff(annotated, raw)
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 12, 255, cv2.THRESH_BINARY)
        with self._ov_lock:
            self._ov_img = annotated
            self._ov_mask = mask          # uint8: cv2.copyTo wants a mask, not bools

    def _publish_live(self, frame):
        """Publish a fresh camera frame with the most recent annotation
        stamped on it, so the video stays smooth while boxes refresh at
        whatever rate the CPU sustains."""
        import cv2
        with self._ov_lock:
            ov_img, ov_mask = self._ov_img, self._ov_mask
        out = frame
        if (ov_img is not None and ov_mask is not None
                and ov_img.shape == frame.shape):
            # cv2.copyTo stamps the painted pixels in C; numpy fancy-indexing
            # the same mask is several times slower and this runs per frame.
            out = cv2.copyTo(ov_img, ov_mask, frame.copy())
        self._publish(out)

    def _capture_loop(self, cap, W, H, scale):
        """Reader thread: always hold the NEWEST frame and keep the stream
        moving at camera rate, independent of how slow analysis is."""
        import cv2
        last_pub = 0.0
        while self.running:
            ok, frame = cap.read()
            if not ok:
                time.sleep(0.01)
                continue
            if scale != 1.0:
                frame = cv2.resize(frame, (W, H), interpolation=cv2.INTER_AREA)
            with self._lock:
                self._latest = frame
                self._latest_seq += 1
                self._last_raw = frame
            # Cap publishing at ~15 fps: smooth to the eye, and it leaves the
            # CPU budget for detection rather than spending it on JPEG encode.
            now = time.monotonic()
            if now - last_pub >= 1 / 15.0:
                last_pub = now
                self._publish_live(frame)

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
        cap = cv2.VideoCapture(src)
        if not self.is_file:
            # A live source (webcam/RTSP/HTTP) keeps producing frames faster
            # than our CPU can analyse them. OpenCV's default internal buffer
            # (several frames deep) then fills up, and cap.read() starts
            # returning older and older queued frames — the feed drifts
            # further behind real time the longer it runs. Shrinking the
            # buffer to 1 makes read() always hand back the newest frame
            # instead. Not every backend honours this — harmless if ignored.
            try:
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            except Exception:
                pass
        return cap

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
            src_w, src_h = W, H
            # Downscale oversized sources (4K drones/CCTV) before ANY analysis.
            # Everything downstream — boxes, snapshots, calibration, the
            # dashboard — then works in one consistent coordinate space.
            scale = 1.0
            if W > config.LIVE_MAX_W or H > config.LIVE_MAX_H:
                scale = min(config.LIVE_MAX_W / float(W),
                            config.LIVE_MAX_H / float(H))
                W, H = int(round(W * scale)), int(round(H * scale))
            self.frame_w, self.frame_h = W, H

            # Live gets its OWN model instance so its ByteTrack state never
            # collides with a file-processing run.
            model = YOLO(config.VEHICLE_MODEL)
            _, helmet_model = pipeline.load()
            seatbelt_model = pipeline.load_seatbelt()
            device = resolve_device()
            # Look calibration up at the source's NATIVE resolution (that's the
            # space its quad was drawn in), then scale the quad to match the
            # downscaled frames we actually analyse.
            cal_pts, cal_target, cal_dir = pipeline.load_calibration(
                self.source if self.is_file else None, src_w, src_h)
            if cal_pts and scale != 1.0:
                cal_pts = [[x * scale, y * scale] for x, y in cal_pts]
            # Approx-speed scale is per-camera; scale it with the frame too,
            # since we may be analysing a downscaled copy.
            ppm = pipeline.load_pixels_per_meter(
                self.source if self.is_file else None, src_w, src_h)
            if ppm and scale != 1.0:
                ppm *= scale
            engine = ViolationEngine(
                W, H, fps,
                transform_fn=pipeline.make_transform_fn(cal_pts, cal_target),
                allowed_direction=cal_dir, ppm=ppm)
            sly = pipeline.load_stop_line_y(
                self.source if self.is_file else None, src_w, src_h)
            if sly:
                engine.stop_line_y = sly * H
            slx = pipeline.load_stop_line_x(
                self.source if self.is_file else None, src_w, src_h)
            if slx:
                engine.stop_line_x = slx * W
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
            state = pipeline.new_run_state(fps, seq_base=0, frame_w=W,
                                           every=self.every)
            state["speed_quad"] = cal_pts
            _roi, _zone = pipeline.load_signal_setup(
                self.source if self.is_file else None, src_w, src_h)
            if _roi:
                state["signal_roi"] = [_roi[0] * W, _roi[1] * H,
                                       _roi[2] * W, _roi[3] * H]
            if _zone:
                engine.red_light_zone = [[x * W, y * H] for x, y in _zone]
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
                if scale != 1.0:
                    f0 = cv2.resize(f0, (W, H), interpolation=cv2.INTER_AREA)
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

            play_t0 = time.monotonic()
            dropped = 0
            paced = bool(self.is_file and fps > 0)
            # A live camera gets a dedicated reader thread (see _capture_loop);
            # a file is paced in this thread instead, where dropping frames is
            # what keeps replay at true speed.
            reader = None
            if not self.is_file:
                reader = threading.Thread(
                    target=self._capture_loop, args=(cap, W, H, scale),
                    daemon=True)
                reader.start()
            last_seq = -1
            while self.running:
                # --- LIVE CAMERA: analyse the newest captured frame ---------
                if not self.is_file:
                    with self._lock:
                        frame = self._latest
                        seq = self._latest_seq
                    if frame is None or seq == last_seq:
                        time.sleep(0.005)      # nothing new yet
                        continue
                    skipped = (seq - last_seq - 1) if last_seq >= 0 else 0
                    dropped += max(0, skipped)
                    last_seq = seq
                    cur = fidx
                    fidx += 1
                    annotated = pipeline.process_frame(
                        model, engine, frame, cur, device, helmet_model,
                        state, seatbelt_model, time.monotonic() - t0)
                    self._set_overlay(frame, annotated)
                    self.stats = {"frames": fidx, "dropped": dropped,
                                  "vehicles": len(state["vehicle_ids"]),
                                  "violations": len(engine.events)}
                    if fidx % 15 == 0:
                        db.set_meta("vehicle_count", len(state["vehicle_ids"]))
                    continue

                # --- real-time pacing for FILE replay ---------------------
                # Detection on CPU is far slower than playback (a 4K clip
                # analyses at ~1 fps against 25 fps of video). Without pacing
                # the clip crawls and the dashboard looks frozen or broken.
                # A live camera solves this by simply dropping the frames it
                # was too busy to look at, so a replayed file does the same:
                # the video always runs at its true speed and we analyse
                # whichever frame is current when the AI is ready.
                if paced:
                    now = time.monotonic()
                    due = play_t0 + fidx / fps
                    if now < due:
                        time.sleep(min(0.2, due - now))     # ahead: wait
                    else:
                        behind = int((now - play_t0) * fps) - fidx
                        for _ in range(max(0, behind)):     # behind: skip
                            if not cap.grab():              # grab = no decode
                                break
                            fidx += 1
                            dropped += 1

                ok, frame = cap.read()
                if not ok:
                    # File sources play ONCE — looping would re-count every
                    # vehicle and re-issue every violation on each pass.
                    break
                if scale != 1.0:
                    frame = cv2.resize(frame, (W, H), interpolation=cv2.INTER_AREA)
                cur = fidx
                fidx += 1
                with self._lock:
                    self._last_raw = frame

                # Pacing already throttles the analysis rate by dropping
                # frames, so every frame we still decode is worth analysing.
                # File replay has exact per-frame timing, so speed uses
                # frame_idx/fps (None) — still exact, because dropped frames
                # don't change what frame number the analysed frame actually is.
                if paced or cur % self.every == 0:
                    annotated = pipeline.process_frame(
                        model, engine, frame, cur, device, helmet_model,
                        state, seatbelt_model, None)
                    self._publish(annotated)

                self.stats = {"frames": fidx,
                              "dropped": dropped,
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
