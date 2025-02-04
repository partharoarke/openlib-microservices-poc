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
        # Query all works
        cur.execute("SELECT work_key, data FROM works;")
        rows = cur.fetchall()

        for row in rows:
            work_key = row[0]
            work_json = row[1]  # This is the JSONB data
            # Parse the authors array
            authors_array = None
            if isinstance(work_json, dict):
                authors_array = work_json.get("authors", [])

            if authors_array:
                for author_obj in authors_array:
                    # The typical structure is: { "author": {"key": "/authors/OL..."}, ... }
                    # Some works might have different formats, so add safety checks
                    author_info = author_obj.get("author")
                    if author_info:
                        author_key = author_info.get("key")  # e.g. "/authors/OL10000031A"
                        if author_key:
                            try:
                                # Insert or upsert into author_works
                                cur.execute("""
                                    INSERT INTO author_works (author_key, work_key)
                                    VALUES (%s, %s)
                                    ON CONFLICT (author_key, work_key) DO NOTHING;
                                """, (author_key, work_key))
                            except Exception as e:
                                print(f"Error inserting into author_works: {e}")
    conn.close()

if __name__ == "__main__":
    main()

