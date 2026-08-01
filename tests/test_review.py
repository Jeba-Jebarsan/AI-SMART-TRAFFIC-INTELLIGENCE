"""Officer review workflow: the AI proposes, a named human decides.

These tests exist because the claim "an officer approves every fine" is the
load-bearing one in this product - it is what makes the evidence defensible,
what stops a false positive becoming a real fine, and what we tell judges and
police. A claim that important must be enforced by the code, not by a button
being hidden, so the tests below check the SERVER refuses, not the UI.
"""
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "backend"))

import config     # noqa: E402

# Point the DB at a scratch file BEFORE db is imported, so a test run can never
# touch the operator's real traffic.db (we have destroyed a real challan once).
_tmp = tempfile.mkdtemp(prefix="review_test_")
config.DB_PATH = os.path.join(_tmp, "test.db")

import db        # noqa: E402
import alerts    # noqa: E402

PASSED = []


def check(name, cond):
    PASSED.append((name, bool(cond)))
    print(("PASS" if cond else "FAIL"), "-", name)


def add(challan_id, status="PENDING"):
    db.insert_violation({
        "challan_id": challan_id, "track_id": 1, "type": "No Helmet",
        "plate": "ABC-1234", "plate_conf": 0.9, "speed_kmph": None,
        "fine": 2000, "timestamp": "2026-08-01T09:00:00", "frame_index": 10,
        "snapshot": None, "location": "test", "status": status,
    })
    return [r for r in db.all_violations() if r["challan_id"] == challan_id][0]


db.init_db()
db.clear()

# --- R1  a detected violation starts PENDING, never approved -----------------
v = add("T-0001")
check("R1 a new violation is PENDING", (v["status"] or "PENDING") == "PENDING")
check("R1 nobody is recorded as having reviewed it", not v["reviewed_by"])

# --- R2  approving records the officer and the time --------------------------
row = db.review_violation(v["id"], "approve", "PC 4471 Perera")
check("R2 approve sets APPROVED", row["status"] == "APPROVED")
check("R2 approve names the officer", row["reviewed_by"] == "PC 4471 Perera")
check("R2 approve timestamps the decision", bool(row["reviewed_at"]))

# --- R3  an unnamed approval is not an approval ------------------------------
v2 = add("T-0002")
try:
    db.review_violation(v2["id"], "approve", "   ")
    ok = False
except ValueError:
    ok = True
check("R3 a blank officer name is refused", ok)
still = [r for r in db.all_violations() if r["id"] == v2["id"]][0]
check("R3 the refused approval did not change the status",
      (still["status"] or "PENDING") == "PENDING")

# --- R4  rejection is recorded, not deleted ----------------------------------
row = db.review_violation(v2["id"], "reject", "SI Fernando", "rider was pushing the bike")
check("R4 reject sets REJECTED", row["status"] == "REJECTED")
check("R4 the rejected violation still exists",
      any(r["id"] == v2["id"] for r in db.all_violations()))

# --- R5  every decision lands in the append-only audit trail ------------------
log = db.audit_log(violation_id=v2["id"])
check("R5 the rejection is in the audit trail", len(log) == 1)
check("R5 the audit row names the officer", log[0]["officer"] == "SI Fernando")
check("R5 the audit row keeps the reason",
      log[0]["note"] == "rider was pushing the bike")
check("R5 the audit row records the transition",
      log[0]["from_status"] == "PENDING" and log[0]["to_status"] == "REJECTED")

# --- R6  reopening is itself an auditable act --------------------------------
db.review_violation(v2["id"], "reopen", "IP Silva", "reviewing again")
log = db.audit_log(violation_id=v2["id"])
check("R6 reopening appends rather than overwrites", len(log) == 2)
check("R6 the earlier rejection is still on record",
      any(e["to_status"] == "REJECTED" for e in log))

# --- R7  an unknown action is refused ----------------------------------------
try:
    db.review_violation(v2["id"], "delete", "IP Silva")
    ok = False
except ValueError:
    ok = True
check("R7 an unknown review action is refused", ok)

# --- R8  a PENDING challan cannot be emailed to the police -------------------
# This is the one that matters. Detection used to email the police directly.
pending = add("T-0003")
ok, msg = alerts.send_alert(pending)
check("R8 sending a PENDING challan is refused", ok is False)
check("R8 the refusal explains why", "approve" in msg.lower())

rejected = add("T-0004", status="REJECTED")
ok, _ = alerts.send_alert(rejected)
check("R8 sending a REJECTED challan is refused", ok is False)

# --- R9  status filtering drives the review queue ----------------------------
counts = {s: len(db.all_violations(status=s))
          for s in ("PENDING", "APPROVED", "REJECTED")}
check("R9 PENDING queue holds only unreviewed rows", counts["PENDING"] == 2)
check("R9 APPROVED queue holds only approved rows", counts["APPROVED"] == 1)
check("R9 stats report the queue", db.stats()["pending"] == 2
      and db.stats()["approved"] == 1)

# --- R10  only approved fines count as money ---------------------------------
s = db.stats()
check("R10 approved_fines counts approved challans only",
      s["approved_fines"] == 2000 and s["total_fines"] > s["approved_fines"])

# --- R11  clearing the session cannot erase the audit trail ------------------
before = len(db.audit_log(limit=10000))
db.clear()
after = db.audit_log(limit=10000)
check("R11 clear() does not delete audit history", len(after) >= before)
check("R11 clear() records that it destroyed challans",
      any(e["action"] == "SESSION_RESET" for e in after))
check("R11 the reset row says how many were destroyed",
      any(e["action"] == "SESSION_RESET" and "4 violation" in (e["note"] or "")
          for e in after))

fails = [n for n, ok in PASSED if not ok]
print(f"\n{len(PASSED) - len(fails)}/{len(PASSED)} review tests passed")
if fails:
    print("FAILED:", *fails, sep="\n  ")
sys.exit(1 if fails else 0)
