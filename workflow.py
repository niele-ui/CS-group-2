"""
GridCare-Lite: Outage-to-Resolution Workflow
CS 112 Final Course Project - Group 2

Implements the full operational workflow against gridcare_lite/db_schema.sql:
    log outage -> create work order -> assign technician -> update status
    -> resolve -> report

Also covers customer complaints and role-based permission checks.

Every function here validates against the real schema, including the CHECK
constraints on status columns, so an invalid state transition raises rather
than silently writing a bad row.
"""

import os
import sqlite3
import hashlib
from datetime import datetime

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db_schema.sql")

# ---------------------------------------------------------------- permissions
ROLE_PERMISSIONS = {
    "Administrator": {"view_reports", "create_work_order", "assign_work_order",
                       "resolve_outage", "view_all_outages", "log_outage",
                       "log_complaint", "manage_users"},
    "Engineer": {"view_reports", "view_all_outages", "log_outage"},
    "Technician": {"resolve_outage", "update_work_order", "view_assigned_work"},
    "CustomerService": {"log_complaint", "view_all_outages", "link_complaint"},
}

VALID_OUTAGE_STATUS = ("Reported", "In Progress", "Resolved")
VALID_WORK_ORDER_STATUS = ("Assigned", "In Progress", "Completed")
VALID_SEVERITY = ("Low", "Medium", "High", "Critical")


class PermissionDeniedError(PermissionError):
    """Raised when a role attempts an action it is not authorised for."""


def check_permission(role, action):
    """Raise PermissionDeniedError unless `role` may perform `action`."""
    if role not in ROLE_PERMISSIONS:
        raise PermissionDeniedError(f"Unknown role: {role}")
    if action not in ROLE_PERMISSIONS[role]:
        raise PermissionDeniedError(f"Role '{role}' is not permitted to '{action}'")
    return True


# ---------------------------------------------------------------- db helpers
def hash_password(password):
    """SHA-256 hash. Adequate for coursework demonstration only; a real
    deployment needs a salted hash such as bcrypt."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def init_db(db_path=":memory:", seed_demo=False):
    """Create a GridCare-Lite database from db_schema.sql and return the
    open connection. Foreign keys are enforced, which SQLite does not do by
    default and which several of our integrity checks depend on."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    if seed_demo:
        seed_demo_data(conn)
    conn.commit()
    return conn


def seed_demo_data(conn):
    """One user per role plus a minimal utility/substation, for demos and tests."""
    cur = conn.cursor()
    accounts = [
        ("admin1", "admin123", "Niele Afia Nyamekye", "Administrator"),
        ("eng1", "engineer123", "Antipas Malual Mabeny", "Engineer"),
        ("tech1", "tech123", "Diamond Obrempong Owusu Sekyere", "Technician"),
        ("cs1", "cs123", "Ethan Elom Koku Agbenu", "CustomerService"),
    ]
    for username, pw, full_name, role in accounts:
        cur.execute("SELECT 1 FROM users WHERE username = ?", (username,))
        if cur.fetchone() is None:
            cur.execute(
                "INSERT INTO users (username, password_hash, full_name, role) "
                "VALUES (?, ?, ?, ?)",
                (username, hash_password(pw), full_name, role),
            )
    cur.execute("SELECT 1 FROM utilities WHERE utility_id = 1")
    if cur.fetchone() is None:
        cur.execute("INSERT INTO utilities (utility_id, name, region) "
                    "VALUES (1, 'Electricity Company of Ghana', 'Greater Accra')")
    cur.execute("SELECT 1 FROM substations WHERE substation_id = 1")
    if cur.fetchone() is None:
        cur.execute(
            "INSERT INTO substations (substation_id, name, utility_id, region, status) "
            "VALUES (1, 'Achimota Substation', 1, 'Greater Accra', 'Active')")
    conn.commit()


def authenticate(conn, username, password):
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ? AND is_active = 1", (username,))
    row = cur.fetchone()
    if row and row["password_hash"] == hash_password(password):
        return row
    return None


# ---------------------------------------------------------------- outages
def log_outage(conn, substation_id, reported_by, description, severity="Medium"):
    """Report a new outage. Starts in 'Reported' status per the schema CHECK."""
    if severity not in VALID_SEVERITY:
        raise ValueError(f"severity must be one of {VALID_SEVERITY}, got '{severity}'")
    if not description or not str(description).strip():
        raise ValueError("description is required")

    cur = conn.cursor()
    cur.execute("SELECT 1 FROM substations WHERE substation_id = ?", (substation_id,))
    if cur.fetchone() is None:
        raise ValueError(f"No substation with id {substation_id}")
    cur.execute("SELECT 1 FROM users WHERE user_id = ?", (reported_by,))
    if cur.fetchone() is None:
        raise ValueError(f"No user with id {reported_by}")

    cur.execute(
        """INSERT INTO outages
           (substation_id, reported_by, description, severity, status, reported_at)
           VALUES (?, ?, ?, ?, 'Reported', ?)""",
        (substation_id, reported_by, description, severity, datetime.now().isoformat()),
    )
    conn.commit()
    return cur.lastrowid


def get_outage(conn, outage_id):
    cur = conn.cursor()
    cur.execute("SELECT * FROM outages WHERE outage_id = ?", (outage_id,))
    row = cur.fetchone()
    if row is None:
        raise ValueError(f"No outage with id {outage_id}")
    return row


# ---------------------------------------------------------------- work orders
def assign_work_order(conn, outage_id, created_by, assigned_to, scheduled_for):
    """Create a work order against an outage and move it to 'In Progress'.

    Refuses to assign work to an already-resolved outage, which is the
    invalid-state-transition case the schema alone would not catch.
    """
    outage = get_outage(conn, outage_id)
    if outage["status"] == "Resolved":
        raise ValueError(
            f"Cannot assign a work order to outage {outage_id}: already Resolved"
        )

    cur = conn.cursor()
    for uid, label in [(created_by, "created_by"), (assigned_to, "assigned_to")]:
        cur.execute("SELECT 1 FROM users WHERE user_id = ?", (uid,))
        if cur.fetchone() is None:
            raise ValueError(f"No user with id {uid} (for {label})")

    cur.execute(
        """INSERT INTO work_orders
           (outage_id, created_by, assigned_to, scheduled_for, status)
           VALUES (?, ?, ?, ?, 'Assigned')""",
        (outage_id, created_by, assigned_to, scheduled_for),
    )
    work_order_id = cur.lastrowid
    cur.execute("UPDATE outages SET status = 'In Progress' WHERE outage_id = ?",
                (outage_id,))
    _record_status_change(conn, work_order_id, created_by, None, "Assigned")
    conn.commit()
    return work_order_id


def update_work_order_status(conn, work_order_id, new_status, changed_by, notes=None):
    if new_status not in VALID_WORK_ORDER_STATUS:
        raise ValueError(f"status must be one of {VALID_WORK_ORDER_STATUS}")

    cur = conn.cursor()
    cur.execute("SELECT status FROM work_orders WHERE work_order_id = ?", (work_order_id,))
    row = cur.fetchone()
    if row is None:
        raise ValueError(f"No work order with id {work_order_id}")
    old_status = row["status"]

    cur.execute(
        "UPDATE work_orders SET status = ?, work_completed_notes = ?, updated_at = ? "
        "WHERE work_order_id = ?",
        (new_status, notes, datetime.now().isoformat(), work_order_id),
    )
    _record_status_change(conn, work_order_id, changed_by, old_status, new_status)
    conn.commit()


def _record_status_change(conn, work_order_id, changed_by, old_status, new_status):
    conn.execute(
        """INSERT INTO status_history
           (work_order_id, changed_by, old_status, new_status, changed_at)
           VALUES (?, ?, ?, ?, ?)""",
        (work_order_id, changed_by, old_status, new_status, datetime.now().isoformat()),
    )


def resolve_outage(conn, outage_id, work_order_id, resolved_by=None, notes=None):
    outage = get_outage(conn, outage_id)
    if outage["status"] == "Resolved":
        raise ValueError(f"Outage {outage_id} is already Resolved")

    cur = conn.cursor()
    cur.execute("SELECT 1 FROM work_orders WHERE work_order_id = ?", (work_order_id,))
    if cur.fetchone() is None:
        raise ValueError(f"No work order with id {work_order_id}")

    cur.execute("UPDATE outages SET status = 'Resolved', resolved_at = ? "
                "WHERE outage_id = ?",
                (datetime.now().isoformat(), outage_id))
    cur.execute("UPDATE work_orders SET status = 'Completed', "
                "work_completed_notes = ?, updated_at = ? WHERE work_order_id = ?",
                (notes, datetime.now().isoformat(), work_order_id))
    if resolved_by:
        _record_status_change(conn, work_order_id, resolved_by, "In Progress", "Completed")
    conn.commit()


def get_resolution_time(conn, outage_id):
    """Hours from report to resolution, or None if still open."""
    outage = get_outage(conn, outage_id)
    if outage["resolved_at"] is None:
        return None
    delta = (datetime.fromisoformat(outage["resolved_at"])
             - datetime.fromisoformat(outage["reported_at"]))
    return delta.total_seconds() / 3600


# ---------------------------------------------------------------- complaints
def log_complaint(conn, logged_by, customer_name, description, contact_info=None,
                  outage_id=None):
    if not customer_name or not str(customer_name).strip():
        raise ValueError("customer_name is required")
    if not description or not str(description).strip():
        raise ValueError("description is required")

    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE user_id = ?", (logged_by,))
    if cur.fetchone() is None:
        raise ValueError(f"No user with id {logged_by}")
    if outage_id is not None:
        cur.execute("SELECT 1 FROM outages WHERE outage_id = ?", (outage_id,))
        if cur.fetchone() is None:
            raise ValueError(f"No outage with id {outage_id}")

    cur.execute(
        """INSERT INTO complaints
           (logged_by, outage_id, customer_name, contact_info, description, logged_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (logged_by, outage_id, customer_name, contact_info, description,
         datetime.now().isoformat()),
    )
    conn.commit()
    return cur.lastrowid


def link_complaint_to_outage(conn, complaint_id, outage_id):
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM complaints WHERE complaint_id = ?", (complaint_id,))
    if cur.fetchone() is None:
        raise ValueError(f"No complaint with id {complaint_id}")
    cur.execute("SELECT 1 FROM outages WHERE outage_id = ?", (outage_id,))
    if cur.fetchone() is None:
        raise ValueError(f"No outage with id {outage_id}")

    cur.execute("UPDATE complaints SET outage_id = ? WHERE complaint_id = ?",
                (outage_id, complaint_id))
    conn.commit()


# ---------------------------------------------------------------- reporting
def get_outage_status_breakdown(conn):
    cur = conn.cursor()
    cur.execute("SELECT status, COUNT(*) AS n FROM outages GROUP BY status")
    return {r["status"]: r["n"] for r in cur.fetchall()}


def get_work_order_status_breakdown(conn):
    cur = conn.cursor()
    cur.execute("SELECT status, COUNT(*) AS n FROM work_orders GROUP BY status")
    return {r["status"]: r["n"] for r in cur.fetchall()}


def get_reports_summary(conn):
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) AS n FROM outages")
    total_outages = cur.fetchone()["n"]
    cur.execute("SELECT COUNT(*) AS n FROM outages WHERE status != 'Resolved'")
    open_outages = cur.fetchone()["n"]
    cur.execute("SELECT COUNT(*) AS n FROM outages WHERE status = 'Resolved'")
    resolved = cur.fetchone()["n"]
    cur.execute("SELECT COUNT(*) AS n FROM work_orders")
    total_wo = cur.fetchone()["n"]
    cur.execute("SELECT COUNT(*) AS n FROM complaints")
    total_complaints = cur.fetchone()["n"]

    cur.execute("SELECT reported_at, resolved_at FROM outages WHERE resolved_at IS NOT NULL")
    times = []
    for r in cur.fetchall():
        d = datetime.fromisoformat(r["resolved_at"]) - datetime.fromisoformat(r["reported_at"])
        times.append(d.total_seconds() / 3600)

    return {
        "total_outages": total_outages,
        "open_outages": open_outages,
        "resolved_outages": resolved,
        "total_work_orders": total_wo,
        "total_complaints": total_complaints,
        "mean_resolution_hours": round(sum(times) / len(times), 3) if times else None,
    }


def get_full_dashboard(conn, requesting_role):
    """Role-gated dashboard. Raises PermissionDeniedError for roles without
    'view_reports'."""
    check_permission(requesting_role, "view_reports")
    summary = get_reports_summary(conn)
    summary["outage_status_breakdown"] = get_outage_status_breakdown(conn)
    summary["work_order_status_breakdown"] = get_work_order_status_breakdown(conn)
    return summary


if __name__ == "__main__":
    print("GridCare-Lite workflow demo\n" + "=" * 45)
    conn = init_db(":memory:", seed_demo=True)

    outage_id = log_outage(conn, substation_id=1, reported_by=2,
                            description="Transformer fault at Achimota",
                            severity="High")
    print(f"Logged outage {outage_id}: status = {get_outage(conn, outage_id)['status']}")

    wo_id = assign_work_order(conn, outage_id, created_by=1, assigned_to=3,
                               scheduled_for="2026-08-30")
    print(f"Assigned work order {wo_id}: outage status = "
          f"{get_outage(conn, outage_id)['status']}")

    resolve_outage(conn, outage_id, wo_id, resolved_by=3, notes="Transformer replaced")
    print(f"Resolved: status = {get_outage(conn, outage_id)['status']}, "
          f"time = {get_resolution_time(conn, outage_id):.4f} hours")

    cid = log_complaint(conn, logged_by=4, customer_name="Ama Serwaa",
                         description="No power since morning")
    link_complaint_to_outage(conn, cid, outage_id)
    print(f"Logged complaint {cid} and linked to outage {outage_id}")

    print("\nAdministrator dashboard:")
    for k, v in get_full_dashboard(conn, "Administrator").items():
        print(f"  {k}: {v}")

    try:
        get_full_dashboard(conn, "Technician")
    except PermissionDeniedError as e:
        print(f"\nTechnician blocked as expected: {e}")
