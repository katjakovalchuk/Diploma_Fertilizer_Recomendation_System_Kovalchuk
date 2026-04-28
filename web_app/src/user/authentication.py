from flask import Blueprint, request, redirect, render_template, session, jsonify
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

import re

from data_base.connection import get_connection

BASE = "/diploma/fertilizer_recommendation"
auth = Blueprint("auth", __name__)

pass_hasher = PasswordHasher()
email_regex = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,7}")


@auth.route(BASE + "/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        surname = request.form["surname"]
        region = request.form["region"]
        gmail = request.form["gmail"]
        password = request.form["password"]
        repeat_password = request.form["repeat_password"]

        if len(password) < 8:
            return jsonify({"error": "Password must be at least 8 characters long"}), 400

        if password != repeat_password:
            return jsonify({"error": "Passwords do not match"}), 400
        
        hash_password = pass_hasher.hash(password)

        if not email_regex.match(gmail):
            return jsonify({"error": "Invalid email format"}), 400

        if not all([name, surname, region, gmail, password]):
            return jsonify({"error": "Please, fill all fields"}), 400

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE gmail = %s", (gmail,))
        if cur.fetchone():
            return jsonify({"error": "Email already registered"}), 409

        cur.execute(
            """
            INSERT INTO users (name, surname, region, gmail, password)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (name, surname, region, gmail, hash_password),
        )
        conn.commit()
        conn.close()
        return redirect(BASE + "/login")

    return render_template("register_page.html")


@auth.route(BASE + "/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        gmail = request.form["gmail"]
        password = request.form["password"]

        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, password FROM users WHERE gmail = %s 
            """,
            (gmail,),
        )
        result = cur.fetchone()
        if not result:
            return jsonify({"error":"Invalid credentials"}), 401

        user_id, user_password = result
        conn.close()

        try:
            pass_hasher.verify(user_password, password)
        except VerifyMismatchError:
            return jsonify({"error": "Invalid credentials"}), 401

        session["user_id"] = user_id

        return redirect(BASE + "/your_fields_page")

    return render_template("login_page.html")
