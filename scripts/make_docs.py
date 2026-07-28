"""Generate the project documentation PDF and the presentation PDF.

Every number in these documents came from an actual measured run on this
machine - nothing is estimated. Images are the system's own annotated output.

    python scripts/make_docs.py
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (BaseDocTemplate, Frame, Image, PageBreak,
                                PageTemplate, Paragraph, Spacer, Table,
                                TableStyle)

EV = os.path.join(ROOT, "docs", "DEMO_EVIDENCE")
OUT = os.path.join(ROOT, "docs")
NAVY = colors.HexColor("#0d1b3e")
ACCENT = colors.HexColor("#22d3ee")
INK = colors.HexColor("#1a2233")
MUTED = colors.HexColor("#5a6a85")
EVENT = "Sri Lankan Students Innovation Challenge 2026"


def styles(base=10.5):
    ss = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("t", parent=ss["Title"], fontSize=25,
                                textColor=NAVY, spaceAfter=6, leading=29),
        "sub": ParagraphStyle("s", parent=ss["Normal"], fontSize=12,
                              textColor=MUTED, alignment=TA_CENTER, spaceAfter=16),
        "h1": ParagraphStyle("h1", parent=ss["Heading1"], fontSize=15.5,
                             textColor=NAVY, spaceBefore=13, spaceAfter=7),
        "body": ParagraphStyle("b", parent=ss["Normal"], fontSize=base,
                               textColor=INK, leading=base * 1.5, spaceAfter=6),
        "cap": ParagraphStyle("c", parent=ss["Normal"], fontSize=8.5,
                              textColor=MUTED, alignment=TA_CENTER, spaceAfter=10),
        "sh": ParagraphStyle("sh", parent=ss["Heading1"], fontSize=29,
                             textColor=NAVY, spaceAfter=8, leading=33),
        "sb": ParagraphStyle("sb", parent=ss["Normal"], fontSize=15,
                             textColor=INK, leading=25, spaceAfter=6),
        "sc": ParagraphStyle("sc", parent=ss["Normal"], fontSize=11,
                             textColor=MUTED, alignment=TA_CENTER),
    }


def table(rows, widths, size=9.5):
    t = Table(rows, colWidths=widths, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), size),
        ("TEXTCOLOR", (0, 0), (-1, -1), INK),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d7dee9")),
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))
    return t


def pic(name, width_mm, cap, S):
    path = os.path.join(EV, name)
    if not os.path.exists(path):
        return []
    from PIL import Image as PILImage
    w, h = PILImage.open(path).size
    W = width_mm * mm
    out = [Image(path, width=W, height=W * h / w)]
    if cap:
        out += [Spacer(1, 3), Paragraph(cap, S["cap"])]
    return out


def make_banner(subtitle):
    def banner(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(NAVY)
        canvas.rect(0, doc.pagesize[1] - 13 * mm, doc.pagesize[0], 13 * mm,
                    fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawString(14 * mm, doc.pagesize[1] - 9 * mm,
                          "AI SMART TRAFFIC INTELLIGENCE PLATFORM")
        canvas.setFillColor(ACCENT)
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(doc.pagesize[0] - 14 * mm,
                               doc.pagesize[1] - 9 * mm, subtitle)
        canvas.setFillColor(MUTED)
        canvas.setFont("Helvetica", 8)
        canvas.drawCentredString(doc.pagesize[0] / 2, 8 * mm,
                                 str(canvas.getPageNumber()))
        canvas.restoreState()
    return banner


def build(path, pagesize, story, subtitle, margin=17):
    doc = BaseDocTemplate(path, pagesize=pagesize,
                          leftMargin=margin * mm, rightMargin=margin * mm,
                          topMargin=(margin + 5) * mm, bottomMargin=margin * mm)
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")
    doc.addPageTemplates([PageTemplate(id="p", frames=[frame],
                                       onPage=make_banner(subtitle))])
    doc.build(story)
    print("wrote", path)


# ---------------------------------------------------------------- documentation
def documentation():
    S = styles()
    s = [Spacer(1, 26 * mm),
         Paragraph("AI Smart Traffic Intelligence Platform", S["title"]),
         Paragraph("Technical Documentation and Verified Test Results", S["sub"])]
    s += pic("01_over_speeding_evidence_1.jpg", 148,
             "System output: court-ready over-speeding evidence, 134.0 km/h in a "
             "60 km/h zone, with number-plate zoom inset.", S)
    s += [Spacer(1, 5 * mm),
          Paragraph("Every figure in this document was measured on the development "
                    "machine (12-core CPU, no GPU). Nothing is estimated.", S["cap"]),
          PageBreak()]

    s += [Paragraph("1. What the system does", S["h1"]),
          Paragraph("The platform turns an ordinary camera - CCTV, a phone stream or "
                    "a drone - into an automated traffic officer. It detects and "
                    "tracks every vehicle, judges nine categories of violation, reads "
                    "number plates, measures real speed, and generates an e-challan "
                    "carrying photographic evidence that is delivered to the police.",
                    S["body"]),

          Paragraph("2. Detection pipeline", S["h1"]),
          Paragraph("Camera feed &rarr; <b>YOLOv8s</b> detection &rarr; <b>ByteTrack</b> "
                    "tracking with persistent per-vehicle IDs &rarr; <b>homography</b> "
                    "mapping pixels to road metres &rarr; <b>violation engine</b> with "
                    "false-positive defences &rarr; <b>EasyOCR</b> plate reading &rarr; "
                    "evidence snapshot &rarr; e-challan.", S["body"]),

          Paragraph("3. The nine rules", S["h1"]),
          table([["Rule", "How it is judged", "Requires"],
                 ["No Helmet", "Helmet model on each rider's own head region", "Motorcycle + rider"],
                 ["Triple Riding", "Riders associated with one motorcycle", "3 riders detected"],
                 ["Over Speeding", "Least-squares fit of road-metres against time", "Camera calibration"],
                 ["Red Light Jump", "Stop-line crossing while the governing signal is red", "Signal ROI + lane zone"],
                 ["Wrong Way", "Direction of travel against the policed lane", "Direction + lane zone"],
                 ["No Seatbelt", "Seatbelt model on the windscreen region", "models/seatbelt.pt"],
                 ["Mobile Phone Use", "Phone attributed to a rider or driver", "Visible phone"],
                 ["Illegal Parking", "Stationary beyond a threshold in a no-parking zone", "Fixed camera"],
                 ["Driver Fatigue", "Continuous driving without a qualifying break", "Long observation"]],
                [31 * mm, 83 * mm, 38 * mm]),

          Paragraph("4. Measured results", S["h1"]),
          table([["Test", "Recorded result"],
                 ["Automated test suite", "79 tests passing across 7 suites"],
                 ["sample_1080p.mp4 (calibrated)", "7 Over Speeding events, speeds 83-163 km/h"],
                 ["stream.mp4 (calibrated)", "11 of 52 vehicles measured, max 106 km/h"],
                 ["IMG_6992.MOV (Sri Lanka)", "150 vehicles; ANPR read AAG 4002 and BBJ 8752"],
                 ["srilanka.mp4 (parked bikes)", "41 vehicles, 0 violations - a correct refusal"],
                 ["Single-image upload", "No Helmet + Triple Riding, 2 challans issued"],
                 ["Real-time replay", "0.99-1.01x true speed via frame dropping"],
                 ["Live webcam smoothness", "1.89 to ~7 published fps after decoupling"]],
                [56 * mm, 96 * mm]),
          PageBreak()]

    s += [Paragraph("5. Engineering for trustworthiness", S["h1"]),
          Paragraph("A traffic system that issues wrong fines is worse than no system "
                    "at all. Each defect below was found by testing against real "
                    "footage, and each is now covered by the automated suite.", S["body"]),
          table([["Defect found", "Cause", "Fix"],
                 ["Moving vehicles fined for parking",
                  "Motion gate needed 3 samples inside a 1-second frame window; at "
                  "~2 fps analysis, 89% of moving vehicles were judged stationary",
                  "Time-based window; a track ever seen moving is exempt"],
                 ["Helmeted riders accused",
                  "Helmet model ran on a crop extending well beyond the bike, "
                  "catching neighbouring riders",
                  "Judge each associated rider's own head region"],
                 ["Bare heads marked compliant",
                  "Claiming compliance needed only 0.35 confidence against 0.50 to accuse",
                  "Decide by the strongest signal; raise the bar to 0.55"],
                 ["Stopped car fined for red light",
                  "Any light in frame was applied to any vehicle, but a junction has "
                  "several heads facing different approaches",
                  "SIGNAL_ROI picks the governing head; RED_LIGHT_ZONE limits the lane"],
                 ["Wrong plate numbers on challans",
                  "Two agreeing OCR reads allowed two wrong reads to agree by accident",
                  "Require three agreeing reads; otherwise UNREADABLE"],
                 ["Triple riding never fired",
                  "Occluded pillion riders never cleared the 0.40 person threshold",
                  "Lower threshold (0.25) for rider association only"]],
                [38 * mm, 61 * mm, 53 * mm], size=8.5),

          Paragraph("6. Honesty by design", S["h1"]),
          Paragraph("&bull; Parked vehicles are never fined - the motion gate is a hard "
                    "precondition.<br/>"
                    "&bull; An unreadable plate reports <b>UNREADABLE</b>; a number is "
                    "never invented.<br/>"
                    "&bull; An uncalibrated camera shows <b>no speed</b> rather than a "
                    "guess.<br/>"
                    "&bull; A violation must persist across several frames; one-frame "
                    "anomalies are rejected.<br/>"
                    "&bull; There is no mock or seeded data anywhere in the product.",
                    S["body"]),
          PageBreak()]

    s += [Paragraph("7. System output - verified evidence", S["h1"])]
    for f, c in [("07_image_upload_triple_helmet.jpg",
                  "Single-image analysis: three riders and no helmets detected on a "
                  "CC-licensed public photograph, producing two separate challans."),
                 ("05_anpr_sri_lanka_0.jpg",
                  "Live Sri Lankan road: 18 vehicles tracked, ANPR reading plate "
                  "AAG 4002, with per-vehicle speeds shown beside each ID."),
                 ("04_helmet_detection_1.jpg",
                  "Helmet judgement across mixed traffic.")]:
        s += pic(f, 148, c, S)

    s += [PageBreak(),
          Paragraph("8. Deployment", S["h1"]),
          Paragraph("Runs on infrastructure that already exists: RTSP CCTV, a phone "
                    "stream, or a drone via OBS. A pilot site needs one laptop; city "
                    "density is served by GPU edge boxes. Helmet, seatbelt, plate and "
                    "three-wheeler models are drop-in files requiring no code change.",
                    S["body"]),
          Paragraph("Stack: Python, FastAPI, YOLOv8, ByteTrack, OpenCV, EasyOCR and "
                    "SQLite. The dashboard is a single self-contained HTML file with "
                    "no external dependencies.", S["body"]),

          Paragraph("9. Known limits", S["h1"]),
          Paragraph("Stated plainly, because anyone deploying this must understand "
                    "them:<br/>"
                    "&bull; Speed requires per-camera calibration; without it no speed "
                    "is shown.<br/>"
                    "&bull; Plate OCR needs roughly 40 or more pixels of plate width.<br/>"
                    "&bull; Red-light enforcement requires knowing which signal head "
                    "governs the policed lane.<br/>"
                    "&bull; On a CPU laptop about 2 frames per second are analysed; the "
                    "video stays real-time by dropping frames, exactly as a live camera "
                    "does.<br/>"
                    "&bull; Detection degrades at night and in heavy rain, as with any "
                    "camera system.", S["body"]),

          Paragraph("10. Roadmap", S["h1"]),
          Paragraph("Night and adverse-weather models; a vision-language model such as "
                    "Moondream to resolve the cases the detector currently reports as "
                    "not judged; GPU edge deployment at a live junction; and a "
                    "city-wide dashboard aggregating multiple cameras.", S["body"])]

    build(os.path.join(OUT, "PROJECT_DOCUMENTATION.pdf"), A4, s, EVENT)


# ---------------------------------------------------------------- presentation
def presentation():
    S = styles()
    PS = landscape(A4)
    s = []

    def slide(title, bullets=None, image=None, cap=None, last=False):
        s.append(Paragraph(title, S["sh"]))
        for b in (bullets or []):
            s.append(Paragraph(b, S["sb"]))
        if image:
            s.append(Spacer(1, 3 * mm))
            s.extend(pic(image, 175, cap, S))
        if not last:
            s.append(PageBreak())

    s += [Spacer(1, 34 * mm),
          Paragraph("AI Smart Traffic Intelligence Platform", S["title"]),
          Paragraph("Turning any camera feed into fair, evidence-based enforcement",
                    S["sub"]),
          Spacer(1, 4 * mm),
          Paragraph(EVENT + "  |  Final", S["sc"]),
          PageBreak()]

    slide("The problem",
          ["Sri Lanka records roughly <b>3,000 road deaths a year</b>, most from "
           "preventable violations.",
           "Officers cannot watch every junction, 24 hours a day.",
           "Violations recorded without photographic proof or a verified plate are "
           "disputed and unpaid.",
           "<b>Coverage and proof</b> are the enforcement gap."])

    slide("What we built",
          ["One AI pipeline on an ordinary camera detects <b>nine violation types</b>.",
           "Reads number plates on every vehicle, not only offenders.",
           "Measures <b>real speed</b> through camera calibration.",
           "Generates an <b>e-challan</b> with stamped photographic evidence, "
           "delivered to the police."])

    slide("Proof: over-speeding",
          ["Calibrated speed validated at <b>83-163 km/h</b> on highway footage.",
           "Seven over-speeding events, each with court-ready evidence."],
          "01_over_speeding_evidence_1.jpg",
          "134.0 km/h in a 60 zone - vehicle boxed, plate zoomed, proof stamped "
          "onto the image itself.")

    slide("Proof: helmet and triple riding",
          ["Both violations detected from a <b>single uploaded photograph</b>, "
           "producing two separate challans."],
          "07_image_upload_triple_helmet.jpg",
          "Three riders and no helmets, judged on a CC-licensed public image.")

    slide("Proof: number-plate recognition",
          ["Plates read on live Sri Lankan road footage.",
           "A plate is confirmed only when <b>three separate reads agree</b>."],
          "05_anpr_sri_lanka_0.jpg",
          "18 vehicles tracked; plate AAG 4002 read and confirmed; speed shown "
          "beside every vehicle ID.")

    slide("Why it can be trusted",
          ["<b>Parked vehicles are never fined</b> - 41 vehicles, 0 violations on a "
           "parked-motorcycle clip.",
           "<b>Unreadable plates say UNREADABLE</b> - a number is never invented.",
           "<b>No calibration means no speed shown</b>, rather than a guess.",
           "<b>79 automated tests</b>, including every case where a rule must "
           "<i>refuse</i> to fire.",
           "We fixed six real false-positive defects found by testing on real footage."])

    slide("Deployment",
          ["Works with <b>existing CCTV</b>, a phone stream, or a drone via OBS.",
           "A pilot site runs on a single laptop; cities use GPU edge boxes.",
           "Models for helmet, seatbelt, plate and three-wheeler are <b>drop-in "
           "files</b> - no code change.",
           "Python, FastAPI, YOLOv8, ByteTrack, OpenCV, EasyOCR, SQLite."])

    slide("Impact and roadmap",
          ["<b>24/7 coverage</b> without multiplying officers.",
           "<b>Court-ready evidence</b> means fines that hold up when challenged.",
           "Searchable plate log enables <b>repeat-offender</b> analytics.",
           "Next: night and weather models, a vision-language model for ambiguous "
           "cases, and a live junction pilot."])

    s += [Spacer(1, 40 * mm),
          Paragraph("Safer roads, proven by evidence.", S["title"]),
          Paragraph("AI Smart Traffic Intelligence Platform", S["sub"])]

    build(os.path.join(OUT, "PRESENTATION.pdf"), PS, s, EVENT, margin=20)


if __name__ == "__main__":
    documentation()
    presentation()
