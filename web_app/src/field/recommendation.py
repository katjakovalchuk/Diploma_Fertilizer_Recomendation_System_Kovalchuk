"""
Module for generating fertilizer recommendations.
"""

import pandas as pd

from data_base.connection import get_connection
from src.field.simulation import Simulation


class Recommendation:
    """
    Class responsible for preparing the recommendation.
    """

    micro_ = ["Fe", "Zn", "Mn", "Cu", "B", "Mo"]
    macro_ = ["N", "P", "K", "Mg", "Ca", "S"]

    oxid_form_of_elems = {
        "P": "P2O5",
        "K": "K2O",
        "Mg": "MgO",
        "Ca": "CaO",
    }

    oxid_form_mapping = {"P": 2.29, "K": 1.2, "Mg": 1.66, "Ca": 1.4}

    def __init__(self, user_id, crop_id, field_name, target_yield):
        self.user_id = user_id
        self.crop_id = crop_id
        self.field_name = field_name
        self.target_yield = target_yield

        self.connection = get_connection()
        self.cur = self.connection.cursor()

    def get_crop_nutrition_uptake(self):
        """
        Gets from the database how many tons/grams per hectare
        are required by the crop the user is growing to produce 1 ton of yield.
        """
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
            columns = [desc[0] for desc in self.cur.description]
            crop_nutrition_uptake = pd.DataFrame([result], columns=columns)
        else:
            crop_nutrition_uptake = None

        return crop_nutrition_uptake

    def get_fertilizers_data(self):
        """
        Retrieves fertilizer data from the database.
        """
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
        return fertilizers

    def elems_per_zone(self, df_of_zone):
        """
        Creates a list of elements for a zone whose levels need to be improved
        to increase yield.
        """
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
        """
        Converts an element into its oxide form to correctly account for it
        when searching for required substances in fertilizer.
        """
        cols = []
        for elem in elems.keys():
            if elem in self.oxid_form_of_elems.keys():
                cols.append(f"{self.oxid_form_of_elems[elem]} %")
            else:
                cols.append(f"{elem} %")
        return cols

    def calculate_deficit(self, elem, original_, new_):
        """
        Calculates the deficiency of an element in the soil.
        """
        deficit = new_ - original_
        if elem in self.micro_:
            deficit_kg = (deficit * 3.75) / 1000
        else:
            deficit_kg = deficit * 3.75

        if elem in self.oxid_form_mapping.keys():
            deficit_kg = deficit_kg * self.oxid_form_mapping[elem]
        return deficit_kg

    def get_crop_need(self, elem, target_yield, crops_nutritients):
        """
        Calculates how much of an element is required by the plant to achieve the target yield.
        """
        if elem in self.oxid_form_of_elems:
            oxid_value = (
                crops_nutritients.get(self.oxid_form_of_elems[elem], 0) * target_yield
            )
            return oxid_value * self.oxid_form_mapping[elem]
        elif elem in self.micro_:
            g_per_ha = crops_nutritients.get(elem, 0) * target_yield
            return g_per_ha / 1000
        else:
            return crops_nutritients.get(elem, 0) * target_yield

    def fertilizer_mapping(self):
        """
        Calculates the required amount of fertilizer and maps it
        to available fertilizers in the database
        to find an optimal solution.
        """
        ferlizers = self.get_fertilizers_data()
        if ferlizers is None or ferlizers.empty:
            raise ValueError("Fertilizers table is empty")

        crops_nutrients = self.get_crop_nutrition_uptake().iloc[0].to_dict()
        if crops_nutrients is None:
            raise ValueError(f"No nutrition data for crop '{self.crop_id}'")

        simulation_ = Simulation(self.user_id, self.crop_id, self.field_name)

        simulation = pd.DataFrame(simulation_.return_simulation())
        zone_names = simulation_.return_zone_names()

        simulation_per_zone = simulation.loc[
            simulation.groupby("zone_idx")["simulated_prediction"].idxmax()
        ]
        simulation_per_zone["zone_name"] = simulation_per_zone["zone_idx"].map(
            zone_names
        )

        results = []

        for _, zone_df in simulation_per_zone.iterrows():
            elems = self.elems_per_zone(zone_df)

            if not elems:
                results.append(
                    {
                        "zone_name": zone_df["zone_name"],
                        "elements": "—",
                        "best": [],
                        "percentage_increase": None,
                    }
                )
                continue

            cols = self.oxid_form_convertation(elems)

            fertilizer = ferlizers[ferlizers[cols].any(axis=1)].copy()

            for elem, elem_values in elems.items():
                deficit_kg = self.calculate_deficit(
                    elem, elem_values[0], elem_values[1]
                )

                crop_need = self.get_crop_need(elem, self.target_yield, crops_nutrients)

                if elem in self.oxid_form_mapping.keys():
                    total_kg = deficit_kg + crop_need

                    fertilizer[
                        f"needed kg/he for {self.oxid_form_of_elems[elem]} %"
                    ] = total_kg / (
                        fertilizer[f"{self.oxid_form_of_elems[elem]} %"] / 100
                    )
                else:
                    total_kg = deficit_kg + crop_need
                    fertilizer[f"needed kg/he for {elem} %"] = total_kg / (
                        fertilizer[f"{elem} %"] / 100
                    )

            needed_cols = []
            for column_name in cols:
                needed_cols.append(f"needed kg/he for {column_name}")

            fertilizer["needed kg/he"] = fertilizer[
                [col for col in needed_cols if col in fertilizer.columns]
            ].sum(axis=1)

            best = fertilizer.sort_values("needed kg/he").head(1)

            results.append(
                {
                    "zone_name": zone_df["zone_name"],
                    "elements": ", ".join(elems.keys()),
                    "best": best[["product_name", "needed kg/he"]]
                    .rename(
                        columns={
                            "product_name": "fertilizer",
                            "needed kg/he": "amount",
                        }
                    )
                    .to_dict("records"),
                    "percentage_increase": zone_df["percentage_increase"],
                }
            )

        return results
