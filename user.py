"""
ClinicCare-Lite: User model
CS 112 Final Course Project - Group 2

Clinician and Patient accounts, with ID-format and password-strength
validation.

Storage is JSON (data/users.json) rather than SQLite, matching the file-based
pattern used by the rest of ClinicCare-Lite.

Security note: passwords are hashed with a salted SHA-256 here. That is better
than the unsalted hashing used elsewhere in this project, but a real health
system would use a purpose-built KDF such as bcrypt or Argon2. This is
coursework, and the limitation is deliberate and documented rather than
overlooked.
"""

import os
import json
import re
import hashlib
import secrets
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
USERS_PATH = os.path.join(DATA_DIR, "users.json")

# Clinician IDs: 'clin' + 3 digits, e.g. clin001
# Patient IDs:   'pat'  + 4 digits, e.g. pat2026
ID_PATTERNS = {
    "clinician": re.compile(r"^clin\d{3}$"),
    "patient": re.compile(r"^pat\d{4}$"),
}

MIN_PASSWORD_LENGTH = 8


def _load():
    if not os.path.exists(USERS_PATH):
        return {}
    with open(USERS_PATH, "r") as f:
        return json.load(f)


def _save(data):
    os.makedirs(os.path.dirname(USERS_PATH), exist_ok=True)
    with open(USERS_PATH, "w") as f:
        json.dump(data, f, indent=4)


class User:
    def __init__(self, user_id, full_name, role, email=None, password=None):
        if not User.validate_id(user_id, role):
            raise ValueError(
                f"Invalid {role} ID format: '{user_id}'. "
                f"Expected {'clinNNN' if role == 'clinician' else 'patNNNN'}."
            )
        if password is not None and not User.validate_password(password):
            raise ValueError(
                "Password too weak. Requires at least "
                f"{MIN_PASSWORD_LENGTH} characters including an uppercase "
                "letter, a lowercase letter, and a digit."
            )

        self.user_id = user_id
        self.full_name = full_name
        self.role = role
        self.email = email
        self.salt = secrets.token_hex(16) if password else None
        self.password_hash = User.hash_password(password, self.salt) if password else None
        self.created_at = datetime.now().isoformat()
        self.is_active = True

    # ---------------------------------------------------------- validation
    @staticmethod
    def validate_id(user_id, role):
        """True if user_id matches the required format for its role."""
        if not isinstance(user_id, str):
            return False
        pattern = ID_PATTERNS.get(str(role).lower())
        if pattern is None:
            return False
        return bool(pattern.match(user_id))

    @staticmethod
    def validate_password(password):
        """True if the password meets minimum strength requirements."""
        if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
            return False
        if not re.search(r"[A-Z]", password):
            return False
        if not re.search(r"[a-z]", password):
            return False
        if not re.search(r"\d", password):
            return False
        return True

    @staticmethod
    def validate_email(email):
        if not isinstance(email, str):
            return False
        return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))

    # ---------------------------------------------------------- auth
    @staticmethod
    def hash_password(password, salt):
        return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()

    @staticmethod
    def authenticate(user_id, password):
        """Return the stored user dict on success, else None."""
        users = _load()
        u = users.get(str(user_id))
        if not u or not u.get("is_active") or not u.get("password_hash"):
            return None
        if User.hash_password(password, u["salt"]) == u["password_hash"]:
            return u
        return None

    # ---------------------------------------------------------- persistence
    def save(self):
        users = _load()
        if str(self.user_id) in users:
            raise ValueError(f"User {self.user_id} already exists")
        users[str(self.user_id)] = self.__dict__
        _save(users)
        return self.user_id

    @staticmethod
    def get(user_id):
        return _load().get(str(user_id))

    @staticmethod
    def all_by_role(role):
        return [u for u in _load().values() if u["role"] == role]

    @staticmethod
    def deactivate(user_id):
        users = _load()
        if str(user_id) not in users:
            raise ValueError(f"No user with id {user_id}")
        users[str(user_id)]["is_active"] = False
        _save(users)


if __name__ == "__main__":
    print("ClinicCare-Lite User model demo\n" + "=" * 45)

    print("ID validation:")
    for uid, role in [("clin001", "clinician"), ("pat2026", "patient"),
                      ("12", "patient"), ("abcd2026", "patient"),
                      ("clin1", "clinician")]:
        print(f"  {uid:12s} as {role:10s} -> {User.validate_id(uid, role)}")

    print("\nPassword validation:")
    for pw in ["weak", "Str0ngPass", "alllowercase1", "NOLOWERCASE1", "Sh0rt"]:
        print(f"  {pw:16s} -> {User.validate_password(pw)}")
