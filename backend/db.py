"""SQLite storage for violations + tracked vehicles + a key/value meta table.

The dashboard reads exclusively through the FastAPI layer, which reads from
here, so the DB is the single source of truth at runtime. The pipeline also
mirrors everything to results.json as a static backup.

Every row carries source='ai' — the platform is live-only and produces no
mock/demo data; each live session starts from a clean database.
"""
import json
import sqlite3
import threading
from contextlib import contextmanager

import config

_lock = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS violations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    challan_id  TEXT UNIQUE,
    track_id    INTEGER,
    type        TEXT,
    plate       TEXT,
    plate_conf  REAL,
    plate_img   TEXT,
    speed_kmph  REAL,
    drive_seconds REAL,
    fine        INTEGER,
    timestamp   TEXT,
    frame_index INTEGER,
    video_s     REAL,
    box         TEXT,
    snapshot    TEXT,
    location    TEXT,
    status      TEXT DEFAULT 'PENDING',
    source      TEXT DEFAULT 'ai'
);
CREATE TABLE IF NOT EXISTS vehicles (
    track_id       INTEGER PRIMARY KEY,
    cls            TEXT,
    plate          TEXT,
    plate_conf     REAL,
    plate_img      TEXT,
    plate_hits     INTEGER DEFAULT 0,
    plate_note     TEXT,
    helmet_status  TEXT,
    seatbelt_status TEXT,
    top_speed      REAL,
    over_speed     INTEGER DEFAULT 0,
    first_seen     TEXT,
    last_seen      TEXT,
    source         TEXT DEFAULT 'ai'
);
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);
-- Append-only review trail. Rows are INSERTed and never UPDATEd or DELETEd,
-- anywhere in this codebase — that is the whole point of it. A challan that
-- gets quietly cancelled must still leave a mark naming who cancelled it, so
-- clear() writes a SESSION_RESET row here rather than wiping the table.
CREATE TABLE IF NOT EXISTS audit (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    ts           TEXT,
    violation_id INTEGER,
    challan_id   TEXT,
    action       TEXT,
    from_status  TEXT,
    to_status    TEXT,
    officer      TEXT,
    note         TEXT
);
"""

# columns added after the first release — applied to old DBs on startup
_MIGRATIONS = {
    "violations": {
        "plate_img": "TEXT", "video_s": "REAL",
        "box": "TEXT", "source": "TEXT DEFAULT 'ai'",
        "drive_seconds": "REAL",
        "reviewed_by": "TEXT",
        "reviewed_at": "TEXT",
        "review_note": "TEXT",
    },
    "vehicles": {
        "plate_hits": "INTEGER DEFAULT 0",
        "plate_note": "TEXT",
        "helmet_status": "TEXT",
        "seatbelt_status": "TEXT",
        "top_speed": "REAL",
        "over_speed": "INTEGER DEFAULT 0",
    },
}


@contextmanager
def get_conn():
    conn = sqlite3.connect(config.DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with _lock, get_conn() as c:
        c.executescript(SCHEMA)
        for table, cols in _MIGRATIONS.items():
            have = {r["name"] for r in c.execute(f"PRAGMA table_info({table})")}
            for col, decl in cols.items():
                if col not in have:
                    c.execute(f"ALTER TABLE {table} ADD COLUMN {col} {decl}")


def clear():
    """Wipe violations/vehicles/meta at the start of a live session.

    The audit table is deliberately NOT wiped. An append-only trail that any
    caller can erase proves nothing, so the wipe is itself recorded — including
    how many challans were destroyed and how many of those a human had already
    approved. That row is what makes "a cancelled challan always leaves a mark"
    true in code rather than only on a slide.
    """
    with _lock, get_conn() as c:
        n = c.execute("SELECT COUNT(*) n FROM violations").fetchone()["n"]
        approved = c.execute(
            "SELECT COUNT(*) n FROM violations WHERE status='APPROVED'"
        ).fetchone()["n"]
        c.execute("DELETE FROM violations")
        c.execute("DELETE FROM vehicles")
        c.execute("DELETE FROM meta")
        if n:
            c.execute(
                """INSERT INTO audit
                     (ts, violation_id, challan_id, action, from_status,
                      to_status, officer, note)
                   VALUES (?, NULL, NULL, 'SESSION_RESET', NULL, NULL,
                           'system', ?)""",
                (_now(), f"{n} violation(s) cleared for a new session "
                         f"({approved} had been approved)"))


def _now():
    import datetime
    return datetime.datetime.now().isoformat(timespec="seconds")


REVIEW_ACTIONS = {"approve": "APPROVED", "reject": "REJECTED",
                  "reopen": "PENDING"}


def review_violation(vid: int, action: str, officer: str, note: str = ""):
    """Record a human decision on one violation. Returns the updated row.

    Raises ValueError for an unknown action, a missing violation, or a blank
    officer name — an approval nobody is named on is not an approval.
    """
    action = (action or "").strip().lower()
    if action not in REVIEW_ACTIONS:
        raise ValueError(f"unknown action {action!r}")
    officer = (officer or "").strip()
    if not officer:
        raise ValueError("officer name is required")
    to_status = REVIEW_ACTIONS[action]
    ts = _now()
    with _lock, get_conn() as c:
        row = c.execute("SELECT * FROM violations WHERE id=?", (vid,)).fetchone()
        if row is None:
            raise ValueError(f"no violation with id {vid}")
        from_status = row["status"] or "PENDING"
        c.execute(
            "UPDATE violations SET status=?, reviewed_by=?, reviewed_at=?, "
            "review_note=? WHERE id=?",
            (to_status, officer, ts, note or None, vid))
        c.execute(
            """INSERT INTO audit
                 (ts, violation_id, challan_id, action, from_status, to_status,
                  officer, note)
               VALUES (?,?,?,?,?,?,?,?)""",
            (ts, vid, row["challan_id"], action.upper(), from_status,
             to_status, officer, note or None))
        return dict(c.execute("SELECT * FROM violations WHERE id=?",
                              (vid,)).fetchone())


def audit_log(limit=200, violation_id=None):
    q = "SELECT * FROM audit"
    args = []
    if violation_id is not None:
        q += " WHERE violation_id = ?"
        args.append(violation_id)
    q += " ORDER BY id DESC LIMIT ?"
    args.append(limit)
    with get_conn() as c:
        return [dict(r) for r in c.execute(q, args).fetchall()]


def is_empty():
    with get_conn() as c:
        return c.execute("SELECT COUNT(*) n FROM violations").fetchone()["n"] == 0


def violation_count():
    with get_conn() as c:
        return c.execute("SELECT COUNT(*) n FROM violations").fetchone()["n"]


def insert_violation(v: dict):
    v.setdefault("plate_img", None)
    v.setdefault("video_s", None)
    v.setdefault("box", None)
    v.setdefault("source", "ai")
    v.setdefault("drive_seconds", None)
    with _lock, get_conn() as c:
        c.execute(
            """INSERT OR IGNORE INTO violations
               (challan_id, track_id, type, plate, plate_conf, plate_img,
                speed_kmph, drive_seconds, fine, timestamp, frame_index, video_s, box,
                snapshot, location, status, source)
               VALUES (:challan_id,:track_id,:type,:plate,:plate_conf,:plate_img,
                       :speed_kmph,:drive_seconds,:fine,:timestamp,:frame_index,:video_s,:box,
                       :snapshot,:location,:status,:source)""",
            v,
        )


def upsert_vehicle(v: dict):
    """Insert/refresh one tracked vehicle (best CONFIRMED plate + compliance)."""
    v.setdefault("plate", None)
    v.setdefault("plate_conf", None)
    v.setdefault("plate_img", None)
    v.setdefault("plate_hits", 0)
    v.setdefault("plate_note", None)
    v.setdefault("helmet_status", None)
    v.setdefault("seatbelt_status", None)
    v.setdefault("top_speed", None)
    v.setdefault("over_speed", 0)
    v.setdefault("source", "ai")
    with _lock, get_conn() as c:
        c.execute(
            """INSERT INTO vehicles
                 (track_id, cls, plate, plate_conf, plate_img, plate_hits,
                  plate_note, helmet_status, seatbelt_status, top_speed,
                  over_speed, first_seen, last_seen, source)
               VALUES (:track_id,:cls,:plate,:plate_conf,:plate_img,:plate_hits,
                       :plate_note,:helmet_status,:seatbelt_status,:top_speed,
                       :over_speed,:first_seen,:last_seen,:source)
               ON CONFLICT(track_id) DO UPDATE SET
                 cls=excluded.cls, plate=excluded.plate,
                 plate_conf=excluded.plate_conf, plate_img=excluded.plate_img,
                 plate_hits=excluded.plate_hits, plate_note=excluded.plate_note,
                 helmet_status=excluded.helmet_status,
                 seatbelt_status=excluded.seatbelt_status,
                 top_speed=excluded.top_speed, over_speed=excluded.over_speed,
                 last_seen=excluded.last_seen""",
            v,
        )


def all_vehicles(limit=300):
    with get_conn() as c:
        return [dict(r) for r in c.execute(
            "SELECT * FROM vehicles ORDER BY "
            "(plate IS NOT NULL AND plate != 'UNKNOWN') DESC, last_seen DESC "
            "LIMIT ?", (limit,)).fetchall()]


def set_meta(key, value):
    with _lock, get_conn() as c:
        c.execute("INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)",
                  (key, json.dumps(value)))


def get_meta(key, default=None):
    with get_conn() as c:
        r = c.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return json.loads(r["value"]) if r else default


def all_violations(limit=500, vtype=None, plate=None, status=None):
    q = "SELECT * FROM violations"
    conds, args = [], []
    if vtype:
        conds.append("type = ?")
        args.append(vtype)
    if status:
        # Rows written before the review workflow existed have no status;
        # they are pending, not invisible.
        conds.append("COALESCE(status, 'PENDING') = ?")
        args.append(status.upper())
    if plate:
        conds.append("REPLACE(UPPER(plate), ' ', '') LIKE ?")
        args.append("%" + plate.upper().replace(" ", "") + "%")
    if conds:
        q += " WHERE " + " AND ".join(conds)
    q += " ORDER BY id DESC LIMIT ?"
    args.append(limit)
    with get_conn() as c:
        return [dict(r) for r in c.execute(q, args).fetchall()]


def stats():
    with get_conn() as c:
        rows = [dict(r) for r in c.execute(
            "SELECT type, COUNT(*) n, COALESCE(SUM(fine),0) f "
            "FROM violations GROUP BY type").fetchall()]
        total = c.execute(
            "SELECT COUNT(*) n, COALESCE(SUM(fine),0) f FROM violations").fetchone()
        # violations bucketed by minute-of-hour for the timeline chart
        timeline = [dict(r) for r in c.execute(
            "SELECT substr(timestamp, 12, 5) t, COUNT(*) n "
            "FROM violations GROUP BY t ORDER BY t").fetchall()]
        # plates recognised across all tracked vehicles (the ANPR metric)
        plates = c.execute(
            "SELECT COUNT(*) n FROM vehicles "
            "WHERE plate IS NOT NULL AND plate != 'UNKNOWN'").fetchone()
        veh_rows = c.execute("SELECT COUNT(*) n FROM vehicles").fetchone()
        # repeat offenders: same readable plate, 2+ violations
        repeat = [dict(r) for r in c.execute(
            "SELECT plate, COUNT(*) n, SUM(fine) f FROM violations "
            "WHERE plate IS NOT NULL AND plate != 'UNKNOWN' "
            "GROUP BY plate HAVING n >= 2 ORDER BY n DESC LIMIT 8").fetchall()]
        avg_speed = c.execute(
            "SELECT AVG(speed_kmph) s FROM violations "
            "WHERE type='Over Speeding' AND speed_kmph IS NOT NULL").fetchone()
        # highest-speed records: fastest tracked vehicles (calibrated clips only,
        # so top_speed is a real metric reading — 0/absent otherwise)
        top_speeds = [dict(r) for r in c.execute(
            "SELECT track_id, plate, cls, top_speed, over_speed FROM vehicles "
            "WHERE top_speed IS NOT NULL AND top_speed > 0 "
            "ORDER BY top_speed DESC LIMIT 5").fetchall()]
        status_rows = [dict(r) for r in c.execute(
            "SELECT COALESCE(status, 'PENDING') s, COUNT(*) n, "
            "COALESCE(SUM(fine),0) f FROM violations GROUP BY s").fetchall()]
        audit_n = c.execute("SELECT COUNT(*) n FROM audit").fetchone()

    by_status = {r["s"]: r["n"] for r in status_rows}
    # Only an APPROVED challan is a real fine. The headline money figure must
    # not count what a human has not yet agreed to, or the dashboard is
    # advertising revenue the system invented by itself.
    approved_fines = next((r["f"] for r in status_rows if r["s"] == "APPROVED"), 0)
    by_type = {r["type"]: {"count": r["n"], "fines": r["f"]} for r in rows}
    return {
        "total_violations": total["n"],
        "total_fines": total["f"],
        "by_status": by_status,
        "pending": by_status.get("PENDING", 0),
        "approved": by_status.get("APPROVED", 0),
        "rejected": by_status.get("REJECTED", 0),
        "approved_fines": approved_fines,
        "audit_entries": audit_n["n"],
        "no_helmet": by_type.get("No Helmet", {}).get("count", 0),
        "by_type": by_type,
        "timeline": timeline,
        "vehicles": get_meta("vehicle_count", 0),
        "vehicle_rows": veh_rows["n"],
        "plates_read": plates["n"],
        "repeat_offenders": repeat,
        "avg_over_speed": round(avg_speed["s"], 1) if avg_speed["s"] else None,
        "top_speeds": top_speeds,
        "max_speed": round(top_speeds[0]["top_speed"], 1) if top_speeds else None,
        "location": get_meta("location_override")
        or get_meta("location", config.CAMERA_LOCATION),
        "processed_at": get_meta("processed_at"),
        "data_source": get_meta("data_source", "none"),
        "frame_size": get_meta("frame_size"),      # [w, h] of the last run
        "video_fps": get_meta("video_fps"),
        "device": get_meta("device"),
        "speed_calibrated": get_meta("speed_calibrated", False),
        "alerts_sent": get_meta("alerts_sent", 0),
    }
