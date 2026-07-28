"""Generate docs/PRESENTATION_GUIDE.pdf - the run-sheet for presentation day.

    python scripts/make_guide.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
os.chdir(ROOT)

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, Spacer

from make_docs import EVENT, OUT, build, pic, styles, table


def main():
    S = styles()
    P = lambda t, k="body": Paragraph(t, S[k])   # noqa: E731

    s = [Spacer(1, 20 * mm),
         P("Presentation Day Run-Sheet", "title"),
         P("AI Smart Traffic Intelligence Platform  |  Final", "sub"),
         Spacer(1, 6 * mm),

         P("1. Before you leave home", "h1"),
         table([["Check", "Why it matters"],
                ["Run <b>python tests/run_all.py</b>", "Expect 79 passing. Proves nothing broke overnight"],
                ["Start the server yourself in your own terminal",
                 "A server started by another process can die mid-demo"],
                ["Open http://localhost:8000 and press <b>Ctrl+F5</b>",
                 "The dashboard is cached hard; a stale page looks broken"],
                ["Play each demo clip once, end to end",
                 "Warms the models and confirms violations appear"],
                ["Screen-record one perfect run",
                 "Your fallback if anything stalls on stage"],
                ["Charge the laptop and bring the charger",
                 "On battery Windows throttles the CPU and analysis halves"]],
               [64 * mm, 88 * mm]),

         P("2. In the room, before you speak", "h1"),
         P("&bull; Plug into mains power. This is the single biggest performance factor.<br/>"
           "&bull; Close Chrome tabs, Teams, OneDrive - they steal the CPU the detector needs.<br/>"
           "&bull; Start the first clip <b>before</b> you begin talking. The models take "
           "about ten seconds to load and that silence looks like a crash.<br/>"
           "&bull; Have the screen recording open in a second tab, ready to play.<br/>"
           "&bull; Set the dashboard to full screen and check it is readable from the back."),

         P("3. Demo order", "h1"),
         P("Roughly six minutes. Spend most of it on the product, not the slides."),
         table([["Time", "Do this", "Say this"],
                ["0:00", "Title slide", "Six weeks ago we pitched an idea. Today we run it."],
                ["0:30", "Play <b>sample_1080p.mp4</b>",
                 "This is a live feed through the AI. Those numbers are real speed, "
                 "from surveyed road geometry."],
                ["1:30", "Click an Over Speeding challan",
                 "Photo evidence, speed stamped on the image, plate crop, fine, PDF "
                 "for the police. No human typed anything."],
                ["2:30", "Click <b>Send to Police</b>",
                 "The full package - challan, evidence photo, plate crop - goes to the "
                 "traffic mailbox."],
                ["3:00", "Upload <b>triple_phone.jpg</b>",
                 "Two violations from one photograph: no helmet and triple riding."],
                ["4:00", "Play <b>srilanka.mp4</b>",
                 "Watch the counter. It stays at zero - these bikes are parked. Ask "
                 "any other team what theirs does with a parked motorcycle."],
                ["5:00", "Vehicles / ANPR tab", "Every vehicle logged, plates confirmed by three agreeing reads."],
                ["5:30", "Close", "Safer roads, proven by evidence."]],
               [14 * mm, 46 * mm, 92 * mm], size=8.6),
         PageBreak(),

         P("4. Numbers to have ready", "h1"),
         P("Quote these confidently - each is a measured result, not an estimate."),
         table([["Claim", "Figure"],
                ["Automated tests passing", "79 across 7 suites"],
                ["Speed verified", "83-163 km/h on two calibrated cameras"],
                ["Over-speeding events found", "7 on the highway clip, 3 on the second"],
                ["Vehicles tracked, Sri Lankan road", "150, with plates AAG 4002 and BBJ 8752 read"],
                ["Parked-bike clip", "41 vehicles, 0 violations"],
                ["Replay accuracy", "0.99-1.01x true speed"],
                ["Image analysis", "About 2 seconds once models are loaded"],
                ["Rider detection improvement", "yolov8n 12 riders associated, yolov8s 41"]],
               [76 * mm, 76 * mm]),

         P("5. Questions you will be asked", "h1"),
         table([["Question", "Answer"],
                ["How accurate is the speed?",
                 "Exact when calibrated. Four surveyed road corners map pixels to "
                 "metres, then we fit distance against time across many frames with "
                 "outlier rejection. Uncalibrated cameras show no speed at all."],
                ["How do you avoid false positives?",
                 "Four layers: a confidence floor, a motion gate, multi-frame "
                 "persistence, and a confidence gate on speed. We also found and fixed "
                 "six real false-positive defects by testing on real footage."],
                ["What if the plate is unreadable?",
                 "It says UNREADABLE. We never invent a number - a wrong plate on a "
                 "challan is worse than no challan."],
                ["Does it work at night or in rain?",
                 "Detection degrades like any camera system. Models are drop-in "
                 "replaceable, so a night-trained model swaps in without code changes."],
                ["Why is it not analysing every frame?",
                 "It is real-time. On a CPU we analyse about two frames a second and "
                 "drop the rest, exactly as a live camera does. The video never slows. "
                 "A GPU edge box analyses every frame."],
                ["Why did rule X not fire in your demo?",
                 "Because the footage does not contain that offence. The system reports "
                 "only what it can prove. All nine rules are implemented and tested."],
                ["What does deployment cost?",
                 "It runs on cameras that already exist. A pilot needs one laptop; a "
                 "city needs GPU edge boxes. No new cameras, no custom hardware."]],
               [44 * mm, 108 * mm], size=8.6),
         PageBreak(),

         P("6. If something goes wrong", "h1"),
         table([["Symptom", "Do this"],
                ["Video looks frozen at the start",
                 "Normal - models are loading, about ten seconds. Keep talking."],
                ["Image upload seems stuck",
                 "The first upload loads the models. Wait. Warm runs take two seconds."],
                ["Dashboard looks wrong or empty",
                 "Press Ctrl+F5. It is almost always a cached page."],
                ["Server not responding",
                 "Restart it in your terminal, then Ctrl+F5. Meanwhile play the recording."],
                ["A violation does not appear",
                 "Do not debug on stage. Switch to the recording and continue."],
                ["Everything is very slow",
                 "Check you are on mains power and close background apps."]],
               [52 * mm, 100 * mm]),

         P("7. What to say about the gaps", "h1"),
         P("Do not hide them - lead with them. This is your strongest material, "
           "because every other team will claim everything works perfectly."),
         P("<i>\"All nine rules are implemented and unit-tested. We are demonstrating "
           "the ones our footage genuinely contains. We will not stage a violation we "
           "did not observe, because fabricated evidence is exactly what this system "
           "exists to prevent. During development we found six cases where our own "
           "system accused the wrong person - a stopped car fined for a red light "
           "belonging to another lane, helmeted riders flagged for no helmet - and we "
           "fixed every one. That restraint is the product.\"</i>", "body"),

         P("8. Closing line", "h1"),
         P("<b>\"Nine violation types, number plates, real speed, automatic challans - "
           "one pipeline, running on a laptop, on cameras this country already owns. "
           "Safer roads, proven by evidence.\"</b>")]

    build(os.path.join(OUT, "PRESENTATION_GUIDE.pdf"), A4, s, EVENT)


if __name__ == "__main__":
    main()
