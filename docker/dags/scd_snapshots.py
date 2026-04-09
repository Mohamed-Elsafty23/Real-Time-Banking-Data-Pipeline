"""
Airflow DAG: dbt snapshots (SCD Type 2) then refresh of mart models.
"""
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

with DAG(
    dag_id="analytics_scd2_refresh",
    default_args=default_args,
    description="dbt snapshot (SCD2) followed by marts build",
    schedule_interval="@daily",
    start_date=datetime(2024, 6, 1),
    catchup=False,
    tags=["dbt", "snowflake", "scd2", "marts"],
) as dag:
    dbt_snapshot = BashOperator(
        task_id="dbt_snapshot",
        bash_command="cd /opt/airflow/banking_dbt && dbt snapshot --profiles-dir /home/airflow/.dbt",
    )
    dbt_run_marts = BashOperator(
        task_id="dbt_run_marts",
        bash_command="cd /opt/airflow/banking_dbt && dbt run --select marts --profiles-dir /home/airflow/.dbt",
    )
    dbt_snapshot >> dbt_run_marts
