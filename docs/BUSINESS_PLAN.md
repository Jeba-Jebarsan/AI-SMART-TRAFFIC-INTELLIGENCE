# Round 2 — Business Plan

**Team Three Hacks | AI Smart Traffic Intelligence Platform**
Startup Innovation Competition 2026 — Second Round

---

## 0. What the judges asked, and where each answer lives

The Round-1 panel stopped us on time, said the idea and the build were good, and
asked for seven things. This document answers all seven. Use this table to find
any answer in ten seconds during Q&A.

| # | What the judge asked | Section |
|---|---|---|
| 1 | How will you sell it? Who is the customer? | 1, 2 |
| 2 | How do you connect with the Sri Lanka Police / government? | 2 |
| 3 | At full scale, how do you get the zone data — speed limits, parking areas, road limits? | 3 |
| 4 | How do you import data from existing CCTV? | 4 |
| 5 | Proper revenue model — what it costs you, what you earn from one province | 5, 6, 7 |
| 6 | Proper SWOT analysis | 8 |
| 7 | How do you implement it in the real world, and what will go wrong? | 9, 10 |
| + | How do people subscribe or licence it? | 5.2 |

**The one-sentence answer to all of it:** we sell *coverage*, not software — a
police force pays roughly LKR 4,500 a month for a camera that watches one point
of road 24 hours a day, against roughly LKR 300,000 a month for the three
constables it would take to do the same shift pattern, and every fine our system
proposes comes with a timestamped photograph that a human officer signs before
it is issued.

---

## 1. Who actually pays

There is a difference between the people who *benefit* and the people who
*sign*. Getting that wrong is how good ideas die in Sri Lanka.

| Segment | Who signs | Why they buy | Sales cycle |
|---|---|---|---|
| **Municipal councils** (Colombo MC, Kandy MC, Moratuwa, Negombo, Galle) | Municipal Commissioner | They already own CCTV and get no value from it; congestion and parking chaos is their daily political pain | 1–3 months |
| **Sri Lanka Police — Traffic Division** | Ministry of Public Security, via Police HQ | Manpower shortage; cannot put officers everywhere; wants evidence that survives a dispute | 12–24 months |
| **Road Development Authority / Expressways** | RDA Expressway Division | Speed enforcement on E01/E02/E03 is already camera-based and already budgeted | 6–12 months |
| **Private fleets** (bus operators, logistics, plantation, courier, factory yards) | Fleet owner / CEO | Insurance premiums, crash liability, driver behaviour, cargo loss | 2–6 weeks |
| **Insurers** | Head of Motor | Better risk pricing; a fleet with our scorecard is measurably lower risk | 3–6 months |
| **Universities, ports, BOI zones, hospitals** | Facilities / Security head | Private roads, no legal complexity at all, they can just buy it | 2–6 weeks |
| **Donor programmes** (ADB, World Bank, WHO road-safety) | Programme manager | Road-safety targets with money attached and no police budget line needed | 6–12 months |

**The strategic point:** the police are the *biggest* customer and the *slowest*
customer. A three-person team cannot survive a two-year procurement cycle with
no revenue. So we run two tracks in parallel — a **private track that pays the
bills** and a **government track that builds the legitimacy**. Section 2 is how
those two tracks connect.

---

## 2. Go-to-market: how we actually reach the Sri Lanka Police

We do not walk into Police HQ and ask for a contract. That is not how it works
and pretending otherwise is the fastest way to lose credibility with this panel.
We climb a ladder, and each rung is something the other side can say yes to
without spending money or taking a risk.

### Rung 1 — Give away evidence, not enforcement (month 0–3)

A free 30-day **Road Safety Audit** at one junction for one municipal council.
We issue **zero fines**. We hand over a report:

> At this junction, over 30 days: 1,412 riders without helmets, 87 wrong-way
> movements, peak offending 07:10–08:30 and 17:40–19:00, this is the map of
> where it happens.

Nobody gets fined, so nobody gets angry, so nobody has to be brave to say yes.
The council gets data it has never had in its life. **Cost to us: two cameras and
a month of electricity. Value to us: the first real reference in the country.**

*Route in:* the OIC of the local traffic division, or the Municipal Commissioner.
Both are reachable through a university introduction, a Chamber of Commerce
event, or simply a letter — this is Sri Lanka, the country is small, and a
working demo opens doors that a slide deck does not.

### Rung 2 — Get a named champion (month 3–6)

Take that report to the **National Council for Road Safety** (under the Ministry
of Transport & Highways) and to Police Traffic HQ. The NCRS exists specifically
to reduce road deaths, has the mandate, and has thin data. We ask them for
exactly one thing, and it is free for them to give:

**A letter of support for a supervised pilot.**

That letter is the single most valuable asset in this whole plan. It costs the
ministry nothing, and it is what makes every later conversation — procurement,
donors, investors, insurers — possible.

### Rung 3 — Supervised enforcement pilot (month 6–12)

One police division, cameras we install and control, and one non-negotiable rule:

> **The AI proposes. A police officer decides.** Every challan appears in an
> officer's review queue with the photograph, the rule, and the confidence. It
> becomes a fine only when a human presses approve.

This single design choice solves four problems at once: the legal admissibility
problem, the public-trust problem, the false-positive problem, and the "a robot
fined me" newspaper headline. It also happens to be how automated enforcement
was introduced in almost every country that did it successfully.

What we measure in the pilot, and publish:

- Officer minutes per challan issued (should collapse from ~20 to under 1)
- Violation rate at the junction, week 1 vs week 12 (should fall — deterrence is
  the actual product; fines are just the mechanism)
- Disputes raised, and disputes upheld (must be near zero, or we are not ready)
- False-positive rate, measured against officer rejections in the review queue

### Rung 4 — Procurement (month 12–24)

Two doors, and we go through the second one:

1. **Bid a tender directly.** Requires supplier registration, audited accounts,
   performance bonds, and the patience of a saint. We will register, but we do
   not plan around this.
2. **Sub-contract under an existing government IT integrator.** Somebody already
   holds the vendor registration and already maintains police or ICTA systems.
   They want new capability; we want their paperwork and their relationships.
   **This is the recommended path** — it converts a two-year procurement problem
   into a two-month partnership negotiation.

### The parallel track that keeps the lights on

While all of the above is happening, we sell to private fleets, universities,
ports and factory yards, which have **no procurement cycle at all**. A bus
company can sign in a week. This is not a distraction from the police plan — it
is what funds the police plan, and it produces the accuracy statistics we will
need when the police finally ask "how good is it, really?"

### The highest-leverage channel: insurance

Get **one** motor insurer to offer a premium discount to any fleet running our
driver scorecard. The moment that exists, the insurer's agents sell our product
for us to every fleet in their book, and we pay nothing for it. Low cost to
attempt, enormous payoff if it lands.

---

## 3. The hard question: where does the zone data come from at scale?

This is the question the panel pressed hardest on, and they were right to. Today,
for the demo, a human opens each clip and clicks four corners of the road and
types in the real-world distance. That lives in `data/calibration.json`. It is
fine for five cameras. It is **impossible for five thousand**.

Here is the answer, and it starts with an insight the demo currently hides.

### 3.1 There are two kinds of data, and they scale completely differently

| Kind | Example | Must it be per-camera? | Cost |
|---|---|---|---|
| **Camera geometry** — where the ground plane sits in *this* image | the 4-point homography, metres per pixel | **Yes.** Unavoidable. Every camera sees a different scene. | Minutes, once, per camera |
| **World knowledge** — what the law says about *this piece of road* | speed limit, no-parking zone, one-way direction, stop line, school zone | **No.** It belongs to the map, not the camera. | Once, nationally |

Our demo conflates the two, which makes the work look 100× bigger than it is.
Separating them is the whole solution.

### 3.2 Step one — geo-register each camera once (4 minutes)

Instead of clicking four corners and typing metres, the operator drags four
points on the camera image and the matching four points on a **satellite
basemap**. That produces a homography between image pixels and real-world
coordinates.

That single four-minute act then delivers, for free, everything we currently do
by hand:

- **Metres per pixel** → speed measurement
- **Stop-line position** → red-light rule, because the map knows where the
  junction line is
- **Legal direction of travel** → wrong-way rule, from the road centreline
- **No-parking polygons** → illegal parking, projected from the map into the
  camera's view automatically
- **School zones, bus halts, pedestrian crossings** → context rules

**The arithmetic:** 1,000 cameras × 4 minutes = 67 person-hours. Two people, two
weeks, for an entire province. That is a line item, not a blocker.

And it is done **once**. If a camera is physically moved or knocked, we detect it
automatically — the static background of the scene changes — and the system
raises "recalibrate me" and **stops enforcing the geometric rules** rather than
silently fining the wrong people.

### 3.3 Step two — import the world once, nationally

We do not create this data. It already exists, mostly in government hands. Our
job is ingestion, in this order of preference:

1. **RDA road register** — national road classes and centreline geometry.
2. **Survey Department of Sri Lanka / provincial GIS** — municipal boundaries,
   which is what legally determines whether a road is "built-up" and therefore
   what the default limit is.
3. **Local authority gazetted traffic schemes** — no-parking, one-way, bus halts.
   Municipal councils already hold these. They are currently paper and PDF.
   Digitising Colombo MC's schemes is a few weeks of work for one person, once,
   and then it never has to be done again.
4. **OpenStreetMap** — free, and already carries `maxspeed`, `oneway`, bus stops,
   crossings and school locations for urban Sri Lanka. Use as the bootstrap layer
   and the gap-filler.
5. **Statutory defaults** — where nothing at all is known, fall back to the
   default limit in the Motor Traffic Act for that road class and vehicle class.
   No sign, no survey, no data entry needed. **The law itself is the data.**
6. **Learned proposals** — after 30 days of watching, the system proposes changes
   for a human to approve: *"95% of vehicles here travel 38–46 km/h — is the
   posted limit right?"* or *"vehicles habitually stand here for 6+ minutes — is
   this a parking bay or a hotspot?"* Proposed, never auto-enforced.

### 3.4 Step three — refuse to guess. This is already built.

The reason the data problem does not stop us on day one is that the system
already knows what it does not know. We fixed exactly this before Round 1:

- `SPEED_APPROX = False` — no calibration, **no speed reading at all**. It used
  to guess, and it produced 155 km/h for a car sitting at a junction. We deleted
  the guess.
- `STOP_LINE_Y = None` — no surveyed stop line, **the red-light rule cannot
  fire**. There is a test that enforces this.

So an uncalibrated camera does not produce garbage. It produces less.

### 3.5 Which rules need world data, and which do not

| Rule | What it needs from the world | Live on day 1? |
|---|---|---|
| No Helmet | nothing | **Yes** |
| Triple Riding | nothing | **Yes** |
| Wheelie / stunt riding | nothing | **Yes** |
| Mobile Phone Use | nothing | **Yes** |
| No Rest Break | nothing (time only) | **Yes** |
| No Seatbelt | nothing (needs a working detector model) | model pending |
| Wrong Way | legal direction of travel | after geo-registration |
| Over Speeding | ground plane + posted limit | after geo-registration |
| Illegal Parking | no-parking polygon | after zone import |
| Red Light Jump | stop line + signal state | after geo-registration |

**Six of ten rules work on day one with zero map data.** We deploy immediately,
then enrich over weeks. That is land-and-expand applied to engineering, and it
means the customer sees value in week one instead of month six.

---

## 4. How we get data out of existing CCTV

### 4.1 We connect to their cameras; we do not ask them to change anything

Practically every installed CCTV camera and NVR in the country speaks **ONVIF /
RTSP**. We pull a stream. No firmware change, no rewiring, no new hardware on the
pole. If a council has 200 cameras, we can be reading them the same week.

### 4.2 Process at the edge — the arithmetic that decides everything

This is the point that makes the difference between "possible on Sri Lankan
municipal networks" and "not possible".

| Approach | Network load, 1,000 cameras | Verdict |
|---|---|---|
| Backhaul every video stream to a central server | 1,000 × 2 Mbps = **2 Gbps sustained**, ~21 TB/day | Impossible and unaffordable |
| Run detection on an edge box at the site, send **events only** | a challan is a JSON record + one JPEG ≈ 250 KB; at a generous 200 events/camera/day ≈ 50 GB/day, bursty, ~5 Mbps average | Runs on what is already installed |

That is roughly a **400× reduction in bandwidth**. One edge box (a Jetson Orin
Nano class device, or a small Intel box — our system runs on CPU today) handles
about four cameras, sits in the existing cabinet, and survives the link going
down by queueing events locally.

### 4.3 What we store, and what we do not

We keep the **evidence frame**, not the stream. Retention is set by the operator,
default 90 days, then automatic purge. That is deliberate: the Personal Data
Protection Act No. 9 of 2022 requires data minimisation and purpose limitation,
and "we kept every second of video of every citizen forever" is both a legal
problem and a political one.

### 4.4 The uncomfortable truth about the installed base

Most municipal CCTV in Sri Lanka was installed for theft and crowd monitoring. It
is mounted high, angled wide, and often 720p. That is fine for seeing a crowd and
useless for reading a number plate.

**Expect only around 40% of any existing camera estate to be usable for
enforcement without repositioning.** We budget for that in the pilot survey and
tell the customer before they sign, rather than discovering it afterwards. Where
cameras do not exist or cannot be reused, we supply our own — which is a hardware
revenue line, not a problem.

---

## 5. Revenue model

### 5.1 The principle: we sell coverage, priced against the cost of a constable

| | One traffic constable | One camera on our platform |
|---|---|---|
| Cost per month (all-in) | ~LKR 100,000 | LKR 4,500 subscription + LKR 1,250 amortised setup |
| Hours covered per day | 8 (one shift) | 24 |
| To cover one point 24/7 | **3 officers ≈ LKR 300,000/month** | **LKR 5,750/month** |
| Rules watched at once | 2–3 realistically | 10 |
| Produces photographic evidence | No | Every time |

**Roughly 50× cheaper per point-hour of coverage.** And we are not replacing
officers — we are telling them *where to stand*. That framing matters enormously
when the buyer is a police force with a union and a manpower shortage.

### 5.2 How you subscribe or licence it

| Tier | Who it is for | What you get | Price |
|---|---|---|---|
| **Audit** | First contact — a council or a division | 30-day road-safety report, 2 cameras, **no fines issued** | **Free** |
| **Enforce** | Municipal council, police division | Per camera, all 10 rules, dashboard, officer review queue, cloud or on-prem | **LKR 3,500** / camera / month |
| **Enforce + ANPR** | Same, where plates matter | Adds plate recognition, owner lookup, PDF challan export | **LKR 5,500** / camera / month |
| **Fleet** | Bus, logistics, plantation, courier | Depot and in-vehicle cameras, driver scorecards, monthly safety report | **LKR 25,000** / month up to 25 vehicles, then LKR 800 / vehicle |
| **Provincial Licence** | Ministry / Police HQ | Unlimited cameras in one province, **on-premise**, source-code escrow, 99.5% SLA, training, named support | **LKR 12,000,000** / province / year |
| **Insight** | Insurers, RDA, researchers, donor programmes | Anonymised aggregate risk maps and blackspot analytics — **no plates, no faces** | LKR 250,000 / report, or LKR 2,000,000 / year |

**One-time charges**

| Item | Price | What it covers |
|---|---|---|
| Site Activation | **LKR 45,000** / camera | Survey, geo-registration, zone import, acceptance test, officer training |
| Edge appliance | **LKR 138,000** / box (4 cameras) | Hardware at cost + 15%, 3-year warranty |
| Integration | Quoted | Links into DMT vehicle register, existing spot-fine and e-payment systems |

**Why on-premise matters:** a police force will not put criminal evidence in
somebody else's cloud, and it should not. The Provincial Licence exists precisely
because the biggest customer needs a deployment model the SaaS tier cannot offer.
That is not a compromise — it is the highest-margin product we sell.

### 5.3 What we will NOT do: take a share of the fines

We were asked how we earn, and the obvious-looking answer is "take 10% of every
fine". We are deliberately refusing it, for three reasons:

1. **It is probably not legal.** Fines under the Motor Traffic Act are public
   revenue. Assigning a slice to a private company is a serious constitutional
   and audit problem.
2. **It creates exactly the wrong incentive.** A company paid per fine is a
   company that wants more fines. Our actual goal is *fewer violations*. A
   successful deployment should see offending fall — and under revenue share,
   success would bankrupt us.
3. **It is politically fatal.** "Foreign-funded startup profits from fining
   Sri Lankan motorists" is a headline that ends the company in a week.

Subscription pricing means we get paid for **coverage and deterrence**, which is
the outcome the customer actually wants. We think this answer, not the revenue
number, is the mature part of our business model — and we expect a judge to test
us on it.

---

## 6. The numbers: from one province to national

**All figures LKR. Assumed rate LKR 300 = USD 1. These are our own modelled
assumptions, clearly labelled — see Section 13 for what must be verified before
we quote any of it as fact.**

### 6.1 Chosen beachhead: Western Province

Colombo, Gampaha and Kalutara. Highest vehicle density, highest crash count, the
most existing CCTV, the National Council for Road Safety and Police HQ are all
physically there, and it contains both the municipal customers and the fleet
customers. One province, walkable in a day, no domestic flights.

### 6.2 Year 1 — prove it (pilots + first paid deployments)

| Revenue line | Volume | Amount |
|---|---|---|
| Site activation | 80 cameras × 45,000 | 3,600,000 |
| Edge appliances | 20 boxes × 138,000 | 2,760,000 |
| Enforce subscriptions | 80 cameras × 4,500 × 8 months avg | 2,880,000 |
| Fleet subscriptions | 8 operators × 25,000 × 8 months | 1,600,000 |
| **Total revenue Y1** | | **10,840,000** (~USD 36,000) |

| Cost line | | Amount |
|---|---|---|
| Team (6 people, avg 200,000/month) | | 14,400,000 |
| Cloud, tooling, licences | | 1,800,000 |
| Hardware cost of goods | | 2,400,000 |
| Travel, legal, company formation, bid costs | | 3,000,000 |
| **Total cost Y1** | | **21,600,000** (~USD 72,000) |
| **Net Y1** | | **−10,760,000** |

**That deficit is the funding ask.** We are raising **LKR 15,000,000
(~USD 50,000)** for 18 months of runway with buffer.

### 6.3 Year 2 — own Western Province

| Revenue line | Volume | Amount |
|---|---|---|
| Site activation | 520 new cameras × 45,000 | 23,400,000 |
| Enforce subscriptions | 600 cameras × 4,500 × 12 | 32,400,000 |
| Provincial Licence — Western | 1 | 12,000,000 |
| Fleet | 40 operators avg 25,000 × 12 | 12,000,000 |
| Insight reports | 2 | 2,000,000 |
| **Total revenue Y2** | | **81,800,000** (~USD 273,000) |
| Total cost Y2 (14 people + infra + COGS + ops) | | 64,000,000 |
| **Net Y2** | | **+17,800,000 — breakeven year** |

### 6.4 Year 3 — three more provinces and the first export

| Revenue line | Volume | Amount |
|---|---|---|
| Enforce subscriptions | 2,200 cameras × 4,500 × 12 | 118,800,000 |
| Provincial Licences | 4 × 12,000,000 | 48,000,000 |
| Site activation | 1,600 × 45,000 | 72,000,000 |
| Fleet | 150 operators | 45,000,000 |
| Export pilot (regional) | ~USD 60,000 | 18,000,000 |
| **Total revenue Y3** | | **301,800,000** (~USD 1,000,000) |

### 6.5 The honest ceiling — and why that is fine

Fully saturated, Sri Lanka is roughly **5,000 enforcement cameras, 9 provincial
licences and a few hundred fleets ≈ LKR 480M ≈ USD 1.6M annual recurring
revenue.**

We will say this to the panel plainly, because they will work it out anyway:
**Sri Lanka alone is not a large enough market to build a large company in.**

It is, however, exactly the right market to *prove* one in — and the product
transfers without modification to Bangladesh, Nepal, Pakistan, Vietnam, Kenya,
Nigeria and Tanzania, where the road-death rate is worse, the traffic mix is the
same (motorcycles, three-wheelers, mixed lanes — the thing Western products are
*not* built for), and there is donor money attached to fixing it. Sri Lanka is
the reference customer, not the whole business.

### 6.6 Gross margin

| Tier | Direct cost per unit / month | Price | Gross margin |
|---|---|---|---|
| Enforce (cloud) | ~LKR 900 (compute, storage, support) | 3,500 | **74%** |
| Enforce + ANPR | ~LKR 1,500 | 5,500 | **73%** |
| Provincial Licence | ~LKR 250,000/month (support + on-site) | 1,000,000/month | **75%** |
| Edge hardware | 120,000 | 138,000 | 13% (deliberately near cost) |

Hardware is sold near cost on purpose. It is not a business; it is the thing that
gets our software onto the pole.

---

## 7. Cost structure and what we need

**Team we hire in Year 1 (6 people):** 2 ML/CV engineers, 1 backend/platform,
1 field deployment & calibration engineer, 1 business development, 1 founder on
partnerships and compliance.

**Use of the LKR 15M raise:** ~60% salaries, ~15% pilot hardware, ~10% legal and
data-protection compliance, ~10% field operations and travel, ~5% buffer.

**What we need that is not money:**

1. One letter of support from the National Council for Road Safety or Police
   Traffic HQ.
2. One municipal council willing to host a free 30-day audit.
3. An introduction to one government IT integrator with existing vendor
   registration.
4. Access to a labelled Sri Lankan traffic dataset — or the permission to build
   one.

---

## 8. SWOT

### Strengths

- **It exists.** A working system with 10 rules running on live video, 85
  automated tests, and evidence images we produced ourselves — not a mockup.
- **Built for Sri Lankan traffic.** Motorcycles, three-wheelers, mixed lanes,
  pillion riders. Most imported systems are tuned for orderly car traffic and
  degrade badly here.
- **It refuses to guess.** No calibration means no speed reading; no surveyed
  stop line means the red-light rule cannot fire. We deleted two features that
  produced confident wrong answers. In an evidence product, that restraint is
  the feature.
- **Cheap to run.** CPU-capable, edge-first, no GPU cluster and no fat network.
- **Local team, local cost base, local language support**, and the ability to be
  at the customer's junction the same afternoon.

### Weaknesses

- **No revenue, no reference customer, no registered company yet.**
- **No measured accuracy figure.** We have not yet benchmarked against a labelled
  Sri Lankan ground-truth set, so we cannot state a precision number — and a
  court will eventually ask for one. This is our top engineering priority.
- **The seatbelt rule does not work.** The model we obtained is a classifier that
  cannot localise a belt and fails to discriminate, so we disabled the rule
  rather than ship a feature that accuses innocent drivers. Honest, but it is a
  gap on the feature list.
- **Three part-time students.** No procurement experience, no legal counsel, no
  operations function.
- **We depend on somebody else's camera quality**, which we do not control.
- **Plate recognition is unproven on Sri Lankan plates at scale**, especially old
  plates, motorcycle rear plates, and mud.

### Opportunities

- **Roughly 3,000 road deaths a year** and enforcement is still manual and
  spot-based. The gap between what happens and what is caught is enormous.
- **Existing municipal CCTV is a sunk asset** we can activate for near-zero
  marginal cost — the buyer has already paid for the hard part.
- **PDPA No. 9 of 2022** creates a compliance burden that large foreign vendors
  handle badly and a local team can handle natively. Regulation as a moat.
- **Donor funding for road safety** (ADB, World Bank, WHO Decade of Action
  2021–2030) can fund pilots without touching a police budget line.
- **The fleet and insurance market needs no government sale at all.**
- **Regional export** — same traffic mix, worse problem, bigger budgets.

### Threats

- **Global smart-city vendors bundling ANPR free with hardware.** Hikvision,
  Dahua, Huawei and their integrators can give the software away to win the
  camera contract. **This is our single biggest commercial threat**, and Section
  11 is our answer to it.
- **Procurement risk** — tenders written around an incumbent, or simply never
  issued.
- **Political change** resetting our sponsor and restarting the relationship from
  zero.
- **Public and media backlash** — "surveillance state", "AI is fining people".
- **One high-profile false positive** destroying trust faster than a hundred
  correct detections build it.
- **Legal challenge** to machine-generated evidence.
- **Team attrition** — we are students, and graduation is a real risk to
  continuity.
- **Import cost and currency volatility** on edge hardware.

---

## 9. Real-world implementation roadmap

| Phase | Months | What we do | Done when |
|---|---|---|---|
| **0. Harden** | 0–3 | Register the company. Build a labelled Sri Lankan ground-truth set and publish real precision/recall. Fix or replace the seatbelt detector. Build the officer review queue. PDPA gap assessment. | We can state an accuracy number and defend it |
| **1. Audit** | 2–5 | Free 30-day road-safety audit at 2 junctions with 1 municipal council. No fines. | A signed report with a council logo on it |
| **2. Champion** | 4–7 | Take the report to NCRS and Police Traffic HQ. | A letter of support in hand |
| **3. Supervised pilot** | 6–12 | 20–40 cameras in one division. Every challan human-approved. Publish officer-time and violation-rate results. | Disputes upheld ≈ 0; officer time per challan under 1 minute |
| **4. Commercial base** | 3–12 | In parallel: 8 fleet customers, 2 universities/ports. | Revenue covering more than half of burn |
| **5. Province** | 12–24 | Western Province at 600 cameras. Sign the provincial licence. Integrate with DMT and the e-payment system. | Breakeven |
| **6. Scale + export** | 24–36 | 3 more provinces. First regional pilot. | USD 1M run rate |

### The three integrations that make it real

1. **Department of Motor Traffic vehicle register** — plate to registered owner.
   Without it a challan cannot be delivered. This requires a formal data-sharing
   agreement and is the longest-lead item in the whole plan; we start it in
   Phase 2, not Phase 5.
2. **The existing spot-fine / e-payment rails** — we must issue into the system
   citizens already use, not invent a new one.
3. **Police case management** — a challan that gets disputed has to flow into the
   existing process.

### Legal foundation we build on

- **Evidence (Special Provisions) Act No. 14 of 1995** — the statute that makes
  computer-generated evidence admissible in Sri Lanka, subject to proving the
  system was operating properly. **This is why our audit trail, our calibration
  records, and our "refuse when uncalibrated" behaviour are legal assets, not
  just good engineering.**
- **Electronic Transactions Act No. 19 of 2006 (as amended)** — legal validity of
  electronic records and signatures.
- **Personal Data Protection Act No. 9 of 2022** — lawful basis, data
  minimisation, retention limits, subject access. We design to it from day one.
- **Motor Traffic Act (Chapter 203)** — the offences themselves and the spot-fine
  mechanism.

---

## 10. What will go wrong, and what we do about it

| Challenge | Why it bites | What we do |
|---|---|---|
| **Procurement takes 2 years** | We run out of money first | Private-sector revenue track funds us; sub-contract under a registered integrator instead of bidding alone |
| **Is AI evidence admissible?** | A dispute could invalidate every challan | Human officer approves every fine; full audit trail; calibration certificate per camera; build to the Evidence (Special Provisions) Act |
| **Privacy backlash / PDPA** | Reputational and legal | No face recognition. Plates only, for a lawful purpose. 90-day retention then auto-purge. Published policy. Anonymised analytics tier |
| **"Big Brother" media story** | Kills political sponsorship | Lead with deterrence and lives, not fines. Publish violation-rate reductions, not revenue collected. Refuse fine revenue share (Section 5.3) |
| **Existing cameras are the wrong quality/angle** | Half the estate is unusable | Survey before signing; state the usable percentage up front; sell our own cameras where needed |
| **Poor plate images at night / in rain** | ANPR accuracy collapses | Never issue a challan on a low-confidence plate — route to human review. Vote-pool multiple reads. IR-capable cameras at ANPR sites |
| **A false positive fines an innocent person** | One story destroys years of trust | Human approval gate; confidence thresholds tuned for precision over recall; visible one-click dispute; publish our own error rate |
| **Power cuts and network drops** | Sri Lankan reality | Edge box with local queueing and UPS; events sync when the link returns; nothing is lost |
| **Corruption / "make this challan disappear"** | Undermines the entire product | Immutable append-only audit log; every view, approval and cancellation attributed to a named officer; supervisor reporting on cancellation rates |
| **Chinese vendors bundle it free** | We cannot beat free on price | Compete on Sri Lankan accuracy, local support, PDPA compliance, and data sovereignty — and sell as software onto *their* installed hardware rather than against it |
| **Political change resets the sponsor** | Six months lost | Cultivate the permanent civil service and NCRS, not the minister; keep municipal and private revenue independent of national politics |
| **Team graduates and disperses** | The company stops | Incorporate with a real vesting agreement now; hire the first engineer with the seed round |
| **Officers resist — it threatens overtime and discretion** | Quiet non-adoption kills pilots | Position it as *deployment intelligence* — it tells them where to stand — never as a replacement. Involve the OIC in designing the review queue |

---

## 11. Competition, and why we survive it

| Competitor | Their strength | Our answer |
|---|---|---|
| **Hikvision / Dahua / Huawei integrators** | Bundle ANPR free with the camera contract; unbeatable on price | We run *on top of* their hardware. Sell the software layer to the same buyer. Compete on local accuracy, PDPA compliance and data sovereignty — three things a foreign black box cannot offer a police force |
| **International ITS vendors (NEC, Siemens, Kapsch)** | Credibility, references, full stack | 10–50× our price and tuned for orderly car traffic. They lose money on a Sri Lanka-sized contract; we do not |
| **Local system integrators** | Government relationships, vendor registration | Partner, do not fight. They want new capability; we want their paperwork |
| **In-house government build (ICTA / university)** | Free, politically easy | Slow, unmaintained after the grant ends. We are the maintained option — and we can be the vendor *to* the in-house programme |
| **Do nothing** | Costs nothing today | The honest incumbent, and our real competitor. Beat it with the free 30-day audit that makes the invisible problem visible |

**Where the defensibility actually is** — and it is not the model, because anyone
can download YOLO:

1. **The calibrated camera estate.** A thousand geo-registered cameras is months
   of field work a competitor must repeat from scratch.
2. **Workflow lock-in.** Once challans flow through our review queue and officers
   are trained on it, switching costs are measured in retraining, not licences.
3. **A labelled Sri Lankan dataset** — plates, helmets, three-wheelers, night,
   monsoon — that no foreign vendor has and cannot easily build.
4. **Legal precedent.** The first vendor whose challan survives a court challenge
   effectively owns the category.
5. **Cost structure.** A local team on an LKR cost base undercuts anyone
   importing engineers.

---

## 12. The metrics we will be judged on

| Metric | Y1 target | Why it matters |
|---|---|---|
| Cameras live | 80 | The unit we sell |
| Paying customers | 10 | Proof it is a business, not a project |
| Precision on the ground-truth set | > 95% per enforced rule | Our licence to operate |
| Disputes upheld against us | < 0.5% | Legal survival |
| Officer minutes per challan | < 1 (from ~20) | The buyer's actual ROI |
| Violation rate at pilot junctions, wk1 → wk12 | −25% | **The outcome that justifies the whole thing** |
| Gross margin | > 70% | It scales |
| Monthly burn | < LKR 1.8M | Runway |

---

## 13. Numbers we must verify before quoting them as fact

We are stating these as our own modelled assumptions in Round 2, not as
established facts, and we should verify each before it goes on a slide:

- Exact annual road-death and serious-injury figures — source: Sri Lanka Police
  Traffic Division / National Council for Road Safety statistics
- Current spot-fine amounts under the Motor Traffic Act (they were amended
  recently)
- The statutory speed-limit table by road class and vehicle class
- Number of CCTV cameras already installed by Colombo MC and other councils
- Actual all-in monthly cost of a traffic constable
- Registered vehicle counts by class — source: Department of Motor Traffic
- Current LKR/USD rate at presentation time
- The economic cost of road crashes as a share of GDP (ADB/WHO studies exist)

**Saying "this is our assumption, here is our working, and here is what we would
verify" is stronger in front of a panel than quoting a confident number we cannot
source.**

---

## 14. Expected Round-2 judge questions

### On the business model

**"Why won't the police just build this themselves?"**
> They could, and a university project probably will. The question is who
> maintains it in year three when the grant ends and the student has graduated.
> We are selling maintained capability with an SLA and someone to call, and we
> are happy to be the vendor to a government programme rather than its rival.

**"Why subscription and not a share of the fines?"**
> Three reasons. Fines are public revenue and assigning a private share of them
> is an audit and constitutional problem. Being paid per fine means wanting more
> fines, and our goal is fewer violations — success would bankrupt us. And
> "startup profits from fining motorists" ends the company in a week.
> Subscription pays us for coverage and deterrence, which is what the customer
> actually wants.

**"LKR 3,500 per camera — how did you get that number?"**
> By pricing against the alternative. Covering one point around the clock takes
> three constables, roughly LKR 300,000 a month. We are about fifty times
> cheaper per point-hour, our gross margin at that price is about 74%, and it is
> small enough to fit in a council's existing maintenance budget without a new
> approval.

**"Sri Lanka is too small a market."**
> Agreed, and we will say it before you do — fully saturated, Sri Lanka is about
> USD 1.6M of annual recurring revenue. Sri Lanka is where we prove it. The same
> product, unchanged, addresses Bangladesh, Nepal, Pakistan, Vietnam and East
> Africa, where the traffic mix is identical, the death rate is worse, and there
> is donor money attached.

**"Who is your first paying customer, realistically?"**
> Not the police. A private fleet or a university campus — private roads, no
> legal complexity, a decision-maker who can sign in a week. That revenue funds
> the two-year government track.

### On implementation

**"How do you get the parking zones and speed limits for a whole city?"**
> By separating two things our demo currently mixes up. Camera geometry has to be
> done once per camera — four minutes of clicking, 67 person-hours for a thousand
> cameras, two people for two weeks. World knowledge — limits, no-parking, one-way
> — belongs in the map, not the camera, and it already exists in the RDA road
> register, municipal gazetted schemes and OpenStreetMap. Where nothing is known,
> we fall back to the statutory default for that road class. And where we still
> do not know, the rule simply does not fire — six of our ten rules need no map
> data at all, so we deploy on day one and enrich over weeks.

**"What if the camera gets moved?"**
> We detect it — the static background of the scene changes — and the system
> stops enforcing the geometric rules and asks to be recalibrated, rather than
> silently fining the wrong people.

**"Can you handle a thousand cameras?"**
> Not by sending a thousand video streams anywhere — that is 2 Gbps sustained and
> it would not work on Sri Lankan municipal networks. We process at the edge and
> send only events. A challan is about 250 KB. That is roughly a 400× reduction,
> and it is the reason this is deployable on infrastructure that already exists.

**"Is your evidence admissible in court?"**
> The Evidence (Special Provisions) Act No. 14 of 1995 makes computer-generated
> evidence admissible if you can show the system was operating properly. So we
> keep a calibration certificate per camera, an immutable audit log, and — most
> importantly — a police officer approves every single challan before it is
> issued. The AI proposes; a human decides. We are not asking a court to trust an
> algorithm.

**"What about privacy?"**
> No face recognition, ever. Plates only, for a lawful enforcement purpose,
> retained 90 days and then automatically purged. That is designed against the
> Personal Data Protection Act No. 9 of 2022, and our analytics product is fully
> anonymised — no plates, no faces.

**"What is your accuracy?"**
> We do not have a defensible published number yet, and we are not going to
> invent one. Building a labelled Sri Lankan ground-truth set and publishing real
> precision and recall per rule is our number-one engineering priority before any
> enforcement pilot. What we can show today is the opposite discipline: we
> disabled our speed estimate and our red-light rule on uncalibrated cameras, and
> we disabled the seatbelt rule entirely, because they produced confident wrong
> answers.

### The awkward ones

**"You are three students. Why you?"**
> Because we built it, it runs, and we are here. We are not claiming to be the
> people who will negotiate a national procurement contract — that is why our
> plan sub-contracts under an existing registered integrator instead of bidding
> alone. What we bring is a working system tuned for Sri Lankan traffic and a
> cost base no foreign vendor can match.

**"Hikvision will give this away free with their cameras."**
> That is our single biggest commercial threat and we plan for it directly. Our
> answer is not to compete on price. It is to run on top of their hardware and
> sell the layer they cannot: accuracy on Sri Lankan traffic, PDPA compliance,
> data that stays in the country, and an engineer who arrives the same afternoon.

**"What if the government says no?"**
> Then we have a fleet, insurance and campus business that does not need them,
> and we build the accuracy record and the reference customers that make the
> answer different in two years. The government track is the biggest prize, not
> the only one.

**"What happens when you graduate?"**
> We incorporate now with a vesting agreement, and the first use of the seed
> round is a full-time engineer. We are not pretending this survives on
> goodwill.

---

*Prepared by Team Three Hacks for the Startup Innovation Competition 2026,
second round. Financial figures are our own modelled assumptions and are labelled
as such; see Section 13.*
