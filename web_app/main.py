from flask import Flask, request, redirect, render_template, session, jsonify


from argon2 import PasswordHasher

import pandas as pd
import json

# import re
# import os

from data_base.connection import get_connection

from src.user.authentication import auth
from src.user.user_page import user_
from src.user.login_required import login_required

# from src.field.simulation import Simulation
from src.field.recommendation import Recommendation
from src.field.your_fields_search import YourFieldsSearch

BASE = "/diploma/fertilizer_recommendation"

app = Flask(__name__)
app.secret_key = "dev_secret_key"
app.register_blueprint(auth)
app.register_blueprint(user_)
app.jinja_env.globals.update(enumerate=enumerate)

pass_hasher = PasswordHasher()

FIELDS_DATA = []

REQUIRED_SOIL_ANALYSIS_COLS = {
    "area",
    "Name",
    "OM",
    "Ca",
    "Mg",
    "Mn",
    "B",
    "Cu",
    "Mo",
    "Fe",
    "Zn",
    "S",
    "P",
    "K",
    "Na",
    "pH",
    "C.E.C",
}

VALIDATE_NAME_MAP = {
    "Organic_M": "OM",
    "Organic M.": "OM",
    "Organic M": "OM",
}


def normalize_column_names(df):
    return df.rename(columns=VALIDATE_NAME_MAP)


@app.route(BASE)
def index():
    return render_template("index.html")


def get_field_data(user_id, field_name):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
            SELECT crop_number, target_yield, field_area
            FROM field_data 
            WHERE user_id = %s AND field_name = %s
        """,
        (user_id, field_name),
    )
    result = cur.fetchone()
    cur.close()
    conn.close()

    if result:
        crop_id = "Crop_" + str(result[0])
        target_yield = result[1] / result[2]
    else:
        crop_id = None
        target_yield = None

    return crop_id, target_yield


@app.route(BASE + "/recommendation", methods=["GET", "POST"])
@login_required
def recommendation_formulation():
    id_user = session.get("user_id")
    field_name = request.args.get("field_name")
    if not field_name:
        return jsonify({"error": "field_name is required"}), 400

    if field_name is not None:
        field_name = str(field_name)
    else:
        field_name = None

    print("USER ID ", id_user)
    print("FIELD NAME ", field_name)
    crop_id, tagret_yield = get_field_data(id_user, field_name)
    if crop_id is None or tagret_yield is None:
        return jsonify({"error": "Crop or target yield not found"}), 404

    print("FIELD NAME ", field_name)
    print("Start recomendation")
    recommendation_ = Recommendation(id_user, crop_id, field_name, tagret_yield)
    recomendation = recommendation_.fertilizer_mapping()
    print("Finish recomendation")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
            INSERT INTO recommendation (user_id, recommendation, field_name)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, field_name)
            DO UPDATE SET recommendation = EXCLUDED.recommendation
        """,
        (id_user, json.dumps(recomendation), field_name),
    )
    conn.commit()
    conn.close()

    return render_template("recomendation_page.html", recommendation=recomendation)


@app.route(BASE + "/your_fields_page", methods=["GET", "POST"])
@login_required
def field_search():
    user_id = session.get("user_id")
    print("USER id ", user_id)
    searcher = YourFieldsSearch(user_id)
    fields_data = searcher.get_user_fields_list(user_id)
    return render_template("your_fields_page.html", fields=fields_data)


@app.route(BASE + "/field_creation", methods=["GET", "POST"])
@login_required
def add_field():
    if request.method == "POST":
        # print("FORM DATA:", dict(request.form))
        # print("FILES:", dict(request.files))

        id_user = session.get("user_id")
        crop_number = None
        field_name = request.form["field_name"]
        field_area = request.form["area"]
        farm_name = request.form["farm"]
        crop_name = request.form["crop"]
        target_yield_field = request.form["target_yield_field"]
        fertilizer_type = request.form["fertilizer_type"]
        if "soil_analysis" not in request.files:
            return jsonify({"error": "Soil analysis file is required"}), 400

        soil_analysis = request.files["soil_analysis"]

        if soil_analysis.filename == "":
            return jsonify({"error": "Soil analysis file is required"}), 400

        if not soil_analysis.filename.endswith(".csv"):
            return jsonify({"error": "Only CSV files are accepted"}), 400

        try:
            df = pd.read_csv(soil_analysis)
            df = normalize_column_names(df)
        except Exception as e:
            import traceback

            traceback.print_exc()
            return jsonify({"error": f"Invalid CSV file: {e}"}), 400

        if df.empty:
            return jsonify({"error": "CSV file is empty"}), 400

        if not REQUIRED_SOIL_ANALYSIS_COLS.issubset(df.columns):
            missing = REQUIRED_SOIL_ANALYSIS_COLS - set(df.columns)

            return jsonify({"error": f"CSV missing columns: {missing}"}), 400

        soil_analysis_json = json.loads(df.to_json(orient="records"))

        if not all([field_name, field_area, farm_name, crop_name, target_yield_field]):
            return jsonify({"error": "Please, fill all fields"}), 400

        try:
            field_area = float(field_area)
            target_yield = float(target_yield_field)
        except ValueError:
            return jsonify({"error": "Area and yield must be numbers"}), 400

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT id FROM field_data WHERE user_id = %s AND field_name = %s",
            (id_user, field_name),
        )
        if cur.fetchone():
            conn.close()
            return jsonify({"error": f"Field '{field_name}' already exists"}), 409

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

        cur.execute(
            """
            INSERT INTO field_data 
            (
            user_id, field_name, field_area, farm_name, 
            crop_name, crop_number, fertilizer_type, soil_analysis, target_yield
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                target_yield,
            ),
        )
        # print("inserted data")
        conn.commit()
        conn.close()
        return redirect(BASE + f"/recommendation?field_name={field_name}")

    return render_template("field_creation.html")


@app.route(BASE + "/field", methods=["GET", "POST"])
@login_required
def one_field():
    user_id = session.get("user_id")
    field_name = request.args.get("field_name")

    searcher = YourFieldsSearch(user_id)
    fields_data = searcher.format_data(user_id, field_name)

    if fields_data is None or fields_data.empty:
        return render_template(
            "field.html",
            farm_name="",
            field_name=field_name,
            crop_name="",
            soil_zones=[],
            recommendation=[],
        )

    farm_name = fields_data["farm_name"].iloc[0]
    crop_name = fields_data["crop_name"].iloc[0]
    soil_zones = fields_data.to_dict(orient="records")

    required_cols = ["zone_name", "elements", "best", "percentage_increase"]

    if all(col in fields_data.columns for col in required_cols):
        recommendation = (
            fields_data[required_cols].dropna(subset=["best"]).to_dict(orient="records")
        )
    else:
        recommendation = []

    return render_template(
        "field.html",
        farm_name=farm_name,
        field_name=field_name,
        crop_name=crop_name,
        soil_zones=soil_zones,
        recommendation=recommendation,
    )


if __name__ == "__main__":
    app.run(debug=True)
