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
    'openlib_publish_works',
    default_args=default_args,
    schedule_interval='@once'
)

# Sensor to wait for the works file
wait_for_file = FileSensor(
    task_id='wait_for_works_file',
    filepath='/data/dumps/ol_dump_works_trunc.txt',
    fs_conn_id='fs_default',
    poke_interval=10,
    timeout=3600,
    mode="poke",
    dag=dag
)

def publish_works_to_kafka():
    kafka_broker = os.getenv('KAFKA_BROKER', 'kafka:9092')
    topic = 'openlib-works'
    producer = KafkaProducer(
        bootstrap_servers=[kafka_broker],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    dumps_folder = os.getenv('DUMPS_DIR', '/data/dumps')
    works_file = os.path.join(dumps_folder, 'ol_dump_works_trunc.txt')

    print(f"Reading file: {works_file}")

    with open(works_file, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) != 5:
                continue
            record_type, key, revision, last_modified, record_json = parts
            if record_type != '/type/work':
                continue
            data = json.loads(record_json)
            # Inject the file's timestamp from the 4th column:
            data["file_last_modified"] = last_modified
            print(f"Publishing work for key: {data.get('key')}")
            producer.send(topic, data)
            producer.flush()

publish_task = PythonOperator(
    task_id='publish_works',
    python_callable=publish_works_to_kafka,
    dag=dag
)

wait_for_file >> publish_task

