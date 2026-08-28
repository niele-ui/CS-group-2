"""
ClinicCare-Lite: HealthTask and TaskSubmission models
CS 112 Final Course Project - Group 2

Administrative task assignment and review for a clinic.

Scope boundary, stated deliberately: this module manages *administrative*
tasks and file submissions. It does not diagnose, interpret symptoms,
recommend treatment, or substitute for clinical judgement. Nothing here
should be built on in a way that implies otherwise.

Storage is JSON (data/tasks.json, data/submissions.json), matching user.py.
"""

import os
import json
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
TASKS_PATH = os.path.join(DATA_DIR, "tasks.json")
SUBMISSIONS_PATH = os.path.join(DATA_DIR, "submissions.json")

ALLOWED_FILE_TYPES = (".pdf", ".jpg", ".jpeg", ".png", ".csv", ".txt")
MAX_FILE_SIZE_MB = 10

VALID_TASK_STATUS = ("Assigned", "Submitted", "Reviewed", "Completed")
VALID_REVIEW_OUTCOMES = ("Reviewed - Normal", "Needs Follow-up", "Escalated")


def _load(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)


def _save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


class HealthTask:
    """An administrative task a clinician assigns to a patient."""

    def __init__(self, task_id, clinician_id, patient_id, title, description, due_date):
        if not title or not str(title).strip():
            raise ValueError("title is required")
        if not clinician_id or not patient_id:
            raise ValueError("clinician_id and patient_id are both required")

        self.task_id = task_id
        self.clinician_id = clinician_id
        self.patient_id = patient_id
        self.title = title
        self.description = description
        self.due_date = due_date
        self.status = "Assigned"
        self.created_at = datetime.now().isoformat()

    def save(self):
        tasks = _load(TASKS_PATH)
        tasks[str(self.task_id)] = self.__dict__
        _save(TASKS_PATH, tasks)
        return self.task_id

    @staticmethod
    def get(task_id):
        return _load(TASKS_PATH).get(str(task_id))

    @staticmethod
    def all_for_patient(patient_id):
        return [t for t in _load(TASKS_PATH).values() if t["patient_id"] == patient_id]

    @staticmethod
    def all_for_clinician(clinician_id):
        return [t for t in _load(TASKS_PATH).values()
                if t["clinician_id"] == clinician_id]

    @staticmethod
    def set_status(task_id, status):
        if status not in VALID_TASK_STATUS:
            raise ValueError(f"status must be one of {VALID_TASK_STATUS}")
        tasks = _load(TASKS_PATH)
        if str(task_id) not in tasks:
            raise ValueError(f"No task with id {task_id}")
        tasks[str(task_id)]["status"] = status
        _save(TASKS_PATH, tasks)


class TaskSubmission:
    """A patient's response to a HealthTask, optionally with a file."""

    def __init__(self, submission_id, task_id, patient_id, file_name=None,
                 file_size_mb=0.0, submission_text=None):
        self.submission_id = submission_id
        self.task_id = task_id
        self.patient_id = patient_id
        self.file_name = file_name
        self.file_size_mb = file_size_mb
        self.submission_text = submission_text
        self.submitted_at = datetime.now().isoformat()
        self.review_status = "Pending Review"
        self.reviewed_by = None
        self.reviewed_at = None
        self.notes = None

    # ---------------------------------------------------------- validation
    @staticmethod
    def validate_file(file_name, file_size_mb):
        """Returns (is_valid, error_message)."""
        if not file_name:
            return False, "No file name provided"
        ext = os.path.splitext(file_name)[1].lower()
        if ext not in ALLOWED_FILE_TYPES:
            return False, f"Unsupported file type: {ext}"
        if file_size_mb > MAX_FILE_SIZE_MB:
            return False, f"File too large: {file_size_mb}MB (max {MAX_FILE_SIZE_MB}MB)"
        if file_size_mb <= 0:
            return False, "File appears to be empty"
        return True, None

    # ---------------------------------------------------------- persistence
    def save(self):
        """Persist the submission. Rejects duplicates for the same task and
        patient, and validates the attached file if there is one."""
        if self.file_name:
            valid, err = TaskSubmission.validate_file(self.file_name, self.file_size_mb)
            if not valid:
                raise ValueError(err)

        subs = _load(SUBMISSIONS_PATH)
        for s in subs.values():
            if s["task_id"] == self.task_id and s["patient_id"] == self.patient_id:
                raise ValueError(
                    "Duplicate submission: this task already has a submission "
                    "from this patient"
                )

        subs[str(self.submission_id)] = self.__dict__
        _save(SUBMISSIONS_PATH, subs)

        tasks = _load(TASKS_PATH)
        if str(self.task_id) in tasks:
            tasks[str(self.task_id)]["status"] = "Submitted"
            _save(TASKS_PATH, tasks)
        return self.submission_id

    # ---------------------------------------------------------- review
    def review_submission(self, outcome, reviewer_id, notes=None):
        """Record a clinician's review.

        Only the clinician the task was assigned by may review it. This is the
        access-control check that matters most in this module: a submission is
        health information, and any clinician being able to open any patient's
        file would defeat the point of having roles at all.
        """
        if outcome not in VALID_REVIEW_OUTCOMES:
            raise ValueError(f"outcome must be one of {VALID_REVIEW_OUTCOMES}")

        tasks = _load(TASKS_PATH)
        task = tasks.get(str(self.task_id))
        if task is None:
            raise ValueError(f"No task with id {self.task_id}")
        if task["clinician_id"] != reviewer_id:
            raise PermissionError(
                "Only the clinician assigned to this task may review the submission"
            )

        self.review_status = outcome
        self.reviewed_by = reviewer_id
        self.reviewed_at = datetime.now().isoformat()
        self.notes = notes

        subs = _load(SUBMISSIONS_PATH)
        subs[str(self.submission_id)] = self.__dict__
        _save(SUBMISSIONS_PATH, subs)

        tasks[str(self.task_id)]["status"] = "Reviewed"
        _save(TASKS_PATH, tasks)

    @staticmethod
    def get(submission_id):
        return _load(SUBMISSIONS_PATH).get(str(submission_id))

    @staticmethod
    def all_for_task(task_id):
        return [s for s in _load(SUBMISSIONS_PATH).values() if s["task_id"] == task_id]

    @staticmethod
    def all_pending_review():
        return [s for s in _load(SUBMISSIONS_PATH).values()
                if s["review_status"] == "Pending Review"]


if __name__ == "__main__":
    print("ClinicCare-Lite task workflow demo\n" + "=" * 45)
    os.makedirs(DATA_DIR, exist_ok=True)
    _save(TASKS_PATH, {})
    _save(SUBMISSIONS_PATH, {})

    t = HealthTask(1, "clin001", "pat2026", "Log blood pressure",
                   "Record BP twice daily for one week", "2026-09-05")
    t.save()
    print(f"Created task 1: status = {HealthTask.get(1)['status']}")

    s = TaskSubmission(1, task_id=1, patient_id="pat2026",
                       file_name="bp_readings.pdf", file_size_mb=1.2)
    s.save()
    print(f"Patient submitted: task status = {HealthTask.get(1)['status']}")

    for fn, size in [("malware.exe", 1.0), ("scan.pdf", 50.0), ("ok.pdf", 2.0)]:
        valid, err = TaskSubmission.validate_file(fn, size)
        print(f"  validate {fn:14s} {size:5.1f}MB -> {valid}{'' if valid else '  (' + err + ')'}")

    try:
        s.review_submission("Reviewed - Normal", reviewer_id="clin999")
    except PermissionError as e:
        print(f"Wrong clinician blocked: {e}")

    s.review_submission("Reviewed - Normal", reviewer_id="clin001", notes="Within range")
    print(f"Correct clinician reviewed: task status = {HealthTask.get(1)['status']}")

    try:
        TaskSubmission(2, task_id=1, patient_id="pat2026",
                       file_name="again.pdf", file_size_mb=1.0).save()
    except ValueError as e:
        print(f"Duplicate blocked: {e}")
