"""
ClinicCare-Lite — Sample Data & User Accounts (Week 5)
Seeds data/users.json, data/tasks.json, and data/submissions.json with demo
accounts and a couple of tasks in different states, so the app isn't empty
for a live demo.

Run with: python seed_cliniccare.py
Assumes user.py and health_task.py are importable from the same folder.
"""

import json
import os
from user import User
from health_task import HealthTask, TaskSubmission

DATA_DIR = 'data'


def ensure_data_files():
    os.makedirs(DATA_DIR, exist_ok=True)
    for fname in ('users.json', 'tasks.json', 'submissions.json'):
        path = os.path.join(DATA_DIR, fname)
        if not os.path.exists(path):
            with open(path, 'w') as f:
                json.dump({}, f)


def seed():
    ensure_data_files()

    # Demo accounts — one clinician, two patients. IDs follow the 8-digit
    # format the User class validates (clinician ends 0000, patient ends
    # with a year 2022-2028).
    clinician = User('10000000', 'Dr. Adjoa Boateng', 'adjoa.boateng@clinic.demo', 'Cl1n!c2026', 'clinician')
    patient1 = User('20242026', 'Yaw Osei', 'yaw.osei@demo.edu', 'P@tient2026', 'patient')
    patient2 = User('20262027', 'Efua Danso', 'efua.danso@demo.edu', 'P@tient2027', 'patient')

    for user in (clinician, patient1, patient2):
        user.save()

    # One task submitted and awaiting review, one still assigned
    t1 = HealthTask(1, clinician_id='10000000', patient_id='20242026',
                     title='Log blood pressure', description='Submit this week\'s BP reading',
                     due_date='2026-09-01')
    t1.save()

    t2 = HealthTask(2, clinician_id='10000000', patient_id='20262027',
                     title='Upload lab result', description='Submit latest bloodwork PDF',
                     due_date='2026-09-03')
    t2.save()

    s1 = TaskSubmission(1, task_id=1, patient_id='20242026', file_name='bp_reading.pdf', file_size_mb=1.2)
    s1.save()

    print("ClinicCare-Lite seeded: 1 clinician, 2 patients, 2 tasks, 1 pending submission.")
    print("Demo login: clinician ID 10000000 / password Cl1n!c2026")
    print("Demo login: patient ID 20242026 / password P@tient2026")


if __name__ == '__main__':
    seed()
