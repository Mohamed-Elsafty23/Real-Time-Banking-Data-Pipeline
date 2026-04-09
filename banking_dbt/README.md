# banking_dbt

dbt models for this pipeline: **RAW** sources in Snowflake → **staging** views → **marts** (facts and dimensions) → **snapshots** (SCD Type 2).

See the [repository README](../README.md) for architecture, run order, and environment setup. Typical commands (with profiles configured):

```bash
cd banking_dbt
dbt deps
dbt run
dbt test
dbt snapshot
```
