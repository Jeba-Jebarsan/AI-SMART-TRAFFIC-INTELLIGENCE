"""Generate the PowerPoint deck (docs/PRESENTATION.pptx).

Built for the Startup Innovation Competition 2026: a 30-minute online slot
covering problem, solution, target market, innovation, business model,
sustainability and scalability - not only the technology.

Every image is the system's own annotated output and every technical figure is
a measured result. Commercial figures are labelled as projections with their
assumptions stated, because inventing revenue numbers would undermine the one
thing this project is built on.

    python scripts/make_pptx.py
"""
import os

from pptx import Presentation
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

from _pptx_helpers import (CYAN, GOLD, GREEN, H, MUTED, NAVY, PANEL, W, WHITE,
                           accent_bar, bg, box, header, picture, stat)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


def bullets(s, items, top=2.05, size=18, gap=14, left=0.8, width=11.6):
    box(s, Inches(left), Inches(top), Inches(width), Inches(4.0), items,
        size=size, colour=WHITE, space=gap)


def two_col(s, left_title, left_items, right_title, right_items, top=2.0):
    for i, (t, items) in enumerate([(left_title, left_items),
                                    (right_title, right_items)]):
        x = Inches(0.8 + i * 6.1)
        card = s.shapes.add_shape(1, x, Inches(top), Inches(5.7), Inches(4.3))
        card.fill.solid(); card.fill.fore_color.rgb = PANEL
        card.line.color.rgb = NAVY; card.shadow.inherit = False
        box(s, x + Inches(0.3), Inches(top + 0.22), Inches(5.1), Inches(0.5),
            t, size=17, colour=CYAN, bold=True)
        box(s, x + Inches(0.3), Inches(top + 0.85), Inches(5.1), Inches(3.2),
            items, size=13.5, colour=WHITE, space=10)


def main():
    prs = Presentation()
    prs.slide_width, prs.slide_height = W, H
    blank = prs.slide_layouts[6]
    S = lambda: prs.slides.add_slide(blank)   # noqa: E731

    # 1 title
    s = S(); bg(s); accent_bar(s)
    box(s, Inches(0.9), Inches(2.0), Inches(11.5), Inches(1.3),
        "AI Smart Traffic Intelligence Platform", size=44, colour=WHITE, bold=True)
    box(s, Inches(0.9), Inches(3.4), Inches(11.5), Inches(0.7),
        "Turning any camera feed into fair, evidence-based enforcement",
        size=20, colour=CYAN)
    box(s, Inches(0.9), Inches(4.4), Inches(11.5), Inches(0.6),
        "Team Three Hacks  |  Startup Innovation Competition 2026",
        size=15, colour=MUTED)
    for i, (v, l) in enumerate([("9", "violation types"), ("79", "automated tests"),
                                ("83-163", "km/h speed verified")]):
        stat(s, Inches(0.9 + i * 3.15), Inches(5.4), v, l)

    # 2 problem
    s = S(); bg(s); header(s, "The problem", "PROBLEM STATEMENT")
    bullets(s, ["Sri Lanka records roughly **3,000 road deaths a year**, most from "
                "preventable violations.",
                "Officers cannot watch every junction, 24 hours a day - enforcement "
                "is a **human bottleneck**.",
                "Violations recorded **without photographic proof or a verified "
                "plate** are disputed and go unpaid.",
                "No searchable record means **repeat offenders go unnoticed**."],
            size=18.5)
    box(s, Inches(0.8), Inches(6.0), Inches(11.6), Inches(0.7),
        "Coverage and proof are the enforcement gap.", size=20, colour=GOLD, bold=True)

    # 3 opportunity
    s = S(); bg(s); header(s, "The opportunity", "WHY NOW")
    two_col(s, "What already exists",
            ["Colombo alone has **over 100 road cameras** already installed.",
             "Police already issue spot fines - the legal framework is in place.",
             "Smartphones and drones make any road coverable today."],
            "What is missing",
            ["Those cameras are **watched by people, or not at all**.",
             "No automatic link from camera to challan to payment.",
             "Enforcement scales with headcount, not with technology."])
    box(s, Inches(0.8), Inches(6.5), Inches(11.6), Inches(0.6),
        "We do not need new cameras. We need intelligence behind the ones already there.",
        size=16, colour=GOLD, bold=True, align=PP_ALIGN.CENTER)

    # 4 solution
    s = S(); bg(s); header(s, "Our solution", "THE PRODUCT")
    bullets(s, ["One AI pipeline on an ordinary camera detects **nine violation types**.",
                "Reads **number plates on every vehicle**, not only offenders.",
                "Measures **real road speed** through geometric calibration.",
                "Issues an **e-challan with stamped photographic evidence**, "
                "delivered to the police automatically."])
    box(s, Inches(0.8), Inches(5.6), Inches(11.6), Inches(0.9),
        "Camera  ->  YOLOv8s  ->  ByteTrack  ->  Homography  ->  Violation engine  "
        "->  ANPR  ->  e-Challan", size=15, colour=CYAN, bold=True)

    # 5 nine rules
    s = S(); bg(s); header(s, "Nine violations, one pipeline", "CAPABILITY")
    for i, name in enumerate(["No Helmet", "Triple Riding", "Over Speeding",
                              "Red Light Jump", "Wrong Way", "No Seatbelt",
                              "Mobile Phone Use", "Illegal Parking", "Driver Fatigue"]):
        cx = Inches(0.8 + (i % 3) * 4.0); cy = Inches(2.2 + (i // 3) * 1.25)
        card = s.shapes.add_shape(1, cx, cy, Inches(3.7), Inches(1.0))
        card.fill.solid(); card.fill.fore_color.rgb = PANEL
        card.line.color.rgb = NAVY; card.shadow.inherit = False
        box(s, cx, cy + Inches(0.28), Inches(3.7), Inches(0.5), name,
            size=17, colour=WHITE, bold=True, align=PP_ALIGN.CENTER)
    box(s, Inches(0.8), Inches(6.2), Inches(11.6), Inches(0.6),
        "Plus ANPR on every tracked vehicle, building a searchable enforcement log.",
        size=15, colour=MUTED, align=PP_ALIGN.CENTER)

    # 6-8 evidence
    for title, img, cap in [
        ("Proof: over-speeding", "01_over_speeding_evidence_1.jpg",
         "134.0 km/h in a 60 zone - vehicle boxed, plate zoomed, proof stamped onto "
         "the image. **7 events** measured at **83-163 km/h** across two cameras."),
        ("Proof: helmet and triple riding", "07_image_upload_triple_helmet.jpg",
         "Both violations detected from a **single uploaded photograph**, producing "
         "**two separate challans**."),
        ("Proof: number-plate recognition", "05_anpr_sri_lanka_0.jpg",
         "Live Sri Lankan road: 18 vehicles tracked, plate **AAG 4002** read and "
         "confirmed. A plate counts only when **three separate reads agree**.")]:
        s = S(); bg(s); header(s, title, "VERIFIED SYSTEM OUTPUT")
        picture(s, img, Inches(1.4), Inches(1.95), Inches(10.5), Inches(4.3))
        box(s, Inches(0.8), Inches(6.45), Inches(11.6), Inches(0.8), cap,
            size=14, colour=MUTED, align=PP_ALIGN.CENTER)

    # 9 innovation / uniqueness
    s = S(); bg(s); header(s, "What makes it different", "INNOVATION AND UNIQUENESS")
    two_col(s, "Typical systems",
            ["Single purpose - a speed camera, or a plate reader.",
             "Report a number with no proof attached.",
             "Demo well, then fail on real roads with false positives.",
             "Need dedicated hardware at each site."],
            "Ours",
            ["**Nine rules in one pipeline**, on any camera.",
             "**Evidence-first**: every fine carries a stamped photo and plate crop.",
             "**Engineered to refuse** - it reports only what it can prove.",
             "**Runs on cameras that already exist**, on a laptop CPU."])

    # 10 trust
    s = S(); bg(s); header(s, "Why it can be trusted", "THE REAL DIFFERENTIATOR")
    bullets(s, ["**Parked vehicles are never fined** - 41 vehicles, 0 violations on a "
                "parked-motorcycle clip.",
                "**Unreadable plates say UNREADABLE** - a number is never invented.",
                "**No calibration means no speed shown**, rather than a misleading guess.",
                "**A violation must persist across frames** - one-frame anomalies rejected.",
                "**No mock data exists** anywhere in the product."], size=17, gap=12)
    for i, (v, l, c) in enumerate([("6", "false-positive defects found and fixed", GOLD),
                                   ("79", "automated tests passing", GREEN),
                                   ("0", "violations on parked bikes", CYAN)]):
        stat(s, Inches(0.9 + i * 3.9), Inches(5.55), v, l, colour=c, w=Inches(3.6))

    # 11 engineering rigour
    s = S(); bg(s); header(s, "Found by testing on real roads", "ENGINEERING RIGOUR")
    for i, (d, c) in enumerate([
            ("Moving vehicles fined for parking",
             "Motion gate misjudged 89% of moving vehicles as stationary"),
            ("Helmeted riders accused of no helmet",
             "Helmet crop was catching neighbouring riders"),
            ("Bare heads marked compliant",
             "Compliance threshold was lower than the accusation threshold"),
            ("Stopped car fined for a red light",
             "A signal from a different approach was applied to it"),
            ("Wrong plate numbers on challans",
             "Two agreeing OCR reads could both be wrong")]):
        y = Inches(2.05 + i * 0.95)
        box(s, Inches(0.85), y, Inches(5.3), Inches(0.8), d, size=15,
            colour=WHITE, bold=True)
        box(s, Inches(6.4), y, Inches(6.2), Inches(0.8), c, size=13.5, colour=MUTED)
    box(s, Inches(0.85), Inches(6.85), Inches(11.6), Inches(0.5),
        "We fixed cases where our own system accused the wrong person. Each is now a test.",
        size=14, colour=CYAN, bold=True)

    # 12 target users / market
    s = S(); bg(s); header(s, "Who it is for", "TARGET USERS AND MARKET")
    two_col(s, "Primary users",
            ["**Sri Lanka Police traffic division** - automated enforcement on "
             "existing junction cameras.",
             "**Road Development Authority / municipal councils** - highway "
             "corridors, school and hospital zones.",
             "**Commercial fleet operators** - seatbelt and driver-fatigue "
             "compliance for buses and lorries."],
            "Why they buy",
            ["Enforcement reach without hiring proportionally more officers.",
             "Evidence that survives dispute, so fines are actually collected.",
             "Data on where violations concentrate, to target scarce resources.",
             "Fleet operators reduce insurance exposure and liability."])
    box(s, Inches(0.8), Inches(6.5), Inches(11.6), Inches(0.6),
        "Entry point: a single pilot junction. Expansion: corridor, then city.",
        size=15, colour=GOLD, bold=True, align=PP_ALIGN.CENTER)

    # 13 business model
    s = S(); bg(s); header(s, "Business model", "HOW IT SUSTAINS ITSELF")
    for i, (t, d) in enumerate([
            ("Pilot deployment fee",
             "One-off setup and calibration per camera site"),
            ("Annual software licence",
             "Per-camera subscription covering updates and model improvements"),
            ("Support and analytics tier",
             "Dashboards, reporting and repeat-offender analytics for authorities"),
            ("Fleet compliance package",
             "Per-vehicle monitoring sold to commercial operators")]):
        y = Inches(2.0 + i * 1.15)
        card = s.shapes.add_shape(1, Inches(0.85), y, Inches(11.6), Inches(0.95))
        card.fill.solid(); card.fill.fore_color.rgb = PANEL
        card.line.color.rgb = NAVY; card.shadow.inherit = False
        box(s, Inches(1.15), y + Inches(0.12), Inches(4.6), Inches(0.7), t,
            size=15.5, colour=CYAN, bold=True)
        box(s, Inches(5.9), y + Inches(0.14), Inches(6.4), Inches(0.7), d,
            size=13.5, colour=WHITE)
    box(s, Inches(0.85), Inches(6.75), Inches(11.6), Inches(0.6),
        "Cost advantage: no new cameras and no per-site hardware, so a pilot is "
        "software and calibration only.", size=14, colour=GOLD, bold=True)

    # 14 sustainability
    s = S(); bg(s); header(s, "Sustainability", "ECONOMIC, SOCIAL, ENVIRONMENTAL")
    two_col(s, "Economically self-sustaining",
            ["Runs on **infrastructure already paid for**.",
             "One laptop starts a pilot; no civil works, no gantries.",
             "Recovered fines fund expansion without new capital."],
            "Socially and environmentally sound",
            ["**Fairness**: identical rules for every driver, no discretion.",
             "**Fewer deaths** through deterrence, not punishment.",
             "**Lower emissions** - smoother traffic and fewer crash-related jams.",
             "**Privacy-respecting**: plates confirmed three times or marked "
             "unreadable; no identity inference."])

    # 15 deployment
    s = S(); bg(s); header(s, "Deployment", "PRACTICAL AND MODULAR")
    bullets(s, ["Works with **existing CCTV**, a phone stream, or a drone via OBS.",
                "A pilot site runs on a **single laptop**; cities use GPU edge boxes.",
                "Helmet, seatbelt, plate and three-wheeler models are **drop-in "
                "files** - no code change.",
                "Python, FastAPI, YOLOv8, ByteTrack, OpenCV, EasyOCR, SQLite.",
                "Dashboard is a **single self-contained HTML file**, no external "
                "dependencies."], size=17, gap=12)

    # 16 scalability / roadmap
    s = S(); bg(s); header(s, "Scalability and future plans", "WHERE THIS GOES")
    for i, (phase, what) in enumerate([
            ("Now", "Working system, 79 tests, verified on real Sri Lankan road footage"),
            ("Next 3 months", "Live pilot at one signalised junction with police partnership"),
            ("6-12 months", "Corridor deployment; night and adverse-weather models; "
                            "trained three-wheeler class for local traffic"),
            ("Beyond", "City-wide multi-camera dashboard; vision-language models for "
                       "ambiguous cases; export to comparable South Asian markets")]):
        y = Inches(2.1 + i * 1.15)
        box(s, Inches(0.9), y, Inches(2.6), Inches(0.7), phase, size=16,
            colour=GOLD, bold=True)
        box(s, Inches(3.6), y, Inches(8.9), Inches(0.9), what, size=14.5, colour=WHITE)
    box(s, Inches(0.9), Inches(6.8), Inches(11.6), Inches(0.5),
        "Each camera added is software only - marginal cost falls as coverage grows.",
        size=14, colour=CYAN, bold=True)

    # 17 close
    s = S(); bg(s); accent_bar(s)
    box(s, Inches(0.9), Inches(2.7), Inches(11.5), Inches(1.2),
        "Safer roads, proven by evidence.", size=42, colour=WHITE, bold=True)
    box(s, Inches(0.9), Inches(4.0), Inches(11.5), Inches(0.7),
        "Nine violation types. Real speed. Verified plates. Automatic challans.",
        size=18, colour=CYAN)
    box(s, Inches(0.9), Inches(4.9), Inches(11.5), Inches(0.6),
        "On cameras this country already owns.", size=17, colour=GOLD, bold=True)
    box(s, Inches(0.9), Inches(6.0), Inches(11.5), Inches(0.6),
        "Team Three Hacks  |  github.com/Jeba-Jebarsan/AI-SMART-TRAFFIC-INTELLIGENCE",
        size=13, colour=MUTED)

    out = os.path.join(ROOT, "docs", "PRESENTATION.pptx")
    try:
        prs.save(out)
    except PermissionError:
        # The deck is open in PowerPoint. Don't lose the build - write beside it.
        out = os.path.join(ROOT, "docs", "PRESENTATION_v2.pptx")
        prs.save(out)
        print("NOTE: PRESENTATION.pptx is open in PowerPoint; wrote a copy instead.")
    print("wrote", out, "|", len(prs.slides._sldIdLst), "slides")


if __name__ == "__main__":
    main()
