from __future__ import annotations

from database.db import create_notification, get_caregiver_connections, get_user_by_id


def send_caregiver_alert(emergency_id: int, elderly_user_id: int):
    connections = get_caregiver_connections_by_elderly(elderly_user_id)
    for connection in connections:
        create_notification(
            recipient_id=connection["caregiver_user_id"],
            emergency_id=emergency_id,
            message=f"New emergency alert for {get_user_by_id(elderly_user_id)['name']}",
        )
    return len(connections)


def get_caregiver_connections_by_elderly(elderly_user_id: int):
    conn = __import__("database.db", fromlist=["get_db_connection"]).get_db_connection()
    rows = conn.execute(
        "SELECT * FROM caregiver_connections WHERE elderly_user_id = ?",
        (elderly_user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
