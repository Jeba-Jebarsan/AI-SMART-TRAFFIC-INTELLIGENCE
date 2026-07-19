"""
AI vehicle speed-estimation module.

Consumes the EXISTING YOLO + ByteTrack tracking output (no re-detection): the
ViolationEngine feeds this estimator each tracked vehicle's bottom-centre point
every frame, and it turns those points into a filtered km/h reading.

TWO MODES:
  * ACCURATE (camera calibrated) — the point is projected from image pixels to
    real-world road metres via the perspective (homography) transform, and
    speed is a least-squares regression of metres-vs-time with outlier
    rejection. Only THIS mode is trusted for a speeding FINE.
  * APPROX (no calibration) — speed is derived from pixel displacement over
    time via config.PIXELS_PER_METER. Good enough to show a live speed for
    EVERY vehicle (so the dashboard's Speed filter works without setup), but it
    is rough and camera-angle dependent, so it is shown labelled "~approx" and
    NEVER issues a fine (confident() stays False in this mode).

Filtering applied in both modes: multi-frame window (never a single-frame
delta), a movement-consistency check so a jittering/parked box shows no speed,
and EMA smoothing so the number doesn't flicker.
"""
import math
from collections import defaultdict, deque

import config


def _fit(samples):
    """Least-squares fit of road-position (metres) against time (seconds).

    Returns (slope_m_per_s, r2, n) for the [(t, y), ...] samples, or None when
    there are too few points or no time span. `r2` (how straight-line the
    motion is) doubles as the "movement is consistent" confidence signal.
    """
    n = len(samples)
    if n < 2:
        return None
    t0 = samples[0][0]
    ts = [t - t0 for t, _ in samples]
    ys = [y for _, y in samples]
    if ts[-1] - ts[0] <= 0:
        return None
    mt = sum(ts) / n
    my = sum(ys) / n
    stt = sum((t - mt) ** 2 for t in ts)
    if stt <= 0:
        return None
    slope = sum((t - mt) * (y - my) for t, y in zip(ts, ys)) / stt
    ss_tot = sum((y - my) ** 2 for y in ys)
    if ss_tot <= 1e-9:
        return slope, 0.0, n
    ss_res = sum((y - (my + slope * (t - mt))) ** 2 for t, y in zip(ts, ys))
    r2 = max(0.0, 1.0 - ss_res / ss_tot)
    return slope, r2, n


class SpeedEstimator:
    """Per-track real-world speed estimation from projected road positions.

    One instance lives inside each ViolationEngine. It holds no detection or
    tracking logic of its own — it only turns the already-tracked points it is
    fed into filtered km/h readings.
    """

    def __init__(self, fps, transform_fn=None):
        self.fps = max(float(fps or 25.0), 1.0)
        self.transform_fn = transform_fn
        self.win = max(6, int(self.fps * 1.4))          # ~1.4 s window
        self.min_samples = max(5, int(self.fps * 0.4))
        # calibrated mode stores (t, road_metres); approx mode stores (t, x, y)
        self._samples = defaultdict(lambda: deque(maxlen=self.win))
        self._ema = {}            # track_id -> EMA-smoothed km/h
        self._top = {}            # track_id -> highest km/h seen

    @property
    def approx(self):
        """True when there's no calibration -> speeds are pixel-based estimates."""
        return self.transform_fn is None

    def set_transform_fn(self, fn):
        """Hot-swap the perspective transform (the live 🎯 tool applies one
        mid-session). Per-track history is cleared so samples from the old mode
        can't mix with the new one."""
        self.transform_fn = fn
        self._samples.clear()
        self._ema.clear()

    # ------------------------------------------------------------------ ingest
    def update(self, tid, image_point, frame_idx, t=None):
        """Feed one tracked observation — image_point is the vehicle's
        bottom-centre in pixels.

        `t` is the observation time in SECONDS. Pass a real wall-clock timestamp
        for a live camera (CCTV/drone FPS fluctuates, so frame_idx/fps drifts);
        omit it for a video file, where frame_idx/fps is exact."""
        if tid is None:
            return
        t = (frame_idx / self.fps) if t is None else float(t)
        buf = self._samples[tid]
        if buf and buf[-1][0] == t:                     # same frame twice
            return
        if self.transform_fn is not None:
            y = self.transform_fn(image_point)          # metres, or None if outside quad
            if y is None:
                return
            buf.append((t, y))
        else:
            buf.append((t, float(image_point[0]), float(image_point[1])))

    # ------------------------------------------------------- accurate (metres)
    def _clean(self, tid):
        """Cleaned (t, metres) samples with gross outliers dropped (calibrated)."""
        buf = list(self._samples.get(tid, ()))
        if len(buf) < 4:
            return buf
        fit = _fit(buf)
        if fit is None:
            return buf
        slope = fit[0]
        t0 = buf[0][0]
        ts = [t - t0 for t, _ in buf]
        ys = [y for _, y in buf]
        mt = sum(ts) / len(ts)
        my = sum(ys) / len(ys)
        res = [abs(y - (my + slope * (t - mt))) for t, y in zip(ts, ys)]
        rstd = math.sqrt(sum(r * r for r in res) / len(res)) or 1.0
        keep = [buf[i] for i, r in enumerate(res)
                if r <= config.SPEED_OUTLIER_SIGMA * rstd]
        return keep if len(keep) >= 3 else buf

    def _raw_calibrated(self, tid):
        fit = _fit(self._clean(tid))
        if fit is None:
            return 0.0, 0.0, 0
        slope, r2, n = fit
        return abs(slope) * 3.6, r2, n

    # ------------------------------------------------------- approx (pixels)
    def _raw_approx(self, tid):
        """(km/h, quality, n) from pixel displacement. `quality` is the ratio
        of net displacement to total path length — near 1.0 for a vehicle
        travelling in a straight line, near 0 for a box jittering in place."""
        buf = list(self._samples.get(tid, ()))
        n = len(buf)
        if n < 3:
            return 0.0, 0.0, n
        t0, x0, y0 = buf[0]
        t1, x1, y1 = buf[-1]
        dt = t1 - t0
        if dt <= 0:
            return 0.0, 0.0, n
        net = math.hypot(x1 - x0, y1 - y0)
        path = sum(math.hypot(buf[i][1] - buf[i - 1][1], buf[i][2] - buf[i - 1][2])
                   for i in range(1, n))
        quality = (net / path) if path > 0 else 0.0
        kmph = (net / config.PIXELS_PER_METER) / dt * 3.6
        return kmph, quality, n

    def _raw_kmph(self, tid):
        return self._raw_approx(tid) if self.approx else self._raw_calibrated(tid)

    # ------------------------------------------------------------------ output
    def confident(self, tid):
        """True only when a speed is trustworthy enough to base a FINE on —
        which requires calibration. Approx (pixel) speeds are never confident,
        so over-speeding fines can never come from a rough estimate."""
        if self.approx:
            return False
        buf = self._samples.get(tid)
        if not buf or len(buf) < self.min_samples:
            return False
        if (buf[-1][0] - buf[0][0]) < config.SPEED_MIN_SECONDS:
            return False
        kmph, r2, n = self._raw_kmph(tid)
        return (n >= self.min_samples and r2 >= config.SPEED_MIN_R2
                and 0.0 < kmph <= config.SPEED_SANITY_MAX)

    def speed(self, tid):
        """EMA-smoothed km/h for display, in either mode (0.0 when unavailable
        or when the box is basically stationary/jittering)."""
        # exact-only by default: without calibration, show no speed rather than
        # a rough (and easily "random"-looking) pixel estimate
        if self.approx and not config.SPEED_APPROX:
            return 0.0
        buf = self._samples.get(tid)
        if not buf or len(buf) < 3:
            return 0.0
        kmph, quality, n = self._raw_kmph(tid)
        if kmph <= 0 or kmph > config.SPEED_SANITY_MAX:
            return self._ema.get(tid, 0.0)
        # in approx mode, only show a speed for a vehicle that's genuinely
        # moving in one direction (not a box wobbling in place)
        if self.approx and (quality < 0.5 or n < 4):
            return self._ema.get(tid, 0.0)
        prev = self._ema.get(tid)
        a = config.SPEED_EMA_ALPHA
        val = kmph if prev is None else a * kmph + (1 - a) * prev
        self._ema[tid] = val
        trustworthy = self.confident(tid) if not self.approx else (quality >= 0.6)
        if trustworthy and val > self._top.get(tid, 0.0):
            self._top[tid] = val
        return val

    def top_speed(self, tid):
        """Highest km/h seen for this track (0.0 if never)."""
        return self._top.get(tid, 0.0)
