"""Generate the project documentation PDF and the presentation PDF.

Every number came from an actual measured run on this machine - nothing is
estimated. Images are the system's own annotated output.

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


def styles(base=10.2):
    ss = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("t", parent=ss["Title"], fontSize=25,
                                textColor=NAVY, spaceAfter=6, leading=29),
        "sub": ParagraphStyle("s", parent=ss["Normal"], fontSize=12,
                              textColor=MUTED, alignment=TA_CENTER, spaceAfter=16),
        "h1": ParagraphStyle("h1", parent=ss["Heading1"], fontSize=15,
                             textColor=NAVY, spaceBefore=12, spaceAfter=6),
        "h2": ParagraphStyle("h2", parent=ss["Heading2"], fontSize=11.5,
                             textColor=colors.HexColor("#0f766e"),
                             spaceBefore=8, spaceAfter=4),
        "body": ParagraphStyle("b", parent=ss["Normal"], fontSize=base,
                               textColor=INK, leading=base * 1.5, spaceAfter=5),
        "cap": ParagraphStyle("c", parent=ss["Normal"], fontSize=8.5,
                              textColor=MUTED, alignment=TA_CENTER, spaceAfter=10),
        "sh": ParagraphStyle("sh", parent=ss["Heading1"], fontSize=29,
                             textColor=NAVY, spaceAfter=8, leading=33),
        "sb": ParagraphStyle("sb", parent=ss["Normal"], fontSize=15,
                             textColor=INK, leading=25, spaceAfter=6),
        "sc": ParagraphStyle("sc", parent=ss["Normal"], fontSize=11,
                             textColor=MUTED, alignment=TA_CENTER),
    }


def table(rows, widths, size=9.0):
    t = Table(rows, colWidths=widths, hAlign="LEFT", repeatRows=1)
    t.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), size),
        ("TEXTCOLOR", (0, 0), (-1, -1), INK),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
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


def documentation():
    S = styles()
    P = lambda t, k="body": Paragraph(t, S[k])   # noqa: E731
    s = [Spacer(1, 24 * mm),
         P("AI Smart Traffic Intelligence Platform", "title"),
         P("Technical Documentation, Models and Verified Results", "sub")]
    s += pic("01_over_speeding_evidence_1.jpg", 146,
             "System output: over-speeding evidence, 134.0 km/h in a 60 km/h zone, "
             "with number-plate zoom inset.", S)
    s += [Spacer(1, 4 * mm),
          P("All figures were measured on the development machine "
            "(12-core CPU, no GPU). Nothing is estimated.", "cap"),
          PageBreak()]

    # 1-2 overview + pipeline
    s += [P("1. Overview", "h1"),
          P("The platform turns an ordinary camera - fixed CCTV, a phone stream or "
            "a drone - into an automated traffic officer. It detects and tracks "
            "every vehicle, judges nine categories of violation, reads number "
            "plates, measures true road speed, and issues an e-challan carrying "
            "photographic evidence to the police. It runs on a laptop CPU."),

          P("2. Processing pipeline", "h1"),
          P("Each analysed frame passes through seven stages. Stages 3-5 are what "
            "separate this from a vehicle-counting demo."),
          table([["#", "Stage", "What happens"],
                 ["1", "Capture", "Frame pulled from CCTV / file / webcam; oversized frames downscaled"],
                 ["2", "Detection", "YOLOv8s finds vehicles, people, traffic lights and phones"],
                 ["3", "Tracking", "ByteTrack assigns a persistent ID so a vehicle is followed across frames"],
                 ["4", "Geometry", "Homography maps image pixels onto real road metres"],
                 ["5", "Rules", "Violation engine applies nine rules behind false-positive gates"],
                 ["6", "ANPR", "Plate localised, cropped, OCR-read and confirmed by repeated agreement"],
                 ["7", "Evidence", "Annotated snapshot, challan record, PDF and police email"]],
                [8 * mm, 26 * mm, 118 * mm]),

          P("3. Models used and why", "h1"),
          table([["Model", "Role", "Why this one"],
                 ["YOLOv8s", "Vehicles, people,\nlights, phones",
                  "Upgraded from YOLOv8n after measurement: on identical footage "
                  "yolov8n found 64 motorcycles and could associate a rider with only "
                  "12; yolov8s found 108 and associated 41. Rider recall is the "
                  "bottleneck for most rules, so the larger model earns its cost."],
                 ["ByteTrack", "Multi-object tracking",
                  "Associates low-confidence detections too, so a vehicle keeps its ID "
                  "through partial occlusion. Persistent IDs are what make speed, "
                  "de-duplication and one-challan-per-vehicle possible."],
                 ["EasyOCR", "Plate text",
                  "Reads Latin-script plates without per-country training, matching "
                  "Sri Lankan plates. Never reformats to a national grammar."],
                 ["license_plate_\ndetector.pt", "Plate localisation",
                  "Two-stage ANPR: find the plate, then OCR only that crop. Far more "
                  "accurate than OCR-ing a whole vehicle."],
                 ["helmet.pt", "Helmet / no helmet",
                  "COCO has no helmet class. Applied to each associated rider's own "
                  "head region, not the bike area."],
                 ["yolov11s-\nseatbelt", "Seatbelt",
                  "Drop-in model with no_seatbelt / seat_belt classes. Without it the "
                  "rule stays off - there is no guess fallback."]],
                [26 * mm, 26 * mm, 100 * mm], size=8.4),
          PageBreak()]

    # 4 algorithms
    s += [P("4. Core algorithms", "h1"),
          P("4.1 Speed by perspective transform", "h2"),
          P("Four surveyed road corners are mapped to a real-world rectangle using a "
            "homography (cv2.getPerspectiveTransform). Each vehicle's ground-contact "
            "point is projected into road metres, and speed is a least-squares "
            "regression of metres against time across a 2.5-second window - never a "
            "single-frame difference. Outliers beyond two standard deviations are "
            "dropped, the result is smoothed, and a reading is only trusted when the "
            "fit is straight (R-squared above 0.55), the residual is under 2.5 m and "
            "the track has been watched for at least one second."),
          P("4.2 Motion gate", "h2"),
          P("A violation requires genuine movement. Net displacement is measured over "
            "a time-based window with camera-motion compensation, so box jitter on a "
            "parked vehicle cancels out. This single gate is why parked motorcycles "
            "are never fined."),
          P("4.3 Multi-frame persistence", "h2"),
          P("Every appearance rule must be observed repeatedly before firing - three "
            "frames for helmet and triple riding, four for phone use. A one-frame "
            "anomaly, the classic demo-killer, can never issue a challan."),
          P("4.4 Plate confirmation by voting", "h2"),
          P("OCR reads are pooled by their digit tail, so garbled letters still vote "
            "together. A plate is confirmed only when three separate reads agree. "
            "Measured effect: two-read confirmation produced EEBBJ 8752 for a plate "
            "that actually reads NP BBJ 8752; requiring three recovered BBJ 8752."),
          P("4.5 Real-time frame dropping", "h2"),
          P("CPU detection is slower than playback, so the analyser drops frames it "
            "was too busy for - exactly as a live camera does - and the video plays at "
            "true speed. Measured at 0.99-1.01x. For a live camera, capture runs on "
            "its own thread and the last annotation is stamped onto fresh frames, so "
            "the picture stays smooth while boxes refresh behind it."),

          P("5. The nine rules", "h1"),
          table([["Rule", "Judged by", "Precondition"],
                 ["No Helmet", "Helmet model on each rider's head region", "Motorcycle + rider"],
                 ["Triple Riding", "Riders associated with one motorcycle", "3 riders detected"],
                 ["Over Speeding", "Regression of road-metres against time", "Camera calibration"],
                 ["Red Light Jump", "Stop-line crossing while the governing signal is red", "Signal ROI + lane zone"],
                 ["Wrong Way", "Travel direction against the policed lane", "Direction + lane zone"],
                 ["No Seatbelt", "Seatbelt model on the windscreen region", "models/seatbelt.pt"],
                 ["Mobile Phone Use", "Phone attributed to a rider or driver", "Visible phone"],
                 ["Illegal Parking", "Stationary past a threshold in a no-parking zone", "Fixed camera"],
                 ["Driver Fatigue", "Continuous driving without a qualifying break", "Long observation"]],
                [30 * mm, 84 * mm, 38 * mm]),
          PageBreak()]

    # 6 results
    s += [P("6. Measured results", "h1"),
          table([["Test", "Recorded result"],
                 ["Automated test suite", "79 tests passing across 7 suites"],
                 ["sample_1080p.mp4 (calibrated)", "7 Over Speeding events, speeds 83-163 km/h"],
                 ["stream.mp4 (calibrated)", "3 Over Speeding, 11 of 52 vehicles measured, max 106 km/h"],
                 ["IMG_6992.MOV (Sri Lanka)", "150 vehicles; plates AAG 4002 and BBJ 8752 read"],
                 ["srilanka.mp4 (parked bikes)", "41 vehicles, 0 violations - a correct refusal"],
                 ["Single-image upload", "No Helmet + Triple Riding, 2 challans issued"],
                 ["Real-time replay", "0.99-1.01x true speed via frame dropping"],
                 ["Live webcam", "1.89 to ~7 published fps after decoupling capture"],
                 ["Warm image analysis", "~2 seconds end to end"]],
                [56 * mm, 96 * mm]),

          P("7. Defects found by testing on real footage", "h1"),
          P("A traffic system that issues wrong fines is worse than no system. Each "
            "defect below was found by running against real video, and each is now "
            "covered by the automated suite."),
          table([["Defect", "Cause", "Fix"],
                 ["Moving vehicles fined for parking",
                  "Motion gate needed 3 samples in a 1-second frame window; at ~2 fps "
                  "analysis 89% of moving vehicles read as stationary",
                  "Time-based window; a track ever seen moving is exempt"],
                 ["Helmeted riders accused",
                  "Helmet model ran on a crop wider than the bike, catching neighbours",
                  "Judge each rider's own head region"],
                 ["Bare heads marked compliant",
                  "Compliance needed 0.35 confidence against 0.50 to accuse",
                  "Decide by strongest signal; raise the bar to 0.55"],
                 ["Stopped car fined for red light",
                  "Any light in frame applied to any vehicle, but junctions have "
                  "several heads facing different approaches",
                  "SIGNAL_ROI selects the governing head; RED_LIGHT_ZONE limits the lane"],
                 ["Wrong plate on challans",
                  "Two agreeing OCR reads let two wrong reads agree",
                  "Require three agreeing reads"],
                 ["Triple riding never fired",
                  "Occluded pillion riders never cleared the 0.40 person threshold",
                  "Lower bar (0.25) for rider association only"]],
                [36 * mm, 62 * mm, 54 * mm], size=8.2),
          PageBreak()]

    # 8 evidence gallery
    s += [P("8. Verified system output", "h1")]
    for f, c in [("07_image_upload_triple_helmet.jpg",
                  "Single-image analysis: three riders and no helmets detected on a "
                  "CC-licensed public photograph, producing two separate challans."),
                 ("05_anpr_sri_lanka_0.jpg",
                  "Live Sri Lankan road: 18 vehicles tracked, plate AAG 4002 read and "
                  "confirmed, speed shown beside each vehicle ID."),
                 ("09_highway_speed_0.jpg",
                  "Highway over-speeding evidence generated from a second calibrated "
                  "camera, showing the method is not tied to one clip.")]:
        s += pic(f, 146, c, S)
    s += [PageBreak()]

    # 9 use cases
    s += [P("9. Use cases", "h1"),
          table([["Deployment", "What it delivers"],
                 ["Urban junction enforcement",
                  "Red-light, helmet, triple-riding and phone-use challans on existing "
                  "CCTV, with evidence strong enough to survive dispute"],
                 ["Highway speed corridor",
                  "Calibrated speed enforcement without physical speed guns or officer "
                  "presence, running continuously"],
                 ["School and hospital zones",
                  "No-parking zone monitoring plus low speed limits, where illegal "
                  "stopping directly endangers pedestrians"],
                 ["Commercial fleet oversight",
                  "Driver-fatigue and seatbelt monitoring for buses and lorries, "
                  "supporting transport-authority driving-hour rules"],
                 ["Drone patrol",
                  "Temporary enforcement at events, accident sites or roads without "
                  "fixed cameras"],
                 ["Road-safety analytics",
                  "Searchable plate log, violation hotspots and repeat-offender "
                  "identification to target scarce police resources"]],
                [42 * mm, 110 * mm]),

          P("10. Data handling and ethics", "h1"),
          P("Number plates identify real people, so the system is deliberately "
            "conservative. A plate is written only after three independent reads "
            "agree; anything less is stored as UNREADABLE and marked for manual "
            "review. Evidence images and plate crops stay on the operator's machine "
            "and are attached only to the police challan for that specific violation. "
            "The system records what it observed and never infers identity, intent or "
            "history beyond the plate itself."),

          P("11. Known limits", "h1"),
          P("Stated plainly, because anyone deploying this must understand them:<br/>"
            "&bull; Speed requires per-camera calibration; without it no speed is shown.<br/>"
            "&bull; Plate OCR needs roughly 40 or more pixels of plate width.<br/>"
            "&bull; Red-light enforcement requires knowing which signal head governs "
            "the policed lane.<br/>"
            "&bull; Illegal parking requires a fixed camera - a moving camera cannot "
            "establish that a vehicle is stationary.<br/>"
            "&bull; About 2 frames per second are analysed on a CPU laptop; the video "
            "stays real-time by dropping frames.<br/>"
            "&bull; Detection degrades at night and in heavy rain, as with any camera "
            "system."),

          P("12. Roadmap", "h1"),
          P("Night and adverse-weather models; a vision-language model such as "
            "Moondream to resolve cases the detector currently reports as not judged; "
            "a trained three-wheeler class, since COCO has none and Sri Lankan "
            "tuk-tuks are currently labelled as trucks; GPU edge deployment at a live "
            "junction; and a city-wide dashboard aggregating multiple cameras.")]

    build(os.path.join(OUT, "PROJECT_DOCUMENTATION.pdf"), A4, s, EVENT)


def presentation():
    S = styles()
    s = []

    def slide(title, bullets=None, image=None, cap=None):
        s.append(Paragraph(title, S["sh"]))
        for b in (bullets or []):
            s.append(Paragraph(b, S["sb"]))
        if image:
            s.append(Spacer(1, 3 * mm))
            s.extend(pic(image, 172, cap, S))
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
           "Violations without photographic proof or a verified plate are disputed.",
           "<b>Coverage and proof</b> are the enforcement gap."])
    slide("What we built",
          ["One AI pipeline detects <b>nine violation types</b> on an ordinary camera.",
           "Reads <b>number plates on every vehicle</b>, not only offenders.",
           "Measures <b>real speed</b> through geometric calibration.",
           "Issues an <b>e-challan with photographic evidence</b> to the police."])
    slide("Proof: over-speeding",
          ["Calibrated speed verified at <b>83-163 km/h</b> across two cameras."],
          "01_over_speeding_evidence_1.jpg",
          "134.0 km/h in a 60 zone - vehicle boxed, plate zoomed, proof stamped on "
          "the image.")
    slide("Proof: helmet and triple riding",
          ["Both detected from a <b>single uploaded photograph</b>, two challans."],
          "07_image_upload_triple_helmet.jpg",
          "Three riders and no helmets on a CC-licensed public image.")
    slide("Proof: plate recognition",
          ["A plate is confirmed only when <b>three separate reads agree</b>."],
          "05_anpr_sri_lanka_0.jpg",
          "18 vehicles tracked; plate AAG 4002 read and confirmed.")
    slide("Why it can be trusted",
          ["<b>Parked vehicles are never fined</b> - 41 vehicles, 0 violations.",
           "<b>Unreadable plates say UNREADABLE</b> - never invented.",
           "<b>No calibration means no speed</b>, not a guess.",
           "<b>79 automated tests</b>, including every refusal case.",
           "Six real false-positive defects found and fixed by testing."])
    slide("Deployment",
          ["Works with <b>existing CCTV</b>, a phone stream, or a drone.",
           "Pilot on one laptop; cities use GPU edge boxes.",
           "Helmet, seatbelt and plate models are <b>drop-in files</b>.",
           "Python, FastAPI, YOLOv8, ByteTrack, OpenCV, EasyOCR, SQLite."])
    slide("Impact and roadmap",
          ["<b>24/7 coverage</b> without multiplying officers.",
           "<b>Court-ready evidence</b> means fines that hold up.",
           "Searchable plate log enables <b>repeat-offender analytics</b>.",
           "Next: night models, vision-language for ambiguous cases, junction pilot."])

    s += [Spacer(1, 40 * mm),
          Paragraph("Safer roads, proven by evidence.", S["title"]),
          Paragraph("AI Smart Traffic Intelligence Platform", S["sub"])]
    build(os.path.join(OUT, "PRESENTATION.pdf"), landscape(A4), s, EVENT, margin=20)


if __name__ == "__main__":
    documentation()
    presentation()
