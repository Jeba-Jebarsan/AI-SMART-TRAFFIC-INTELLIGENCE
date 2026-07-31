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

    s = [Spacer(1, 18 * mm),
         P("Presentation Run-Sheet", "title"),
         P("Startup Innovation Competition 2026 - Final  |  Saturday 1 August, "
           "8.30 AM<br/>Google Meet: meet.google.com/wey-ncmi-zgc  |  30 minutes  |  "
           "Three speakers", "sub"),
         Spacer(1, 4 * mm),
         P("This is the operations sheet - setup, timing and what to do when "
           "something breaks. The words you actually say are in "
           "<b>docs/SPEAKING_SCRIPTS.md</b>.", "body"),

         P("1. One hour before", "h1"),
         table([["Check", "Why it matters"],
                ["Run <b>python tests/run_all.py</b>", "Expect 85 passing. Proves nothing broke"],
                ["Start the server in your OWN terminal",
                 "A server started by any other process can die mid-demo"],
                ["Open localhost:8000, press <b>Ctrl+F5</b>",
                 "The dashboard caches hard; a stale page looks broken"],
                ["Play every demo clip once, end to end",
                 "Warms the models so nothing loads slowly while judges watch"],
                ["Upload triple_phone.jpg once",
                 "The first image upload loads models and takes ~60s. Do it now, not live"],
                ["Screen-record one perfect run",
                 "Your fallback if anything stalls"],
                ["Mains power, charger connected",
                 "On battery Windows throttles the CPU and analysis halves"],
                ["Close Chrome tabs, OneDrive, anything heavy",
                 "Meet encoding plus AI detection will compete for CPU"]],
               [62 * mm, 90 * mm], size=8.6),

         P("2. Google Meet setup (all three of you)", "h1"),
         P("&bull; Join at <b>8.25 AM</b>, not 8.29. The invitation requires 5 minutes "
           "early and it is the first thing a panel notices.<br/>"
           "&bull; <b>One person shares for the whole session.</b> Handing the share "
           "between three people on Meet wastes a minute every time and often fails. "
           "Speaker 2 should share, because they drive the demo.<br/>"
           "&bull; Share a <b>window</b> (Chrome), not the whole screen - no "
           "notifications, no desktop icons.<br/>"
           "&bull; Tick <b>Share tab audio</b> only if you play a recording with sound.<br/>"
           "&bull; Put the deck in <b>presenter view on a second screen</b> if you have "
           "one; otherwise keep the scripts printed on paper beside you, not in a "
           "window you have to alt-tab to.<br/>"
           "&bull; <b>Cameras on</b> for all three at the start and during Q&amp;A. "
           "During the demo, whoever is not speaking turns their camera off to save "
           "bandwidth.<br/>"
           "&bull; Everyone stays <b>muted</b> except the current speaker.<br/>"
           "&bull; Use a <b>wired connection</b> or sit next to the router. Meet "
           "encoding plus live AI detection is demanding.<br/>"
           "&bull; Open the deck, the dashboard and the fallback recording <b>before</b> "
           "you share anything."),

         P("3. Thirty-minute structure, three speakers", "h1"),
         P("They asked for problem, solution, market, innovation, business model and "
           "scalability. Budget roughly 21 minutes presenting, 9 for Q&amp;A."),
         table([["Time", "Section", "Slides", "Who"],
                ["0:00-2:00", "Opening and the problem", "1-2", "Speaker 1"],
                ["2:00-5:00", "Opportunity and the solution", "3-4", "Speaker 1"],
                ["5:00-7:00", "How it works, capability", "5-6", "Speaker 1"],
                ["7:00-10:00", "Proof: speed, helmet, plates", "7-11", "Speaker 2"],
                ["10:00-14:00", "<b>LIVE DEMO</b>", "dashboard", "Speaker 2"],
                ["14:00-16:00", "Limits, trust, rigour", "12-14", "Speaker 2"],
                ["16:00-18:00", "Innovation and market", "15-16", "Speaker 3"],
                ["18:00-20:00", "Business model, sustainability", "17-18", "Speaker 3"],
                ["20:00-21:00", "Scalability and close", "19-20", "Speaker 3"],
                ["21:00-30:00", "Questions and answers", "-", "All"]],
               [24 * mm, 62 * mm, 32 * mm, 22 * mm], size=8.6),
         PageBreak(),

         P("4. The live demo, step by step", "h1"),
         P("Four minutes. This is what separates you from a slide deck. The full wording is in docs/SPEAKING_SCRIPTS.md."),
         table([["Do this", "Say this"],
                ["Play <b>sample_1080p.mp4</b>",
                 "This is a real feed through the AI. Those speeds come from surveyed "
                 "road geometry, not guesswork."],
                ["Click an Over Speeding challan",
                 "Photo evidence, speed stamped on the image, plate crop, the fine, and "
                 "a PDF for the police. No human typed anything."],
                ["Click <b>Send to Police</b>",
                 "The complete package - challan, evidence photo, plate crop - goes to "
                 "the traffic mailbox automatically."],
                ["Upload <b>triple_phone.jpg</b>",
                 "Two violations from one photograph: no helmet and triple riding, two "
                 "separate challans."],
                ["Play <b>srilanka.mp4</b>",
                 "Watch the violation counter. It stays at zero, because these "
                 "motorcycles are parked. Ask any other team what theirs does with a "
                 "parked bike."],
                ["Open the Vehicles / ANPR tab",
                 "Every vehicle logged with its plate, confirmed only when three "
                 "separate reads agree."]],
               [42 * mm, 110 * mm], size=8.8),
         PageBreak(),

         P("5. Numbers to have ready", "h1"),
         P("Quote these confidently - each is a measured result, not an estimate."),
         table([["Claim", "Figure"],
                ["Automated tests passing", "85 across 7 suites"],
                ["Speed verified", "83-163 km/h on two calibrated cameras"],
                ["Over-speeding events found", "10 on the highway clip, 3 on the second"],
                ["Vehicles tracked, Sri Lankan road", "150, with plates AAG 4002 and BBJ 8752 read"],
                ["Parked-bike clip", "41 vehicles, 0 violations"],
                ["Replay accuracy", "0.99-1.01x true speed"],
                ["Image analysis", "About 2 seconds once models are loaded"],
                ["Rider detection improvement", "yolov8n 12 riders associated, yolov8s 41"]],
               [76 * mm, 76 * mm]),

         P("6. Business questions (this is a startup competition)", "h1"),
         table([["Question", "Answer"],
                ["Who pays for this?",
                 "Police and municipal councils buy enforcement capacity; fleet "
                 "operators buy compliance monitoring. A pilot is software and "
                 "calibration only - no new cameras, no civil works."],
                ["How do you make money?",
                 "A setup fee per camera site, an annual per-camera licence, an "
                 "analytics tier for authorities, and a per-vehicle package for fleets."],
                ["Is it sustainable?",
                 "It runs on infrastructure already paid for, so there is no capital "
                 "barrier. Recovered fines fund expansion, and each new camera is "
                 "software only, so marginal cost falls as coverage grows."],
                ["What is your competitive advantage?",
                 "Most systems do one thing and produce a number. We run many rules on "
                 "any existing camera and attach court-ready evidence to every fine. "
                 "The engineering that makes it refuse to guess is the moat."],
                ["How do you scale?",
                 "One pilot junction, then a corridor, then a city. Nothing about the "
                 "software is Sri Lanka specific, so comparable South Asian markets "
                 "follow."],
                ["What about privacy?",
                 "Plates identify real people, so a number is written only after three "
                 "independent reads agree; otherwise it is marked unreadable for human "
                 "review. Evidence stays with the operator and is attached only to the "
                 "specific challan."]],
               [40 * mm, 112 * mm], size=8.4),
         PageBreak(),

         P("7. Technical questions you will be asked", "h1"),
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

         P("8. If something goes wrong", "h1"),
         table([["Symptom", "Do this"],
                ["Video looks frozen at the start",
                 "Normal - models are loading, about ten seconds. Keep talking."],
                ["Image upload seems stuck",
                 "The first upload loads the models. Wait. Warm runs take two seconds."],
                ["Dashboard looks wrong or empty",
                 "Press Ctrl+F5. It is almost always a cached page."],
                ["Server not responding",
                 "Restart it in your terminal, then Ctrl+F5. Meanwhile play the recording."],
                ["Meet share looks laggy",
                 "Everyone not speaking turns their camera off, share the Chrome window "
                 "only, and lower the clip quality"],
                ["Screen share will not start",
                 "Chrome needs macOS/Windows screen-recording permission. Test this "
                 "the night before, not at 8.29"],
                ["A violation does not appear",
                 "Do not debug on stage. Switch to the recording and continue."],
                ["Everything is very slow",
                 "Check you are on mains power and close background apps."]],
               [52 * mm, 100 * mm]),

         P("9. What to say about the gaps", "h1"),
         P("Do not hide them - lead with them. This is your strongest material, "
           "because every other team will claim everything works perfectly."),
         P("<i>\"All nine rules are implemented and unit-tested. We are demonstrating "
           "the ones our footage genuinely contains. We will not stage a violation we "
           "did not observe, because fabricated evidence is exactly what this system "
           "exists to prevent. During development we found six cases where our own "
           "system accused the wrong person - a stopped car fined for a red light "
           "belonging to another lane, helmeted riders flagged for no helmet - and we "
           "fixed every one. That restraint is the product.\"</i>", "body"),

         P("10. Closing line", "h1"),
         P("<b>\"Nine violation types, number plates, real speed, automatic challans - "
           "one pipeline, running on a laptop, on cameras this country already owns. "
           "Safer roads, proven by evidence.\"</b>")]

    build(os.path.join(OUT, "PRESENTATION_GUIDE.pdf"), A4, s, EVENT)


if __name__ == "__main__":
    main()
