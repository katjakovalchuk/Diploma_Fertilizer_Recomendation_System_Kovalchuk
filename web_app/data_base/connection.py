import psycopg2

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

