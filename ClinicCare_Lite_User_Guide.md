# ClinicCare-Lite — User Guide

CS 112 Final Course Project, Summer 2026

## What ClinicCare-Lite Does

ClinicCare-Lite is an administrative tool that lets a clinician assign health-related
tasks to patients (like submitting a reading or a document), and lets patients submit
those tasks and get them reviewed. It does not diagnose anything or give medical advice —
it only manages the back-and-forth of assigning, submitting, and reviewing.

## Logging In

Your ID is an 8-digit number. Clinician IDs end in `0000`. Patient IDs end in the year
they joined (for example, `2026`). Enter your ID and password on the login screen.

Passwords must be at least 8 characters and include an uppercase letter, a lowercase
letter, a number, and a symbol. If your password doesn't meet this, the app will reject
it when you try to set one.

---

## For Patients

### Viewing Your Tasks

After logging in, go to **Health Tasks** to see what's been assigned to you, including
the due date and current status (Assigned, Submitted, or Reviewed).

### Submitting a Task

1. Open the task you need to complete.
2. Click **Submit**.
3. Upload your file. Accepted file types are `.pdf`, `.jpg`, `.jpeg`, `.png`, and `.csv`,
   and the file must be under 10MB.
4. Submit. The task status changes to "Submitted" and your clinician will review it.

You can only submit once per task. If you try to submit a second file for the same task,
the app will block it — if you made a mistake, contact your clinician rather than trying
to resubmit.

### Messages

Use **Messages** to communicate directly with your clinician outside of a specific task.

---

## For Clinicians

### Assigning a Task

1. Go to **Health Tasks** and click **+ New Task**.
2. Choose the patient, give the task a title and description, and set a due date.
3. Submit. The patient will now see this task on their dashboard.

### Reviewing a Submission

1. Open the submitted task from your dashboard.
2. Click **Review**.
3. Choose an outcome: **Reviewed – Normal**, **Needs Follow-up**, or **Escalated**.
4. Add notes if needed, and submit.

Only the clinician the task was originally assigned to can review it. If another
clinician tries to review it, the app will block the action.

### Operational Analytics

Your dashboard shows:

- Task completion rate
- Backlog (tasks submitted but not yet reviewed)
- Outcome breakdown (Normal / Follow-up / Escalated)
- Number of tasks per clinician

## Common Issues

| Problem | What's happening |
|---|---|
| File upload rejected | Check the file type and size — only PDF, JPG, PNG, and CSV under 10MB are accepted. |
| "Only the assigned clinician can review" error | You're not the clinician this task was assigned to. |
| Can't submit a task again | Each task only accepts one submission per patient. Contact your clinician if you made an error. |
| Weak password rejected at signup | Make sure it has 8+ characters, an uppercase and lowercase letter, a number, and a symbol. |
