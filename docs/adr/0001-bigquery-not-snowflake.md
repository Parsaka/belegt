# ADR 0001: BigQuery as the only warehouse

Status: accepted (2026-10-25)

## Context
Job ads for German data roles ask for BigQuery and Snowflake. Both play the same role: a
cloud warehouse that separates storage from compute.

## Decision
Use BigQuery only. Do not add Snowflake to show the name.

## Reasons
- One tool per job. Two warehouses in one project would only duplicate models.
- BigQuery's free tier (1 TiB queries, 10 GiB storage per month) fits the 1.50 EUR budget;
  Snowflake offers only a 30-day trial.
- BigQuery's on-demand pricing includes VECTOR_SEARCH and row-level security, so it can also
  serve the RAG store, which removes a database.

## Portability
SQL that is specific to BigQuery stays in dbt macros, so the models could move to Snowflake by
changing the adapter and those macros. The main differences to know: micro-partitions and
clustering keys versus partitioning and clustering; virtual warehouses versus slots; and
Snowflake credits versus bytes scanned.
