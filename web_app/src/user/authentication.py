from flask import Blueprint, request, redirect, render_template, session
from argon2 import PasswordHasher

from data_base.connection import get_connection

BASE = "/diploma/fertilizer_recommendation"
auth = Blueprint("auth", __name__)

pass_hasher = PasswordHasher()


@auth.route(BASE + "/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        surname = request.form["surname"]
        region = request.form["region"]
        gmail = request.form["gmail"]
        password = request.form["password"]
        repeat_password = request.form["repeat_password"]
        # print(request.form)

        if password != repeat_password:
            return "Password or Repeat password id incorrect", 400

        hash_password = pass_hasher.hash(password)

        conn = get_connection()
        cur = conn.cursor()
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
        # print(request.form)

        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, password FROM users WHERE gmail = %s 
            """,
            (gmail,),
        )
        user_id, user_password = cur.fetchone()
        # print(user_id)
        # print(user_password)
        # print(user_password[0])
        conn.close()

        if pass_hasher.verify(user_password, password):
            session["user_id"] = user_id
            return redirect(BASE + "/your_fields_page")

    return render_template("login_page.html")
