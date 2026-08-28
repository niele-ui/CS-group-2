"""
GridCare-Lite — Sample Data & User Accounts (Week 5)
Seeds gridcare.db with demo users, substations, and a couple of open outages
so the app has something to show in a live demo instead of an empty database.

Run with: python seed_gridcare.py
Assumes workflow.py (with init_db) is importable from the same folder.
"""

import sqlite3
from workflow import init_db, log_outage, assign_work_order, log_complaint

SAMPLE_USERS = [
    # (username, password_hash placeholder, role)
    ('admin_afia', 'demo_hash_1', 'admin'),
    ('eng_antipas', 'demo_hash_2', 'engineer'),
    ('tech_kwame', 'demo_hash_3', 'technician'),
    ('cs_ama', 'demo_hash_4', 'customer_service'),
]

SAMPLE_SUBSTATIONS = [
    (1, 'Achimota Substation', 'Greater Accra'),
    (2, 'Kumasi Central Substation', 'Ashanti'),
    (3, 'Takoradi Substation', 'Western'),
]


def seed():
    conn = init_db('gridcare.db')
    cur = conn.cursor()

    for username, pw_hash, role in SAMPLE_USERS:
        cur.execute(
            "INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (username, pw_hash, role)
        )

    for sub_id, name, region in SAMPLE_SUBSTATIONS:
        cur.execute(
            "INSERT OR IGNORE INTO substations (substation_id, name, region) VALUES (?, ?, ?)",
            (sub_id, name, region)
        )
    conn.commit()

    # One resolved-looking flow and one still-open, so the reports dashboard has real data
    outage_id = log_outage(conn, substation_id=1, reported_by=1, description='Transformer fault at Achimota', severity='High')
    assign_work_order(conn, outage_id, technician_id=3, scheduled_date='2026-08-30')

    log_outage(conn, substation_id=2, reported_by=2, description='Line down after storm', severity='Medium')

    log_complaint(conn, logged_by=4, customer_name='Kwesi Mensah', description='No power since this morning')

    conn.commit()
    conn.close()
    print("gridcare.db seeded: 4 users, 3 substations, 2 outages, 1 complaint.")


if __name__ == '__main__':
    seed()
