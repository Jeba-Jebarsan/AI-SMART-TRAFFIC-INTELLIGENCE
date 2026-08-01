"""Generate the Round-2 business deck (docs/PRESENTATION_ROUND2.pptx).

FIFTEEN slides. An earlier build ran to 31 and was too long for the slot - a
business round is won by answering seven questions clearly, not by having a
slide for every thought. Everything cut still lives in docs/BUSINESS_PLAN.md,
which is what we hand over afterwards.

Three focus areas, one per speaker, marked in each slide's kicker so the
handover is obvious to the panel without printing a speaker's name anywhere:

    Slides 1-2    Opening
    Part 1  BUSINESS    who will buy it                       slides 3-5
    Part 2  TECHNOLOGY  camera, AI, data, maps, detection     slides 6-10
    Part 3  MONEY & ROLLOUT  pricing, revenue, launch, risk   slides 11-15

Part 2 gets a third of the deck on purpose. "Where does the zone data come
from at scale?" is the question the panel pressed hardest on.

Design rules:
  * Light theme, one teal accent - readable over a compressed Meet stream.
  * Nothing backstage on a slide. No speaker names, no timings.
  * Every commercial figure is labelled as a modelled assumption, with the
    working shown. A number we cannot source does not go on a slide.

    python scripts/make_round2_pptx.py
"""
import os

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

from _pptx_helpers import (ACCENT, AMBER, GREEN, H, INK, MUTED, PANEL,
                           PANEL_LINE, W, accent_bar, bg, box, card, faded_bg,
                           header, stat)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

PAPER = RGBColor(0xFF, 0xFF, 0xFF)


def _rect(slide, x, y, w, h, rgb, line=None):
    s = slide.shapes.add_shape(1, x, y, w, h)
    s.fill.solid()
    s.fill.fore_color.rgb = rgb
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(0.75)
    s.shadow.inherit = False
    return s


def table(s, data, widths, top=2.1, left=0.85, total=11.65, rh=0.5, size=11.5):
    """Row-banded table. data[0] is the header row.

    python-pptx's native table styling is fought more easily than configured,
    so this draws rectangles and textboxes - which also keeps the look
    identical to the cards used everywhere else in the deck.
    """
    y = Inches(top)
    for r, row in enumerate(data):
        fill = ACCENT if r == 0 else (PANEL if r % 2 == 0 else PAPER)
        _rect(s, Inches(left), y, Inches(total), Inches(rh), fill,
              line=None if r == 0 else PANEL_LINE)
        x = left
        for c, cell in enumerate(row):
            cw = total * widths[c]
            box(s, Inches(x + 0.14), y + Inches(0.09), Inches(cw - 0.24),
                Inches(rh), str(cell), size=size,
                colour=PAPER if r == 0 else INK, bold=(r == 0), space=0)
            x += cw
        y += Inches(rh)
    return y


def note(s, text, y=6.85, colour=ACCENT, size=14, bold=True):
    box(s, Inches(0.85), Inches(y), Inches(11.65), Inches(0.6), text,
        size=size, colour=colour, bold=bold)


def rows(s, items, top=2.05, gap=0.79, hgt=0.68, label_w=2.0, size=15):
    """Label-on-the-left, explanation-on-the-right list of cards."""
    for i, (label, detail) in enumerate(items):
        y = Inches(top + i * gap)
        card(s, Inches(0.85), y, Inches(11.65), Inches(hgt))
        box(s, Inches(1.1), y + Inches(0.13), Inches(label_w), Inches(0.45),
            label, size=size, colour=ACCENT, bold=True)
        box(s, Inches(1.2 + label_w), y + Inches(0.15), Inches(11.1 - label_w),
            Inches(0.45), detail, size=12, colour=INK, space=0)


def trio(s, items, top, hgt=1.15, title_size=13, body_size=11):
    """Three equal cards across the page."""
    for i, (t, d) in enumerate(items):
        x = Inches(0.85 + i * 3.92)
        card(s, x, Inches(top), Inches(3.72), Inches(hgt))
        box(s, x + Inches(0.2), Inches(top + 0.12), Inches(3.35), Inches(0.45),
            t, size=title_size, colour=ACCENT, bold=True)
        box(s, x + Inches(0.2), Inches(top + 0.52), Inches(3.35),
            Inches(hgt - 0.55), d, size=body_size, colour=MUTED, space=0)


def main():
    prs = Presentation()
    prs.slide_width, prs.slide_height = W, H
    blank = prs.slide_layouts[6]
    S = lambda: prs.slides.add_slide(blank)   # noqa: E731

    P1 = "PART 1  ·  BUSINESS"
    P2 = "PART 2  ·  TECHNOLOGY"
    P3 = "PART 3  ·  MONEY AND ROLLOUT"

    # ============================================================ 1  title
    s = S(); bg(s)
    faded_bg(s, "12_junction_cctv_clean.jpg", opacity=0.15)
    accent_bar(s)
    box(s, Inches(0.9), Inches(1.75), Inches(11.5), Inches(0.6),
        "SECOND ROUND", size=15, colour=ACCENT, bold=True)
    box(s, Inches(0.9), Inches(2.3), Inches(11.5), Inches(1.7),
        "From a system that works to a business that ships",
        size=42, colour=INK, bold=True)
    box(s, Inches(0.9), Inches(4.05), Inches(11.5), Inches(0.7),
        "AI Smart Traffic Intelligence Platform  -  how it gets onto Sri Lanka's roads",
        size=18, colour=ACCENT)
    box(s, Inches(0.9), Inches(5.5), Inches(11.5), Inches(0.5),
        "Team Three Hacks", size=17, colour=INK, bold=True)
    box(s, Inches(0.9), Inches(6.0), Inches(11.5), Inches(0.5),
        "Startup Innovation Competition 2026", size=14, colour=MUTED)

    # ============================================================ 2  contents
    s = S(); bg(s)
    header(s, "You asked us seven questions", "WHAT THIS DECK ANSWERS")
    table(s, [
        ["Your question", "Answered on"],
        ["Who is the customer, and how do you sell it?", "3"],
        ["How do you connect with the Sri Lanka Police?", "4 - 5"],
        ["How do you import data from existing CCTV?", "6 - 7"],
        ["At scale, where does the zone data come from?", "9 - 10"],
        ["Revenue model - your cost, your earnings from a province", "11 - 13"],
        ["SWOT analysis", "14"],
        ["How do you implement it, and what will go wrong?", "15"],
    ], widths=[0.82, 0.18], top=2.05, rh=0.5)
    trio(s, [
        ("PART 1  ·  BUSINESS", "Who will buy it, and how we reach them.  Slides 3-5"),
        ("PART 2  ·  TECHNOLOGY",
         "Camera, AI, data, maps, detection flow.  Slides 6-10"),
        ("PART 3  ·  MONEY AND ROLLOUT",
         "Pricing, revenue, launch and risk.  Slides 11-15"),
    ], top=5.75, hgt=1.05, title_size=12.5, body_size=11)
    note(s, "We have not re-pitched the detection. You already said it works.",
         y=5.35, size=14)

    # ######################################################### PART 1  BUSINESS
    # ------------------------------------------------------------ 3  customers
    s = S(); bg(s)
    header(s, "Who benefits is not who signs", P1)
    table(s, [
        ["Segment", "Who signs", "Why they buy", "Cycle"],
        ["Municipal councils", "Municipal Commissioner",
         "Own CCTV, get no value from it", "1-3 months"],
        ["Sri Lanka Police - Traffic", "Ministry of Public Security",
         "Manpower gap; needs evidence", "12-24 months"],
        ["RDA / Expressways", "Expressway Division",
         "Speed enforcement already budgeted", "6-12 months"],
        ["Private fleets", "Fleet owner",
         "Insurance, liability, driver behaviour", "2-6 weeks"],
        ["Campuses, ports, BOI zones", "Facilities head",
         "Private roads - no legal complexity", "2-6 weeks"],
        ["Insurers and donor programmes", "Head of Motor / programme manager",
         "Risk pricing; road-safety targets with money", "3-12 months"],
    ], widths=[0.24, 0.24, 0.36, 0.16], top=2.05, rh=0.55, size=11)
    card(s, Inches(0.85), Inches(5.95), Inches(11.65), Inches(1.1))
    box(s, Inches(1.15), Inches(6.1), Inches(11.1), Inches(0.85),
        "The police are our **biggest** customer and our **slowest** customer. Three "
        "students cannot live two years on no revenue - so the private track (fleets, "
        "campuses, ports: no procurement, signs in a week) **funds** the government track.",
        size=13.5, colour=INK, space=0)

    # ------------------------------------------------------------ 4  the ladder
    s = S(); bg(s)
    header(s, "We do not ask for a contract. We climb a ladder.", P1)
    ladder = [
        ("MONTH 0-3", "Give away evidence, not enforcement",
         "Free 30-day road-safety audit at one junction for one council. We issue ZERO "
         "fines. Nobody has to be brave to say yes."),
        ("MONTH 3-6", "Get a named champion",
         "Take that report to the National Council for Road Safety and Police Traffic HQ. "
         "Ask for a letter of support - free for them to give."),
        ("MONTH 6-12", "Supervised enforcement pilot",
         "One division. Every challan approved by an officer. We publish officer-time "
         "saved and the fall in the violation rate."),
        ("MONTH 12-24", "Procurement - through a partner",
         "Sub-contract under an integrator who already holds government vendor "
         "registration. A two-year problem becomes a two-month partnership."),
    ]
    y = 1.92
    for when, title, detail in ladder:
        card(s, Inches(0.85), Inches(y), Inches(11.65), Inches(0.95))
        box(s, Inches(1.05), Inches(y + 0.11), Inches(1.7), Inches(0.4), when,
            size=10.5, colour=ACCENT, bold=True)
        box(s, Inches(2.8), Inches(y + 0.07), Inches(9.4), Inches(0.4), title,
            size=14.5, colour=INK, bold=True)
        box(s, Inches(2.8), Inches(y + 0.45), Inches(9.4), Inches(0.45), detail,
            size=11, colour=MUTED, space=0)
        y += 1.05
    card(s, Inches(0.85), Inches(6.15), Inches(11.65), Inches(0.85))
    box(s, Inches(1.15), Inches(6.3), Inches(11.1), Inches(0.6),
        "Every rung is something the other side can say yes to **without spending money "
        "or taking a risk.**", size=14, colour=INK, space=0)

    # ------------------------------------------------------------ 5  the rule
    s = S(); bg(s)
    accent_bar(s)
    box(s, Inches(0.9), Inches(1.55), Inches(11.5), Inches(0.4), P1, size=13,
        colour=ACCENT, bold=True)
    box(s, Inches(0.9), Inches(2.15), Inches(11.5), Inches(0.5),
        "THE DESIGN DECISION THAT MAKES ENFORCEMENT POSSIBLE", size=13.5,
        colour=MUTED, bold=True)
    box(s, Inches(0.9), Inches(2.7), Inches(11.5), Inches(1.0),
        "The AI proposes. A police officer decides.", size=38, colour=INK, bold=True)
    box(s, Inches(0.9), Inches(3.85), Inches(11.5), Inches(0.5),
        "Built and running today - not a plan.", size=17, colour=GREEN, bold=True)
    box(s, Inches(0.9), Inches(4.35), Inches(11.5), Inches(0.55),
        "Every violation is PENDING until a named officer approves it. Until then the "
        "system refuses to print, export or email it - the block is in the server, not "
        "the screen.", size=14, colour=INK, space=0)
    for i, (t, d) in enumerate([
            ("Legal", "Evidence Act No. 14 of 1995 - a named human is accountable"),
            ("Trust", "No citizen is ever fined by a machine"),
            ("Accuracy", "Officer rejections measure our false-positive rate"),
            ("Auditable", "Approve, reject and cancel are append-only. Even a session "
                          "wipe is recorded")]):
        x = Inches(0.85 + i * 2.95)
        card(s, x, Inches(5.15), Inches(2.75), Inches(1.35))
        box(s, x + Inches(0.18), Inches(5.27), Inches(2.4), Inches(0.4), t,
            size=14, colour=ACCENT, bold=True)
        box(s, x + Inches(0.18), Inches(5.65), Inches(2.4), Inches(0.8), d,
            size=10.5, colour=MUTED, space=0)
    note(s, "We are not asking a court, or a country, to trust an algorithm.", y=6.65,
         size=15)

    # ####################################################### PART 2  TECHNOLOGY
    # ------------------------------------------------------------ 6  six steps
    s = S(); bg(s)
    header(s, "From a camera on a pole to a challan", P2)
    for i, (t, d) in enumerate([
        ("1  CAMERA", "Existing council CCTV, our own camera, or a drone. We pull the "
                      "video over the ONVIF / RTSP standard."),
        ("2  EDGE BOX", "One small computer in the cabinet that is already there. "
                        "It handles about four cameras."),
        ("3  DETECT", "The AI finds vehicles, riders, helmets, phones and plates, and "
                      "gives every vehicle an ID it keeps as it moves."),
        ("4  MEASURE", "The map calibration turns pixels into metres, so we get real "
                       "speed and real position - not a guess."),
        ("5  JUDGE", "Ten rules run at once. Each needs several frames of agreement "
                     "before it will accuse anybody."),
        ("6  EVIDENCE", "A photo stamped with plate, time, place and rule goes to an "
                        "officer's queue. Approved, it becomes a challan."),
    ]):
        x = Inches(0.85 + (i % 3) * 3.92)
        y = Inches(2.05 + (i // 3) * 1.85)
        card(s, x, y, Inches(3.72), Inches(1.65))
        box(s, x + Inches(0.22), y + Inches(0.14), Inches(3.3), Inches(0.4), t,
            size=14, colour=ACCENT, bold=True)
        box(s, x + Inches(0.22), y + Inches(0.55), Inches(3.32), Inches(1.0), d,
            size=11, colour=INK, space=0)
    note(s, "Only step 6 ever leaves the site. Everything before it happens on the pole.",
         y=5.85, size=16)

    # ------------------------------------------------------------ 7  camera + net
    s = S(); bg(s)
    header(s, "Cameras that are already on the poles", P2)
    box(s, Inches(0.85), Inches(1.95), Inches(11.65), Inches(0.5),
        "Almost every installed camera and recorder speaks **ONVIF over RTSP**. We pull a "
        "stream - no firmware change, no rewiring, nothing new on the pole.",
        size=14, colour=INK, space=0)
    trio(s, [
        ("Council CCTV", "Installed and paid for. We just read it."),
        ("Our own camera", "Where none exists, or the angle is wrong."),
        ("Drone", "Already working today - we fly one."),
    ], top=2.5, hgt=0.92, title_size=13, body_size=10.5)
    table(s, [
        ["Approach", "Network load for 1,000 cameras", "Verdict"],
        ["Send every video stream to a central server",
         "1,000 x 2 Mbps = 2 Gbps sustained, ~21 TB per day", "Impossible"],
        ["Detect at the edge, send EVENTS only",
         "A challan is ~250 KB - about 5 Mbps average across the fleet",
         "Runs on what exists"],
    ], widths=[0.31, 0.48, 0.21], top=3.6, rh=0.58, size=11)
    box(s, Inches(0.85), Inches(5.45), Inches(11.65), Inches(0.55),
        "A 400x reduction in bandwidth - deployable on Sri Lankan municipal networks.",
        size=19, colour=ACCENT, bold=True)
    card(s, Inches(0.85), Inches(6.1), Inches(11.65), Inches(0.9))
    box(s, Inches(1.15), Inches(6.25), Inches(11.1), Inches(0.65),
        "**Honest caveat:** most municipal CCTV was installed to watch for theft, not to "
        "read plates. Expect ~40% of any estate to be usable without repositioning - we "
        "survey and say so **before** anyone signs.", size=12.5, colour=INK, space=0)

    # ------------------------------------------------------------ 8  the AI
    s = S(); bg(s)
    header(s, "What the AI does with one frame", P2)
    rows(s, [
        ("Detect", "One pass of the model finds vehicles, people, helmets, phones and "
                   "number plates."),
        ("Track", "The same motorcycle keeps ID #47 across frames, so a rule can watch it "
                  "over time instead of judging a snapshot."),
        ("Associate", "Is this person actually ON that motorcycle? Overlap, centre and "
                      "foot position are all checked - so a pedestrian is never fined."),
        ("Persist", "Three to four frames must agree before any accusation. One bad frame "
                    "is never enough."),
        ("Measure", "Is it genuinely moving? Net displacement with camera shake removed, "
                    "so a parked bike can never be fined."),
        ("Refuse", "No calibration, no geometric rules at all. We deleted our own speed "
                   "estimate rather than ship one that read 155 km/h for a parked car."),
    ])
    note(s, "Four of those six steps exist to STOP it firing, not to make it fire. In a "
            "product whose output is evidence, that is the whole job.", y=6.85, size=14)

    # ------------------------------------------------------------ 9  zone data
    s = S(); bg(s)
    header(s, "Where the zone data comes from", P2)
    box(s, Inches(0.85), Inches(1.95), Inches(11.65), Inches(0.5),
        "Today a human clicks four corners of the road per clip. Fine for five cameras, "
        "impossible for five thousand. We had been mixing up **two kinds of data**:",
        size=14, colour=INK, space=0)
    table(s, [
        ["Kind of data", "Example", "Per camera?", "Cost"],
        ["Camera geometry - where the ground plane sits in THIS image",
         "4-point homography, metres per pixel", "Yes. Unavoidable.", "Minutes, once"],
        ["World knowledge - what the law says about this piece of road",
         "Speed limit, no-parking, one-way, stop line", "No. It belongs to the map.",
         "Once, nationally"],
    ], widths=[0.36, 0.28, 0.22, 0.14], top=2.55, rh=0.72, size=11)
    box(s, Inches(0.85), Inches(4.8), Inches(11.65), Inches(0.5),
        "Fix the geometry by dragging 4 points on the image and 4 on a satellite map. "
        "That one act gives speed, stop lines, direction and no-parking zones.",
        size=13.5, colour=INK, space=0)
    for i, (v, l) in enumerate([("4 min", "per camera, once"),
                                ("67 hrs", "for 1,000 cameras"),
                                ("2 people", "2 weeks, a province"),
                                ("Auto", "re-flags if moved")]):
        stat(s, Inches(0.85 + i * 2.95), Inches(5.4), v, l, colour=ACCENT,
             w=Inches(2.75))
    note(s, "That is a line item on a budget. It is not a blocker.", y=6.85, size=15)

    # ------------------------------------------------------------ 10  the map
    s = S(); bg(s)
    header(s, "The world data already exists", P2)
    for i, (t, colour, items) in enumerate([
        ("WE IMPORT IT ONCE, NATIONALLY", ACCENT, [
            "**RDA road register** - road class and centrelines",
            "**Survey Dept / GIS** - built-up boundaries = the legal 50 km/h limit",
            "**Council gazetted schemes** - no-parking, one-way, bus halts",
            "**OpenStreetMap** - maxspeed, oneway, crossings, schools",
            "**Motor Traffic Act defaults** - where nothing is known, the law is the data",
            "**Learned proposals** - reviewed and approved by a human, never auto-enforced"]),
        ("SIX OF TEN RULES NEED NO MAP AT ALL", GREEN, [
            "**Live on day one:** No Helmet · Triple Riding · Wheelie / stunt riding · "
            "Mobile Phone Use · No Rest Break",
            "**Waiting on a model:** No Seatbelt",
            "**After geo-registration:** Over Speeding · Wrong Way · Red Light Jump",
            "**After zone import:** Illegal Parking",
            "",
            "They do not wait by guessing. They wait by **switching off.**"])]):
        x = Inches(0.85 + i * 6.0)
        card(s, x, Inches(2.05), Inches(5.65), Inches(4.25))
        box(s, x + Inches(0.28), Inches(2.25), Inches(5.1), Inches(0.5), t,
            size=13.5, colour=colour, bold=True)
        box(s, x + Inches(0.28), Inches(2.85), Inches(5.1), Inches(3.3), items,
            size=11.5, colour=INK, space=9)
    note(s, "So we deploy on day one and enrich over weeks. The customer sees value in "
            "week one, not month six.", y=6.5, size=14)

    # #################################################### PART 3  MONEY, ROLLOUT
    # ------------------------------------------------------------ 11  pricing
    s = S(); bg(s)
    header(s, "How you subscribe or licence it", P3)
    table(s, [
        ["Tier", "Who it is for", "Price"],
        ["Audit", "First contact. 30-day report, no fines issued", "Free"],
        ["Enforce", "Per camera. All rules, dashboard, officer review queue",
         "LKR 3,500 / camera / month"],
        ["Enforce + ANPR", "Adds plate recognition, owner lookup, PDF challan",
         "LKR 5,500 / camera / month"],
        ["No-upfront option", "Same service, setup and hardware rolled in over 3 years",
         "LKR 5,000 / camera / month"],
        ["Fleet", "Bus, logistics, plantation, courier. Driver scorecards",
         "LKR 1,000 / vehicle / month"],
        ["Provincial Licence", "Ministry / Police HQ. Unlimited cameras, ON-PREMISE, SLA",
         "LKR 12,000,000 / province / year"],
        ["Site Activation", "One-time: survey, geo-registration, zone import, training",
         "LKR 45,000 / camera"],
    ], widths=[0.20, 0.54, 0.26], top=2.0, rh=0.47, size=11)
    trio(s, [
        ("Anchor on the alternative",
         "Not on our cost. Three constables cover one point 24/7 for ~LKR 300,000/month."),
        ("Operating cost, not capital",
         "A council approves a monthly line; a purchase needs a tender. Hence no-upfront."),
        ("Publish volume tiers early",
         "100+ LKR 3,000 · 500+ LKR 2,600 · 2,000+ LKR 2,200. Never negotiate from zero."),
    ], top=5.5, hgt=1.15, title_size=12.5, body_size=10.5)
    note(s, "Free to enter, cheap to start, cheaper at scale, and never a capital purchase.",
         y=6.8, size=14)

    # ------------------------------------------------------------ 12  affordable?
    s = S(); bg(s)
    header(s, "Is this the right price for Sri Lanka?", P3)
    table(s, [
        ["Buyer", "What they pay us", "Compared with", "Verdict"],
        ["Council, 40 cameras", "LKR 1.68M / year",
         "Less than 2 constables cost for a year", "Fits an existing budget line"],
        ["Police HQ, one province", "LKR 12M / year",
         "A rounding error against the Police budget", "No new budget vote needed"],
        ["Fleet, 25 vehicles", "LKR 1,000 / vehicle / month",
         "About 10% of a commercial motor premium", "Free at a 10% premium discount"],
        ["Versus imported software", "~USD 140 / camera / year",
         "Imported ANPR licences run USD 200-1,000", "We are 3-7x cheaper"],
    ], widths=[0.21, 0.23, 0.31, 0.25], top=2.0, rh=0.6, size=10.5)
    box(s, Inches(0.85), Inches(4.7), Inches(11.65), Inches(0.6),
        "Roughly 50x cheaper per point-hour than three constables. Margin ~74%.",
        size=21, colour=ACCENT, bold=True)
    card(s, Inches(0.85), Inches(5.45), Inches(11.65), Inches(1.5))
    box(s, Inches(1.15), Inches(5.62), Inches(11.1), Inches(0.45),
        "The real pricing risk is not the price. It is getting paid.", size=17,
        colour=AMBER, bold=True)
    box(s, Inches(1.15), Inches(6.12), Inches(11.1), Inches(0.8),
        "Government here pays in 90 to 180 days, and that is what kills small vendors. "
        "So: 25% of activation invoiced up front, the provincial licence billed quarterly "
        "in advance, and private-sector revenue held as working capital.",
        size=12.5, colour=INK, space=0)

    # ------------------------------------------------------------ 13  the numbers
    s = S(); bg(s)
    header(s, "Western Province, three years", P3)
    table(s, [
        ["", "Year 1  -  prove it", "Year 2  -  own it", "Year 3  -  expand"],
        ["Cameras live", "80", "600", "2,200 (4 provinces)"],
        ["Subscriptions + licences", "2.9M", "44.4M", "166.8M"],
        ["Activation, hardware, fleet", "7.9M", "37.4M", "135.0M"],
        ["TOTAL REVENUE", "10.8M  (~$36k)", "81.8M  (~$273k)", "301.8M  (~$1.0M)"],
        ["Total cost", "21.6M", "64.0M", "-"],
        ["NET", "-10.8M   (this is the ask)", "+17.8M   BREAKEVEN", "-"],
    ], widths=[0.30, 0.235, 0.235, 0.23], top=2.0, rh=0.5, size=11.5)
    box(s, Inches(0.85), Inches(5.6), Inches(11.65), Inches(0.45),
        "All figures LKR, assuming LKR 300 = USD 1. Our own modelled assumptions with the "
        "working shown - not published facts.", size=12, colour=MUTED, space=0)
    card(s, Inches(0.85), Inches(6.1), Inches(11.65), Inches(0.95))
    box(s, Inches(1.15), Inches(6.25), Inches(11.1), Inches(0.7),
        "**Saturated, Sri Lanka is only ~USD 1.6M of recurring revenue.** We will say that "
        "before you do. It is the right market to PROVE this in - the same product, "
        "unchanged, fits Bangladesh, Nepal, Vietnam and East Africa, where the traffic mix "
        "is identical and the death rate is worse.", size=12.5, colour=INK, space=0)

    # ------------------------------------------------------------ 14  SWOT
    s = S(); bg(s)
    header(s, "SWOT - an honest one", P3)
    for i, (t, colour, items) in enumerate([
        ("STRENGTHS", GREEN, [
            "It exists - 10 rules on live video, 85 tests, our own evidence",
            "Built for Sri Lankan traffic: bikes, three-wheelers, mixed lanes",
            "It refuses to guess - no calibration, no speed reading",
            "CPU-capable and edge-first: cheap to run",
            "Local team, local cost base, same-afternoon support"]),
        ("WEAKNESSES", AMBER, [
            "No revenue, no reference customer, no registered company",
            "No measured accuracy figure yet - a court will ask",
            "Seatbelt rule disabled: the model we got is unusable",
            "Three part-time students; no procurement or legal experience",
            "We depend on camera quality we do not control"]),
        ("OPPORTUNITIES", ACCENT, [
            "~3,000 deaths a year; enforcement is still manual and spot-based",
            "Existing municipal CCTV is a sunk asset we can activate",
            "PDPA 2022 compliance is a moat foreign vendors handle badly",
            "Donor funding needs no police budget line",
            "Fleet and insurance markets need no government sale at all"]),
        ("THREATS", INK, [
            "Hikvision / Dahua / Huawei bundling ANPR free with hardware",
            "Tenders written around an incumbent, or never issued",
            "Government paying 90-180 days late",
            "One high-profile false positive destroying trust",
            "We are students - graduation is a continuity risk"])]):
        x = Inches(0.85 + (i % 2) * 6.0)
        y = Inches(1.95 + (i // 2) * 2.6)
        card(s, x, y, Inches(5.65), Inches(2.45))
        box(s, x + Inches(0.25), y + Inches(0.14), Inches(5.1), Inches(0.4), t,
            size=13.5, colour=colour, bold=True)
        box(s, x + Inches(0.25), y + Inches(0.58), Inches(5.15), Inches(1.8), items,
            size=10.5, colour=INK, space=6)

    # ------------------------------------------------------------ 15  launch
    s = S(); bg(s)
    header(s, "Launch, risks, and what we need", P3)
    cols = [
        ("HOW WE LAUNCH IT", ACCENT, [
            "**0-3 mo** Incorporate. Publish real accuracy. PDPA assessment. "
            "(Officer review queue: **done**.)",
            "**2-5 mo** Free 30-day audit, 1 council.",
            "**4-7 mo** Letter from NCRS / Police HQ.",
            "**6-12 mo** Supervised pilot, 20-40 cameras.",
            "**3-12 mo** In parallel: 8 fleets, 2 campuses.",
            "**12-24 mo** Western Province, 600 cameras. Breakeven.",
            "**24-36 mo** 3 provinces + first export."]),
        ("WHAT WILL GO WRONG", AMBER, [
            "**Procurement takes 2 years** -> private revenue funds us; go via an integrator",
            "**Is AI evidence admissible?** -> officer approves every fine; audit trail; "
            "calibration certificate",
            "**Privacy backlash** -> no face recognition, ever. Plates only, 90-day purge",
            "**Cameras are the wrong quality** -> survey and say so before anyone signs",
            "**Government pays late** -> bill in advance, hold private revenue as buffer",
            "**A wrong fine** -> human gate (built), one-click dispute, publish our error rate",
            "**'Make this challan disappear'** -> append-only trail; even a session wipe "
            "is recorded"]),
        ("WHAT WE NEED", GREEN, [
            "**LKR 15M** (~USD 50,000) for 18 months of runway. 60% salaries.",
            "",
            "And four things that are not money:",
            "**1.** A letter of support from NCRS or Police Traffic HQ",
            "**2.** One council to host a free 30-day audit",
            "**3.** An introduction to a registered government IT integrator",
            "**4.** Access to a labelled Sri Lankan traffic dataset"]),
    ]
    for i, (t, colour, items) in enumerate(cols):
        x = Inches(0.85 + i * 3.92)
        card(s, x, Inches(1.95), Inches(3.72), Inches(4.35))
        box(s, x + Inches(0.22), Inches(2.12), Inches(3.35), Inches(0.4), t,
            size=12.5, colour=colour, bold=True)
        box(s, x + Inches(0.22), Inches(2.6), Inches(3.4), Inches(3.5), items,
            size=9.5, colour=INK, space=7)
    card(s, Inches(0.85), Inches(6.45), Inches(11.65), Inches(0.75))
    box(s, Inches(1.15), Inches(6.58), Inches(11.1), Inches(0.55),
        "**We already built the hard part.** We are asking for the boring part: one "
        "council, one letter, one pilot.   Thank you - we are happy to take your questions.",
        size=14, colour=INK, space=0)

    names = (["PRESENTATION_ROUND2.pptx"]
             + [f"PRESENTATION_ROUND2_v{i}.pptx" for i in range(2, 9)])
    for i, name in enumerate(names):
        out = os.path.join(ROOT, "docs", name)
        try:
            prs.save(out)
        except PermissionError:
            continue
        if i:
            print(f"NOTE: {names[0]} is open in PowerPoint - wrote {name} instead. "
                  f"Close the deck and re-run to write the real file.")
        print("wrote", out, "|", len(prs.slides._sldIdLst), "slides")
        return
    raise SystemExit("every PRESENTATION_ROUND2*.pptx is locked - close PowerPoint")


if __name__ == "__main__":
    main()
