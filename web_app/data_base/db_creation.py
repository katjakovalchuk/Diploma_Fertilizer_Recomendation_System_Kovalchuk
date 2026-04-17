import psycopg2
import pandas as pd


def get_connection():
    try:
        return psycopg2.connect(
            database="postgres",
            user="postgres",
            password="postgress",
            host="127.0.0.1",
            port=5432,
        )
    except:
        return False


conn = get_connection()
cur = conn.cursor()
if conn:
    print("Connection to the PostgreSQL established successfully.")
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS
        users (
        id SERIAL PRIMARY KEY,
        name text,
        surname text,
        region text, 
        gmail text,
        password text
    )
    """
    )
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS
        field_data (
        id SERIAL PRIMARY KEY,
        user_id INT REFERENCES users(id),
        field_name text,
        field_area float,
        farm_name text,
        crop_name text,
        crop_number INT REFERENCES crops(id),
        fertilizer_type text,
        soil_analysis JSON
    )
    """
    )
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS
        recommendation (
        id SERIAL PRIMARY KEY,
        user_id INT REFERENCES users(id),
        recommendation JSON
    )
    """
    )
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS 
        crops (
        id INT PRIMARY KEY,
        name TEXT
    )
    """
    )
    cur.execute(
        """
    INSERT INTO crops (id, name) VALUES
        (33, 'Barley'),
        (34, 'Corn'),
        (41, 'Sunflower'),
        (45, 'Oilseed'),
        (174, 'Soya')
    """
    )
    cur.execute(
        """
    CREATE TABLE crop_elements 
    (
    crop_id TEXT PRIMARY KEY,
    elements TEXT[]
    )
    """
    )

    cur.execute(
        """
    INSERT INTO crop_elements (crop_id, elements) VALUES
    ('Crop_33', ARRAY['N','P','K','S','Fe','Zn']),
    ('Crop_45', ARRAY['N','P','K','Mg','S']),
    ('Crop_41', ARRAY['N','P','K','Mg','Ca','Fe','Zn','Mn','Cu','B']),
    ('Crop_22', ARRAY['N','P','K','Mg','Ca','Fe','Zn','Mn','Cu','B']),
    ('Crop_34', ARRAY['N','P','K','Mg','Ca','S','Fe','Zn','Mn','B']),
    ('Crop_174', ARRAY['N','P','K','Mg','Ca','S','Fe','Zn','Mn','Cu','B','Mo']);
"""
    )
    conn.commit()
    cur.close()
    conn.close()
else:
    print("Connection failed.")
