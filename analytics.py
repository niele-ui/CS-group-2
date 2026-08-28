"""
ClinicCare-Lite: Operational Analytics
CS 112 Final Course Project - Group 2

Clinician-facing operational metrics: completion rate, review turnaround,
backlog, outcome mix, and load per clinician.

Note on turnaround time: an earlier draft of this module could not compute
review turnaround because TaskSubmission stored only `submitted_at`, not
`reviewed_at`. That field now exists (see health_task.py), so turnaround is a
real measurement here rather than a placeholder.
"""

import os
import json
from datetime import datetime
from collections import Counter

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
TASKS_PATH = os.path.join(DATA_DIR, "tasks.json")
SUBMISSIONS_PATH = os.path.join(DATA_DIR, "submissions.json")


def _load(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)


def get_task_completion_rate():
    """Percentage of tasks that have reached Reviewed or Completed."""
    tasks = _load(TASKS_PATH)
    if not tasks:
        return 0.0
    done = sum(1 for t in tasks.values() if t["status"] in ("Reviewed", "Completed"))
    return round(done / len(tasks) * 100, 1)


def get_average_review_turnaround_hours():
    """Mean hours from patient submission to clinician review.

    Returns None if nothing has been reviewed yet, which is different from
    returning 0 and should not be collapsed into it.
    """
    subs = _load(SUBMISSIONS_PATH)
    deltas = []
    for s in subs.values():
        if s.get("reviewed_at") and s.get("submitted_at"):
            d = datetime.fromisoformat(s["reviewed_at"]) - datetime.fromisoformat(s["submitted_at"])
            deltas.append(d.total_seconds() / 3600)
    if not deltas:
        return None
    return round(sum(deltas) / len(deltas), 4)


def get_backlog_count():
    """Submissions waiting on a clinician."""
    subs = _load(SUBMISSIONS_PATH)
    return sum(1 for s in subs.values() if s["review_status"] == "Pending Review")


def get_overdue_tasks(reference_date=None):
    """Tasks past their due date that are not yet reviewed."""
    ref = reference_date or datetime.now()
    if isinstance(ref, str):
        ref = datetime.fromisoformat(ref)
    overdue = []
    for t in _load(TASKS_PATH).values():
        if t["status"] in ("Reviewed", "Completed"):
            continue
        if not t.get("due_date"):
            continue
        try:
            if datetime.fromisoformat(str(t["due_date"])) < ref:
                overdue.append(t)
        except ValueError:
            continue
    return overdue


def get_outcome_distribution():
    subs = _load(SUBMISSIONS_PATH)
    outcomes = [s["review_status"] for s in subs.values()
                if s["review_status"] != "Pending Review"]
    return dict(Counter(outcomes))


def get_tasks_by_clinician():
    tasks = _load(TASKS_PATH)
    return dict(Counter(t["clinician_id"] for t in tasks.values()))


def get_tasks_by_status():
    tasks = _load(TASKS_PATH)
    return dict(Counter(t["status"] for t in tasks.values()))


def get_escalation_rate():
    """Share of reviewed submissions that were escalated. Worth tracking
    separately from the outcome mix because a rising escalation rate is an
    operational signal, not just a category count."""
    dist = get_outcome_distribution()
    total = sum(dist.values())
    if not total:
        return None
    return round(dist.get("Escalated", 0) / total * 100, 1)


def get_operational_summary():
    return {
        "task_completion_rate_pct": get_task_completion_rate(),
        "backlog_count": get_backlog_count(),
        "overdue_task_count": len(get_overdue_tasks()),
        "mean_review_turnaround_hours": get_average_review_turnaround_hours(),
        "escalation_rate_pct": get_escalation_rate(),
        "outcome_distribution": get_outcome_distribution(),
        "tasks_by_clinician": get_tasks_by_clinician(),
        "tasks_by_status": get_tasks_by_status(),
    }


if __name__ == "__main__":
    print("ClinicCare-Lite operational analytics\n" + "=" * 45)
    summary = get_operational_summary()
    if not summary["tasks_by_status"]:
        print("No task data found. Run health_task.py first to generate a demo task.")
    for k, v in summary.items():
        print(f"  {k}: {v}")
