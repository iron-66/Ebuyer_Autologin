import os
import psycopg2

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

CATEGORIES_DIR = "categories"

conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)

cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    category TEXT NOT NULL
)
""")
conn.commit()


def parse_and_insert_from_files():
    """
    Read each .txt file from the categories directory,
    extract product name and URL, and insert into the database
    """
    for filename in os.listdir(CATEGORIES_DIR):
        category = filename.replace(".txt", "").strip()
        filepath = os.path.join(CATEGORIES_DIR, filename)

        with open(filepath, "r", encoding="utf-8") as file:
            for line in file:
                if ": http" in line:
                    name, url = line.strip().split(": http", 1)
                    name = name.strip()
                    url = "http" + url.strip()
                    cur.execute(
                        "INSERT INTO products (name, url, category) VALUES (%s, %s, %s)",
                        (name, url, category)
                    )
    conn.commit()


parse_and_insert_from_files()
cur.close()
conn.close()
print("Export successful")
