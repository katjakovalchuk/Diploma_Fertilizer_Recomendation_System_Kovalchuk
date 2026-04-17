from data_base.connection import get_connection
from src.field.simulation import Simulation

import pandas as pd


class Recommendation:
    micro_ = ["Fe", "Zn", "Mn", "Cu", "B", "Mo"]
    macro_ = ["N", "P", "K", "Mg", "Ca", "S"]

    oxid_form_of_elems = {
        "P": "P2O5",
        "K": "K2O",
        "Mg": "MgO",
        "Ca": "CaO",
    }

    oxid_form_mapping = {"P": 2.29, "K": 1.2, "Mg": 1.66, "Ca": 1.4}

    def __init__(self, user_id, crop_id, fertilizer_type):
        self.user_id = user_id
        self.crop_id = crop_id
        self.fertilizer_type = fertilizer_type
        # print("FERTILIZER TYPE", self.fertilizer_type)

        self.connection = get_connection()
        self.cur = self.connection.cursor()

    def get_crop_nutrition_uptake(self):
        self.cur.execute(
            """
                SELECT * 
                FROM crop_nutritions 
                WHERE "index" = %s
            """,
            (self.crop_id,),
        )
        result = self.cur.fetchone()

        if result:
            crop_nutrition_uptake = result[0]
        else:
            crop_nutrition_uptake = None

        return crop_nutrition_uptake

    def get_fertilizers_data(self):
        self.cur.execute(
            """
                SELECT *
                FROM fertilizers_table 
            """
        )
        result = self.cur.fetchall()

        if result:
            columns = [desc[0] for desc in self.cur.description]
            fertilizers = pd.DataFrame(result, columns=columns)
        else:
            fertilizers = None
        # print("FERTILIZERS, ", fertilizers)
        return fertilizers

    def elems_per_zone(self, df_of_zone):
        elems = dict()

        if df_of_zone["orig_prediction"] < df_of_zone["simulated_prediction"]:
            elems = dict(
                zip(
                    df_of_zone["combo_features"],
                    zip(df_of_zone["orig_value"], df_of_zone["fetures_values"]),
                )
            )
        return elems

    def oxid_form_convertation(self, elems):
        cols = []
        for elem in elems.keys():
            if elem in self.oxid_form_of_elems.keys():
                cols.append(f"{self.oxid_form_of_elems[elem]} %")
            else:
                cols.append(f"{elem} %")
        return cols

    def calculate_deficit(self, elem, original_, new_):
        deficit = new_ - original_
        deficit_kg = deficit * 3.75
        if elem in self.oxid_form_mapping.keys():
            deficit_kg = deficit_kg * self.oxid_form_mapping[elem]
        return deficit_kg

    def fertilizer_mapping(self):
        ferlizers = self.get_fertilizers_data()
        crops_nutrients = self.get_crop_nutrition_uptake()
        simulation_ = Simulation(self.user_id, self.crop_id)
        simulation = pd.DataFrame(simulation_.return_simulation())

        # print("GOT SIMULATION in RECOMMENDATION ", simulation)

        simulation_per_zone = simulation.loc[
            simulation.groupby("zone_idx")["simulated_prediction"].idxmax()
        ]
        print("SIMULATIONS, ", len(simulation_per_zone))

        results = []

        for _, zone_df in simulation_per_zone.iterrows():
            elems = self.elems_per_zone(zone_df)
            # print("elems in RECOMMENDATION ", elems)
            cols = self.oxid_form_convertation(elems)
            # print("cols in RECOMMENDATION ", cols)

            fertilizer = ferlizers[ferlizers[cols].any(axis=1)].copy()

            for elem, elem_values in elems.items():
                deficit_kg = self.calculate_deficit(
                    elem, elem_values[0], elem_values[1]
                )

                if elem in self.oxid_form_of_elems.keys():
                    fertilizer[
                        f"needed kg/he for {self.oxid_form_of_elems[elem]} %"
                    ] = deficit_kg / (
                        fertilizer[f"{self.oxid_form_of_elems[elem]} %"] / 100
                    )
                else:
                    fertilizer[f"needed kg/he for {elem} %"] = deficit_kg / (
                        fertilizer[f"{elem} %"] / 100
                    )

            needed_cols = []
            for column_name in cols:
                needed_cols.append(f"needed kg/he for {column_name}")

            fertilizer["needed kg/he"] = fertilizer[
                [col for col in needed_cols if col in fertilizer.columns]
            ].sum(axis=1)

            best = fertilizer.sort_values("needed kg/he").head(5)
            # print(best[["product_name", "needed kg/he"]].head())
            results.append(
                {
                    "zone_idx": int(zone_df["zone_idx"]),
                    "elements": ", ".join(elems.keys()),
                    "best": best[["product_name", "needed kg/he"]]
                    .rename(columns={"product_name": "fertilizer", "needed kg/he": "amount"})
                    .to_dict("records"),
                }
            )
        # print("RESULT:    ", len(results))
        # print(results)

        return results
