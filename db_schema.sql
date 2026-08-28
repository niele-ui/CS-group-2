-- ============================================================
-- ClinicCare-Lite Database Schema
-- Clinic Patient Administration and Communication System
-- CS 112 Final Course Project - Group 2
--
-- Security note: this system stores health-related data. Access
-- control is enforced both here (via role checks in application
-- logic) and should be paired with encryption-at-rest for the
-- `health_tasks.details` and `messages.body` columns before any
-- real deployment, per the Week 1 ethics/security boundary doc.
-- ============================================================

PRAGMA foreign_keys = ON;

-- ------------------------------------------------------------
-- Users & Roles (Clinician, Patient)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT NOT NULL UNIQUE,   -- follows the ID format defined in the spec
    password_hash   TEXT NOT NULL,
    full_name       TEXT NOT NULL,
    role            TEXT NOT NULL CHECK (role IN ('Clinician', 'Patient')),
    email           TEXT UNIQUE,
    phone           TEXT,
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ------------------------------------------------------------
-- Health Tasks (assigned by clinicians, actioned by patients)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS health_tasks (
    task_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    assigned_by     INTEGER NOT NULL,   -- users.user_id (Clinician)
    assigned_to     INTEGER NOT NULL,   -- users.user_id (Patient)
    title           TEXT NOT NULL,
    details         TEXT,
    due_date        TEXT,
    status          TEXT NOT NULL DEFAULT 'Pending'
                        CHECK (status IN ('Pending', 'Submitted', 'Reviewed', 'Completed')),
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (assigned_by) REFERENCES users (user_id),
    FOREIGN KEY (assigned_to) REFERENCES users (user_id)
);

-- ------------------------------------------------------------
-- Task Submissions (patient responses, with optional file)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS task_submissions (
    submission_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id         INTEGER NOT NULL,
    submitted_by    INTEGER NOT NULL,   -- users.user_id (Patient)
    submission_text TEXT,
    file_path       TEXT,               -- path to securely stored uploaded file, if any
    submitted_at    TEXT NOT NULL DEFAULT (datetime('now')),
    reviewed_by     INTEGER,            -- users.user_id (Clinician)
    review_notes    TEXT,
    reviewed_at     TEXT,
    FOREIGN KEY (task_id) REFERENCES health_tasks (task_id),
    FOREIGN KEY (submitted_by) REFERENCES users (user_id),
    FOREIGN KEY (reviewed_by) REFERENCES users (user_id)
);

-- ------------------------------------------------------------
-- Appointments
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS appointments (
    appointment_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id      INTEGER NOT NULL,
    clinician_id    INTEGER NOT NULL,
    scheduled_for   TEXT NOT NULL,
    reason          TEXT,
    status          TEXT NOT NULL DEFAULT 'Scheduled'
                        CHECK (status IN ('Scheduled', 'Completed', 'Cancelled', 'No-show')),
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (patient_id) REFERENCES users (user_id),
    FOREIGN KEY (clinician_id) REFERENCES users (user_id)
);

-- ------------------------------------------------------------
-- Private Messaging
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS messages (
    message_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id       INTEGER NOT NULL,
    recipient_id    INTEGER NOT NULL,
    body            TEXT NOT NULL,
    sent_at         TEXT NOT NULL DEFAULT (datetime('now')),
    read_at         TEXT,
    FOREIGN KEY (sender_id) REFERENCES users (user_id),
    FOREIGN KEY (recipient_id) REFERENCES users (user_id)
);

-- ------------------------------------------------------------
-- Notifications
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS notifications (
    notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    content         TEXT NOT NULL,
    notification_type TEXT NOT NULL DEFAULT 'General'
                        CHECK (notification_type IN ('General', 'TaskAssigned', 'Appointment', 'Message')),
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    read_at         TEXT,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);

-- ------------------------------------------------------------
-- Indexes
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_to ON health_tasks (assigned_to);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON health_tasks (status);
CREATE INDEX IF NOT EXISTS idx_appointments_patient ON appointments (patient_id);
CREATE INDEX IF NOT EXISTS idx_appointments_clinician ON appointments (clinician_id);
CREATE INDEX IF NOT EXISTS idx_messages_recipient ON messages (recipient_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications (user_id);

-- Seed accounts are created programmatically (see cliniccare_lite's
-- forthcoming app module in Week 2) using hashed passwords, consistent
-- with GridCare-Lite's approach in app_skeleton.py.
