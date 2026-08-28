"""
GridCare-Lite — Reports & Status Dashboard (Week 4, Part 2)
Extends the Week 3 workflow.py reports with role-access checks and status
breakdowns needed for a real dashboard screen.
"""

import sqlite3
from datetime import datetime

ROLE_PERMISSIONS = {
    'admin': {'view_reports', 'assign_work_order', 'resolve_outage', 'view_all_outages'},
    'engineer': {'view_reports', 'view_all_outages'},
    'technician': {'resolve_outage'},
    'customer_service': {'log_complaint', 'view_all_outages'},
}


def check_permission(role, action):
    """Role-access check. Raises PermissionError if the role can't do this action."""
    if role not in ROLE_PERMISSIONS:
        raise PermissionError(f"Unknown role: {role}")
    if action not in ROLE_PERMISSIONS[role]:
        raise PermissionError(f"Role '{role}' is not permitted to '{action}'")
    return True


def get_outage_status_breakdown(conn):
    cur = conn.cursor()
    cur.execute("SELECT status, COUNT(*) FROM outages GROUP BY status")
    return dict(cur.fetchall())


def get_work_order_status_breakdown(conn):
    cur = conn.cursor()
    cur.execute("SELECT status, COUNT(*) FROM work_orders GROUP BY status")
    return dict(cur.fetchall())


def get_complaint_status_breakdown(conn):
    cur = conn.cursor()
    cur.execute("SELECT status, COUNT(*) FROM complaints GROUP BY status")
    return dict(cur.fetchall())


def get_full_dashboard(conn, requesting_role):
    check_permission(requesting_role, 'view_reports')
    from workflow import get_reports_summary  # Week 3 module
    summary = get_reports_summary(conn)
    summary['outage_status_breakdown'] = get_outage_status_breakdown(conn)
    summary['work_order_status_breakdown'] = get_work_order_status_breakdown(conn)
    summary['complaint_status_breakdown'] = get_complaint_status_breakdown(conn)
    return summary