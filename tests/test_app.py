from app import create_app
from database.db import get_caregiver_connections, get_user_by_email


def test_app_creates_and_has_routes():
    app = create_app()
    client = app.test_client()

    assert client.get("/").status_code == 200
    assert client.get("/register").status_code == 200
    assert client.get("/login").status_code == 200


def test_registration_and_login_flow():
    app = create_app()
    client = app.test_client()

    response = client.post(
        "/register",
        data={
            "name": "Test Elder",
            "email": "test-elder@example.com",
            "phone": "5551234567",
            "age": "76",
            "gender": "Female",
            "password": "password123",
            "confirm_password": "password123",
            "role": "elderly",
            "emergency_contact_name": "Test Caregiver",
            "emergency_contact_phone": "5557654321",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    login_response = client.post(
        "/login",
        data={
            "email": "test-elder@example.com",
            "password": "password123",
            "role": "elderly",
        },
        follow_redirects=True,
    )
    assert login_response.status_code == 200
    assert b"Hello, Test Elder" in login_response.data


def test_profile_can_link_a_caregiver_by_email_for_new_user():
    app = create_app()
    client = app.test_client()

    register_response = client.post(
        "/register",
        data={
            "name": "New Elder",
            "email": "new-elder@example.com",
            "phone": "5557770001",
            "age": "80",
            "gender": "Female",
            "password": "password123",
            "confirm_password": "password123",
            "role": "elderly",
            "emergency_contact_name": "Rohan Care",
            "emergency_contact_phone": "5552220002",
            "emergency_contact_email": "caregiver@example.com",
        },
        follow_redirects=True,
    )
    assert register_response.status_code == 200

    elderly = get_user_by_email("new-elder@example.com")
    assert elderly is not None

    login_response = client.post(
        "/login",
        data={
            "email": "new-elder@example.com",
            "password": "password123",
            "role": "elderly",
        },
        follow_redirects=True,
    )
    assert login_response.status_code == 200

    profile_response = client.post(
        "/profile",
        data={
            "name": "New Elder",
            "phone": "5557770001",
            "age": "80",
            "gender": "Female",
            "caregiver_email": "caregiver@example.com",
            "caregiver_phone": "5552220002",
            "caregiver_name": "Rohan Care",
        },
        follow_redirects=True,
    )
    assert profile_response.status_code == 200

    caregiver_links = get_caregiver_connections(2)
    assert any(item["elderly_user_id"] == elderly["id"] for item in caregiver_links)


def test_caregiver_notification_count_route():
    app = create_app()
    client = app.test_client()

    login_response = client.post(
        "/login",
        data={
            "email": "caregiver@example.com",
            "password": "password123",
            "role": "caregiver",
        },
        follow_redirects=True,
    )
    assert login_response.status_code == 200

    response = client.get("/caregiver/notifications/count")
    assert response.status_code == 200
    payload = response.get_json()
    assert "count" in payload
    assert isinstance(payload["count"], int)


def test_elderly_dashboard_can_link_caregiver_directly():
    app = create_app()
    client = app.test_client()

    login_response = client.post(
        "/login",
        data={
            "email": "elder@example.com",
            "password": "password123",
            "role": "elderly",
        },
        follow_redirects=True,
    )
    assert login_response.status_code == 200

    link_response = client.post(
        "/elderly/dashboard/connect-caregiver",
        data={
            "caregiver_email": "caregiver@example.com",
            "caregiver_phone": "5552220002",
            "caregiver_name": "Rohan Care",
        },
        follow_redirects=True,
    )
    assert link_response.status_code == 200
    assert b"Caregiver linked successfully" in link_response.data

    caregiver_links = get_caregiver_connections(2)
    assert any(item["elderly_user_id"] == 1 for item in caregiver_links)


def test_caregiver_flow_from_emergency_to_resolution():
    app = create_app()
    client = app.test_client()

    elderly_login = client.post(
        "/login",
        data={
            "email": "elder@example.com",
            "password": "password123",
            "role": "elderly",
        },
        follow_redirects=True,
    )
    assert elderly_login.status_code == 200

    sos_response = client.post(
        "/elderly/dashboard/sos",
        data={
            "description": "I fell down and I cannot get up.",
            "input_type": "voice",
            "location_text": "Living room",
        },
    )
    assert sos_response.status_code == 200
    payload = sos_response.get_json()
    emergency_id = payload["emergency_id"]
    assert emergency_id is not None

    confirmation_response = client.post(
        "/elderly/dashboard/confirm",
        data={
            "choice": "help",
            "emergency_id": emergency_id,
            "description": "I fell down and I cannot get up.",
        },
    )
    assert confirmation_response.status_code == 200

    caregiver_logout = client.get("/logout")
    assert caregiver_logout.status_code == 302

    caregiver_login = client.post(
        "/login",
        data={
            "email": "caregiver@example.com",
            "password": "password123",
            "role": "caregiver",
        },
        follow_redirects=True,
    )
    assert caregiver_login.status_code == 200
    assert b"Maya Elder" in caregiver_login.data
    assert b"ACTIVE" in caregiver_login.data or b"Acknowledged" in caregiver_login.data or b"Resolved" in caregiver_login.data

    acknowledge = client.post(f"/caregiver/emergency/{emergency_id}/acknowledge")
    assert acknowledge.status_code == 200
    resolve = client.post(f"/caregiver/emergency/{emergency_id}/resolve")
    assert resolve.status_code == 200

    history_response = client.get("/history", follow_redirects=True)
    assert history_response.status_code == 200
    assert b"I fell down and I cannot get up" in history_response.data
