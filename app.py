"""
GridCare-Lite: Outage and Maintenance Management System
CS 112 Final Course Project - Group 2
Assigned to: Ethan Elom Koku Agbenu (Software Engineer / GridCare-Lite Lead)

Week 1 deliverable: application skeleton with a working SQLite-backed
login screen. Registration, outage logging, work-order management, and
reporting screens are stubbed for Week 2/3 development.

Run:
    python app_skeleton.py
"""

import sqlite3
import hashlib
import os
import tkinter as tk
from tkinter import ttk, messagebox

DB_PATH = os.path.join(os.path.dirname(__file__), "gridcare_lite.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "db_schema.sql")

ROLES = ["Administrator", "Engineer", "Technician", "CustomerService"]


# ------------------------------------------------------------------
# Database helpers
# ------------------------------------------------------------------
def hash_password(password: str) -> str:
    """Simple SHA-256 hash for demo purposes.
    Week 2+ should move to a salted hash (e.g. bcrypt) before any
    real deployment."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables from db_schema.sql if they don't exist yet,
    then seed one demo account per role."""
    with open(SCHEMA_PATH, "r") as f:
        schema_sql = f.read()

    conn = get_connection()
    conn.executescript(schema_sql)
    conn.commit()

    demo_accounts = [
        ("admin1", "admin123", "Niele Afia Nyamekye", "Administrator", "admin@gridcare-lite.test"),
        ("eng1", "engineer123", "Antipas Malual Mabeny", "Engineer", "engineer@gridcare-lite.test"),
        ("tech1", "tech123", "Diamond Obrempong Owusu Sekyere", "Technician", "tech@gridcare-lite.test"),
        ("cs1", "cs123", "Ethan Elom Koku Agbenu", "CustomerService", "cs@gridcare-lite.test"),
    ]
    cur = conn.cursor()
    for username, password, full_name, role, email in demo_accounts:
        cur.execute("SELECT 1 FROM users WHERE username = ?", (username,))
        if cur.fetchone() is None:
            cur.execute(
                """INSERT INTO users (username, password_hash, full_name, role, email)
                   VALUES (?, ?, ?, ?, ?)""",
                (username, hash_password(password), full_name, role, email),
            )
    conn.commit()
    conn.close()


def authenticate(username: str, password: str):
    """Return the user row if credentials are valid, else None."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM users WHERE username = ? AND is_active = 1", (username,)
    )
    row = cur.fetchone()
    conn.close()
    if row and row["password_hash"] == hash_password(password):
        return row
    return None


def register_user(username, password, full_name, role, email):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE username = ?", (username,))
    if cur.fetchone():
        conn.close()
        return False, "Username already exists."
    try:
        cur.execute(
            """INSERT INTO users (username, password_hash, full_name, role, email)
               VALUES (?, ?, ?, ?, ?)""",
            (username, hash_password(password), full_name, role, email),
        )
        conn.commit()
        return True, "Account created successfully."
    except sqlite3.IntegrityError as e:
        return False, f"Could not create account: {e}"
    finally:
        conn.close()


# ------------------------------------------------------------------
# GUI
# ------------------------------------------------------------------
class GridCareLiteApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GridCare-Lite \u2014 Outage & Maintenance Management")
        self.geometry("480x420")
        self.resizable(False, False)
        self.configure(bg="#f2f4f7")

        self.current_user = None

        container = tk.Frame(self, bg="#f2f4f7")
        container.pack(fill="both", expand=True)
        self.container = container

        self.frames = {}
        for F in (LoginFrame, RegisterFrame, DashboardFrame):
            frame = F(parent=container, controller=self)
            self.frames[F] = frame
            frame.place(relwidth=1, relheight=1)

        self.show_frame(LoginFrame)

    def show_frame(self, frame_class):
        frame = self.frames[frame_class]
        if hasattr(frame, "on_show"):
            frame.on_show()
        frame.tkraise()

    def login_success(self, user_row):
        self.current_user = user_row
        self.show_frame(DashboardFrame)


class LoginFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f2f4f7")
        self.controller = controller

        tk.Label(
            self, text="GridCare-Lite", font=("Segoe UI", 20, "bold"), bg="#f2f4f7"
        ).pack(pady=(40, 0))
        tk.Label(
            self,
            text="Outage & Maintenance Management System",
            font=("Segoe UI", 10),
            bg="#f2f4f7",
            fg="#555",
        ).pack(pady=(0, 30))

        form = tk.Frame(self, bg="#f2f4f7")
        form.pack()

        tk.Label(form, text="Username", bg="#f2f4f7").grid(row=0, column=0, sticky="w", pady=5)
        self.username_entry = ttk.Entry(form, width=30)
        self.username_entry.grid(row=0, column=1, pady=5)

        tk.Label(form, text="Password", bg="#f2f4f7").grid(row=1, column=0, sticky="w", pady=5)
        self.password_entry = ttk.Entry(form, width=30, show="*")
        self.password_entry.grid(row=1, column=1, pady=5)

        self.status_label = tk.Label(self, text="", fg="red", bg="#f2f4f7")
        self.status_label.pack(pady=(10, 0))

        btn_frame = tk.Frame(self, bg="#f2f4f7")
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="Log In", command=self.attempt_login).grid(row=0, column=0, padx=5)
        ttk.Button(
            btn_frame, text="Create Account",
            command=lambda: controller.show_frame(RegisterFrame)
        ).grid(row=0, column=1, padx=5)

        tk.Label(
            self,
            text="Demo accounts: admin1/admin123, eng1/engineer123,\n"
                 "tech1/tech123, cs1/cs123",
            font=("Segoe UI", 8), bg="#f2f4f7", fg="#888",
        ).pack(side="bottom", pady=10)

    def on_show(self):
        self.status_label.config(text="")
        self.password_entry.delete(0, tk.END)

    def attempt_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        if not username or not password:
            self.status_label.config(text="Please enter both username and password.")
            return
        user = authenticate(username, password)
        if user:
            self.controller.login_success(user)
        else:
            self.status_label.config(text="Invalid username or password.")


class RegisterFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f2f4f7")
        self.controller = controller

        tk.Label(
            self, text="Create Account", font=("Segoe UI", 16, "bold"), bg="#f2f4f7"
        ).pack(pady=(30, 20))

        form = tk.Frame(self, bg="#f2f4f7")
        form.pack()

        labels = ["Full Name", "Username", "Password", "Email"]
        self.entries = {}
        for i, label in enumerate(labels):
            tk.Label(form, text=label, bg="#f2f4f7").grid(row=i, column=0, sticky="w", pady=5)
            show = "*" if label == "Password" else None
            entry = ttk.Entry(form, width=30, show=show)
            entry.grid(row=i, column=1, pady=5)
            self.entries[label] = entry

        tk.Label(form, text="Role", bg="#f2f4f7").grid(row=len(labels), column=0, sticky="w", pady=5)
        self.role_var = tk.StringVar(value=ROLES[0])
        role_menu = ttk.Combobox(form, textvariable=self.role_var, values=ROLES, state="readonly", width=27)
        role_menu.grid(row=len(labels), column=1, pady=5)

        self.status_label = tk.Label(self, text="", fg="red", bg="#f2f4f7")
        self.status_label.pack(pady=(10, 0))

        btn_frame = tk.Frame(self, bg="#f2f4f7")
        btn_frame.pack(pady=15)
        ttk.Button(btn_frame, text="Register", command=self.attempt_register).grid(row=0, column=0, padx=5)
        ttk.Button(
            btn_frame, text="Back to Login",
            command=lambda: controller.show_frame(LoginFrame)
        ).grid(row=0, column=1, padx=5)

    def on_show(self):
        self.status_label.config(text="")

    def attempt_register(self):
        full_name = self.entries["Full Name"].get().strip()
        username = self.entries["Username"].get().strip()
        password = self.entries["Password"].get()
        email = self.entries["Email"].get().strip()
        role = self.role_var.get()

        if not all([full_name, username, password]):
            self.status_label.config(text="Full name, username, and password are required.")
            return

        success, message = register_user(username, password, full_name, role, email)
        if success:
            messagebox.showinfo("Success", message)
            self.controller.show_frame(LoginFrame)
        else:
            self.status_label.config(text=message)


class DashboardFrame(tk.Frame):
    """Placeholder dashboard. Role-specific views (outage logging,
    work-order assignment, technician task lists, complaint logging)
    are built out in Week 2/3."""

    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f2f4f7")
        self.controller = controller

        self.welcome_label = tk.Label(
            self, text="", font=("Segoe UI", 16, "bold"), bg="#f2f4f7"
        )
        self.welcome_label.pack(pady=(40, 10))

        self.role_label = tk.Label(self, text="", font=("Segoe UI", 11), bg="#f2f4f7", fg="#555")
        self.role_label.pack(pady=(0, 30))

        tk.Label(
            self,
            text="Role-specific dashboard (outage log, work orders,\n"
                 "technician tasks, complaints, reporting) is a\n"
                 "Week 2/3 deliverable.",
            bg="#f2f4f7", fg="#888",
        ).pack()

        ttk.Button(self, text="Log Out", command=self.log_out).pack(pady=30)

    def on_show(self):
        user = self.controller.current_user
        if user:
            self.welcome_label.config(text=f"Welcome, {user['full_name']}")
            self.role_label.config(text=f"Role: {user['role']}")

    def log_out(self):
        self.controller.current_user = None
        self.controller.show_frame(LoginFrame)


if __name__ == "__main__":
    init_db()
    app = GridCareLiteApp()
    app.mainloop()
