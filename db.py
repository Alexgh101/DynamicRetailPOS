import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

host = os.getenv("DB_HOST")
user = os.getenv("DB_USER")
port = os.getenv("DB_PORT")
passw = os.getenv("DB_PASS")
db = os.getenv("DB_NAME")


def get_db_connection():
    return mysql.connector.connect(
        host=host,
        port=port,
        user=user,
        password=passw,
        database=db
    )