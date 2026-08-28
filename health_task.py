"""
ClinicCare-Lite — HealthTask and TaskSubmission models
Builds on the User class from Week 1. Storage: JSON files (data/tasks.json, data/submissions.json)
to match the pattern already used for data/users.json.
"""

import json
import os
from datetime import datetime

TASKS_PATH = 'data/tasks.json'
SUBMISSIONS_PATH = 'data/submissions.json'

ALLOWED_FILE_TYPES = ('.pdf', '.jpg', '.jpeg', '.png', '.csv')
MAX_FILE_SIZE_MB = 10


def _load(path):
    if not os.path.exists(path):
        return {}
    with open(path, 'r') as f:
        return json.load(f)


def _save(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)


class HealthTask:
    def __init__(self, task_id, clinician_id, patient_id, title, description, due_date):
        self.task_id = task_id
        self.clinician_id = clinician_id
        self.patient_id = patient_id
        self.title = title
        self.description = description
        self.due_date = due_date
        self.status = 'Assigned'
        self.created_at = datetime.now().isoformat()

    def save(self):
        tasks = _load(TASKS_PATH)
        tasks[str(self.task_id)] = self.__dict__
        _save(TASKS_PATH, tasks)

    @staticmethod
    def get(task_id):
        tasks = _load(TASKS_PATH)
        return tasks.get(str(task_id))

    @staticmethod
    def all_for_patient(patient_id):
        tasks = _load(TASKS_PATH)
        return [t for t in tasks.values() if t['patient_id'] == patient_id]

    @staticmethod
    def all_for_clinician(clinician_id):
        tasks = _load(TASKS_PATH)
        return [t for t in tasks.values() if t['clinician_id'] == clinician_id]


class TaskSubmission:
    def __init__(self, submission_id, task_id, patient_id, file_name, file_size_mb):
        self.submission_id = submission_id
        self.task_id = task_id
        self.patient_id = patient_id
        self.file_name = file_name
        self.file_size_mb = file_size_mb
        self.submitted_at = datetime.now().isoformat()
        self.review_status = 'Pending Review'
        self.notes = None

    @staticmethod
    def validate_file(file_name, file_size_mb):
        """Returns (is_valid, error_message)."""
        ext = os.path.splitext(file_name)[1].lower()
        if ext not in ALLOWED_FILE_TYPES:
            return False, f"Unsupported file type: {ext}"
        if file_size_mb > MAX_FILE_SIZE_MB:
            return False, f"File too large: {file_size_mb}MB (max {MAX_FILE_SIZE_MB}MB)"
        return True, None

    def save(self):
        # Guard against duplicate submissions for the same task+patient
        subs = _load(SUBMISSIONS_PATH)
        for s in subs.values():
            if s['task_id'] == self.task_id and s['patient_id'] == self.patient_id:
                raise ValueError("Duplicate submission: this task already has a submission from this patient")
        subs[str(self.submission_id)] = self.__dict__
        _save(SUBMISSIONS_PATH, subs)

        # Mark the parent task as submitted
        tasks = _load(TASKS_PATH)
        if str(self.task_id) in tasks:
            tasks[str(self.task_id)]['status'] = 'Submitted'
            _save(TASKS_PATH, tasks)

    def review_submission(self, outcome, reviewer_id, notes=None):
        """outcome must be one of: 'Reviewed - Normal', 'Needs Follow-up', 'Escalated'"""
        valid_outcomes = ('Reviewed - Normal', 'Needs Follow-up', 'Escalated')
        if outcome not in valid_outcomes:
            raise ValueError(f"outcome must be one of {valid_outcomes}")

        # Task ownership check — only the assigned clinician can review
        tasks = _load(TASKS_PATH)
        task = tasks.get(str(self.task_id))
        if task is None:
            raise ValueError(f"No task with id {self.task_id}")
        if task['clinician_id'] != reviewer_id:
            raise PermissionError("Only the assigned clinician can review this submission")

        self.review_status = outcome
        self.notes = notes

        subs = _load(SUBMISSIONS_PATH)
        subs[str(self.submission_id)] = self.__dict__
        _save(SUBMISSIONS_PATH, subs)

        tasks[str(self.task_id)]['status'] = 'Reviewed'
        _save(TASKS_PATH, tasks)

    @staticmethod
    def get(submission_id):
        subs = _load(SUBMISSIONS_PATH)
        return subs.get(str(submission_id))

    @staticmethod
    def all_for_task(task_id):
        subs = _load(SUBMISSIONS_PATH)
        return [s for s in subs.values() if s['task_id'] == task_id]
