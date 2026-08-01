"""Run every unit-test suite in this folder and report a combined result.

    python tests/run_all.py

Each suite is a standalone script that exits non-zero on failure. This runner
shells out to each so a crash in one can't hide the others.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SUITES = ["test_engine.py", "test_seatbelt.py", "test_restbreak.py",
          "test_speed.py", "test_stunts.py", "test_parking.py",
          "test_wrongway.py", "test_review.py"]

failed = []
for s in SUITES:
    print(f"\n===================== {s} =====================")
    rc = subprocess.call([sys.executable, os.path.join(HERE, s)])
    if rc != 0:
        failed.append(s)

print("\n" + "=" * 55)
if failed:
    print("SUITES FAILED:", ", ".join(failed))
    sys.exit(1)
print(f"ALL {len(SUITES)} SUITES PASSED")
