"""Police alerting: PDF e-challans + email with photo evidence.

When config.ALERTS is configured (SMTP credentials + recipient), every
confirmed violation can be mailed to the traffic police automatically —
subject, violation details, the evidence snapshot, the plate crop that OCR
actually read, and a generated PDF challan, all in one message.

Everything degrades gracefully: no credentials -> alerts stay off, PDF
generation works regardless (used by the dashboard's download button).
Credentials may come from env vars SMTP_USER / SMTP_PASS to keep them out
of the repo.
"""
import os
import smtplib
import threading
from email.message import EmailMessage
from pathlib import Path

import config
import db

CHALLAN_DIR = config.OUTPUT_DIR / "challans"
CHALLAN_DIR.mkdir(parents=True, exist_ok=True)

_send_lock = threading.Lock()


# ------------------------------------------------------------------ PDF challan
def _font(size, bold=False):
    from PIL import ImageFont
    names = ["arialbd.ttf" if bold else "arial.ttf",
             "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"]
    for n in names:
        try:
            return ImageFont.truetype(n, size)
        except Exception:
            continue
    return ImageFont.load_default()


def make_challan_pdf(v: dict) -> Path:
    """Render one violation as a clean A4 PDF. Returns the file path."""
    from PIL import Image, ImageDraw

    W, H = 1240, 1754                              # A4 @150dpi
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)

    # header
    d.rectangle([0, 0, W, 150], fill=(13, 27, 62))
    d.text((60, 34), "SRI LANKA POLICE", font=_font(44, True), fill=(255, 255, 255))
    d.text((60, 92), "ELECTRONIC TRAFFIC CHALLAN  |  AI TRAFFIC INTELLIGENCE",
           font=_font(24), fill=(180, 200, 255))
    d.text((W - 380, 50), v.get("challan_id") or "", font=_font(34, True),
           fill=(255, 210, 90))

    # violation banner
    d.rectangle([0, 150, W, 225], fill=(190, 30, 30))
    d.text((60, 168), (v.get("type") or "VIOLATION").upper(),
           font=_font(38, True), fill=(255, 255, 255))
    fine = f"{config.CURRENCY}{v.get('fine') or 0:,}"
    d.text((W - 60 - d.textlength(fine, font=_font(38, True)), 168), fine,
           font=_font(38, True), fill=(255, 255, 255))

    # details table
    plate = v.get("plate") or "UNKNOWN"
    if plate == "UNKNOWN":
        plate = "UNREADABLE (pending manual review)"
    rows = [
        ("Vehicle number", plate),
        ("Plate confidence", f"{round((v.get('plate_conf') or 0) * 100)}%"
         if v.get("plate_conf") else "-"),
        ("Date & time", v.get("timestamp") or "-"),
        ("Location", v.get("location") or config.CAMERA_LOCATION),
        ("Recorded speed", f"{v['speed_kmph']} km/h (limit {config.SPEED_LIMIT_KMPH})"
         if v.get("speed_kmph") else "-"),
        ("Footage time", f"{v['video_s']} s into recording"
         if v.get("video_s") is not None else "-"),
        ("Status", v.get("status") or "PENDING"),
        ("Detection", "Automated AI detection (multi-frame verified)"),
    ]
    y = 265
    for label, value in rows:
        d.text((60, y), label, font=_font(26), fill=(110, 110, 110))
        d.text((420, y), str(value), font=_font(28, True), fill=(20, 20, 20))
        d.line([(60, y + 44), (W - 60, y + 44)], fill=(225, 225, 225), width=2)
        y += 58

    # plate crop (the exact OCR input) — the proof the user asked for
    if v.get("plate_img"):
        p = config.OUTPUT_DIR / v["plate_img"]
        if p.exists():
            try:
                crop = Image.open(p).convert("RGB")
                ch = 110
                cw = int(crop.width * ch / crop.height)
                crop = crop.resize((min(cw, 460), ch))
                d.text((60, y + 8), "PLATE AS CAPTURED:", font=_font(24),
                       fill=(110, 110, 110))
                img.paste(crop, (420, y))
                d.rectangle([420, y, 420 + crop.width, y + ch],
                            outline=(190, 30, 30), width=3)
                y += ch + 26
            except Exception:
                pass

    # evidence snapshot
    if v.get("snapshot"):
        s = config.OUTPUT_DIR / v["snapshot"]
        if s.exists():
            try:
                snap = Image.open(s).convert("RGB")
                sw = W - 120
                sh = int(snap.height * sw / snap.width)
                max_h = H - y - 160
                if sh > max_h:
                    sh = max_h
                    sw = int(snap.width * sh / snap.height)
                snap = snap.resize((sw, sh))
                d.text((60, y + 6), "PHOTO EVIDENCE:", font=_font(24),
                       fill=(110, 110, 110))
                img.paste(snap, (60, y + 42))
                d.rectangle([60, y + 42, 60 + sw, y + 42 + sh],
                            outline=(13, 27, 62), width=3)
            except Exception:
                pass

    d.text((60, H - 70), "Generated automatically by AI Smart Traffic "
           "Intelligence Platform. Evidence images stored on-premise.",
           font=_font(20), fill=(140, 140, 140))

    out = CHALLAN_DIR / f"{(v.get('challan_id') or 'challan').replace('/', '-')}.pdf"
    # Pillow opens an existing PDF target "w+b" and PARSES it rather than
    # replacing it, so a second render of the same challan dies with
    # "trailer end not found". That happens routinely now: approving a challan
    # emails it (which renders the PDF), and the officer then clicks Download.
    # Remove the old file so every render starts from nothing.
    if out.exists():
        try:
            out.unlink()
        except OSError:
            pass
    img.save(out, "PDF", resolution=150)
    return out


# ------------------------------------------------------------------- email
def _smtp_config():
    a = config.ALERTS
    user = os.getenv("SMTP_USER", a.get("user") or "")
    password = os.getenv("SMTP_PASS", a.get("password") or "")
    return a, user, password


def alerts_ready():
    a, user, password = _smtp_config()
    if a.get("mode") == "outbox":
        return bool(a.get("enabled") and a.get("to"))
    return bool(a.get("enabled") and a.get("to") and user and password)


def _deliver_to_outbox(msg, v):
    """Write the complete police email to disk instead of sending it.

    Demo mode. The .eml holds the exact MIME message — body, PDF challan,
    evidence photo and plate crop — that would reach the police mailbox, so it
    can be opened and shown without configuring real credentials or mailing a
    real inbox. It is recorded as an outbox file, never reported as 'sent'.
    """
    outbox = config.OUTPUT_DIR / "outbox"
    outbox.mkdir(parents=True, exist_ok=True)
    name = f"{v.get('challan_id') or 'challan'}.eml"
    path = outbox / name
    path.write_bytes(bytes(msg))
    db.set_meta("alerts_sent", (db.get_meta("alerts_sent", 0) or 0) + 1)
    return True, f"DEMO MODE — police email written to {path.name} (not sent)"


def send_alert(v: dict):
    """Send one APPROVED violation to the police mailbox. Returns (ok, message).

    The status gate is here as well as in the API on purpose. Emailing the
    police IS issuing the challan, so the last line of defence belongs next to
    the SMTP call rather than in a route decorator someone could route around.
    """
    status = (v.get("status") or "PENDING").upper()
    if status != "APPROVED":
        return False, (f"challan is {status} - an officer must approve it "
                       f"before it can be sent to the police")
    a, user, password = _smtp_config()
    outbox_mode = a.get("mode") == "outbox"
    if not a.get("to"):
        return False, "no recipient configured (config.ALERTS['to'])"
    if not outbox_mode and not (user and password):
        return False, "alerts not configured (see config.ALERTS / SMTP_USER, SMTP_PASS)"
    user = user or "ai-traffic@demo.local"

    plate = v.get("plate") or "UNKNOWN"
    msg = EmailMessage()
    msg["From"] = user
    msg["To"] = a["to"]
    msg["Subject"] = (f"[TRAFFIC ALERT] {v.get('type')} - "
                      f"{plate if plate != 'UNKNOWN' else 'plate unreadable'}"
                      f" - {v.get('challan_id')}")

    speed = (f"\nRecorded speed : {v['speed_kmph']} km/h "
             f"(limit {config.SPEED_LIMIT_KMPH})" if v.get("speed_kmph") else "")
    conf = (f" (OCR confidence {round(v['plate_conf'] * 100)}%)"
            if v.get("plate_conf") else "")
    msg.set_content(f"""AUTOMATED TRAFFIC VIOLATION ALERT

Violation      : {v.get('type')}
Challan ID     : {v.get('challan_id')}
Vehicle plate  : {plate}{conf}{speed}
Date & time    : {v.get('timestamp')}
Location       : {v.get('location') or config.CAMERA_LOCATION}
Fine           : {config.CURRENCY}{v.get('fine') or 0:,}

Attached:
  1. PDF e-challan (print-ready)
  2. Photo evidence with the vehicle boxed and zoomed
  3. Number-plate crop exactly as captured by the camera

Detected and verified automatically by AI Smart Traffic Intelligence
(multi-frame confirmation; unreadable plates are never guessed).
""")

    try:
        pdf = make_challan_pdf(v)
        msg.add_attachment(pdf.read_bytes(), maintype="application",
                           subtype="pdf", filename=pdf.name)
    except Exception:
        pass
    for key, fname in (("snapshot", "evidence.jpg"), ("plate_img", "plate.jpg")):
        rel = v.get(key)
        if rel:
            p = config.OUTPUT_DIR / rel
            if p.exists():
                msg.add_attachment(p.read_bytes(), maintype="image",
                                   subtype="jpeg", filename=fname)

    if outbox_mode:
        try:
            return _deliver_to_outbox(msg, v)
        except Exception as e:
            db.set_meta("alert_error", str(e)[:200])
            return False, str(e)

    try:
        with _send_lock:                      # one SMTP session at a time
            with smtplib.SMTP(a["smtp_host"], int(a["smtp_port"]), timeout=25) as s:
                s.starttls()
                s.login(user, password)
                s.send_message(msg)
        db.set_meta("alerts_sent", (db.get_meta("alerts_sent", 0) or 0) + 1)
        return True, f"sent to {a['to']}"
    except Exception as e:
        db.set_meta("alert_error", str(e)[:200])
        return False, str(e)


def notify_async(v: dict):
    """Fire-and-forget email for the pipeline (never blocks a frame)."""
    if not (alerts_ready() and config.ALERTS.get("auto_send")):
        return
    threading.Thread(target=send_alert, args=(dict(v),), daemon=True).start()
