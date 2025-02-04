from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from kafka import KafkaProducer
import json
import os

default_args = {'owner': 'airflow', 'start_date': days_ago(1)}
dag = DAG('test_publish_authors', default_args=default_args, schedule_interval=None)

def publish_authors_to_kafka():
    kafka_broker = os.getenv('KAFKA_BROKER', 'kafka:9092')
    topic = 'openlib-authors'
    producer = KafkaProducer(
        bootstrap_servers=[kafka_broker],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    dumps_folder = os.getenv('DUMPS_DIR', '/data/dumps')
    authors_file = os.path.join(dumps_folder, 'ol_dump_authors_trunc.txt')

    # log/print statement to confirm the file is being read:
    print(f"Reading file: {authors_file}")

    with open(authors_file, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) != 5:
                continue
            record_type, key, revision, last_modified, record_json = parts
            if record_type != '/type/author':
                continue
            data = json.loads(record_json)
            print(f"Publishing record for key: {data.get('key')}")
            producer.send(topic, data)
            producer.flush()

with dag:
    publish_task = PythonOperator(
        task_id='publish_authors',
        python_callable=publish_authors_to_kafka,
        dag=dag
    )

