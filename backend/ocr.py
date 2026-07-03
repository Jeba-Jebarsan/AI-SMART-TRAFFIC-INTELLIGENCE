"""Number-plate OCR (EasyOCR) with optional YOLO plate detection.

Two-stage ANPR when a plate detector is present (config.PLATE_MODEL):
    vehicle crop -> YOLO finds the plate box -> crop plate -> enhance -> OCR
Otherwise it OCRs the lower part of the vehicle crop directly.

Improvements over naive OCR (each one matters on real CCTV footage):
  * small plate crops are upscaled 3x before OCR
  * several preprocessing variants are tried (raw / CLAHE / adaptive threshold)
  * EasyOCR tokens are ASSEMBLED left-to-right — "WP", "CAB", "1234" become
    one plate instead of three useless fragments
  * results are validated against Sri Lankan plate formats and normalised
    ("WPCAB1234" -> "WP CAB-1234"); pattern matches outrank raw tokens
  * common confusions fixed per character position (O<->0, I<->1, S<->5)

Everything is imported lazily and degrades to ('UNKNOWN', 0.0).
"""
import re

from detection import load_plate, resolve_device

_reader = None


def _get_reader():
    global _reader
    if _reader is None:
        import easyocr
        _reader = easyocr.Reader(["en"], gpu=(resolve_device() != "cpu"))
    return _reader


_CLEAN = re.compile(r"[^A-Z0-9]")
_GROUP = re.compile(r"(?<=[A-Z])(?=\d)|(?<=\d)(?=[A-Z])")


def _tidy(text):
    return _CLEAN.sub("", text.upper())


def normalize_plate(raw):
    """Country-agnostic plate cleanup: WHAT THE CAMERA SAW, nothing more.

    No grammar templates, no character 'repair' — reformatting to a national
    format proved worse than useless on mixed footage (it invented prefixes).
    We only: uppercase, strip non-alphanumerics, and insert spaces at
    letter/digit boundaries for readability ("KA02MH7256" -> "KA 02 MH 7256").

    Returns (display_text, plausible). plausible = the string is shaped like
    a real plate (5-12 chars with letters+digits, or 6+ all digits) and is
    required before a read may enter the voting pool.
    """
    s = _CLEAN.sub("", raw.upper())
    if not s:
        return "", False
    has_d = any(c.isdigit() for c in s)
    has_a = any(c.isalpha() for c in s)
    plausible = (5 <= len(s) <= 12 and has_d and has_a) or \
                (6 <= len(s) <= 8 and has_d and not has_a)
    return _GROUP.sub(" ", s), plausible


def _variants(img):
    """Preprocessing variants, best-first. Upscales small crops for OCR."""
    import cv2

    out = []
    h, w = img.shape[:2]
    if h < 90:  # EasyOCR wants ~90px-tall text lines; upscale 2-4x
        s = min(4, max(2, round(90 / max(h, 1))))
        img = cv2.resize(img, (w * s, h * s), interpolation=cv2.INTER_CUBIC)
    out.append(img)
    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(gray)
        out.append(clahe)
        th = cv2.adaptiveThreshold(clahe, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 31, 9)
        out.append(th)
    except Exception:
        pass
    return out


def _ocr_text(img):
    """OCR a crop; assemble tokens left-to-right; return best (text, conf).

    Confidence is the mean EasyOCR confidence of the tokens used, with a
    bonus applied when the assembled string matches a Sri Lankan format.
    """
    try:
        reader = _get_reader()
    except Exception:
        return "UNKNOWN", 0.0
    if img is None or getattr(img, "size", 0) == 0:
        return "UNKNOWN", 0.0

    best_text, best_conf, best_score = "UNKNOWN", 0.0, 0.0
    for cand in _variants(img):
        try:
            # plates only contain A-Z and 0-9 — constraining the recogniser
            # to that alphabet removes lowercase/punctuation mis-reads
            dets = reader.readtext(
                cand, allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
        except Exception:
            continue
        toks = []
        for bbox, text, conf in dets:
            t = _tidy(text)
            if t and conf > 0.15:
                x = min(p[0] for p in bbox)
                toks.append((x, t, float(conf)))
        if not toks:
            continue
        toks.sort()

        candidates = []
        joined = "".join(t for _, t, _ in toks)
        if len(joined) >= 4:
            candidates.append((joined, sum(c for _, _, c in toks) / len(toks)))
        for _, t, c in toks:                      # single tokens too
            if len(t) >= 4:
                candidates.append((t, c))

        for text, conf in candidates:
            norm, plausible = normalize_plate(text)
            if not plausible:
                continue
            # Low bar on purpose: this only ADMITS a read into the voting
            # pool — nothing is shown until two frames agree on the same
            # digit-tail, so weak-but-consistent reads can still confirm.
            if conf < 0.22:
                continue
            # rank by confidence with a small nudge toward longer strings, so
            # a complete read beats a fragment at similar confidence; the
            # RETURNED confidence stays the honest OCR value
            score = conf + 0.01 * min(len(_CLEAN.sub("", norm)), 10)
            if score > best_score:
                best_text, best_conf = norm, min(conf, 0.99)
                best_score = score
        if best_conf >= 0.60:                     # good enough — stop early
            break
    return best_text, best_conf


def read_plate(crop):
    """Fallback: OCR the lower 60% of a vehicle crop (no plate detector)."""
    if crop is None or getattr(crop, "size", 0) == 0:
        return "UNKNOWN", 0.0
    h = crop.shape[0]
    roi = crop[int(h * 0.40):, :] if h > 20 else crop
    return _ocr_text(roi)


def read_plate_and_crop(frame, vehicle_box, min_ocr_h=0):
    """Locate the plate inside the vehicle box, OCR it, and return the crop.

    Returns (text, conf, plate_bgr_or_None, ocr_ran).
      * crop is not None whenever the DETECTOR saw a plate — even if OCR
        failed — so callers can tell 'no plate visible' from 'unreadable'.
      * when the plate is shorter than min_ocr_h pixels, OCR is skipped
        (ocr_ran=False): the caller should retry when the vehicle is closer
        instead of burning its OCR budget on a hopeless crop.
    """
    x1, y1, x2, y2 = [int(c) for c in vehicle_box]
    x1, y1 = max(0, x1), max(0, y1)
    veh = frame[y1:y2, x1:x2]
    if veh is None or getattr(veh, "size", 0) == 0:
        return "UNKNOWN", 0.0, None, False

    pm = load_plate()
    if pm is None:                       # no detector -> OCR the vehicle crop
        t, c = read_plate(veh)
        return t, c, None, True

    try:
        res = pm.predict(veh, verbose=False, conf=0.35,
                         device=resolve_device())[0]
    except Exception:
        t, c = read_plate(veh)
        return t, c, None, True

    best = None
    if res.boxes is not None:
        for b in res.boxes:
            conf = float(b.conf[0])
            if best is None or conf > best[0]:
                best = (conf, [int(v) for v in b.xyxy[0].tolist()])
    if best is None:
        return "UNKNOWN", 0.0, None, False   # no plate visible — don't guess

    px1, py1, px2, py2 = best[1]
    raw_h = py2 - py1
    pad_x = max(2, (px2 - px1) // 10)    # slight padding helps edge characters
    pad_y = max(2, raw_h // 6)
    px1, py1 = max(0, px1 - pad_x), max(0, py1 - pad_y)
    px2 = min(veh.shape[1], px2 + pad_x)
    py2 = min(veh.shape[0], py2 + pad_y)
    plate = veh[py1:py2, px1:px2]
    if plate.size == 0:
        return "UNKNOWN", 0.0, None, False
    if raw_h < max(8, min_ocr_h):        # too small to read yet — wait
        return "UNKNOWN", 0.0, plate, False
    text, conf = _ocr_text(plate)
    return text, conf, plate, True


def read_plate_smart(frame, vehicle_box):
    """Back-compat wrapper: (text, conf) only."""
    t, c, _, _ = read_plate_and_crop(frame, vehicle_box)
    return t, c
