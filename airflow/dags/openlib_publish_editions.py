from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.filesystem import FileSensor
from airflow.utils.dates import days_ago
from kafka import KafkaProducer
import json
import os

default_args = {
    'owner': 'airflow',
    'start_date': days_ago(1)
}

dag = DAG(
    'openlib_publish_editions',
    default_args=default_args,
    schedule_interval='@once'
)

# Sensor to wait for the editions file
wait_for_file = FileSensor(
    task_id='wait_for_editions_file',
    filepath='/data/dumps/ol_dump_editions_trunc.txt',
    fs_conn_id='fs_default',  # Ensure that this connection (of type File) is configured
    poke_interval=10,         # Check every 10 seconds
    timeout=3600,             # Timeout after 1 hour if the file is not found
    mode="poke",
    dag=dag
)

def publish_editions_to_kafka():
    kafka_broker = os.getenv('KAFKA_BROKER', 'kafka:9092')
    topic = 'openlib-editions'
    producer = KafkaProducer(
        bootstrap_servers=[kafka_broker],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    dumps_folder = os.getenv('DUMPS_DIR', '/data/dumps')
    editions_file = os.path.join(dumps_folder, 'ol_dump_editions_trunc.txt')

    print(f"Reading file: {editions_file}")

    with open(editions_file, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) != 5:
                continue
            record_type, key, revision, last_modified, record_json = parts
            if record_type != '/type/edition':
                continue
            data = json.loads(record_json)
            # Insert the file's timestamp for reference
            data["file_last_modified"] = last_modified
            # Extract publish date from top level json
            publish_date = data.get("publish_date")
            # Extract the "work_key" from the "works" array if present
            # Often it's: "works": [{"key": "/works/OLxxxxW"}]
            # Pick the first if multiple
            works_array = data.get("works", [])
            work_key = None
            if works_array:
                # e.g. works_array[0]["key"] might be "/works/OL14903285W"
                work_key = works_array[0].get("key")

            # Embed these fields in the message so the consumer can set them in the DB
            data["publish_date"] = publish_date
            data["work_key"] = work_key  # e.g. "/works/OL10000609W"
            print(f"Publishing edition for key: {data.get('key')}")
            producer.send(topic, data)
            producer.flush()

publish_task = PythonOperator(
    task_id='publish_editions',
    python_callable=publish_editions_to_kafka,
    dag=dag
)

# Ensure that the publishing only starts after the file is detected.
wait_for_file >> publish_task

