from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from database.db import create_user, get_user_by_email

bp = Blueprint("auth", __name__)


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        age = request.form.get("age", "").strip()
        gender = request.form.get("gender", "").strip()
        role = request.form.get("role", "elderly")
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        emergency_contact_name = request.form.get("emergency_contact_name", "").strip()
        emergency_contact_phone = request.form.get("emergency_contact_phone", "").strip()
        emergency_contact_email = request.form.get("emergency_contact_email", "").strip().lower()

        if not all([name, email, phone, age, password, confirm_password]):
            flash("Please complete all required fields.", "error")
            return render_template("register.html")
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("register.html")
        if get_user_by_email(email):
            flash("This email is already registered.", "error")
            return render_template("register.html")

        create_user(
            name=name,
            email=email,
            phone=phone,
            age=int(age),
            gender=gender,
            password=password,
            role=role,
            emergency_contact_name=emergency_contact_name,
            emergency_contact_phone=emergency_contact_phone,
            emergency_contact_email=emergency_contact_email,
        )
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "elderly")
        user = get_user_by_email(email)

        if not user or user["role"] != role or not check_password_hash(user["password_hash"], password):
            flash("Invalid credentials. Please try again.", "error")
            return render_template("login.html")

        session["user_id"] = user["id"]
        session["role"] = user["role"]
        flash(f"Welcome, {user['name']}.", "success")
        if user["role"] == "elderly":
            return redirect(url_for("elderly_dashboard"))
        return redirect(url_for("caregiver_dashboard"))
    return render_template("login.html")


@bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))
