# Real-Time Banking Data Pipeline

End-to-end reference implementation that moves synthetic banking activity from a transactional database into a cloud warehouse, with change capture, object storage, orchestration, and modeled analytics layers. I use it as a portfolio piece to show how the pieces of a modern data platform fit together in a realistic, bounded scenario.

## What it does

The story is straightforward: a small Python service keeps inserting customers, accounts, and transactions into PostgreSQL. Debezium reads the database write-ahead log and publishes change events to Kafka. A consumer batches those events and lands Parquet files in MinIO. Apache Airflow pulls new files from MinIO and loads them into Snowflake as raw tables. dbt then builds staging views, dimensional and fact models, and snapshot-based slowly changing dimensions on top of that raw layer.

GitHub Actions runs linting and a compile pass against the dbt project on pull requests, and can run dbt in a target environment when you wire in secrets.

## Stack

| Area | Tools |
|------|--------|
| Source | PostgreSQL (OLTP-style schema) |
| Simulation | Python, Faker, psycopg2 |
| Streaming / CDC | Apache Kafka, Zookeeper, Debezium Connect |
| Lake-style landing | MinIO (S3 API) |
| Orchestration | Apache Airflow (custom image with dbt) |
| Warehouse & modeling | Snowflake, dbt (staging, marts, snapshots) |
| Containers | Docker Compose |
| Automation | GitHub Actions (CI/CD workflows in `.github/workflows`) |

## Diagram

An editable architecture diagram is in `docs/architecture.drawio`. Open it with [draw.io](https://app.diagrams.net/) (desktop or web) to adjust layout or export PNG or SVG for slides or a CV appendix.

## Repository layout

- `data-generator/` — loads fake banking rows into Postgres; supports a single batch (`--once`) or a bounded loop.
- `kafka-debezium/` — registers the Postgres CDC connector (topic prefix and slot names are specific to this project).
- `consumer/` — reads Debezium topics and writes partitioned Parquet to MinIO.
- `docker/dags/` — Airflow DAGs for bronze load and for dbt snapshots plus marts.
- `banking_dbt/` — dbt project (sources, staging, marts, snapshots).
- `postgres/` — DDL for the OLTP tables.
- `tests/` — small layout checks used by CI.

## Running locally (outline)

1. Copy `.env.example` to `.env` at the repo root and set passwords and MinIO credentials. Add service-specific `.env` files where the components expect them (`consumer/`, `data-generator/`, `kafka-debezium/`, `docker/dags/`) following the same variable names you already use for Postgres, Kafka, MinIO, and Snowflake.
2. Bring up infrastructure: `docker compose up -d` (or `docker-compose` depending on your install).
3. Apply `postgres/schema.sql` to your Postgres instance if it is empty.
4. Start the data generator, register the Debezium connector, then run the Kafka consumer so files appear under your MinIO bucket.
5. Configure Airflow’s environment for Snowflake and MinIO; trigger the bronze DAG and confirm raw tables in Snowflake, then run dbt (manually or via the SCD/marts DAG).

Kafka advertised listeners are set for typical Linux host access (`localhost:29092`); Zookeeper and Kafka include health checks so Connect starts after the broker is ready.

## Customization in this fork

Compared with a minimal tutorial layout, this version uses a dedicated Docker network name, configurable raw table list for the bronze DAG (`RAW_TABLE_LIST`), a configurable Kafka Connect base URL (`KAFKA_CONNECT_URL`), Debezium connector name and replication slot names that match the `core_banking_oltp` topic prefix, explicit dbt model defaults in `dbt_project.yml`, and renamed Airflow DAG IDs for clarity. The SCD DAG now chains snapshot and mart tasks in the correct order.

If you previously ran the older tutorial connector (`postgres-connector`, topic prefix `banking_server`, slot `banking_slot`), delete that connector and replication slot in Postgres before registering this project’s connector, or point the consumer at the matching topic names.

Python entrypoints load `.env` from the component folder first, then the repository root, so you can centralize shared variables at the root if you prefer.

---

**Origin and changes:** This repository started from the public “banking modern data stack” tutorial project and was reworked for my own learning and CV: naming, operational defaults, documentation, diagram, tests, CI cleanup, and the fixes and extensions above. The original idea and overall architecture pattern remain recognizable, but the implementation details and presentation here are mine.
