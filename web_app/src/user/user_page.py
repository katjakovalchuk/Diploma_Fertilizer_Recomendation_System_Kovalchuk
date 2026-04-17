from flask import Blueprint, render_template
from argon2 import PasswordHasher

from data_base.connection import get_connection

BASE = "/diploma/fertilizer_recommendation"
user_ = Blueprint("user_page", __name__)

pass_hasher = PasswordHasher()


@user_.route(BASE + "/user_page", methods=["GET", "POST"])
def user_page():
    id_user = 10  # session.get("user_id")
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
    # print(user_data)

    return render_template("user_page.html", user=user_data)
