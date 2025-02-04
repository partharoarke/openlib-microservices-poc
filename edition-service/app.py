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
        password=os.getenv("POSTGRES_PASSWORD", "postgres")
    )

# Kafka consumer function for editions data
def consume_kafka_messages():
    kafka_broker = os.getenv("KAFKA_BROKER", "kafka:9092")
    topic = 'openlib-editions'
    
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=[kafka_broker],
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='edition-service-group',
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    
    # Process messages continuously
    for message in consumer:
        edition_data = message.value
        print(f"Consumed edition data: {edition_data}")
        
        # Use the file timestamp from the 4th column provided by the producer
        last_modified = edition_data.get("file_last_modified", None)
        # Convert the complete JSON record to a string for the JSONB column
        raw_json = json.dumps(edition_data)

        edition_key = edition_data.get("key")          # e.g. "/books/OL10000402M"
        publish_date = edition_data.get("publish_date")  # from the DAG
        work_key = edition_data.get("work_key")        # from the DAG
        title = edition_data.get("title")
        revision = edition_data.get("revision", 1)
        
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO editions (edition_key, title, publish_date, revision, last_modified, work_key, data)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (edition_key) DO UPDATE
                      SET title = EXCLUDED.title,
                          publish_date = EXCLUDED.publish_date,
                          revision = EXCLUDED.revision,
                          last_modified = EXCLUDED.last_modified,
                          work_key = EXCLUDED.work_key,
                          data = EXCLUDED.data;
                """, (
                    edition_key,
                    title,
                    publish_date,
                    revision,
                    last_modified,
                    work_key,
                    raw_json
                ))
                conn.commit()
            conn.close()
        except Exception as e:
            print("Error updating edition:", e)

# Start Kafka consumer in a background thread
def start_kafka_consumer():
    thread = threading.Thread(target=consume_kafka_messages, daemon=True)
    thread.start()

@app.on_event("startup")
def startup_event():
    start_kafka_consumer()

@app.get("/edition/{edition_id}")
def read_edition(edition_id: str):
    conn = get_db_connection()
    with conn.cursor() as cur:
        # Assuming keys are stored as full strings, e.g., "/books/OL10000299M"
        key = f"/books/{edition_id}"
        cur.execute("SELECT edition_key, title, revision, last_modified, data FROM editions WHERE edition_key = %s", (key,))
        row = cur.fetchone()
    conn.close()
    if row:
        return {
            "edition_key": row[0],
            "title": row[1],
            "revision": row[2],
            "last_modified": str(row[3]) if row[3] else None,
            "data": row[4]
        }
    else:
        return {"error": "Edition not found"}

