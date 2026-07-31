# What footage to record — and why each rule needs it

Every rule below is **already built and tested**. What it is missing is footage
in which the offence is physically visible. This is a filming task, not a coding
task — you can do all of it with a phone in under an hour.

**Send me the files and I will run them and produce the evidence images.**

---

## Ground rules for every clip

| Rule | Why |
|---|---|
| **Landscape**, not portrait | Matches a real camera and fills the slide |
| **1080p**, 30 fps | Higher just costs decode time; lower loses plates |
| **Phone completely still** — wall, ledge, bottle, books | A moving camera makes "is this vehicle stationary?" unanswerable |
| **At least 60 seconds** | Several rules need 20+ seconds of continuous observation |
| **Daylight, plate visible** | OCR needs roughly 40+ pixels of plate width |
| Don't zoom mid-clip | Zooming invalidates the geometry |

---

## 1. Illegal Parking — highest value, easiest to get

> **This is the one your crossing photo could not prove.** Parking means a
> vehicle that stays put. The scooter in that photo had been moving seconds
> earlier, so the system correctly refused to call it parked.

**Shot:** phone propped **completely still** on a wall, aimed at a parked car or
motorcycle by a kerb. Let it run **90 seconds**. The vehicle must never move,
and ideally other traffic drives past in the same frame.

**Why it will fire:** the rule needs 20 seconds stationary, 12+ observations,
and the vehicle never seen moving. Passing traffic in shot is a bonus — it
proves the system tells parked from moving in one frame.

✅ **You need one clip. Ninety seconds. That is the whole task.**

---

## 2. Mobile Phone Use

**Shot:** sit in a **parked** car. Phone on the dashboard or held by a passenger,
filming the driver from the front-right, from about chest height. Driver holds a
phone **clearly visible against a light background**, not down in their lap.
30 seconds.

**Why:** the phone must be detected as a distinct object at 0.50 confidence. It
needs to be seen, not implied by posture.

⚠️ **Film only in a stationary car.** Never while anyone is driving.

---

## 3. No Seatbelt — needs one more thing first

**Shot:** same setup as above. Two takes, 30 seconds each — one belted, one not.
The chest and the diagonal strap must both be in frame.

⚠️ **But this rule will still stay off**, and you should know why before you
film. Our `models/seatbelt.pt` is broken: it reports "no seatbelt" at 100%
confidence for a driver *wearing* a belt and for a photo of an empty motorway.
I disabled it deliberately.

Filming this is only worth it if we also source a working seatbelt
**detection** model (not a classifier). Do the other clips first.

---

## 4. Red Light Jump

**Shot:** a signalised junction, phone still on a wall or railing. You must be
able to see **both** the signal head **and** the stop line for the lane facing
you. Film 2–3 full signal cycles, about 3 minutes.

**Then tell me:** which signal head in frame controls the lane nearest the
camera. That is the one thing the system cannot work out on its own, and it is
why I advised against demoing red light — a junction has four or five heads
facing different directions, and reading the wrong one fines a stopped car.

---

## 5. Over Speeding on a Sri Lankan road

Already demonstrated on two calibrated cameras, so this is optional polish — but
a *local* speeding clip would be much stronger than foreign highway footage.

**Shot:** a straight road from a footbridge or upper floor, camera still,
2 minutes. **Then measure one thing on the ground**: the real-world length and
width of a marked road section in the shot — for example the distance between
two lamp posts, in metres. Without that measurement no speed can be shown.

---

## 6. Wrong Way

**Shot:** a one-way street or a divided carriageway, camera still, 2 minutes.
Tell me which direction is legal. You do not need an actual offender — the value
is showing that lawful traffic is correctly *not* flagged.

---

## Priority if you only have one hour

1. 🥇 **Illegal parking** (90 s) — highest value, easiest, fills a real gap
2. 🥈 **Mobile phone use** (30 s, parked car) — fills a second gap
3. 🥉 **Local speeding clip** + the ground measurement — replaces foreign footage

Red light and seatbelt are **not** worth your time before tomorrow. Red light
needs junction calibration you cannot do in an evening, and seatbelt is blocked
on a model, not on footage.
