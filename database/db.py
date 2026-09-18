from __future__ import annotations

import os
import sqlite3
from typing import Any, Dict, List, Optional

from flask import g
from werkzeug.security import generate_password_hash

from config import config

DB_PATH = "elderguard_ai.db"


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    with open("database/schema.sql", "r", encoding="utf-8") as file:
        conn.executescript(file.read())
    conn.commit()
    conn.close()


def create_demo_data():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] > 0:
        conn.close()
        return

    cur.execute(
        "INSERT INTO users (name, email, phone, age, gender, password_hash, role) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            "Maya Elder",
            "elder@example.com",
            "5551110001",
            72,
            "Female",
            generate_password_hash("password123"),
            "elderly",
        ),
    )
    cur.execute(
        "INSERT INTO users (name, email, phone, age, gender, password_hash, role) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            "Rohan Care",
            "caregiver@example.com",
            "5552220002",
            40,
            "Male",
            generate_password_hash("password123"),
            "caregiver",
        ),
    )
    cur.execute(
        "INSERT INTO caregiver_connections (elderly_user_id, caregiver_user_id, relationship) VALUES (?, ?, ?)",
        (1, 2, "Grandson"),
    )
    cur.execute(
        "INSERT INTO emergency_contacts (user_id, contact_name, contact_phone, contact_email) VALUES (?, ?, ?, ?)",
        (1, "Rohan Care", "5552220002", "caregiver@example.com"),
    )
    cur.execute(
        "INSERT INTO emergencies (user_id, category, description, severity, ai_confidence, input_type, confirmation_status, status, location_text, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (1, "Fall", "I fell down and I cannot get up.", "CRITICAL", 0.92, "voice", "CONFIRMED", "RESOLVED", "Living room", "2026-09-18 08:30:00"),
    )
    cur.execute(
        "INSERT INTO notifications (recipient_id, emergency_id, message, is_read, created_at) VALUES (?, ?, ?, ?, ?)",
        (2, 1, "New emergency alert for Maya Elder", 0, "2026-09-18 08:30:00"),
    )
    conn.commit()
    conn.close()


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_matching_caregiver_for_elderly(name=None, phone=None, email=None):
    conn = get_db_connection()
    caregiver = None

    if phone:
        caregiver = conn.execute(
            "SELECT * FROM users WHERE role = 'caregiver' AND phone = ? LIMIT 1",
            (phone,),
        ).fetchone()

    if caregiver is None and email:
        caregiver = conn.execute(
            "SELECT * FROM users WHERE role = 'caregiver' AND email = ? LIMIT 1",
            (email,),
        ).fetchone()

    if caregiver is None and name:
        caregiver = conn.execute(
            "SELECT * FROM users WHERE role = 'caregiver' AND name = ? LIMIT 1",
            (name,),
        ).fetchone()

    conn.close()
    return dict(caregiver) if caregiver else None


def link_caregiver_to_elderly(elderly_user_id: int, caregiver_email=None, caregiver_phone=None, caregiver_name=None):
    conn = get_db_connection()
    cur = conn.cursor()
    caregiver = None

    if caregiver_email:
        caregiver = conn.execute(
            "SELECT * FROM users WHERE role = 'caregiver' AND email = ? LIMIT 1",
            (caregiver_email,),
        ).fetchone()

    if caregiver is None and caregiver_phone:
        caregiver = conn.execute(
            "SELECT * FROM users WHERE role = 'caregiver' AND phone = ? LIMIT 1",
            (caregiver_phone,),
        ).fetchone()

    if caregiver is None and caregiver_name:
        caregiver = conn.execute(
            "SELECT * FROM users WHERE role = 'caregiver' AND name = ? LIMIT 1",
            (caregiver_name,),
        ).fetchone()

    if caregiver is None:
        conn.close()
        return None

    existing = conn.execute(
        "SELECT 1 FROM caregiver_connections WHERE elderly_user_id = ? AND caregiver_user_id = ? LIMIT 1",
        (elderly_user_id, caregiver["id"]),
    ).fetchone()

    if not existing:
        cur.execute(
            "INSERT INTO caregiver_connections (elderly_user_id, caregiver_user_id, relationship) VALUES (?, ?, ?)",
            (elderly_user_id, caregiver["id"], "Manual link"),
        )

    conn.commit()
    conn.close()
    return dict(caregiver)


def create_user(name, email, phone, age, gender, password, role, emergency_contact_name=None, emergency_contact_phone=None, emergency_contact_email=None):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (name, email, phone, age, gender, password_hash, role) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (name, email, phone, age, gender, generate_password_hash(password), role),
    )
    user_id = cur.lastrowid
    if role == "elderly":
        cur.execute(
            "INSERT INTO emergency_contacts (user_id, contact_name, contact_phone, contact_email) VALUES (?, ?, ?, ?)",
            (user_id, emergency_contact_name, emergency_contact_phone, emergency_contact_email),
        )

        caregiver = get_matching_caregiver_for_elderly(
            name=emergency_contact_name,
            phone=emergency_contact_phone,
            email=emergency_contact_email,
        )
        if caregiver:
            existing = conn.execute(
                "SELECT 1 FROM caregiver_connections WHERE elderly_user_id = ? AND caregiver_user_id = ? LIMIT 1",
                (user_id, caregiver["id"]),
            ).fetchone()
            if not existing:
                cur.execute(
                    "INSERT INTO caregiver_connections (elderly_user_id, caregiver_user_id, relationship) VALUES (?, ?, ?)",
                    (user_id, caregiver["id"], "Emergency contact"),
                )
    conn.commit()
    conn.close()
    return user_id


def save_emergency(user_id, category, description, severity, ai_confidence, input_type, confirmation_status, status, latitude=None, longitude=None, location_text=None, notify_caregiver=False):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO emergencies (user_id, category, description, severity, ai_confidence, input_type, confirmation_status, status, latitude, longitude, location_text) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (user_id, category, description, severity, ai_confidence, input_type, confirmation_status, status, latitude, longitude, location_text),
    )
    emergency_id = cur.lastrowid
    conn.commit()
    conn.close()
    return emergency_id


def get_emergency_by_id(emergency_id: int):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM emergencies WHERE id = ?", (emergency_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def list_emergencies_for_user(user_id: int, limit: int = 20):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM emergencies WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def list_emergencies_for_caregiver(caregiver_user_id: int):
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT e.*, u.name AS elderly_name, u.phone AS elderly_phone, u.age AS elderly_age
        FROM emergencies e
        INNER JOIN caregiver_connections c ON c.elderly_user_id = e.user_id
        INNER JOIN users u ON u.id = e.user_id
        WHERE c.caregiver_user_id = ?
        ORDER BY e.created_at DESC
        """,
        (caregiver_user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def list_notifications_for_user(user_id: int, limit: int = 20):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM notifications WHERE recipient_id = ? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_notification_count(user_id: int):
    conn = get_db_connection()
    row = conn.execute("SELECT COUNT(*) FROM notifications WHERE recipient_id = ? AND is_read = 0", (user_id,)).fetchone()
    conn.close()
    return row[0] if row else 0


def create_notification(recipient_id: int, emergency_id: int, message: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO notifications (recipient_id, emergency_id, message, is_read) VALUES (?, ?, ?, 0)",
        (recipient_id, emergency_id, message),
    )
    conn.commit()
    conn.close()


def set_emergency_status(emergency_id: int, status: str, confirmation_status: str = None):
    conn = get_db_connection()
    cur = conn.cursor()
    if status == "RESOLVED":
        if confirmation_status:
            cur.execute(
                "UPDATE emergencies SET status = ?, confirmation_status = ?, resolved_at = datetime('now') WHERE id = ?",
                (status, confirmation_status, emergency_id),
            )
        else:
            cur.execute(
                "UPDATE emergencies SET status = ?, resolved_at = datetime('now') WHERE id = ?",
                (status, emergency_id),
            )
    else:
        if confirmation_status:
            cur.execute(
                "UPDATE emergencies SET status = ?, confirmation_status = ? WHERE id = ?",
                (status, confirmation_status, emergency_id),
            )
        else:
            cur.execute("UPDATE emergencies SET status = ? WHERE id = ?", (status, emergency_id))
    conn.commit()
    conn.close()


def get_caregiver_connections(caregiver_id: int):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM caregiver_connections WHERE caregiver_user_id = ?",
        (caregiver_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_caregiver_connections_for_elderly(elderly_user_id: int):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT c.*, u.name AS caregiver_name, u.email AS caregiver_email, u.phone AS caregiver_phone FROM caregiver_connections c INNER JOIN users u ON u.id = c.caregiver_user_id WHERE c.elderly_user_id = ?",
        (elderly_user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_contact_for_user(user_id):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM emergency_contacts WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None
