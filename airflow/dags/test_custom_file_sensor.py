from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from custom_file_sensor import CustomFileSensor

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2025, 2, 2)
}

dag = DAG('custom_file_sensor_test', default_args=default_args, schedule_interval=None)

# Define the sensor to look for the file.
sensor_task = CustomFileSensor(
    task_id='wait_for_file',
    filepath='/data/dumps/ol_dump_authors_trunc.txt',  # Absolute path inside the container
    poke_interval=10,  # Check every 10 seconds
    timeout=3600,      # Timeout after 1 hour if file is not found
    dag=dag
)

# Define a downstream task that just prints a message when the file is detected.
def print_success():
    print("File detected by custom sensor!")

print_task = PythonOperator(
    task_id='print_success',
    python_callable=print_success,
    dag=dag
)

sensor_task >> print_task

