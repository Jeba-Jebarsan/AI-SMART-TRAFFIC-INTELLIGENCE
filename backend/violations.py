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


def centroid(box):
    x1, y1, x2, y2 = box
    return (x1 + x2) / 2.0, (y1 + y2) / 2.0


class ViolationEngine:
    def __init__(self, frame_w, frame_h, fps, transform_fn=None,
                 allowed_direction=None):
        self.w = frame_w
        self.h = frame_h
        self.fps = max(float(fps), 1.0)
        self.stop_line_y = config.STOP_LINE_Y * frame_h
        # Wrong-way needs a per-camera allowed direction (set via the
        # calibration tool). None -> wrong-way stays off (honest default).
        self.allowed_dir = allowed_direction
        # Image -> road-metres transform for accurate speed (returns metres
        # along the road, or None if the point is outside the calibrated zone).
        # When None, speed falls back to the rough pixel method.
        self.transform_fn = transform_fn
        self.speed_win = max(int(self.fps), 2)   # ~1 second of samples
        self._fidx = 0                           # latest frame index seen
        # track_id -> rolling history + which violations already fired.
        # "move" holds (frame_idx, virtual_x, virtual_y): a camera-motion-
        # compensated position. Movement is judged as NET displacement over
        # ~1s of wall time, so box jitter on a parked vehicle cancels out
        # instead of accumulating, and frame-skipped runs behave identically.
        self.tracks = defaultdict(
            lambda: {"cent": deque(maxlen=40),
                     "ty": deque(maxlen=self.speed_win),
                     "move": deque(maxlen=90),
                     "vx": 0.0, "vy": 0.0,
                     "nh_hits": 0, "triple_hits": 0,
                     "emitted": set(), "cls": None})
        self.events = []
        # Signal-state memory — honest detection, never invented when absent.
        self._last_signal = None
        self._last_signal_frame = -10 ** 9
        self._red_streak = 0
        self.signal_known = False

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
        """True when the track's NET compensated displacement over the last
        ~second is significant. Net displacement (end minus start position)
        is immune to detector-box jitter: a parked bike whose box wobbles
        +-2px every frame goes nowhere, while a real rider covers distance."""
        st = self.tracks.get(tid)
        if not st or len(st["move"]) < 3:
            return False
        horizon = self._fidx - self.fps          # ~1 second of wall time
        win = [(f, x, y) for f, x, y in st["move"] if f >= horizon]
        if len(win) < 3 or (win[-1][0] - win[0][0]) < self.fps * 0.3:
            return False                         # not enough history yet
        net = math.hypot(win[-1][1] - win[0][1], win[-1][2] - win[0][2])
        return net >= max(12.0, config.MIN_MOVE_FRAC * self.h)

    # ------------------------------------------------------------------ update
    def update(self, frame_idx, vehicles, signal, riders):
        """Advance one frame.

        vehicles: list of {track_id, cls, conf, box}
        riders:   list of {track_id, box, no_helmet, helmet_ok, riders: int}
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

            # transformed bottom-centre (metres along road) for accurate speed
            if self.transform_fn is not None:
                ax = (v["box"][0] + v["box"][2]) / 2.0
                ay = v["box"][3]
                ty = self.transform_fn((ax, ay))
                if ty is not None:
                    st["ty"].append((frame_idx, ty))

            # --- Red-light: centroid crosses the stop line downward while RED
            # (signal read RED repeatedly + the vehicle is genuinely moving)
            if (config.ENABLE["red_light"] and signal == "RED" and self.red_armed
                    and conf_ok and len(st["cent"]) >= 2
                    and "red" not in st["emitted"] and self.is_moving(tid)):
                prev_y = st["cent"][-2][2]
                if prev_y < self.stop_line_y <= cy:
                    st["emitted"].add("red")
                    new.append(self._event("Red Light Jump", tid, v["box"],
                                           frame_idx, ts))

            # --- Over-speeding (only when the camera is speed-calibrated)
            if (config.ENABLE["over_speed"] and self.transform_fn is not None
                    and conf_ok and "speed" not in st["emitted"]):
                spd = self._speed_kmph(st)
                if spd and spd > config.SPEED_LIMIT_KMPH:
                    st["emitted"].add("speed")
                    ev = self._event("Over Speeding", tid, v["box"], frame_idx, ts)
                    ev["speed_kmph"] = round(spd, 1)
                    new.append(ev)

            # --- Wrong-way (only when a per-camera direction is calibrated)
            if (config.ENABLE["wrong_way"] and self.allowed_dir
                    and "wrong" not in st["emitted"]
                    and conf_ok and self.is_moving(tid)
                    and len(st["cent"]) >= 6 and self._wrong_way(st["cent"])):
                st["emitted"].add("wrong")
                new.append(self._event("Wrong Way", tid, v["box"], frame_idx, ts))

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

        self.events.extend(new)
        return new

    # ----------------------------------------------------------------- helpers
    def _speed_kmph(self, st):
        # Accurate path: metres travelled along the road per second.
        if self.transform_fn is not None:
            ty = st["ty"]
            if len(ty) < max(2, self.speed_win // 2):
                return 0.0
            f0, y0 = ty[0]
            f1, y1 = ty[-1]
            seconds = (f1 - f0) / self.fps
            if seconds <= 0:
                return 0.0
            return abs(y1 - y0) / seconds * 3.6

        # Fallback: rough pixel method (needs PIXELS_PER_METER calibration).
        cent = st["cent"]
        if len(cent) < 5:
            return 0.0
        f0, x0, y0 = cent[0]
        f1, x1, y1 = cent[-1]
        seconds = (f1 - f0) / self.fps
        if seconds <= 0:
            return 0.0
        dist_px = math.hypot(x1 - x0, y1 - y0)
        return (dist_px / config.PIXELS_PER_METER) / seconds * 3.6

    def speed_of(self, tid):
        """Current speed (km/h) for on-screen labels — only when speed-calibrated."""
        if self.transform_fn is None:
            return None
        st = self.tracks.get(tid)
        if not st:
            return None
        s = self._speed_kmph(st)
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
        }
