import pandas as pd
import random
import joblib
import shap
from itertools import combinations, product
import time

from datetime import datetime

from data_base.weather_data_db import WeatherDataPreparation
from data_base.connection import get_connection


class Simulation:
    LIST_OF_CULTURES = [
        "Crop_33",
        "Crop_34",
        "Crop_41",
        "Crop_45",
        "Crop_174",
        "Crop_22",
    ]

    FEATURES = [
        "area",
        "Organic_M",
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
        "Crop_22",
        "Crop_34",
        "Crop_41",
        "Crop_45",
        "Crop_33",
        "Crop_174",
    ]

    CHEM_LEVELS = ["Very low", "Low", "Medium", "High", "Very high"]
    ALLOWED_CHEM_LEVELS = ["Very low", "Low", "Medium", "High"]

    ZONE_NAME = dict()

    XGB_MODEL = joblib.load("./models/xgb_weather_.sav")
    XGB_SCALER = joblib.load("./models/scaler_xgb_weather_.pkl")

    def __init__(self, user_id, crop_id, field_name):
        self.user_id = user_id
        self.year = datetime.now().year - 1
        self.crop_id = crop_id
        self.field_name = field_name

        self.connection = get_connection()
        self.cur = self.connection.cursor()

    def get_weather_data(self):
        weather_ = WeatherDataPreparation(self.user_id, self.year)
        # print("WEATHER DATA GOTTEN BY SIMULATION", weather_)
        return weather_.get_weather_data()

    def get_data(self):
        self.cur.execute(
            """
                SELECT soil_analysis
                FROM field_data 
                WHERE user_id = %s and field_name = %s
            """,
            (self.user_id, self.field_name),
        )
        print("SELF USER ID")
        print(self.user_id)
        result = self.cur.fetchone()

        if result:
            soil_analysis = result[0]
        else:
            soil_analysis = None
        # print("SOIL ANALYSIS in SIMULATION, ", soil_analysis)
        return soil_analysis
    
    def features_formulation(self):
        features = []

        soil_analysis = pd.DataFrame(self.get_data())
        if soil_analysis is None:
            raise ValueError(f"No soil data for field '{self.field_name}'")
        
        self.ZONE_NAME = soil_analysis["Name"].to_dict()

        weather_data = self.get_weather_data()
        if weather_data is None or weather_data.empty:
            raise ValueError("Weather data unavailable")
        
        crop = self.crop_id

        soil_data = soil_analysis.drop(
            columns=[
                "Name",
                "ORDER_NO",
                "DATE_REC",
                "DISTRIBUT",
                "DIST_ADDR",
                "DIST_ID",
                "CROPNAME_",
                "FIELDREF",
                "FARMER",
                "FARMER_AD",
                "CUST_ID",
                "DAN",
                "CUST_ORD_",
                "Mg_Index",
                "P_Index",
                "K_Index",
            ],
            errors="ignore",
        )
        soil_data = soil_data.rename(columns={"Organic M": "Organic_M"})

        X_ = pd.DataFrame(index=range(len(soil_data)), columns=self.FEATURES)

        X_.update(soil_data)
        X_ = X_.astype(float)

        X_[self.LIST_OF_CULTURES] = False
        X_[crop] = True
        X_["year"] = self.year

        X_ = X_.merge(weather_data, on="year", how="left")
        X_ = X_.drop(
            columns=[
                "year",
                "location",
                "index",
            ],
            errors="ignore",
        )

        scaler_features = self.XGB_SCALER.feature_names_in_.tolist()
        X_ = X_[scaler_features]

        # print("FEATURES IN SIMULATION, ", X_)
        return X_

    def get_chem_needs_for_crop(self, crop_id):
        self.cur.execute(
            """
                SELECT elements
                FROM crop_elements 
                WHERE crop_id = %s
            """,
            (crop_id,),
        )
        result = self.cur.fetchone()

        if result:
            crop_needs = result[0]
        else:
            crop_needs = None
        print("CHEMICALS NEED FOR CROP IN SIMULATION ", crop_needs)
        return crop_needs

    def epsilots_data(self, elem):
        self.cur.execute(
            """
                SELECT min_elem_value, max_elem_value, content_level
                FROM elements_guideline 
                WHERE Short_elem_name = %s
            """,
            (elem,),
        )
        result = self.cur.fetchall()

        if result:
            cols = [desc[0] for desc in self.cur.description]
            EPSILOTS = pd.DataFrame(result, columns=cols)
        else:
            EPSILOTS = None

        # print("EPSILOTS FOR CROP IN SIMULATION", EPSILOTS)
        return EPSILOTS

    def level_chem_element(self, element, value):
        elem_data = self.epsilots_data(element)
        elem_level = None

        for _, row in elem_data.iterrows():
            # print(row)
            if row["min_elem_value"] <= value <= row["max_elem_value"]:
                level = row["content_level"]
                if level in self.ALLOWED_CHEM_LEVELS:
                    elem_level = level
                    break

        if elem_level is None or elem_level not in self.CHEM_LEVELS:
            return []

        level_index = self.CHEM_LEVELS.index(elem_level)
        elem_levels_to_try = self.CHEM_LEVELS[level_index + 1 :]
        levels = []
        for level in elem_levels_to_try:
            if level in self.ALLOWED_CHEM_LEVELS:
                levels.append(level)
        return levels

    def calculate_percentage_increase(self, orig_value, new_value):
        return ((new_value - orig_value) / abs(orig_value)) * 100

    def simulation(self, X_):
        columns = X_.columns
        needed_chem_elements_for_crop = self.get_chem_needs_for_crop(self.crop_id)

        X_scaled_ = self.XGB_SCALER.fit_transform(X_)
        predicted_yield_ = self.XGB_MODEL.predict(X_scaled_)

        xgb_explainer = shap.TreeExplainer(self.XGB_MODEL, X_scaled_)
        shap_values_ridge = xgb_explainer(X_scaled_)

        HISTORY_ = []

        for j, one_zone_shap in enumerate(shap_values_ridge.values):
            X_row = X_.iloc[[j]]
            X_row_scaled = self.XGB_SCALER.transform(X_row)
            orig_prediction = self.XGB_MODEL.predict(X_row_scaled)

            small_shap = []
            for i, shap_value in enumerate(one_zone_shap):
                if shap_value < 0 and (columns[i] in needed_chem_elements_for_crop):
                    small_shap.append(i)

            MAX_COMB_SIZE = 3
            feature_combinations = []
            for k in range(1, min(len(small_shap), MAX_COMB_SIZE) + 1):
                feature_combinations.extend(combinations(small_shap, k))

            data_ = []
            technical_data = []
            for combination in feature_combinations:
                elem_levels_to_try = {}
                for elem in combination:
                    elem_levels_to_try[elem] = self.level_chem_element(
                        columns[elem], X_.iloc[j, elem]
                    )

                levels_combinations = product(*elem_levels_to_try.values())

                for levels_combination in levels_combinations:
                    X_simulation = X_row.copy()

                    for elem, level in zip(combination, levels_combination):
                        elem_name = columns[elem]
                        EPSILOTS = self.epsilots_data(elem_name)

                        elem_data = EPSILOTS[(EPSILOTS["content_level"] == level)]
                        if elem_data.empty:
                            continue

                        # if level != "Very high":
                        X_simulation.iloc[0, elem] = elem_data[
                            "max_elem_value"
                        ].values[0]
                        # else:
                        #     X_simulation.iloc[0, elem] = elem_data[
                        #         "min_elem_value"
                        #     ].values[0]

                    data_.append(X_simulation.values[0])
                    technical_data.append(
                        {
                            "zone_idx": j,
                            "combo_features": [X_.columns[s] for s in combination],
                            "area": X_["area"][j],
                            "orig_value": [X_.iloc[j, s] for s in combination],
                            "fetures_values": [
                                X_simulation.iloc[0, s] for s in combination
                            ],
                            "orig_prediction": orig_prediction[0],
                        }
                    )

            if not data_:
                HISTORY_.append(
                    {
                        "zone_idx": j,
                        "combo_features": [],
                        "area": X_["area"][j],
                        "orig_value": [],
                        "fetures_values": [],
                        "orig_prediction": orig_prediction[0],
                        "simulated_prediction": orig_prediction[0],
                        "percentage_increase": 0.0,
                    }
                )
                continue

            new_X = pd.DataFrame(data_, columns=X_.columns)
            # print(new_X)
            X_simulations_scaled = self.XGB_SCALER.transform(new_X)
            simulated_prediction = self.XGB_MODEL.predict(X_simulations_scaled)

            for tech_data, sim_pred in zip(technical_data, simulated_prediction):
                one_prediction = tech_data.copy()
                orig_prediction = one_prediction["orig_prediction"]
                one_prediction["simulated_prediction"] = sim_pred
                one_prediction["percentage_increase"] = (
                    self.calculate_percentage_increase(orig_prediction, sim_pred)
                )
                HISTORY_.append(one_prediction)

        return HISTORY_

    def return_zone_names(self):
        print(self.ZONE_NAME)
        return self.ZONE_NAME

    def return_simulation(self):
        X_ = self.features_formulation()
        return self.simulation(X_)
