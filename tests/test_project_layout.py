"""Lightweight checks so CI has a real pytest step without external services."""


def test_dbt_project_file_exists():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    assert (root / "banking_dbt" / "dbt_project.yml").is_file()


def test_dag_files_present():
    from pathlib import Path

    dags = Path(__file__).resolve().parents[1] / "docker" / "dags"
    assert (dags / "minio_to_snowflake_dag.py").is_file()
    assert (dags / "scd_snapshots.py").is_file()
