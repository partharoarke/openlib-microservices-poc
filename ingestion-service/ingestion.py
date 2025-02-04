import os
import psycopg2
import json

def main():
    # Environment variables from docker-compose
    host = os.getenv("POSTGRES_HOST", "postgres")
    dbname = os.getenv("POSTGRES_DB", "openlib_db")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    dumps_folder = os.getenv("DUMPS_DIR", "/data/dumps")

    authors_file = os.path.join(dumps_folder, "ol_dump_authors_2025-01-08.txt")

    # Connect to Postgres
    conn = psycopg2.connect(
        host=host,
        dbname=dbname,
        user=user,
        password=password
    )
    conn.autocommit = True

    # Create the authors table if not exists
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS authors (
        author_key TEXT PRIMARY KEY,
        name TEXT,
        revision INT,
        last_modified TIMESTAMP
    );
    """
    with conn.cursor() as cur:
        cur.execute(create_table_sql)

    # Parse the authors file and insert into the DB
    with open(authors_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            columns = line.split('\t')
            if len(columns) != 5:
                continue

            record_type, key, revision, last_modified, record_json = columns

            # We only care about author lines
            if record_type != '/type/author':
                continue

            # Parse the JSON column
            data = json.loads(record_json)
            author_name = data.get("name", "")
            author_key = data.get("key", "")  # e.g. "/authors/OL9999740A"

            # TODO: Decide later on this:
            # Remove "/authors/" prefix for storing in DB 
            # Let's store the entire key to keep it simple
            # author_key_clean = author_key.replace("/authors/", "")

            try:
                # Insert or upsert
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO authors (author_key, name, revision, last_modified)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (author_key) DO UPDATE
                        SET name = EXCLUDED.name,
                            revision = EXCLUDED.revision,
                            last_modified = EXCLUDED.last_modified;
                    """, (author_key, author_name, int(revision), last_modified))
            except Exception as e:
                print("Error inserting record:", e)

    conn.close()
    print("Ingestion completed successfully!")


if __name__ == "__main__":
    main()

