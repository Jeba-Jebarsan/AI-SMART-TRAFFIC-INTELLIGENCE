"""Camera-location resolution, honest and layered:

1. manual override set from the dashboard (meta 'location_override') — a
   fixed CCTV camera's location is configured once by the operator;
2. GPS embedded in the video file itself (phones write an ISO-6709 tag like
   "+06.9271+079.8612/" into MP4 metadata) — extracted with ffmpeg and
   reverse-geocoded to a street/city name when the internet allows;
3. the config.CAMERA_LOCATION default.

Pixels alone cannot tell you where a road is — anything more would be a
guess, and this system does not guess.
"""
import json
import re
import subprocess
import urllib.parse
import urllib.request

import config
import db

_ISO6709 = re.compile(r"([+-]\d+(?:\.\d+)?)([+-]\d+(?:\.\d+)?)")


def _ffmpeg_exe():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def gps_from_video(path):
    """Return (lat, lon) from the file's metadata, or None."""
    if not path:
        return None
    try:
        p = subprocess.run(
            [_ffmpeg_exe(), "-hide_banner", "-i", str(path)],
            capture_output=True, text=True, timeout=15)
        text = (p.stderr or "") + (p.stdout or "")
    except Exception:
        return None
    for line in text.splitlines():
        low = line.lower()
        if "location" in low or "com.apple.quicktime.location" in low:
            m = _ISO6709.search(line)
            if m:
                try:
                    lat, lon = float(m.group(1)), float(m.group(2))
                    if -90 <= lat <= 90 and -180 <= lon <= 180 and (lat or lon):
                        return lat, lon
                except ValueError:
                    continue
    return None


def reverse_geocode(lat, lon):
    """Best-effort street/city name via OpenStreetMap Nominatim (needs
    internet; fails silently to coordinates)."""
    try:
        url = ("https://nominatim.openstreetmap.org/reverse?format=json&zoom=16&"
               + urllib.parse.urlencode({"lat": lat, "lon": lon}))
        req = urllib.request.Request(
            url, headers={"User-Agent": "ai-traffic-intelligence-demo/1.0"})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode("utf-8"))
        name = data.get("display_name") or ""
        parts = [p.strip() for p in name.split(",")]
        if parts:
            return ", ".join(parts[:3])
    except Exception:
        pass
    return None


def resolve_location(video_path=None):
    """The location string used on overlays, challans and the dashboard."""
    override = db.get_meta("location_override")
    if override:
        return override
    gps = gps_from_video(video_path)
    if gps:
        lat, lon = gps
        name = reverse_geocode(lat, lon)
        coords = f"{abs(lat):.4f}°{'N' if lat >= 0 else 'S'}, " \
                 f"{abs(lon):.4f}°{'E' if lon >= 0 else 'W'}"
        return f"{name} ({coords})" if name else coords
    return config.CAMERA_LOCATION
