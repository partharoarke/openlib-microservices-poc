import psycopg2
import json
import os

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_DB = os.getenv("POSTGRES_DB", "openlib_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")

def main():
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )
    conn.autocommit = True

    with conn.cursor() as cur:
        # Query all editions
        cur.execute("SELECT edition_key, data FROM editions;")
        rows = cur.fetchall()

        for row in rows:
            edition_key = row[0]
            edition_json = row[1]  # JSONB data
            if not isinstance(edition_json, dict):
                continue
            
            # e.g. "isbn_10": ["0108360687"], "isbn_13": ["9780108360688"]
            isbn_10s = edition_json.get("isbn_10", [])
            isbn_13s = edition_json.get("isbn_13", [])

            # Insert each ISBN into the edition_isbns table
            for isbn in isbn_10s + isbn_13s:
                try:
                    cur.execute("""
                        INSERT INTO edition_isbns (isbn, edition_key)
                        VALUES (%s, %s)
                        ON CONFLICT (isbn) DO NOTHING;
                    """, (isbn, edition_key))
                except Exception as e:
                    print(f"Error inserting ISBN {isbn}: {e}")

    conn.close()

if __name__ == "__main__":
    main()

