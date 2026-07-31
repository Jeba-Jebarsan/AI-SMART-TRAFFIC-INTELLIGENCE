"""
The violation logic engine.

It is deliberately decoupled from YOLO: it consumes already-tracked detections
(each with a stable track_id) plus the current signal state, and emits violation
events. Every violation is emitted at most once per track_id (dedup via the
per-track 'emitted' set), which is what stops a single red-light runner from
generating 40 duplicate challans.

False-positive defences (each addresses a real failure seen on test footage):
  * MOTION GATE — a track must actually be moving (after subtracting the
    median motion of all tracks, i.e. camera pan) before helmet / triple /
    red-light logic applies. Parked roadside scooters can never violate.
  * PERSISTENCE — no-helmet and triple-riding must be observed in several
    frames of the same track before an event is emitted; one flickery frame
    is never enough.
  * RED STREAK — the signal must be read RED in several consecutive
    detections before red-light-jump checks arm.
"""
import datetime
import math
import statistics
from collections import defaultdict, deque

import config
import speed


def centroid(box):
    x1, y1, x2, y2 = box
    return (x1 + x2) / 2.0, (y1 + y2) / 2.0


class ViolationEngine:
    def __init__(self, frame_w, frame_h, fps, transform_fn=None,
                 allowed_direction=None, ppm=None):
        self.w = frame_w
        self.h = frame_h
        self.fps = max(float(fps), 1.0)
        # None until this camera is actually calibrated. Red Light Jump then
        # cannot fire and no line is drawn — see config.STOP_LINE_Y.
        self.stop_line_y = (config.STOP_LINE_Y * frame_h
                            if config.STOP_LINE_Y is not None else None)
        # A camera looking ALONG the road sees vehicles cross a horizontal
        # stop line downward. A camera looking ACROSS a junction sees them
        # cross a vertical line sideways, in either direction. Set
        # stop_line_x (pixels) for that geometry and it is used instead.
        self.stop_line_x = None
        # Lane region this camera's signal actually governs, in PIXELS.
        # None = the whole frame, only valid where one signal governs all
        # traffic in view. See config.RED_LIGHT_ZONE.
        self.red_light_zone = None
        # Wrong-way needs a per-camera allowed direction (set via the
        # calibration tool). None -> wrong-way stays off (honest default).
        self.allowed_dir = allowed_direction
        # Image -> road-metres transform for accurate speed (returns metres
        # along the road, or None if the point is outside the calibrated zone).
        # When None, speed stays off (honest: no metric ground truth).
        self.transform_fn = transform_fn
        # Real-world speed estimation (perspective transform + multi-frame
        # regression + outlier rejection + EMA smoothing + confidence gate)
        # lives in its own module, fed the tracking output frame by frame.
        self.speed_est = speed.SpeedEstimator(self.fps, transform_fn, ppm=ppm)
        self._fidx = 0                           # latest frame index seen
        # track_id -> rolling history + which violations already fired.
        # "move" holds (frame_idx, virtual_x, virtual_y): a camera-motion-
        # compensated position. Movement is judged as NET displacement over
        # ~1s of wall time, so box jitter on a parked vehicle cancels out
        # instead of accumulating, and frame-skipped runs behave identically.
        self.tracks = defaultdict(
            lambda: {"cent": deque(maxlen=40),
                     "move": deque(maxlen=90),
                     "aspect": deque(maxlen=40),   # box height/width history
                     "vx": 0.0, "vy": 0.0,
                     "nh_hits": 0, "triple_hits": 0, "sb_hits": 0,
                     "wheelie_hits": 0, "phone_hits": 0,
                     "drive_start": None, "stop_start": None,
                     "park_start": None, "ever_moved": False,
                     "emitted": set(), "cls": None})
        self.events = []
        # Signal-state memory — honest detection, never invented when absent.
        self._last_signal = None
        self._last_signal_frame = -10 ** 9
        self._red_streak = 0
        self.signal_known = False

    def set_transform_fn(self, fn):
        """Hot-apply a new perspective transform (the live calibration tool
        calibrates speed mid-session). Keeps the engine and its speed
        estimator in sync so over-speed + on-screen speed activate together."""
        self.transform_fn = fn
        self.speed_est.set_transform_fn(fn)

    # ------------------------------------------------------------------ signal
    def signal_state(self, frame_idx, detected=None):
        """Return 'RED' / 'YELLOW' / 'GREEN' / 'UNKNOWN'.

        Default (FORCE_SIGNAL=None): state comes ONLY from a detected traffic
        light. The last seen colour is held briefly (lights aren't detected
        every frame) then expires to 'UNKNOWN' — we never invent a signal.
        """
        if config.FORCE_SIGNAL:                       # deliberate demo override
            cycle = config.FORCE_SIGNAL
            period = sum(d for _, d in cycle)
            t = (frame_idx / self.fps) % period
            acc, state = 0.0, cycle[-1][0]
            for s, dur in cycle:
                acc += dur
                if t < acc:
                    state = s
                    break
            self.signal_known = True
            self._red_streak = config.RED_MIN_STREAK if state == "RED" else 0
            return state

        if detected:
            self._red_streak = self._red_streak + 1 if detected == "RED" else 0
            self._last_signal = detected
            self._last_signal_frame = frame_idx
        hold = int(self.fps * 2)
        if self._last_signal and (frame_idx - self._last_signal_frame) <= hold:
            self.signal_known = True
            return self._last_signal
        self.signal_known = False
        self._red_streak = 0
        return "UNKNOWN"

    @property
    def red_armed(self):
        """RED must have been read repeatedly before red-light checks fire."""
        return self._red_streak >= config.RED_MIN_STREAK

    # ------------------------------------------------------------------ motion
    def _apply_motion(self, frame_idx, vehicles):
        """Record camera-compensated motion for every track.

        The median delta across all tracks approximates camera motion (a pan
        makes everything shift together); subtracting it leaves true object
        motion. With few tracks the median is unreliable, so raw motion is
        used — fixed CCTV has near-zero median anyway.
        """
        deltas = {}
        for v in vehicles:
            tid = v["track_id"]
            if tid is None:
                continue
            st = self.tracks[tid]
            if st["cent"]:
                lf, lx, ly = st["cent"][-1]
                cx, cy = centroid(v["box"])
                deltas[tid] = (cx - lx, cy - ly)

        if len(deltas) >= 5:
            cam_dx = statistics.median(d[0] for d in deltas.values())
            cam_dy = statistics.median(d[1] for d in deltas.values())
        else:
            cam_dx = cam_dy = 0.0

        for tid, (dx, dy) in deltas.items():
            st = self.tracks[tid]
            st["vx"] += dx - cam_dx              # integrate compensated motion
            st["vy"] += dy - cam_dy
            st["move"].append((frame_idx, st["vx"], st["vy"]))

    def is_moving(self, tid):
        """True when the track's NET compensated displacement is significant.

        Net displacement (end minus start) is immune to detector-box jitter: a
        parked bike whose box wobbles +-2px every frame goes nowhere, while a
        real rider covers distance.

        The window is expressed in TIME and needs only two observations,
        because the analyser does not run at the video frame rate — live
        replay drops whatever frames the CPU was too busy for. The previous
        version demanded 3 samples inside a 1-second window; once analysis
        dropped below ~3 fps almost nothing qualified, and on real footage
        89% of genuinely moving vehicles were judged stationary. Everything
        gated on motion (helmet, triple riding, phone, wheelie, speed) was
        silently suppressed, and Illegal Parking fired on moving traffic.

        The distance required scales with how long the window actually spans,
        preserving the original "displacement per second" meaning at any
        sampling rate.
        """
        st = self.tracks.get(tid)
        if not st or len(st["move"]) < 2:
            return False
        horizon = self._fidx - self.fps * config.MOVE_WINDOW_SECONDS
        win = [(f, x, y) for f, x, y in st["move"] if f >= horizon]
        if len(win) < 2:
            win = list(st["move"])[-2:]
        secs = (win[-1][0] - win[0][0]) / self.fps
        if secs < 0.2:
            return False                         # not enough history yet
        net = math.hypot(win[-1][1] - win[0][1], win[-1][2] - win[0][2])
        per_sec = max(12.0, config.MIN_MOVE_FRAC * self.h)
        need = max(12.0, per_sec * min(secs, config.MOVE_WINDOW_SECONDS))
        return net >= need

    # ------------------------------------------------------------------ zones
    @staticmethod
    def _in_zone(box, zone):
        """True when a vehicle's ground contact point falls inside `zone`.

        A zone of None means "everywhere". Uses the bottom-centre of the box
        (where the vehicle meets the road) rather than the box centre, so a
        tall vehicle isn't judged by a point floating above the carriageway.
        """
        if not zone:
            return True
        cx = (box[0] + box[2]) / 2.0
        cy = box[3]
        inside = False
        n = len(zone)
        for i in range(n):               # ray-casting point-in-polygon
            x1, y1 = zone[i]
            x2, y2 = zone[(i + 1) % n]
            if (y1 > cy) != (y2 > cy):
                xin = x1 + (cy - y1) * (x2 - x1) / float(y2 - y1 or 1e-9)
                if cx < xin:
                    inside = not inside
        return inside

    # -------------------------------------------------------- illegal parking
    def _in_no_parking_zone(self, box):
        """True when the vehicle sits inside the configured no-parking zone.

        With no zone configured the whole frame counts, which is only safe on
        a camera pointed at a genuine no-stopping area — otherwise every
        vehicle waiting in traffic eventually qualifies. Set
        config.NO_PARKING_ZONE to the kerb/junction area for a real deployment.
        """
        return self._in_zone(box, config.NO_PARKING_ZONE)

    def _parked_seconds(self, tid, frame_idx, signal):
        """Seconds this vehicle has been continuously STATIONARY.

        Stopping is not parking: a red light or a queue is lawful, so the
        clock is held while the signal reads RED, and the threshold is long
        enough that ordinary congestion doesn't reach it. Any real movement
        resets the clock, so only a vehicle that genuinely stays put counts.
        """
        st = self.tracks[tid]
        if self.is_moving(tid) or signal == "RED":
            st["park_start"] = None
            st["ever_moved"] = True
            return 0.0
        # A vehicle this camera has ever seen driving is traffic, not parked.
        # The motion gate can miss movement on a sparsely sampled or briefly
        # occluded track, and without this a car merely crawling in a queue
        # accumulated "parked" time and was fined. Once seen moving, a track
        # is permanently exempt for the rest of its life.
        if st.get("ever_moved"):
            st["park_start"] = None
            return 0.0
        if st["park_start"] is None:
            st["park_start"] = frame_idx
            return 0.0
        return (frame_idx - st["park_start"]) / self.fps

    # ------------------------------------------------------------ rest-break
    def _continuous_drive_seconds(self, tid, frame_idx):
        """Update rest-break bookkeeping for this track and return seconds of
        UNBROKEN continuous driving so far (0 while stopped / never started).
        A stop shorter than BREAK_MIN_STOP_SECONDS (a red light, a jam) does
        NOT reset the clock — only a genuine break does."""
        st = self.tracks[tid]
        if self.is_moving(tid):
            st["stop_start"] = None
            if st["drive_start"] is None:
                st["drive_start"] = frame_idx
            return (frame_idx - st["drive_start"]) / self.fps
        if st["drive_start"] is not None:
            if st["stop_start"] is None:
                st["stop_start"] = frame_idx
            elif (frame_idx - st["stop_start"]) / self.fps >= config.BREAK_MIN_STOP_SECONDS:
                st["drive_start"] = None
                st["stop_start"] = None
                st["emitted"].discard("break")   # a real break re-arms the rule
        return 0.0

    # ------------------------------------------------------------------ update
    def update(self, frame_idx, vehicles, signal, riders, belts=None,
               phones=None, frame_time=None):
        """Advance one frame.

        frame_time: real observation time in SECONDS (wall-clock) for accurate
        speed on a live camera; None -> derived from frame_idx/fps (exact for
        video files).

        vehicles: list of {track_id, cls, conf, box}
        riders:   list of {track_id, box, no_helmet, helmet_ok, riders: int}
        belts:    list of {track_id, box, no_seatbelt, seatbelt_ok} (cars/
                  buses/trucks only; empty/None when no seatbelt model)
        phones:   list of {track_id, box, phone: bool} — a rider/driver with a
                  phone in hand this frame (empty/None when none detected)
        Returns the list of NEW violation events created this frame.
        """
        ts = datetime.datetime.now().isoformat(timespec="seconds")
        new = []

        self._fidx = frame_idx
        self._apply_motion(frame_idx, vehicles)

        for v in vehicles:
            tid = v["track_id"]
            if tid is None:
                continue
            st = self.tracks[tid]
            st["cls"] = v["cls"]
            cx, cy = centroid(v["box"])
            st["cent"].append((frame_idx, cx, cy))
            conf_ok = v.get("conf", 1.0) >= config.CONF["vehicle"]

            # feed the speed estimator this track's bottom-centre point EVERY
            # frame — accurate (road-metres) when calibrated, approximate
            # (pixel-based) otherwise. The estimator handles both internally.
            ax = (v["box"][0] + v["box"][2]) / 2.0
            ay = v["box"][3]
            self.speed_est.update(tid, (ax, ay), frame_idx, frame_time)

            # --- Red-light: centroid crosses the stop line downward while RED
            # (signal read RED repeatedly + the vehicle is genuinely moving)
            # Only vehicles in the lane the signal governs. Without this a
            # junction's other approaches — which have a GREEN of their own —
            # get fined off a red that was never theirs.
            if (config.ENABLE["red_light"] and signal == "RED" and self.red_armed
                    and conf_ok and len(st["cent"]) >= 2
                    and "red" not in st["emitted"] and self.is_moving(tid)
                    and self._in_zone(v["box"], self.red_light_zone)):
                prev_x, prev_y = st["cent"][-2][1], st["cent"][-2][2]
                if self.stop_line_x is not None:
                    # Sideways junction view: count a crossing in EITHER
                    # direction, since both carriageways face the camera.
                    crossed = ((prev_x < self.stop_line_x <= cx)
                               or (prev_x > self.stop_line_x >= cx))
                elif self.stop_line_y is not None:
                    crossed = prev_y < self.stop_line_y <= cy
                else:
                    # No stop line calibrated for this camera: we do not know
                    # where the line legally sits, so nothing can cross it.
                    crossed = False
                if crossed:
                    st["emitted"].add("red")
                    new.append(self._event("Red Light Jump", tid, v["box"],
                                           frame_idx, ts))

            # --- Over-speeding (only when the camera is speed-calibrated, the
            # vehicle is genuinely MOVING, and the estimator is CONFIDENT —
            # enough frames of consistent motion. The motion gate guarantees a
            # stopped / jittering vehicle can never be issued a speeding fine.)
            if (config.ENABLE["over_speed"] and self.transform_fn is not None
                    and conf_ok and "speed" not in st["emitted"]
                    and self.is_moving(tid) and self.speed_est.confident(tid)):
                spd = self.speed_est.speed(tid)
                if spd and spd > config.SPEED_LIMIT_KMPH:
                    st["emitted"].add("speed")
                    ev = self._event("Over Speeding", tid, v["box"], frame_idx, ts)
                    ev["speed_kmph"] = round(spd, 1)
                    new.append(ev)

            # --- Wrong-way (only when a per-camera direction is calibrated,
            # and only inside the lane zone that direction describes. On a
            # two-way road the opposing carriageway is lawfully travelling the
            # other way, so an unzoned direction rule would flag every one of
            # those vehicles — the zone is what makes this safe to enable.)
            if (config.ENABLE["wrong_way"] and self.allowed_dir
                    and "wrong" not in st["emitted"]
                    and conf_ok and self.is_moving(tid)
                    and self._in_zone(v["box"], config.WRONG_WAY_ZONE)
                    and len(st["cent"]) >= 6 and self._wrong_way(st["cent"])):
                st["emitted"].add("wrong")
                new.append(self._event("Wrong Way", tid, v["box"], frame_idx, ts))

            # --- Illegal parking (stationary far too long to be traffic)
            if config.ENABLE["illegal_parking"] and "park" not in st["emitted"]:
                park_secs = self._parked_seconds(tid, frame_idx, signal)
                # Require a well-observed track before accusing anyone of
                # parking: a vehicle seen only a handful of times has no
                # motion history worth trusting, and "no evidence of movement"
                # must never be mistaken for evidence of stillness.
                if (park_secs >= config.ILLEGAL_PARK_SECONDS and conf_ok
                        and len(st["move"]) >= config.PARK_MIN_OBSERVATIONS
                        and self._in_no_parking_zone(v["box"])):
                    st["emitted"].add("park")
                    ev = self._event("Illegal Parking", tid, v["box"],
                                     frame_idx, ts)
                    ev["parked_seconds"] = round(park_secs, 1)
                    new.append(ev)

            # --- Continuous driving / no rest break (fatigue rule)
            if config.ENABLE["no_rest_break"]:
                drive_secs = self._continuous_drive_seconds(tid, frame_idx)
                if (drive_secs >= config.MAX_CONTINUOUS_DRIVE_SECONDS
                        and conf_ok and "break" not in st["emitted"]):
                    st["emitted"].add("break")
                    ev = self._event("No Rest Break", tid, v["box"], frame_idx, ts)
                    ev["drive_seconds"] = round(drive_secs, 1)
                    new.append(ev)

        # --- Helmet + triple-riding (from rider associations).
        # Requires: a tracked, MOVING motorcycle with at least one associated
        # rider, and the condition observed across several frames.
        for r in riders:
            tid = r.get("track_id")
            if tid is None or r.get("riders", 0) < 1:
                continue
            if not self.is_moving(tid):
                continue
            st = self.tracks[tid]

            if config.ENABLE["no_helmet"] and "helmet" not in st["emitted"]:
                if r.get("no_helmet"):
                    st["nh_hits"] += 1
                elif r.get("helmet_ok"):
                    st["nh_hits"] = 0          # positive helmet sighting resets
                if st["nh_hits"] >= config.HELMET_MIN_HITS:
                    st["emitted"].add("helmet")
                    new.append(self._event("No Helmet", tid, r["box"],
                                           frame_idx, ts))

            if config.ENABLE["triple_riding"] and "triple" not in st["emitted"]:
                if r.get("riders", 0) >= 3:
                    st["triple_hits"] += 1
                else:
                    st["triple_hits"] = max(0, st["triple_hits"] - 1)
                if st["triple_hits"] >= config.TRIPLE_MIN_HITS:
                    st["emitted"].add("triple")
                    new.append(self._event("Triple Riding", tid, r["box"],
                                           frame_idx, ts))

            # --- Wheelie / stunt riding. A wheelie makes the bike's box SPIKE
            # taller than that same bike's own baseline aspect (height/width).
            # A relative spike (not an absolute value) is what separates a
            # wheelie from a merely tall rear-view rider. Motion + a baseline
            # history + persistence are all required, so it can't misfire on
            # one odd frame or a normal upright bike.
            if config.ENABLE["wheelie"] and "wheelie" not in st["emitted"]:
                x1, y1, x2, y2 = r["box"]
                asp = (y2 - y1) / max(1.0, x2 - x1)
                st["aspect"].append(asp)
                if len(st["aspect"]) >= config.WHEELIE_MIN_HISTORY:
                    base = statistics.median(list(st["aspect"])[:-3])
                    if asp >= max(config.WHEELIE_MIN_ASPECT,
                                  base * config.WHEELIE_RISE_RATIO):
                        st["wheelie_hits"] += 1
                    else:
                        st["wheelie_hits"] = max(0, st["wheelie_hits"] - 1)
                    if st["wheelie_hits"] >= config.WHEELIE_MIN_HITS:
                        st["emitted"].add("wheelie")
                        new.append(self._event("Wheelie Stunt", tid, r["box"],
                                               frame_idx, ts))

        # --- Seatbelt (cars/buses/trucks only, requires the optional
        # seatbelt model — see build_seatbelt_status). Same rules as helmet:
        # positive detection required, multi-frame persistence, must be moving.
        for b in (belts or []):
            tid = b.get("track_id")
            if tid is None or not self.is_moving(tid):
                continue
            st = self.tracks[tid]
            if config.ENABLE["no_seatbelt"] and "seatbelt" not in st["emitted"]:
                if b.get("no_seatbelt"):
                    st["sb_hits"] += 1
                elif b.get("seatbelt_ok"):
                    st["sb_hits"] = 0
                if st["sb_hits"] >= config.SEATBELT_MIN_HITS:
                    st["emitted"].add("seatbelt")
                    new.append(self._event("No Seatbelt", tid, b["box"],
                                           frame_idx, ts))

        # --- Mobile phone use (rider/driver holding a phone while the vehicle
        # is moving). The phone comes from the default model's COCO 'cell
        # phone' class, associated to the vehicle in build_phone_status. Same
        # discipline: positive detection, motion gate, multi-frame persistence.
        for p in (phones or []):
            tid = p.get("track_id")
            if tid is None or not self.is_moving(tid):
                continue
            st = self.tracks[tid]
            if config.ENABLE["phone_use"] and "phone" not in st["emitted"]:
                if p.get("phone"):
                    st["phone_hits"] += 1
                else:
                    st["phone_hits"] = max(0, st["phone_hits"] - 1)
                if st["phone_hits"] >= config.PHONE_MIN_HITS:
                    st["emitted"].add("phone")
                    new.append(self._event("Mobile Phone Use", tid, p["box"],
                                           frame_idx, ts))

        self.events.extend(new)
        return new

    # ----------------------------------------------------------------- helpers
    def speed_of(self, tid):
        """Current smoothed speed (km/h) for on-screen labels + the dashboard,
        for every genuinely MOVING vehicle. Accurate when the camera is
        calibrated, otherwise an APPROXIMATE pixel estimate (shown as ~approx).

        A vehicle must pass the MOTION GATE first — camera-compensated net
        displacement over ~1s — so a PARKED bike whose tracker box jitters can
        never show a phantom 5-10 km/h. Returns None when not moving / too new.
        Speeding FINES use speed_est.confident() (calibrated-only) — never this."""
        if not self.is_moving(tid):
            return None
        s = self.speed_est.speed(tid)
        return int(round(s)) if s and s > 1 else None

    def _wrong_way(self, cent):
        f0, x0, y0 = cent[0]
        f1, x1, y1 = cent[-1]
        vx, vy = x1 - x0, y1 - y0
        mag = math.hypot(vx, vy)
        if mag < 6:  # not moving enough to judge
            return False
        ax, ay = self.allowed_dir or config.ALLOWED_DIRECTION
        amag = math.hypot(ax, ay) or 1.0
        cos = (vx * ax + vy * ay) / (mag * amag)
        return cos < config.WRONG_WAY_MIN_DOT

    def _event(self, vtype, tid, box, frame_idx, ts):
        return {
            "type": vtype,
            "track_id": tid,
            "box": [float(x) for x in box],
            "frame_index": frame_idx,
            "timestamp": ts,
            "fine": config.FINES.get(vtype, 1000),
            "speed_kmph": None,
            "drive_seconds": None,
        }
