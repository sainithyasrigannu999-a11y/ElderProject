from __future__ import annotations

from flask import Flask, flash, redirect, render_template, request, session, url_for

from ai.emergency_classifier import classify_emergency
from config import Config
from database.db import create_demo_data, create_user, get_db_connection, get_user_by_email, get_user_by_id, init_db, list_emergencies_for_user, list_emergencies_for_caregiver, list_notifications_for_user, save_emergency, set_emergency_status, get_notification_count, get_emergency_by_id, create_notification, get_caregiver_connections, get_caregiver_connections_for_elderly, get_user_by_id as fetch_user_by_id, link_caregiver_to_elderly
from services.alert_service import send_caregiver_alert
from werkzeug.security import check_password_hash


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.secret_key = app.config["SECRET_KEY"]

    init_db()
    create_demo_data()

    @app.context_processor
    def inject_user_and_notifications():
        user = None
        if "user_id" in session:
            user = fetch_user_by_id(session["user_id"])
        notifications = []
        unread_count = 0
        if user:
            notifications = list_notifications_for_user(user["id"], limit=5)
            unread_count = get_notification_count(user["id"])
        return {"current_user": user, "notifications": notifications, "unread_count": unread_count}

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            data = {
                "name": request.form.get("name", "").strip(),
                "email": request.form.get("email", "").strip().lower(),
                "phone": request.form.get("phone", "").strip(),
                "age": request.form.get("age", "").strip(),
                "gender": request.form.get("gender", "").strip(),
                "password": request.form.get("password", ""),
                "confirm_password": request.form.get("confirm_password", ""),
                "role": request.form.get("role", "elderly"),
                "emergency_contact_name": request.form.get("emergency_contact_name", "").strip(),
                "emergency_contact_phone": request.form.get("emergency_contact_phone", "").strip(),
                "emergency_contact_email": request.form.get("emergency_contact_email", "").strip().lower(),
            }

            if not data["name"] or not data["email"] or not data["phone"] or not data["age"] or not data["password"]:
                flash("Please complete all required fields.", "error")
                return render_template("register.html", form=data)
            try:
                age = int(data["age"])
            except ValueError:
                flash("Age must be a valid number.", "error")
                return render_template("register.html", form=data)
            if age < 1 or age > 120:
                flash("Age must be between 1 and 120.", "error")
                return render_template("register.html", form=data)
            if "@" not in data["email"] or "." not in data["email"]:
                flash("Please enter a valid email address.", "error")
                return render_template("register.html", form=data)
            if len(data["phone"]) < 7:
                flash("Please enter a valid phone number.", "error")
                return render_template("register.html", form=data)
            if data["password"] != data["confirm_password"]:
                flash("Passwords do not match.", "error")
                return render_template("register.html", form=data)
            if data["role"] == "elderly":
                if not data["emergency_contact_name"] or not data["emergency_contact_phone"]:
                    flash("Emergency contact details are required for elderly users.", "error")
                    return render_template("register.html", form=data)
            user = get_user_by_email(data["email"])
            if user:
                flash("An account with that email already exists.", "error")
                return render_template("register.html", form=data)

            new_user_id = create_user(
                name=data["name"],
                email=data["email"],
                phone=data["phone"],
                age=age,
                gender=data["gender"],
                password=data["password"],
                role=data["role"],
                emergency_contact_name=data["emergency_contact_name"],
                emergency_contact_phone=data["emergency_contact_phone"],
                emergency_contact_email=data["emergency_contact_email"],
            )
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))
        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            role = request.form.get("role", "elderly")
            user = get_user_by_email(email)
            if not user or user["role"] != role:
                flash("Invalid login details. Please try again.", "error")
                return render_template("login.html")
            if not check_password_hash(user["password_hash"], password):
                flash("Incorrect password.", "error")
                return render_template("login.html")
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            flash(f"Welcome back, {user['name']}.", "success")
            if user["role"] == "elderly":
                return redirect(url_for("elderly_dashboard"))
            return redirect(url_for("caregiver_dashboard"))
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        flash("You have been logged out.", "success")
        return redirect(url_for("login"))

    @app.route("/elderly/dashboard")
    def elderly_dashboard():
        if "user_id" not in session or session.get("role") != "elderly":
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))
        user = fetch_user_by_id(session["user_id"])
        emergencies = list_emergencies_for_user(user["id"], limit=10)
        status = "Safe"
        if emergencies and emergencies[0]["status"] in ("ACTIVE", "PENDING"):
            status = "Emergency"
        elif emergencies and emergencies[0]["status"] == "WARNING":
            status = "Warning"
        caregiving_connections = get_caregiver_connections_for_elderly(user["id"])
        return render_template("elderly_dashboard.html", user=user, emergencies=emergencies, status=status, config=app.config, caregiver_connections=caregiving_connections)

    @app.route("/elderly/dashboard/connect-caregiver", methods=["POST"])
    def connect_caregiver():
        if "user_id" not in session or session.get("role") != "elderly":
            return {"error": "Unauthorized"}, 401

        caregiver_email = request.form.get("caregiver_email", "").strip().lower()
        caregiver_phone = request.form.get("caregiver_phone", "").strip()
        caregiver_name = request.form.get("caregiver_name", "").strip()

        if not (caregiver_email or caregiver_phone or caregiver_name):
            flash("Please provide a caregiver email, phone number, or name.", "error")
            return redirect(url_for("elderly_dashboard"))

        result = link_caregiver_to_elderly(
            session["user_id"],
            caregiver_email=caregiver_email,
            caregiver_phone=caregiver_phone,
            caregiver_name=caregiver_name,
        )

        if result:
            flash("Caregiver linked successfully.", "success")
        else:
            flash("No matching caregiver was found. Please check the details and try again.", "error")

        return redirect(url_for("elderly_dashboard"))

    @app.route("/elderly/dashboard/sos", methods=["POST"])
    def elderly_sos():
        if "user_id" not in session or session.get("role") != "elderly":
            return {"error": "Unauthorized"}, 401
        description = request.form.get("description") or "I need emergency help."
        location_text = request.form.get("location_text") or "Location not provided"
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")
        input_type = request.form.get("input_type") or "sos"
        result = classify_emergency(description)
        emergency_id = save_emergency(
            user_id=session["user_id"],
            category=result["category"],
            description=description,
            severity=result["severity"],
            ai_confidence=result["confidence"],
            input_type=input_type,
            confirmation_status="PENDING",
            status="ACTIVE",
            latitude=latitude,
            longitude=longitude,
            location_text=location_text,
            notify_caregiver=True,
        )
        send_caregiver_alert(emergency_id, session["user_id"])
        return {"message": "Emergency alert sent to caregiver.", "emergency_id": emergency_id, "result": result}, 200

    @app.route("/elderly/dashboard/confirm", methods=["POST"])
    def elderly_confirmation():
        if "user_id" not in session or session.get("role") != "elderly":
            return {"error": "Unauthorized"}, 401
        choice = request.form.get("choice", "").lower()
        description = request.form.get("description") or "Emergency response"
        emergency_id = request.form.get("emergency_id")
        emergency = get_emergency_by_id(emergency_id) if emergency_id else None
        if not emergency:
            return {"error": "Emergency not found."}, 404
        if choice in ("ok", "okay", "im okay", "i am okay"):
            set_emergency_status(emergency["id"], "RESOLVED", "SAFE")
            return {"message": "Emergency cancelled as safe."}, 200
        if choice in ("help", "need help", "yes", "confirm"):
            set_emergency_status(emergency["id"], "ACTIVE", "CONFIRMED")
            send_caregiver_alert(emergency["id"], emergency["user_id"])
            return {"message": "Emergency escalated for caregiver support."}, 200
        set_emergency_status(emergency["id"], "ACTIVE", "NO_RESPONSE")
        send_caregiver_alert(emergency["id"], emergency["user_id"])
        return {"message": "No response detected. Emergency escalated."}, 200

    @app.route("/caregiver/dashboard")
    def caregiver_dashboard():
        if "user_id" not in session or session.get("role") != "caregiver":
            flash("Please log in as a caregiver.", "error")
            return redirect(url_for("login"))
        user = fetch_user_by_id(session["user_id"])
        emergencies = list_emergencies_for_caregiver(session["user_id"])
        notifications = list_notifications_for_user(user["id"], limit=5)
        total_users = len(get_caregiver_connections(session["user_id"]))
        active_count = 0
        warning_count = 0
        resolved_count = 0
        for emergency in emergencies:
            status = (emergency.get("status") or "").upper()
            if status in {"ACTIVE", "PENDING", "ACKNOWLEDGED"}:
                active_count += 1
            if status == "RESOLVED":
                resolved_count += 1
            if (emergency.get("severity") or "").upper() == "WARNING":
                warning_count += 1
        return render_template(
            "caregiver_dashboard.html",
            user=user,
            emergencies=emergencies,
            notifications=notifications,
            total_users=total_users,
            active_count=active_count,
            warning_count=warning_count,
            resolved_count=resolved_count,
        )

    @app.route("/caregiver/emergency/<int:emergency_id>")
    def emergency_details(emergency_id):
        if "user_id" not in session or session.get("role") != "caregiver":
            flash("Please log in as a caregiver.", "error")
            return redirect(url_for("login"))
        emergency = get_emergency_by_id(emergency_id)
        if not emergency:
            flash("Emergency not found.", "error")
            return redirect(url_for("caregiver_dashboard"))
        elderly = fetch_user_by_id(emergency["user_id"])
        return render_template("emergency_details.html", emergency=emergency, elderly=elderly)

    @app.route("/caregiver/emergency/<int:emergency_id>/acknowledge", methods=["POST"])
    def acknowledge_emergency(emergency_id):
        if "user_id" not in session or session.get("role") != "caregiver":
            return {"error": "Unauthorized"}, 401
        set_emergency_status(emergency_id, "ACTIVE", "ACKNOWLEDGED")
        return {"message": "Emergency acknowledged."}, 200

    @app.route("/caregiver/emergency/<int:emergency_id>/resolve", methods=["POST"])
    def resolve_emergency(emergency_id):
        if "user_id" not in session or session.get("role") != "caregiver":
            return {"error": "Unauthorized"}, 401
        set_emergency_status(emergency_id, "RESOLVED", "RESOLVED")
        return {"message": "Emergency marked resolved."}, 200

    @app.route("/history")
    def history():
        if "user_id" not in session:
            flash("Please log in to view your emergency history.", "error")
            return redirect(url_for("login"))
        user = fetch_user_by_id(session["user_id"])
        if session.get("role") == "caregiver":
            emergencies = list_emergencies_for_caregiver(user["id"])
        else:
            emergencies = list_emergencies_for_user(user["id"], limit=50)
        return render_template("history.html", user=user, emergencies=emergencies)

    @app.route("/profile", methods=["GET", "POST"])
    def profile():
        if "user_id" not in session:
            flash("Please log in to update your profile.", "error")
            return redirect(url_for("login"))
        user = fetch_user_by_id(session["user_id"])
        if request.method == "POST":
            name = request.form.get("name", user["name"]).strip()
            phone = request.form.get("phone", user["phone"]).strip()
            age = request.form.get("age", user["age"]) or user["age"]
            gender = request.form.get("gender", user["gender"]) or user["gender"]
            password = request.form.get("password", "").strip()
            caregiver_email = request.form.get("caregiver_email", "").strip().lower()
            caregiver_phone = request.form.get("caregiver_phone", "").strip()
            caregiver_name = request.form.get("caregiver_name", "").strip()

            conn = get_db_connection()
            cur = conn.cursor()
            if password:
                cur.execute(
                    "UPDATE users SET name = ?, phone = ?, age = ?, gender = ?, password_hash = ? WHERE id = ?",
                    (name, phone, age, gender, __import__('werkzeug.security').security.generate_password_hash(password), session["user_id"]),
                )
            else:
                cur.execute(
                    "UPDATE users SET name = ?, phone = ?, age = ?, gender = ? WHERE id = ?",
                    (name, phone, age, gender, session["user_id"]),
                )
            conn.commit()
            conn.close()

            if user["role"] == "elderly":
                linked = link_caregiver_to_elderly(
                    session["user_id"],
                    caregiver_email=caregiver_email,
                    caregiver_phone=caregiver_phone,
                    caregiver_name=caregiver_name,
                )
                if linked:
                    flash("Profile updated and caregiver linked successfully.", "success")
                elif caregiver_email or caregiver_phone or caregiver_name:
                    flash("Profile updated, but no matching caregiver was found. Please check the email or phone number.", "error")
                else:
                    flash("Profile updated successfully.", "success")
                return redirect(url_for("profile"))

            flash("Profile updated successfully.", "success")
            return redirect(url_for("profile"))
        return render_template("profile.html", user=user)

    @app.route("/caregiver/notifications/count")
    def caregiver_notification_count():
        if "user_id" not in session or session.get("role") != "caregiver":
            return {"error": "Unauthorized"}, 401
        return {"count": get_notification_count(session["user_id"])}, 200

    @app.route("/notifications")
    def notifications():
        if "user_id" not in session:
            flash("Please log in to view notifications.", "error")
            return redirect(url_for("login"))
        user = fetch_user_by_id(session["user_id"])
        notifications = list_notifications_for_user(user["id"], limit=30)
        return render_template("notifications.html", notifications=notifications, user=user)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5001)