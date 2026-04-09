# Real-Time Banking Data Pipeline

**Portfolio project —** synthetic core-banking data, CDC streaming, object storage, Airflow orchestration, Snowflake bronze ingest, and dbt analytics (staging, marts, SCD2 snapshots), with Docker Compose locally and GitHub Actions for automation.

---

## Architecture

High-level flow: OLTP → Kafka/Debezium → Parquet in MinIO → Airflow → Snowflake raw → dbt models. CI/CD runs alongside in GitHub Actions.

![End-to-end pipeline architecture](Banking_Data_Pipeline.png)

*Figure: components and data movement (topic prefix in this repo: `core_banking_oltp.public.*`).*

For an editable version (layers, colors, export to SVG), open [`docs/architecture.drawio`](docs/architecture.drawio) in [draw.io / diagrams.net](https://app.diagrams.net/).

---

## What it does

A Python generator continuously inserts customers, accounts, and transactions into PostgreSQL. Debezium captures changes from the WAL into Kafka topics. A consumer batches events into Parquet and uploads them to MinIO. Airflow downloads new objects and loads them into Snowflake raw tables. dbt builds staging views, dimensional and fact marts, and snapshot-based slowly changing dimensions. GitHub Actions lint the Python code, run lightweight tests, and compile or deploy dbt when you configure secrets.

---

## Portfolio highlights (CV-friendly)

- Designed an **event-driven path** from OLTP to a warehouse using **CDC** (Debezium) and **Kafka**, not only batch files.
- Landed streaming-derived data in **S3-compatible storage** (MinIO) as **Parquet**, then **orchestrated** loads with **Airflow** and modeled in **dbt** on **Snowflake**.
- Containerized the stack with **Docker Compose** (health checks, broker listeners suited to Linux hosts) and added **CI** (Ruff, pytest, dbt compile) plus optional **CD** for dbt.

---

## Tech stack

| Layer | Tools |
|--------|--------|
| Source OLTP | PostgreSQL |
| Synthetic load | Python, Faker, psycopg2 |
| CDC / streaming | Apache Kafka, Zookeeper, Debezium Connect |
| Data lake landing | MinIO (S3 API), Parquet |
| Orchestration | Apache Airflow (image includes dbt) |
| Warehouse & transforms | Snowflake, dbt (staging, marts, snapshots) |
| Local runtime | Docker Compose |
| Automation | GitHub Actions (`.github/workflows`) |

---

## Repository layout

| Path | Role |
|------|------|
| `data-generator/` | Inserts fake banking rows; `--once` or bounded loop |
| `kafka-debezium/` | Registers Postgres CDC connector (`core_banking_oltp`, custom slot name) |
| `consumer/` | Kafka → batched Parquet → MinIO |
| `docker/dags/` | DAGs: bronze MinIO→Snowflake; dbt snapshots + marts |
| `banking_dbt/` | dbt project (sources, staging, marts, snapshots) |
| `postgres/` | OLTP DDL |
| `tests/` | Layout checks for CI |
| `docs/architecture.drawio` | Editable diagram |
| `Banking_Data_Pipeline.png` | Architecture figure (used above) |

---

## Prerequisites

- Docker and Docker Compose
- A Snowflake account (database, warehouse, role, and a **RAW** schema with tables/stages aligned to your COPY strategy)
- Python 3.11+ if you run the generator, connector script, or consumer on the host (see `requirements.txt`)
- For GitHub Actions: repository secrets for Postgres (CI service), Snowflake (dbt compile/run), as in `.github/workflows`

---

## Run locally (condensed)

1. **Environment:** Copy `.env.example` to `.env` at the repo root. Fill `consumer/.env`, `data-generator/.env`, `kafka-debezium/.env`, and `docker/dags/.env` (or rely on root `.env` where variables overlap — scripts load component dir first, then root).
2. **Infra:** `docker compose up -d` (builds Airflow image on first run).
3. **OLTP schema:** Apply `postgres/schema.sql` to the Compose Postgres if the volume is empty.
4. **MinIO:** Ensure the bucket from `MINIO_BUCKET` exists (consumer creates it if missing).
5. **CDC:** When Kafka Connect is up, run `python kafka-debezium/generate_and_post_connector.py` (set `KAFKA_CONNECT_URL` if not `http://localhost:8083`).
6. **Stream path:** Start `data-generator/faker_generator.py`, then `consumer/kafka_to_minio.py` (Kafka bootstrap should match your `.env`, e.g. `localhost:29092` on Linux).
7. **Warehouse:** In Snowflake, align raw tables and file format with what the bronze DAG expects (Parquet, schema `RAW` or as in your `sources.yml`).
8. **Airflow:** Open the UI (port 8080 by default), enable **`raw_layer_snowflake_sync`** and **`analytics_scd2_refresh`**, confirm connections/credentials from `docker/dags/.env`.
9. **dbt:** Install profiles under `~/.dbt` (or the path Airflow uses) and run `dbt build` from `banking_dbt/` when validating outside Airflow.

Kafka uses `localhost:29092` on the host for the external listener; Zookeeper and Kafka expose health checks so Connect starts after the broker is ready.

---

## Steps to finish the project (checklist)

Use this as a end-to-end completion guide and as interview talking points.

1. **Repository** — Push to GitHub, set default branch to `main`, add a short repo description and topics (e.g. `dbt`, `airflow`, `kafka`, `snowflake`, `cdc`, `data-engineering`).
2. **Secrets** — Add GitHub Actions secrets for Snowflake and CI Postgres per `.github/workflows/ci.yml` and `cd.yml`; confirm CI passes on a branch.
3. **Snowflake** — Create database, warehouse, and **RAW** schema; create or generate raw tables compatible with Parquet `COPY`; grant the Airflow/dbt role usage rights.
4. **MinIO** — Confirm bucket, prefixes (`customers/`, `accounts/`, `transactions/`), and that Parquet files appear after the consumer runs.
5. **Debezium** — One active connector with this repo’s names; remove any old tutorial connector/slot if topics do not match (`core_banking_oltp.public.*`).
6. **Airflow** — DAGs parsed without import errors; bronze DAG runs successfully; SCD DAG runs dbt with a valid profiles directory inside the container.
7. **dbt** — `dbt build` or `dbt run` + `dbt test` succeed; document target and schema in your portfolio if recruiters ask.
8. **Evidence** — Keep one screenshot or query result (raw row counts, mart sample) for interviews; optional: link `Banking_Dashboard.png` or your BI file if you use one.
9. **README** — Ensure this file and `Banking_Data_Pipeline.png` stay in sync with the real architecture; update the figure when you change the stack.

---

## Customizations in this version

Docker network name **`rtbanking-lakehouse-net`**; bronze DAG **`raw_layer_snowflake_sync`** with optional **`RAW_TABLE_LIST`**; SCD/marts DAG **`analytics_scd2_refresh`** with `dbt snapshot` → `dbt run --select marts`; Debezium connector **`rtbanking-postgres-cdc`** and slot **`rtbanking_cdc_slot`**; **`KAFKA_CONNECT_URL`** override; dbt defaults for staging (views) and marts (tables); dual **`.env`** resolution (folder + repo root).

If you still have the older tutorial connector (`postgres-connector`, prefix `banking_server`, slot `banking_slot`), remove it and the old replication slot before registering this project’s connector, or the consumer will not see the right topics.

---

## Origin and attribution

This repository grew out of the public **banking modern data stack** tutorial. I reworked naming, operations, Airflow DAGs, dbt project defaults, tests, CI, documentation, and the architecture assets (`Banking_Data_Pipeline.png`, `docs/architecture.drawio`) for my own portfolio. The overall pattern is similar; the specifics and presentation here are my own.
