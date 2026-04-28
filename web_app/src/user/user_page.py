from flask import Blueprint, render_template, session
from argon2 import PasswordHasher

from data_base.connection import get_connection
from src.user.login_required import login_required

BASE = "/diploma/fertilizer_recommendation"
user_ = Blueprint("user_page", __name__)

pass_hasher = PasswordHasher()


@user_.route(BASE + "/user_page", methods=["GET", "POST"])
@login_required
def user_page():
    id_user = session.get("user_id")
    print("USER ID, ", id_user)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT name, surname, gmail, region
        FROM users
        WHERE id = %s
        """,
        (id_user,),
    )
    user_data = cur.fetchone()
    conn.close()

    return render_template("user_page.html", user=user_data)
