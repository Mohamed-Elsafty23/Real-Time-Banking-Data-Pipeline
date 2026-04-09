# Real-Time Banking Data Pipeline

Personal portfolio project: an **end-to-end streaming and batch pipeline** that turns synthetic core-banking activity into **analytics-ready models** in Snowflake—wired with **CDC**, a **lake-style landing zone**, **orchestration**, and **dbt** transformations, all reproducible with **Docker Compose**.

---

## Architecture

Flow: synthetic OLTP writes → PostgreSQL → Debezium/Kafka CDC → batched Parquet in MinIO → Airflow loads raw tables in Snowflake → dbt builds staging, facts, dimensions, and SCD Type 2 snapshots. CI/CD runs on GitHub Actions.

![End-to-end architecture: data generator → PostgreSQL → Debezium/Kafka → consumer → MinIO → Airflow → Snowflake → dbt; GitHub Actions for CI/CD](Banking_Data_Pipeline.png)

*Editable source for the diagram (adjust layout or export SVG): [`docs/architecture.drawio`](docs/architecture.drawio) — open in [diagrams.net](https://app.diagrams.net/).*

**CDC topic naming in this repo:** `core_banking_oltp.public.*` (customers, accounts, transactions).

---

## What I built (portfolio highlights)

- **Change data capture** from PostgreSQL (logical replication / Debezium) into Kafka topics with a project-specific connector and replication slot.
- **Stream-to-lake path:** a Python consumer batches CDC payloads and writes **partitioned Parquet** to **MinIO** (S3-compatible).
- **Orchestration:** Airflow DAGs for **bronze ingest** (MinIO → Snowflake) and for **dbt snapshots + marts** with a correct task dependency chain.
- **Modeling:** dbt **staging → marts** (facts/dimensions) and **snapshots** for slowly changing dimensions.
- **Platform hygiene:** Docker Compose with health checks and sensible startup order, **Ruff** + **pytest** in CI, `.env.example`, and layout tests so the repo stays verifiable without a full stack running in GitHub.

---

## Tech stack

| Layer | Technologies |
|--------|----------------|
| Source OLTP | PostgreSQL |
| Data simulation | Python, Faker, psycopg2 |
| Streaming / CDC | Kafka, Zookeeper, Debezium Connect |
| Object storage | MinIO |
| Orchestration | Apache Airflow (image includes dbt) |
| Warehouse & transforms | Snowflake, dbt |
| Local runtime | Docker Compose |
| Automation | GitHub Actions (`ci.yml`, `cd.yml`) |

---

## Repository layout

| Path | Role |
|------|------|
| `data-generator/` | Inserts synthetic customers, accounts, transactions (`--once` or loop). |
| `kafka-debezium/` | Registers the Postgres CDC connector (`KAFKA_CONNECT_URL` override supported). |
| `consumer/` | Kafka → MinIO Parquet batches. |
| `docker/dags/` | DAGs: bronze sync and dbt snapshot/marts. |
| `banking_dbt/` | Sources, staging, marts, snapshots. |
| `postgres/` | OLTP DDL. |
| `tests/` | Fast checks used in CI. |

**Airflow DAG IDs:** `raw_layer_snowflake_sync` (bronze), `analytics_scd2_refresh` (snapshots then marts).

---

## Run it locally (checklist)

1. **Environment:** Copy [`.env.example`](.env.example) to `.env` at the repo root. Add matching `.env` files under `consumer/`, `data-generator/`, `kafka-debezium/`, and `docker/dags/` as needed (scripts also load the root `.env` after the local one).
2. **Infra:** `docker compose up -d` (builds the Airflow image on first run).
3. **Schema:** Apply [`postgres/schema.sql`](postgres/schema.sql) if the database is empty.
4. **Pipeline:** Start the generator → POST the Debezium connector → run the consumer → confirm objects in MinIO → enable/trigger Airflow DAGs and run dbt (or rely on the dbt DAG).

**Host Kafka:** consumers on the machine use `localhost:29092` (see `docker-compose.yml`).

Optional bronze tuning: set `RAW_TABLE_LIST` (comma-separated) in the Airflow/dags environment if you change raw table names.

---

## CI/CD

- **CI** (push/PR to `main` / `dev`): install deps, **Ruff**, **pytest**, **dbt compile** (Snowflake secrets required for compile in your fork).
- **CD** (push to `main`): dbt run and test against your configured Snowflake target when secrets are set.

---

## Acknowledgement

This project is **based on** the public **banking modern data stack** tutorial-style repository. I **reimplemented and extended** it for my portfolio: naming (topics, connector, DAGs, Docker network), Compose hardening, dbt project defaults, env handling, tests, CI cleanup, documentation, and the architecture assets above—including **`Banking_Data_Pipeline.png`** and **`docs/architecture.drawio`**. The overall pattern is familiar; the specifics here are how I chose to ship and document it.
