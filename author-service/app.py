from fastapi import FastAPI
import psycopg2
import os
import threading
import json
from kafka import KafkaConsumer

app = FastAPI()

# Database connection function
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        dbname=os.getenv("POSTGRES_DB", "openlib_db"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "password")
    )

# Kafka consumer function
def consume_kafka_messages():
    kafka_broker = os.getenv("KAFKA_BROKER", "kafka:9092")
    topic = 'openlib-authors'

    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=[kafka_broker],
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='author-service-group',
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )

    # Process messages continuously
    for message in consumer:
        author_data = message.value
        print(f"Consumed author data: {author_data}")

        # Use the timestamp from the file's 4th column.
        # Your Kafka producer should add this field as "file_last_modified".
        last_modified = author_data.get("file_last_modified", None)

        # Store the full JSON record in the 'data' column.
        # We use json.dumps to convert the dictionary into a JSON string,
        # which psycopg2 will adapt to the JSONB column.
        raw_json = json.dumps(author_data)

        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO authors (author_key, name, revision, last_modified, data)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (author_key) DO UPDATE
                      SET name = EXCLUDED.name,
                          revision = EXCLUDED.revision,
                          last_modified = EXCLUDED.last_modified,
                          data = EXCLUDED.data;
                """, (
                    author_data.get("key"),
                    author_data.get("name"),
                    author_data.get("revision", 1),
                    last_modified,
                    raw_json
                ))
                conn.commit()
            conn.close()
        except Exception as e:
            print("Error updating author:", e)

# Start Kafka consumer in a background thread
def start_kafka_consumer():
    thread = threading.Thread(target=consume_kafka_messages, daemon=True)
    thread.start()

@app.on_event("startup")
def startup_event():
    start_kafka_consumer()

@app.get("/author/{author_id}")
def read_author(author_id: str):
    conn = get_db_connection()
    with conn.cursor() as cur:
        # Assuming the keys are stored as full strings, e.g., "/authors/OL10000031A"
        key = f"/authors/{author_id}"
        cur.execute("SELECT author_key, name, revision, last_modified, data FROM authors WHERE author_key = %s", (key,))
        row = cur.fetchone()
    conn.close()
    if row:
        return {
            "author_key": row[0],
            "name": row[1],
            "revision": row[2],
            "last_modified": str(row[3]) if row[3] else None,
            "data": row[4]
        }
    else:
        return {"error": "Author not found"}

