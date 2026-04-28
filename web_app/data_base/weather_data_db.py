from data_base.connection import get_connection

from dotenv import load_dotenv
import codecs
import requests
import os
import sys
import pandas as pd
from datetime import datetime


load_dotenv()
API_KEY = os.getenv("API_KEY")


class WeatherDataPreparation:
    def __init__(self, user_id, year):
        self.user_id = user_id
        self.year = year

        self.base_url = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/"
        self.unit_group = "metric"
        self.content_type = "json"
        self.include = "days"

        self.connection = get_connection()
        self.cur = self.connection.cursor()

    def get_location_from_db(self):
        self.cur.execute(
            """
                SELECT region 
                FROM users 
                WHERE id = %s
            """,
            (self.user_id,),
        )
        result = self.cur.fetchone()

        if result:
            location = str(result[0])
        else:
            location = None

        return location

    def get_weather_from_db(self, location, year):
        print(f"Searching DB: location={location!r}, year={year!r}, type={type(year)}")
        self.cur.execute(
            """
                SELECT * 
                FROM weather_data 
                WHERE location = %s AND year= %s
            """,
            (location, year),
        )
        result_ = self.cur.fetchall()
        # print(f"DB result count: {len(result_)}")
        columns = [desc[0] for desc in self.cur.description]
        df = pd.DataFrame(result_, columns=columns)
        # df = df.drop(columns=["year"]).reset_index(drop=True)

        if result_:
            weather_data = df
        else:
            weather_data = None
        # print("found weather data in db for location ", location, " and year ", year)

        return weather_data

    def dates_formulation(self):
        start_date = datetime(self.year, 5, 1).strftime("%Y-%m-%d")
        end_date = datetime(self.year, 10, 31).strftime("%Y-%m-%d")

        return start_date, end_date

    def api_query_formulation(self, location):
        start_date, end_date = self.dates_formulation()
        api_query = self.base_url + location

        if start_date:
            api_query += "/" + start_date
            if end_date:
                api_query += "/" + end_date

        api_query += "?"

        if self.unit_group:
            api_query += "&unitGroup=" + self.unit_group

        if self.content_type:
            api_query += "&contentType=" + self.content_type

        if self.include:
            api_query += "&include=" + self.include

        api_query += "&key=" + API_KEY
        print("API QUERY:", api_query)
        return api_query

    def get_weather_from_api(self, api_query):
        response = requests.get(api_query)
        # print("STATUS:", response.status_code)
        # print("TEXT:", response.text[:300])

        if response.status_code != 200:
            raise Exception(
                f"Weather API error {response.status_code}: {response.text}"
            )

        try:
            data = response.json()
        except Exception:
            raise Exception(f"Invalid JSON response: {response.text}")

        weather_data = pd.DataFrame(data["days"])
        print("Got weather data from API")
        return weather_data

    def format_data(self, weather_data):
        weather_data["datetime"] = pd.to_datetime(weather_data["datetime"])
        weather_data["month"] = weather_data["datetime"].dt.month
        weather_data["year"] = weather_data["datetime"].dt.year

        weather_df_ = (
            weather_data.groupby(["year", "month"])
            .agg(
                mean_tempmax=("tempmax", "mean"),
                std_tempmax=("tempmax", "std"),
                mean_tempmin=("tempmin", "mean"),
                std_tempmin=("tempmin", "std"),
                mean_temp=("temp", "mean"),
                std_temp=("temp", "std"),
                mean_humidity=("humidity", "mean"),
                std_humidity=("humidity", "std"),
                mean_precip=("precip", "mean"),
                std_precip=("precip", "std"),
                mean_cloudcover=("cloudcover", "mean"),
                std_cloudcover=("cloudcover", "std"),
            )
            .reset_index()
        )

        wether_table = weather_df_.pivot(
            index="year",
            columns="month",
            values=[
                "mean_tempmax",
                "std_tempmax",
                "mean_tempmin",
                "std_tempmin",
                "mean_temp",
                "std_temp",
                "mean_humidity",
                "std_humidity",
                "mean_precip",
                "std_precip",
                "mean_cloudcover",
                "std_cloudcover",
            ],
        )

        wether_table.columns = [
            f"{feature}_month_{month}" for feature, month in wether_table.columns
        ]

        wether_table = wether_table.reset_index()
        return wether_table

    def write_weather_data_into_db(self, weather_data, location):
        columns = [col for col in weather_data.columns if col != "location"]

        values = ", ".join(["%s"] * (len(columns) + 1))
        col_names = ", ".join(columns) + ", location"

        for _, row in weather_data.iterrows():
            self.cur.execute(
                "SELECT 1 FROM weather_data WHERE location = %s AND year = %s",
                (location, row["year"]),
            )
            if self.cur.fetchone() is None:
                row_values = [row[col] for col in columns] + [location]
                self.cur.execute(
                    f"INSERT INTO weather_data ({col_names}) VALUES ({values})",
                    row_values,
                )
        self.connection.commit()

    def get_weather_data(self):
        location = self.get_location_from_db()
        db_weather_data = self.get_weather_from_db(location, self.year)

        if db_weather_data is not None and not db_weather_data.empty:
            return db_weather_data

        api_query = self.api_query_formulation(location)
        api_weather_data = self.get_weather_from_api(api_query)
        formatted_data = self.format_data(api_weather_data)

        self.write_weather_data_into_db(formatted_data, location)
        print("Return weather data ", formatted_data)
        return formatted_data
