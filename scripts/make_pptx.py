"""Generate the PowerPoint deck (docs/PRESENTATION.pptx).

Widescreen 16:9, dark theme matching the dashboard. Every image is the
system's own annotated output and every figure is a measured result.

    python scripts/make_pptx.py
"""
import os

from PIL import Image as PILImage
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Emu, Inches, Pt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
EV = os.path.join(ROOT, "docs", "DEMO_EVIDENCE")

W, H = Inches(13.333), Inches(7.5)          # 16:9
NAVY = RGBColor(0x0B, 0x14, 0x28)
PANEL = RGBColor(0x11, 0x1E, 0x3D)
CYAN = RGBColor(0x22, 0xD3, 0xEE)
WHITE = RGBColor(0xF2, 0xF6, 0xFF)
MUTED = RGBColor(0x9F, 0xB3, 0xD1)
GOLD = RGBColor(0xFF, 0xC7, 0x4D)
GREEN = RGBColor(0x4A, 0xDE, 0x80)


def bg(slide, colour=NAVY):
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = colour


def box(slide, x, y, w, h, text, size=18, colour=WHITE, bold=False,
        align=PP_ALIGN.LEFT, font="Segoe UI", space=6):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    lines = text if isinstance(text, list) else [text]
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(space)
        # inline **bold** segments
        for j, seg in enumerate(str(line).split("**")):
            if not seg:
                continue
            r = p.add_run()
            r.text = seg
            r.font.size = Pt(size)
            r.font.name = font
            r.font.color.rgb = colour
            r.font.bold = bold or (j % 2 == 1)
    return tb


def accent_bar(slide):
    s = slide.shapes.add_shape(1, 0, 0, W, Inches(0.09))
    s.fill.solid()
    s.fill.fore_color.rgb = CYAN
    s.line.fill.background()
    s.shadow.inherit = False


def picture(slide, name, x, y, max_w, max_h):
    """Place an image scaled to fit the given box, centred horizontally."""
    path = os.path.join(EV, name)
    if not os.path.exists(path):
        return None
    iw, ih = PILImage.open(path).size
    scale = min(max_w / iw, max_h / ih)
    w, h = int(iw * scale), int(ih * scale)
    return slide.shapes.add_picture(path, x + int((max_w - w) / 2), y,
                                    width=w, height=h)


def header(slide, title, kicker=None):
    accent_bar(slide)
    if kicker:
        box(slide, Inches(0.7), Inches(0.42), Inches(11), Inches(0.4),
            kicker, size=13, colour=CYAN, bold=True)
    box(slide, Inches(0.7), Inches(0.78), Inches(12), Inches(1.0),
        title, size=34, colour=WHITE, bold=True)


def stat(slide, x, y, value, label, colour=GOLD, w=Inches(2.9)):
    card = slide.shapes.add_shape(1, x, y, w, Inches(1.35))
    card.fill.solid()
    card.fill.fore_color.rgb = PANEL
    card.line.color.rgb = RGBColor(0x29, 0x4A, 0x8F)
    card.shadow.inherit = False
    box(slide, x, y + Inches(0.14), w, Inches(0.6), value, size=30,
        colour=colour, bold=True, align=PP_ALIGN.CENTER)
    box(slide, x, y + Inches(0.78), w, Inches(0.5), label, size=11.5,
        colour=MUTED, align=PP_ALIGN.CENTER)


def main():
    prs = Presentation()
    prs.slide_width, prs.slide_height = W, H
    blank = prs.slide_layouts[6]

    # 1 — title
    s = prs.slides.add_slide(blank); bg(s); accent_bar(s)
    box(s, Inches(0.9), Inches(2.1), Inches(11.5), Inches(1.3),
        "AI Smart Traffic Intelligence Platform", size=44, colour=WHITE, bold=True)
    box(s, Inches(0.9), Inches(3.5), Inches(11.5), Inches(0.7),
        "Turning any camera feed into fair, evidence-based enforcement",
        size=20, colour=CYAN)
    box(s, Inches(0.9), Inches(4.5), Inches(11.5), Inches(0.6),
        "Sri Lankan Students Innovation Challenge 2026  |  Final",
        size=15, colour=MUTED)
    for i, (v, l) in enumerate([("9", "violation types"), ("79", "automated tests"),
                                ("83-163", "km/h verified")]):
        stat(s, Inches(0.9 + i * 3.15), Inches(5.4), v, l)

    # 2 — problem
    s = prs.slides.add_slide(blank); bg(s)
    header(s, "The problem", "WHY THIS MATTERS")
    box(s, Inches(0.8), Inches(2.1), Inches(11.6), Inches(3.6),
        ["Sri Lanka records roughly **3,000 road deaths a year**, most from preventable violations.",
         "Officers cannot watch every junction, 24 hours a day.",
         "Violations recorded **without photographic proof or a verified plate** are disputed and unpaid.",
         "No searchable record means repeat offenders go unnoticed."],
        size=19, colour=WHITE, space=16)
    box(s, Inches(0.8), Inches(6.0), Inches(11.6), Inches(0.7),
        "Coverage and proof are the enforcement gap.", size=20, colour=GOLD, bold=True)

    # 3 — solution
    s = prs.slides.add_slide(blank); bg(s)
    header(s, "What we built", "THE SOLUTION")
    box(s, Inches(0.8), Inches(2.05), Inches(11.6), Inches(3.2),
        ["One AI pipeline on an ordinary camera detects **nine violation types**.",
         "Reads **number plates on every vehicle**, not only offenders.",
         "Measures **real speed** through per-camera geometric calibration.",
         "Generates an **e-challan with stamped photographic evidence**, delivered to police."],
        size=19, colour=WHITE, space=15)
    box(s, Inches(0.8), Inches(5.5), Inches(11.6), Inches(0.9),
        "Camera  ->  YOLOv8s  ->  ByteTrack  ->  Homography  ->  Violation engine  "
        "->  ANPR  ->  e-Challan", size=15, colour=CYAN, bold=True)

    # 4 — nine rules
    s = prs.slides.add_slide(blank); bg(s)
    header(s, "Nine violations, one pipeline", "CAPABILITY")
    rules = [("No Helmet", GREEN), ("Triple Riding", GREEN), ("Over Speeding", GREEN),
             ("Red Light Jump", GREEN), ("Wrong Way", GREEN), ("No Seatbelt", GREEN),
             ("Mobile Phone Use", GREEN), ("Illegal Parking", GREEN),
             ("Driver Fatigue", GREEN)]
    for i, (name, col) in enumerate(rules):
        cx = Inches(0.8 + (i % 3) * 4.0)
        cy = Inches(2.2 + (i // 3) * 1.25)
        card = s.shapes.add_shape(1, cx, cy, Inches(3.7), Inches(1.0))
        card.fill.solid(); card.fill.fore_color.rgb = PANEL
        card.line.color.rgb = RGBColor(0x29, 0x4A, 0x8F); card.shadow.inherit = False
        box(s, cx, cy + Inches(0.28), Inches(3.7), Inches(0.5), name,
            size=17, colour=WHITE, bold=True, align=PP_ALIGN.CENTER)
    box(s, Inches(0.8), Inches(6.2), Inches(11.6), Inches(0.6),
        "Plus ANPR on every tracked vehicle, building a searchable log.",
        size=15, colour=MUTED, align=PP_ALIGN.CENTER)

    # 5 — evidence: over-speeding
    s = prs.slides.add_slide(blank); bg(s)
    header(s, "Proof: over-speeding", "VERIFIED OUTPUT")
    picture(s, "01_over_speeding_evidence_1.jpg", Inches(1.4), Inches(1.95),
            Inches(10.5), Inches(4.3))
    box(s, Inches(0.8), Inches(6.45), Inches(11.6), Inches(0.8),
        "134.0 km/h in a 60 zone - vehicle boxed, plate zoomed, proof stamped onto "
        "the image. **7 over-speeding events** measured at **83-163 km/h**.",
        size=14.5, colour=MUTED, align=PP_ALIGN.CENTER)

    # 6 — evidence: helmet + triple
    s = prs.slides.add_slide(blank); bg(s)
    header(s, "Proof: helmet and triple riding", "VERIFIED OUTPUT")
    picture(s, "07_image_upload_triple_helmet.jpg", Inches(1.4), Inches(1.95),
            Inches(10.5), Inches(4.3))
    box(s, Inches(0.8), Inches(6.45), Inches(11.6), Inches(0.8),
        "Both violations detected from a **single uploaded photograph**, producing "
        "**two separate challans**.", size=14.5, colour=MUTED, align=PP_ALIGN.CENTER)

    # 7 — evidence: ANPR
    s = prs.slides.add_slide(blank); bg(s)
    header(s, "Proof: number-plate recognition", "VERIFIED OUTPUT")
    picture(s, "05_anpr_sri_lanka_0.jpg", Inches(1.4), Inches(1.95),
            Inches(10.5), Inches(4.3))
    box(s, Inches(0.8), Inches(6.45), Inches(11.6), Inches(0.8),
        "Live Sri Lankan road: 18 vehicles tracked, plate **AAG 4002** read and "
        "confirmed. A plate counts only when **three separate reads agree**.",
        size=14.5, colour=MUTED, align=PP_ALIGN.CENTER)

    # 8 — trust
    s = prs.slides.add_slide(blank); bg(s)
    header(s, "Why it can be trusted", "THE DIFFERENTIATOR")
    box(s, Inches(0.8), Inches(1.95), Inches(11.6), Inches(3.4),
        ["**Parked vehicles are never fined** - 41 vehicles, 0 violations on a parked-motorcycle clip.",
         "**Unreadable plates say UNREADABLE** - a number is never invented.",
         "**No calibration means no speed shown**, rather than a misleading guess.",
         "**A violation must persist across frames** - one-frame anomalies are rejected.",
         "**No mock data exists** anywhere in the product."],
        size=17.5, colour=WHITE, space=13)
    for i, (v, l, c) in enumerate([("6", "false-positive defects found and fixed", GOLD),
                                   ("79", "automated tests passing", GREEN),
                                   ("0", "violations on parked bikes", CYAN)]):
        stat(s, Inches(0.9 + i * 3.9), Inches(5.55), v, l, colour=c, w=Inches(3.6))

    # 9 — engineering rigour
    s = prs.slides.add_slide(blank); bg(s)
    header(s, "Found by testing on real footage", "ENGINEERING RIGOUR")
    rows = [("Moving vehicles fined for parking",
             "Motion gate misjudged 89% of moving vehicles as stationary"),
            ("Helmeted riders accused of no helmet",
             "Helmet crop caught neighbouring riders"),
            ("Bare heads marked compliant",
             "Compliance threshold lower than the accusation threshold"),
            ("Stopped car fined for a red light",
             "Signal from a different approach was applied to it"),
            ("Wrong plate numbers on challans",
             "Two agreeing OCR reads could both be wrong")]
    for i, (defect, cause) in enumerate(rows):
        y = Inches(2.05 + i * 0.95)
        box(s, Inches(0.85), y, Inches(5.3), Inches(0.8), defect,
            size=15, colour=WHITE, bold=True)
        box(s, Inches(6.4), y, Inches(6.2), Inches(0.8), cause,
            size=13.5, colour=MUTED)
    box(s, Inches(0.85), Inches(6.85), Inches(11.6), Inches(0.5),
        "Each is now covered by the automated test suite.",
        size=14, colour=CYAN, bold=True)

    # 10 — deployment
    s = prs.slides.add_slide(blank); bg(s)
    header(s, "Deployment", "PRACTICAL AND MODULAR")
    box(s, Inches(0.8), Inches(2.05), Inches(11.6), Inches(3.4),
        ["Works with **existing CCTV**, a phone stream, or a drone via OBS - no new hardware.",
         "A pilot site runs on a **single laptop**; cities use GPU edge boxes.",
         "Helmet, seatbelt, plate and three-wheeler models are **drop-in files** - no code change.",
         "Python, FastAPI, YOLOv8, ByteTrack, OpenCV, EasyOCR, SQLite.",
         "The dashboard is a **single self-contained HTML file** with no external dependencies."],
        size=18, colour=WHITE, space=14)

    # 11 — impact
    s = prs.slides.add_slide(blank); bg(s)
    header(s, "Impact and roadmap", "WHERE THIS GOES")
    box(s, Inches(0.8), Inches(2.05), Inches(11.6), Inches(3.2),
        ["**24/7 coverage** without multiplying officers.",
         "**Court-ready evidence** means fines that hold up when challenged.",
         "A searchable plate log enables **repeat-offender analytics**.",
         "Next: night and weather models, a vision-language model for ambiguous cases, "
         "and a live junction pilot."],
        size=18.5, colour=WHITE, space=15)
    box(s, Inches(0.8), Inches(5.9), Inches(11.6), Inches(0.9),
        "Colombo already has over a hundred road cameras. We turn each one into a "
        "traffic officer.", size=17, colour=GOLD, bold=True)

    # 12 — close
    s = prs.slides.add_slide(blank); bg(s); accent_bar(s)
    box(s, Inches(0.9), Inches(2.9), Inches(11.5), Inches(1.2),
        "Safer roads, proven by evidence.", size=42, colour=WHITE, bold=True)
    box(s, Inches(0.9), Inches(4.2), Inches(11.5), Inches(0.6),
        "AI Smart Traffic Intelligence Platform", size=19, colour=CYAN)
    box(s, Inches(0.9), Inches(5.0), Inches(11.5), Inches(0.6),
        "github.com/Jeba-Jebarsan/AI-SMART-TRAFFIC-INTELLIGENCE",
        size=14, colour=MUTED)

    out = os.path.join(ROOT, "docs", "PRESENTATION.pptx")
    prs.save(out)
    print("wrote", out, "|", len(prs.slides.__iter__.__self__._sldIdLst), "slides")


if __name__ == "__main__":
    main()
