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

# Kafka consumer function for works data
def consume_kafka_messages():
    kafka_broker = os.getenv("KAFKA_BROKER", "kafka:9092")
    topic = 'openlib-works'
    
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=[kafka_broker],
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='work-service-group',
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    
    # Process messages continuously
    for message in consumer:
        work_data = message.value
        print(f"Consumed work data: {work_data}")
        
        # Use the file timestamp from the 4th column (provided by the producer as "file_last_modified")
        last_modified = work_data.get("file_last_modified", None)
        # Store the full JSON record in the 'data' column
        raw_json = json.dumps(work_data)
        
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO works (work_key, title, revision, last_modified, data)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (work_key) DO UPDATE
                      SET title = EXCLUDED.title,
                          revision = EXCLUDED.revision,
                          last_modified = EXCLUDED.last_modified,
                          data = EXCLUDED.data;
                """, (
                    work_data.get("key"),
                    work_data.get("title"),
                    work_data.get("revision", 1),
                    last_modified,
                    raw_json
                ))
                conn.commit()
            conn.close()
        except Exception as e:
            print("Error updating work:", e)

# Start Kafka consumer in a background thread
def start_kafka_consumer():
    thread = threading.Thread(target=consume_kafka_messages, daemon=True)
    thread.start()

@app.on_event("startup")
def startup_event():
    start_kafka_consumer()

@app.get("/work/{work_id}")
def read_work(work_id: str):
    conn = get_db_connection()
    with conn.cursor() as cur:
        # Assuming keys are stored as full strings, e.g., "/works/OL10000278W"
        key = f"/works/{work_id}"
        cur.execute("SELECT work_key, title, revision, last_modified, data FROM works WHERE work_key = %s", (key,))
        row = cur.fetchone()
    conn.close()
    if row:
        return {
            "work_key": row[0],
            "title": row[1],
            "revision": row[2],
            "last_modified": str(row[3]) if row[3] else None,
            "data": row[4]
        }
    else:
        return {"error": "Work not found"}

