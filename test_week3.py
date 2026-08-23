"""
Week 3 - Part 7 (Ethan Elom Koku Agbenu, with Afia): Testing Module Interactions

Smoke and integration tests for the GridCare-Lite outage-to-resolution
workflow (workflow.py, Part 5).

Unlike test_week3_as_received.py, this suite builds its database from the
ACTUAL gridcare_lite/db_schema.sql used elsewhere in the repo, rather than a
simplified ad-hoc schema. That distinction matters: the ad-hoc version
passed 2/2 tests while hiding three real integration bugs (see
WEEK3_EVALUATION.md). Testing "module interactions" only means something if
the modules under test are talking to the actual schema the rest of the
project uses.

9 test cases, matching the count stated in the Week 3 submission doc:
    1.  test_outage_creation
    2.  test_outage_default_severity
    3.  test_outage_requires_valid_substation
    4.  test_full_workflow_resolves
    5.  test_work_order_created_on_assignment
    6.  test_outage_status_in_progress_after_assignment
    7.  test_resolution_time_none_before_resolution
    8.  test_resolution_time_computed_after_resolution
    9.  test_get_resolution_time_unknown_outage_raises

Run with:
    python -m unittest test_week3.py -v
"""

import unittest
import sqlite3
import os
import time

import workflow

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "real_gridcare_schema.sql")


class TestGridCareWorkflow(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        self.conn.execute("PRAGMA foreign_keys = ON;")
        with open(SCHEMA_PATH) as f:
            self.conn.executescript(f.read())

        cur = self.conn.cursor()
        cur.execute("INSERT INTO utilities (utility_id, name, region) VALUES (1, 'Test Utility', 'Test Region')")
        cur.execute("""INSERT INTO substations (substation_id, name, utility_id, region, status)
                        VALUES (1, 'Test Substation', 1, 'Test Region', 'Active')""")
        cur.execute("""INSERT INTO users (user_id, username, password_hash, full_name, role)
                        VALUES (1, 'eng1', 'x', 'Engineer One', 'Engineer')""")
        cur.execute("""INSERT INTO users (user_id, username, password_hash, full_name, role)
                        VALUES (2, 'tech1', 'x', 'Technician One', 'Technician')""")
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    # -- Outage creation -------------------------------------------------
    def test_outage_creation(self):
        outage_id = workflow.log_outage(self.conn, substation_id=1, reported_by=1,
                                         description='Transformer fault')
        cur = self.conn.cursor()
        cur.execute("SELECT status FROM outages WHERE outage_id = ?", (outage_id,))
        self.assertEqual(cur.fetchone()[0], 'Reported')

    def test_outage_default_severity(self):
        outage_id = workflow.log_outage(self.conn, substation_id=1, reported_by=1,
                                         description='Transformer fault')
        cur = self.conn.cursor()
        cur.execute("SELECT severity FROM outages WHERE outage_id = ?", (outage_id,))
        self.assertEqual(cur.fetchone()[0], 'Medium')

    def test_outage_requires_valid_substation(self):
        with self.assertRaises(sqlite3.IntegrityError):
            workflow.log_outage(self.conn, substation_id=999, reported_by=1,
                                 description='Fault at nonexistent substation')

    # -- Full workflow -----------------------------------------------------
    def test_full_workflow_resolves(self):
        outage_id = workflow.log_outage(self.conn, 1, 1, 'Test outage')
        wo_id = workflow.assign_work_order(self.conn, outage_id, created_by=1,
                                            assigned_to=2, scheduled_for='2026-08-25')
        workflow.resolve_outage(self.conn, outage_id, wo_id)
        cur = self.conn.cursor()
        cur.execute("SELECT status FROM outages WHERE outage_id = ?", (outage_id,))
        self.assertEqual(cur.fetchone()[0], 'Resolved')

    def test_work_order_created_on_assignment(self):
        outage_id = workflow.log_outage(self.conn, 1, 1, 'Test outage')
        wo_id = workflow.assign_work_order(self.conn, outage_id, created_by=1,
                                            assigned_to=2, scheduled_for='2026-08-25')
        cur = self.conn.cursor()
        cur.execute("SELECT status, assigned_to FROM work_orders WHERE work_order_id = ?", (wo_id,))
        status, assigned_to = cur.fetchone()
        self.assertEqual(status, 'Assigned')
        self.assertEqual(assigned_to, 2)

    def test_outage_status_in_progress_after_assignment(self):
        outage_id = workflow.log_outage(self.conn, 1, 1, 'Test outage')
        workflow.assign_work_order(self.conn, outage_id, created_by=1,
                                    assigned_to=2, scheduled_for='2026-08-25')
        cur = self.conn.cursor()
        cur.execute("SELECT status FROM outages WHERE outage_id = ?", (outage_id,))
        self.assertEqual(cur.fetchone()[0], 'In Progress')

    # -- Resolution time -----------------------------------------------------
    def test_resolution_time_none_before_resolution(self):
        outage_id = workflow.log_outage(self.conn, 1, 1, 'Test outage')
        self.assertIsNone(workflow.get_resolution_time(self.conn, outage_id))

    def test_resolution_time_computed_after_resolution(self):
        outage_id = workflow.log_outage(self.conn, 1, 1, 'Test outage')
        wo_id = workflow.assign_work_order(self.conn, outage_id, created_by=1,
                                            assigned_to=2, scheduled_for='2026-08-25')
        time.sleep(0.01)
        workflow.resolve_outage(self.conn, outage_id, wo_id)
        resolution_hours = workflow.get_resolution_time(self.conn, outage_id)
        self.assertIsNotNone(resolution_hours)
        self.assertGreaterEqual(resolution_hours, 0)

    def test_get_resolution_time_unknown_outage_raises(self):
        with self.assertRaises(ValueError):
            workflow.get_resolution_time(self.conn, outage_id=999)


if __name__ == '__main__':
    unittest.main()
