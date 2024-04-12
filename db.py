import os

import psycopg2

from datatypes import Suggestion


DATABASE = os.getenv("PG_DATABASE")
HOST = os.getenv("PG_HOST")
PORT = os.getenv("PG_PORT")
USER = os.getenv("PG_USER")
PASSWORD = os.getenv("PG_PASSWORD")

MAIN_TABLE = "DATA"
SUGGESTION_TABLE = "PROPOSED_DATA"

if None in (DATABASE, HOST, PORT, USER, PASSWORD):
    print("Specify DB credentials via environment variables")
    exit()


conn = psycopg2.connect(
    database=DATABASE,
    host=HOST,
    port=PORT,
    user=USER,
    password=PASSWORD,
)

cursor = conn.cursor()


def fetch_all_data(table_name: str="", columns: list[str]=[]) -> list[tuple]:
    if not table_name:
        table_name = MAIN_TABLE
    if not columns:
        columns = ["id", "name", "address", "latitude", "longtitude", "image"]
    columns_joined = ", ".join(columns)
    cursor.execute(f"SELECT {columns_joined} FROM {table_name}")
    return cursor.fetchall()


def insert_suggestion(sug: Suggestion):
    cursor.execute(
        f"""
            INSERT INTO {SUGGESTION_TABLE}(name, address, description, image)
            VALUES (%s, %s, %s, %s)
        """, (sug.name, sug.address, sug.description, sug.photo))
    conn.commit()


def fetch_suggestions() -> list[tuple]:
    cursor.execute(f"SELECT * FROM {SUGGESTION_TABLE}")
    return cursor.fetchall()


def delete_suggestion(sug_id: int):
    cursor.execute(f"DELETE FROM {SUGGESTION_TABLE} WHERE ID = {sug_id}")
    conn.commit()

