from flask import Flask, request, redirect, render_template, session
from argon2 import PasswordHasher

import pandas as pd
import json
import re
import os

from data_base.connection import get_connection

from src.user.authentication import auth
from src.user.user_page import user_

from src.field.simulation import Simulation
from src.field.recommendation import Recommendation

BASE = "/diploma/fertilizer_recommendation"

app = Flask(__name__)
app.secret_key = "dev_secret_key"
app.register_blueprint(auth)
app.register_blueprint(user_)
app.jinja_env.globals.update(enumerate=enumerate)

pass_hasher = PasswordHasher()


@app.route(BASE)
def index():
    return render_template("index.html")


@app.route(BASE + "/your_fields_page", methods=["GET", "POST"])
def your_fields_page():
    id_user = session.get("user_id")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT field_name, field_area,
        farm_name, crop_name, soil_analysis
        FROM field_data WHERE user_id = %s
        """,
        (id_user,),
    )
    user_fields_data = cur.fetchone()
    conn.close()

    if user_fields_data:
        print(111111111111111111111)
    else:
        print(222222222222)

    return render_template("your_fields_page.html")


@app.route(BASE + "/field_creation", methods=["GET", "POST"])
def add_field():
    if request.method == "POST":
        id_user = session.get("user_id")
        crop_number = None
        field_name = request.form["field_name"]
        field_area = request.form["area"]
        farm_name = request.form["farm"]
        crop_name = request.form["crop"]
        fertilizer_type = request.form["fertilizer_type"]

        # print(crop_name, field_name, field_area, farm_name, fertilizer_type)
        soil_analysis = request.files["soil_analysis"]
        df = pd.read_csv(soil_analysis)
        df = df.where(pd.notnull(df), None)
        soil_analysis_json = json.loads(df.to_json(orient="records"))

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
                SELECT id 
                FROM crops 
                WHERE name = %s
            """,
            (crop_name,),
        )
        result = cur.fetchone()
        if result:
            crop_number = result[0]
        else:
            crop_number = None
        # print(crop_number)

        cur.execute(
            """
            INSERT INTO field_data 
            (
            user_id, field_name, field_area, farm_name, 
            crop_name, crop_number, fertilizer_type, soil_analysis
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                id_user,
                field_name,
                float(field_area),
                farm_name,
                crop_name,
                crop_number,
                fertilizer_type,
                json.dumps(soil_analysis_json),
            ),
        )
        print("inserted data")
        conn.commit()
        conn.close()
        return redirect(BASE + "/recommendation")

    return render_template("field_creation.html")


@app.route(BASE + "/field_search", methods=["GET", "POST"])
def field_search():
    pass


def get_field_data(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
            SELECT crop_number, fertilizer_type 
            FROM field_data 
            WHERE id = %s
        """,
        (user_id,),
    )
    result = cur.fetchall()

    if result:
        crop_id = "Crop_" + str(result[0][0])
        fertilizer_type = result[0][1]
    else:
        crop_id = None
        fertilizer_type = None

    return crop_id, fertilizer_type


@app.route(BASE + "/recommendation", methods=["GET", "POST"])
def recommendation_formulation():
    id_user = 10  # session.get("user_id")
    print("USER ID ", id_user)
    crop_id, fertilizer_type = get_field_data(id_user)
    print("Start recomendation")
    recommendation_ = Recommendation(id_user, crop_id, fertilizer_type)
    recomendation = recommendation_.fertilizer_mapping()
    print("Finish recomendation")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
            INSERT INTO recommendation (user_id, recommendation)
            VALUES (%s, %s)
        """,
        (id_user, json.dumps(recomendation)),
    )
    conn.commit()
    conn.close()

    return render_template("recomendation_page.html", recommendation=recomendation)


if __name__ == "__main__":
    app.run(debug=True)
