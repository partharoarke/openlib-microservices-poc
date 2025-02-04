from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

# Import the "main" functions from your scripts
from scripts.populate_author_works import main as populate_author_works_main
from scripts.populate_edition_isbns import main as populate_edition_isbns_main

def populate_author_works_wrapper():
    # Call the function from your script
    populate_author_works_main()

def populate_edition_isbns_wrapper():
    # Call the function from your script
    populate_edition_isbns_main()

default_args = {
    'owner': 'airflow',
    'start_date': days_ago(1)
}

dag = DAG(
    dag_id='openlib_populate_reftables',
    default_args=default_args,
    schedule_interval=None
)

task_author_works = PythonOperator(
    task_id='populate_author_works',
    python_callable=populate_author_works_wrapper,
    dag=dag
)

task_edition_isbns = PythonOperator(
    task_id='populate_edition_isbns',
    python_callable=populate_edition_isbns_wrapper,
    dag=dag
)

task_author_works >> task_edition_isbns

