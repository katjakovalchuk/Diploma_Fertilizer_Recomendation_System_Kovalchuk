"""
Module that creates a connection to the database.
"""

import psycopg2


def get_connection():
    """
    Function that establishes a
    connection with database

    Returns False if connection fails
    """
    try:
        return psycopg2.connect(
            database="fertilizer_recommendation_db",
            user="postgres",
            password="",  #your postgress user password
            host="127.0.0.1",
            port=5432,
        )
    except:
        return False
