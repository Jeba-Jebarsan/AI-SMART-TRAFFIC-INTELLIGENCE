# Speaking Scripts — Team Three Hacks

**Startup Innovation Competition 2026 — Final**
Saturday 1 August 2026 · 8:30 AM · Google Meet · `meet.google.com/wey-ncmi-zgc`
30 minutes · three speakers

---

## How to use this

- ***Italic text*** = what you **say**.
- **[Square brackets]** = what you **do** (click, change slide, share screen).
- You do not have to say it word for word. Use your own words, but keep the **order** and keep the **numbers**.
- Read your part out loud **three times** before Saturday, with a timer.
- If you run long, cut examples. **Never cut the numbers.**

> **Nothing in this document is on the slides.** The panel sees every pixel we
> project, so speaker names and timings live here only.

---

## The split

| Speaker | Slides | Covers | Time |
|---|---|---|---|
| **Speaker 1** | 1–6 | Opening, problem, opportunity, solution, how it works, capability | 7 min |
| **Speaker 2** | 7–14 + **live demo** | All the proof, the demo, honesty about limits, engineering rigour | 9 min |
| **Speaker 3** | 15–20 | Innovation, market, business model, sustainability, scale, close | 5 min |
| **All three** | — | Questions and answers | 9 min |

**Speaker 2 shares the screen for the whole session.** Handing the share
between three people on Google Meet wastes a minute every time and often
fails. Speaker 2 changes slides for everyone.

### Minute by minute

| Time | What happens | Who |
|---|---|---|
| −5 min | All three join. Cameras on. Test audio. | All |
| 0:00 | Opening + problem | Speaker 1 |
| 2:00 | Opportunity + solution | Speaker 1 |
| 5:00 | How it works + capability | Speaker 1 |
| 7:00 | Proof slides | Speaker 2 |
| 10:00 | **LIVE DEMO** | Speaker 2 |
| 14:00 | Limits, trust, rigour | Speaker 2 |
| 16:00 | Innovation + market | Speaker 3 |
| 18:00 | Business model + sustainability | Speaker 3 |
| 20:00 | Scale + close | Speaker 3 |
| 21:00 | Q&A | All |

---

# SPEAKER 1 — The opening (7 minutes)

Your job is to make the panel **care** before they see any technology.
Start with a person, not a product. Speak **slowly** for the first thirty
seconds — that is the part everyone rushes.

## Slide 1 — Title

**[Slide 1 on screen. Look at the camera, not the slide. Pause two seconds before you speak.]**

> *Good morning. Thank you for having us.*
>
> *Somewhere in Sri Lanka this morning, a man is riding to work without a helmet. He passes under a traffic camera. That camera sees him perfectly.*
>
> *And nothing happens.*
>
> *Not because the camera failed. Because nobody was watching it.*
>
> *We are Team Three Hacks. I am [your name], and with me are [name] and [name]. We built the AI Smart Traffic Intelligence Platform — a system that watches those cameras when nobody else can.*

## Slide 2 — The problem

> *Sri Lanka loses around three thousand lives on the road every year. Most of those deaths come from things that are easy to see. No helmet. Too much speed. Three people on one motorcycle.*
>
> *So why does it keep happening? Three reasons.*
>
> ***First, coverage.*** *A police officer cannot stand at every junction, twenty-four hours a day. Enforcement is limited by how many people we can hire.*
>
> ***Second, proof.*** *When a fine is written without a photograph and without a verified number plate, it gets argued about. Many are never paid.*
>
> ***Third, memory.*** *Nothing is recorded in a way you can search. So a driver who breaks the rule every single day looks exactly like a driver who broke it once.*
>
> *The gap is not cameras. The gap is coverage and proof.*

## Slide 3 — The opportunity

> *Here is what makes this the right moment.*
>
> *Colombo alone already has more than one hundred road cameras installed. The police already have the legal power to issue fines. The hardware is there. The law is there.*
>
> *What is missing is the middle. Nothing connects the camera to the fine. A human has to sit and watch, or nobody watches at all.*
>
> *So we are not asking anyone to buy new cameras. We are putting intelligence behind the cameras this country already owns.*

## Slide 4 — Our solution

> *This is what we built.*
>
> *One AI system, running on an ordinary camera, that watches traffic and judges violations.*
>
> *It reads the number plate of every vehicle — not only the ones that break a rule.*
>
> *It measures real road speed in kilometres per hour, using the actual geometry of the road.*
>
> *And when it finds a violation, it creates an electronic fine with the photograph stamped onto it, and sends it to the police automatically.*
>
> *All of that runs on a single laptop. No new hardware.*

## Slide 5 — How it works

**[Point at each box as you say it. Do not read the slide — just walk through the six words.]**

> *Six steps.*
>
> ***It sees*** *— the AI model finds vehicles, riders, helmets and plates.*
>
> ***It follows*** *— every vehicle gets an identity it keeps as it moves across the screen.*
>
> ***It measures*** *— we survey four corners of the road, so the system knows how many metres one pixel is worth.*
>
> ***It judges*** *— the rules run, and each one has to pass safety checks before it will accuse anybody.*
>
> ***It identifies*** *— it reads the number plate, and only accepts it when three separate reads agree.*
>
> ***And it acts*** *— it produces the fine, with the evidence attached.*

## Slide 6 — Capability, and the handover

⚠️ **Important:** do **not** say "we detect nine violations" and stop there.
That makes nine sound like a ceiling. Say it like this:

> *Now, what can it actually catch?*
>
> *Nine rules are live today. No helmet. Triple riding. Over speeding. Red light jumping. Wrong way. No seatbelt. Mobile phone use. Illegal parking. Driver fatigue.*
>
> *But the important word on this slide is not "nine". It is* ***engine.***
>
> *Underneath all nine is one shared core — detection, tracking, and road geometry. Each rule is a small module on top of that core. So when a client asks for lane discipline, or bus-lane misuse, or blocked pedestrian crossings, that is days of work, not a new product.*
>
> *That is the difference between a feature and a platform.*
>
> *But anybody can put words on a slide. So I am going to hand over to [name], who will show you it actually working.*

**[Stop talking. Mute yourself.]**

---

# SPEAKER 2 — The proof and the demo (9 minutes)

You are the most important speaker. Slides win nothing; a working system wins.

> ⚠️ **Your one rule: if something breaks, do not debug it on stage.**
> Switch to the backup recording and keep talking.

## Slide 7 — Over speeding

> *Thank you [name].*
>
> *This is not a picture we drew. This is the system's own output.*
>
> *One hundred and thirty-four kilometres an hour, in a sixty zone. The vehicle is boxed. The number plate is zoomed in. And the speed is stamped onto the image itself, so it cannot be separated from the evidence later.*
>
> *We measured seven of these events, between eighty-three and one hundred and sixty-three kilometres an hour, on two different cameras.*

## Slide 8 — Speed is measured, not guessed

> *I want to be clear about where that number comes from, because this is where most systems are weak.*
>
> *We survey four corners of the road, and we map the camera pixels onto real metres. Then we fit distance against time across many frames, and we throw away readings that do not fit.*
>
> *When we replay a video at a known speed, we get between zero point nine nine and one point zero one times the true speed.*
>
> *And if a camera has not been calibrated, we show* ***no speed at all.*** *Not a guess. Nothing. We actually removed that guess from our own system last week, because a number you cannot defend is worse than no number.*

## Slide 9 — Helmet and triple riding

> *This one came from a single photograph. Not a video — one image.*
>
> *The system found two separate violations in it. No helmet, and three people on one motorcycle. It produced two separate fines.*

## Slide 10 — The bystander is not counted

**This is the slide to be proud of. Slow down here.**

> *Look at this one carefully.*
>
> *The rider on the scooter has no helmet, and she is fined.*
>
> *But look at the person crouching right next to the bike. He overlaps it. A naive system counts him as a passenger and issues a triple-riding fine. Ours does not — it matches riders to their motorcycle using geometry, so he is correctly ignored.*
>
> *Anybody can draw a box around a motorcycle.* ***Judging correctly is the hard part.*** *That is the whole product.*

## Slide 11 — Number plates

> *A fine without a number plate is useless. So we read plates on a real Sri Lankan road.*
>
> *One hundred and fifty vehicles tracked. Plates read and confirmed.*
>
> *But here is the rule we set for ourselves. A number plate is only written onto a fine when* ***three separate reads agree*** *with each other. If they do not agree, the system writes UNREADABLE.*
>
> *We never invent a number. A wrong plate on a fine is worse than no fine at all — because it punishes an innocent person.*

## LIVE DEMO — four minutes

**[Switch your share to the browser. Dashboard already open and warmed up.]**

| Do this | Say this |
|---|---|
| Play **sample_1080p.mp4** | *This is a real camera feed going through the AI right now. Watch the boxes appear. Those speeds are being calculated live.* |
| Click an **Over Speeding** challan | *Here is the fine. Photograph, speed, plate crop, the amount, and a PDF ready for the police. Nobody typed any of this.* |
| Click **Send to Police** | *And the whole package goes to the traffic mailbox automatically.* |
| Upload **triple_phone.jpg** | *Now a single photograph. Two violations, two fines, about two seconds.* |
| Play **srilanka.mp4** | *Now watch the violation counter. It stays at zero. These motorcycles are parked. Forty-one vehicles, zero fines. Ask any other team what their system does with a parked bike.* |
| Open the **Vehicles / ANPR** tab | *And every vehicle is logged with its plate, whether it broke a rule or not. That is the searchable record that was missing.* |

**[Switch back to the slides.]**

## Slide 12 — What the camera can and cannot see

> **This is your strongest moment. Do not skip it, and do not apologise while
> saying it.** Every other team will claim everything works perfectly. You will
> be the only team that explains its limits — and judges notice that.

> *I want to answer a question before you ask it.*
>
> *Every rule is built and tested. But you did not see all nine fire in that demo. Here is the honest reason.*
>
> ***Every rule needs a particular camera view.***
>
> *Helmet and triple riding need any view where the rider is visible. We have that footage, so you saw those work.*
>
> *Speed needs four surveyed road corners. We calibrated two cameras, so you saw speed work on those.*
>
> *Red light jumping needs the stop line, and it needs to know which signal head controls which lane — a junction has four or five signals facing different directions. Once you calibrate a junction it fires. We will not guess where the line is.*
>
> *Illegal parking needs a fixed camera, because you cannot prove a vehicle is still if the camera itself is moving.*
>
> *And seatbelt and phone use need a front view of the driver, close enough to resolve a chest and a hand. A fleet operator's in-cab camera has that. Road CCTV pointed down a carriageway does not.*
>
> *We could have staged these. We chose not to. We demonstrate only what our footage genuinely contains — because fabricated evidence is exactly the thing this system exists to prevent.*

## Slide 13 — Why it can be trusted

> *So what makes this trustworthy?*
>
> *Parked vehicles are never fined. Forty-one vehicles, zero violations.*
>
> *Unreadable plates say unreadable.*
>
> *No calibration means no speed, rather than a misleading number.*
>
> *A violation has to persist across several frames, so a single strange frame cannot fine anybody.*
>
> *And if one of our own models cannot prove it is reliable, we switch it off rather than trust it.*

## Slide 14 — Engineering rigour, and the handover

> *That last point is not theoretical. Let me tell you what happened this week.*
>
> *We tested our own seatbelt model properly for the first time — and it failed. It reported "no seatbelt" on a driver who was clearly wearing one, and on a photograph of an empty motorway.*
>
> *We had a choice. Ship it and hope no judge noticed, or switch it off and tell you.*
>
> *We switched it off. The system now refuses to load any model that cannot localise what it is accusing, and it prints a warning when it does.*
>
> *That is one of eight cases where we found our own system accusing the wrong person. A stopped car fined for a red light belonging to another lane. Helmeted riders flagged for no helmet. A sleeping driver tagged as being on the phone.*
>
> *We fixed every one, and each of them is now an automated test. Eighty-five tests, all passing.*
>
> ***That restraint is not a limitation of the product. It is the product.***
>
> *[Name] will now tell you what this becomes as a business.*

**[Stop sharing the browser. Go back to slides. Mute.]**

---

# SPEAKER 3 — The business (5 minutes)

This is a **startup** competition, not a science fair. The panel is listening
for one thing: **does this survive outside a laptop?**

> ⚠️ **Never invent a revenue number.** If they push for figures, say you will
> model them from pilot data. A made-up projection is the one thing that would
> contradict everything Speaker 2 just said.

## Slide 15 — What makes it different

> *Thank you [name].*
>
> *Let me put us next to what already exists.*
>
> *Typical systems do one thing. A speed camera measures speed. A plate reader reads plates. They give you a number with no proof attached. And they usually need dedicated hardware installed at every site.*
>
> *We run many rules on one engine, on any camera. Every fine carries a stamped photograph and a plate crop. And we run on cameras that already exist, on a laptop processor.*
>
> *Our real advantage is not the detection. Anybody can download a detection model. Our advantage is the engineering that makes it* ***refuse to guess.*** *That took months, and it is very hard to copy — because you only find those cases by testing on real roads.*

## Slide 16 — Who it is for

> *Three groups of users.*
>
> ***First, the police traffic division.*** *They get enforcement reach without hiring more officers.*
>
> ***Second, the Road Development Authority and municipal councils*** *— highway corridors, school zones, hospital zones.*
>
> ***Third — and this is the one that pays fastest — commercial fleet operators.*** *Bus and lorry companies. They need seatbelt and driver fatigue compliance, and they have a direct financial reason to want it: insurance and liability.*
>
> *We do not need to win the whole country on day one. We need one pilot junction. Then a corridor. Then a city.*

## Slide 17 — Business model

> *Four revenue lines.*
>
> *A one-off deployment fee to set up and calibrate a camera site.*
>
> *An annual software licence per camera, which covers updates and improved models.*
>
> *An analytics tier for authorities — dashboards, reporting, repeat offender analysis.*
>
> *And a per-vehicle compliance package for fleet operators.*
>
> *The important part is our cost base. Because we need no new cameras and no hardware at each site, a pilot is software and calibration only. Our cost to add the tenth camera is far lower than our cost to add the first.*

## Slide 18 — Sustainability

> *Sustainability, in three ways.*
>
> ***Economically,*** *it runs on infrastructure the country has already paid for. There is no capital barrier to starting. And recovered fines fund the next camera, so it does not need permanent subsidy.*
>
> ***Socially,*** *it applies exactly the same rule to every driver. No discretion, no negotiation at the roadside. And the goal is deterrence, not punishment — a road where people wear helmets because they know the camera is awake.*
>
> ***And on privacy,*** *which matters because number plates identify real people. A plate is only written after three independent reads agree. Evidence stays with the operator and is attached only to that one specific fine. We do not build profiles of people.*

## Slide 19 — Scalability

> *Where this goes.*
>
> ***Today,*** *a working system, eighty-five tests, verified on real Sri Lankan road footage.*
>
> ***In three months,*** *a live pilot at one signalised junction with a police partnership, plus models trained for night and rain.*
>
> ***In six to twelve months,*** *a corridor deployment on GPU edge boxes, and a trained three-wheeler class — because our roads are full of them and standard models do not know what they are.*
>
> ***Beyond that,*** *a city-wide dashboard, and export. Nothing in this software is specific to Sri Lanka. India, Bangladesh and Pakistan have the same roads and the same problem.*

## Slide 20 — The close

**[Slow down. This is the last thing they hear. Look at the camera.]**

> *So, to finish where we started.*
>
> *That man riding without a helmet this morning passed a camera that saw him perfectly, and nothing happened.*
>
> *Real speed. Verified number plates. Automatic fines with the photograph attached. On the cameras this country already owns.*
>
> ***Safer roads, proven by evidence.***
>
> *Thank you. We would be happy to take your questions.*

---

# Questions the judges will ask

The name in brackets is who answers. **Do not all speak at once** — that is the
most common mistake on a video call. If a question is not yours, stay muted.

## Sri Lanka context questions

These come from a local panel and they are the ones teams usually fumble.

| Question | Answer |
|---|---|
| **Have you spoken to the Sri Lanka Police?** | Not formally yet. That is our next step and the reason we are here. We built the system first so that conversation starts with a demonstration, not a proposal. |
| **Our roads are full of three-wheelers. Does it handle them?** | Honestly, not as a separate class yet. The standard model was trained on international data and usually labels a tuk-tuk as a truck. It still tracks it, still reads its plate, still catches its violations — but the label is wrong, and a trained three-wheeler class is explicitly on our six-month plan. |
| **What about a rider with no helmet carrying a child?** | The system detects each rider on the motorcycle independently, so it will record both the helmet violation and the rider count. What the fine should be is a policy decision for the police, not for us — we supply the evidence. |
| **Sri Lankan plates have Sinhala characters and provincial letters. Can it read them?** | It reads the Latin letters and digits, which is what identifies the vehicle on the register. We deliberately do **not** reformat a read to fit a national plate grammar, because that turns a bad read into a confident wrong answer. Provincial prefixes are the next OCR improvement. |
| **Our junctions are chaotic — motorcycles between lanes, no lane discipline. Will it cope?** | That is exactly why we built the false-positive gates. In heavy mixed traffic a naive system produces hundreds of wrong fines. Ours needs motion, persistence across frames, and geometric association before it will accuse anyone. It will report fewer violations than a naive system — and that is the point. |
| **What about rain and the monsoon?** | Detection degrades in heavy rain, like any camera system. Our models are drop-in files, so a weather-trained model swaps in with no code change. We would rather tell you that now than have you discover it in November. |
| **Who pays the fine, and how is it collected?** | We do not collect fines. We produce the evidence package and the challan; issuing and collection stay entirely with the police, inside their existing legal process. We are the eyes, not the court. |
| **What if an officer or a politician wants a fine removed?** | Every violation carries a photograph and a timestamp, and the record is in the system before any human sees it. That does not eliminate discretion, but it makes quiet deletion visible. |
| **Is our internet and power reliable enough?** | A pilot site runs entirely on one local machine — no cloud dependency. It stores locally and syncs when a connection is available. Power is the same constraint every CCTV camera already has. |
| **Why should a Sri Lankan authority buy from students?** | Because we built the thing, we tested it on Sri Lankan footage, and we found and fixed our own failures rather than hiding them. We are asking for a pilot junction, not a national contract. |

## Business questions *(Speaker 3)*

| Question | Answer |
|---|---|
| **Who actually pays for this?** | Police and municipal councils buy enforcement capacity. Fleet operators buy compliance monitoring, and they buy fastest because it lowers their insurance exposure. A pilot needs no new cameras and no civil works, so the buying decision is small. |
| **What are your revenue projections?** | We have not published projections, because we do not have pilot data yet and we will not invent numbers. What we can tell you is the cost structure: a pilot is software and calibration only, and the marginal cost of each additional camera falls. |
| **What stops a big company copying you?** | The detection model is public — anyone can download it. What took us months is the layer that stops false accusations: motion gates, persistence checks, plate voting, calibration, model validation. That is the moat, and it only comes from testing on real roads. |
| **Is this sustainable without grants?** | Yes. It runs on infrastructure already paid for, so there is no capital barrier, and recovered fines fund expansion. |
| **How do you get the first customer?** | One junction, one police partnership, at our cost. We are asking for a pilot site, not a purchase order. |
| **What is your team's plan after the competition?** | Get the pilot. Everything else follows from having one real junction running for three months. |

## Technical questions *(Speaker 2)*

| Question | Answer |
|---|---|
| **How accurate is the speed?** | Exact when calibrated. Four surveyed road corners map pixels to metres, then we fit distance against time across many frames with outlier rejection. Replay accuracy is 0.99–1.01× true speed. Uncalibrated cameras show no speed at all. |
| **Why did seatbelt not fire in the demo?** | Two reasons, and I will give you both. It needs a front view of the driver, which our road footage does not have. And when we tested our seatbelt model properly, it failed — it called a belted driver "no seatbelt". We disabled the rule. The system now refuses to load a model that cannot localise what it accuses. |
| **Why did illegal parking not fire?** | It needs a fixed camera. You cannot prove a vehicle is stationary if the camera itself is moving, and our clip was filmed by hand while walking. The system correctly refused to accuse anyone. |
| **How do you avoid false positives?** | Four layers: a confidence floor, a motion gate, multi-frame persistence, and a confidence gate on speed. We found and fixed eight real false-positive defects by testing on real footage, and each is now a test. |
| **What if the plate is unreadable?** | It says UNREADABLE. We never invent a number. A wrong plate on a fine is worse than no fine. |
| **Why is it not analysing every frame?** | Because it is real-time. On a laptop CPU we analyse about two frames a second and drop the rest, exactly as a live camera does. A GPU edge box analyses every frame. |
| **Can it be fooled by a covered plate?** | The violation is still recorded with photographic evidence; only the plate field says UNREADABLE, and it goes to a human for review. Deliberately obscuring a plate is itself an offence. |
| **Is this just YOLO with a dashboard?** | YOLO tells you a motorcycle is present. It does not tell you the rider has no helmet, how fast they are going in km/h, whether they are parked, or what their plate is. Everything between detection and a defensible fine is ours. |

## Awkward questions *(whoever is asked — answer calmly)*

| Question | Answer |
|---|---|
| **Is this a real product or a student project?** | It is a working system with 85 automated tests, verified on real Sri Lankan road footage. It is not yet deployed at a live junction — that is exactly what we are here asking for. |
| **What if the AI fines an innocent person?** | That is the risk we designed against hardest. Every fine carries the photograph, so a human can check it in two seconds. And we found and fixed eight such cases in our own system before today. |
| **Is this surveillance? What about privacy?** | Driving on a public road is already a licensed, regulated activity, and these cameras already exist. We keep evidence attached to a specific offence, confirm a plate three times before recording it, and build no profiles of people. |
| **Isn't this just punishing poor people who cannot afford helmets?** | The goal is deterrence, not revenue. A camera that everyone knows is awake changes behaviour before it issues a single fine — and the people who die on these roads are overwhelmingly the same people. |
| **Who on the team did what?** | Answer honestly and briefly. Name the three roles and move on. |

---

# Six rules for the call

1. **Join at 8:25 AM.** Not 8:29.
2. **Only one person unmuted at a time.** On a video call, two voices sound like chaos.
3. **Cameras on for all three**, at the start and during Q&A. During the demo, whoever is not speaking turns their camera off to save bandwidth.
4. **Never say "sorry, this isn't working".** Say *"let me show you the recorded run"* and keep going.
5. **If you do not know an answer, say so**, then say what you would do to find out. Judges respect that far more than a bluff.
6. **Finish on time.** Stopping at 21 minutes with a strong close beats being cut off at 25.
