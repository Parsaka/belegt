# Pipeline summary (duckdb)

## dbt build

_no run_results.json_

## Rows per mart

_query failed: Catalog Error: Table with name "marts.dim_installation" does not exist because schema "marts" does not exist.

LINE 1: ... 'dim_installation' as model, count(*) as n from marts.dim_installation
                                                                     ^^^^^^^^^^^^^_

## Installations by match decision and path

_query failed: Catalog Error: Table with name "marts.dim_installation" does not exist because schema "marts" does not exist.

LINE 3:         from marts.dim_installation group by 1, 2 order by 3 desc
                              ^^^^^^^^^^^^^^^^^^^^^^_

## Verified tonnes attributed to a company, by year (last five)

_query failed: Catalog Error: Table with name "marts.fct_verified_emissions" does not exist because schema "marts" does not exist.

LINE 4:         from marts.fct_verified_emissions as f
                              ^^^^^^^^^^^^^^^^^^^^^^^^_

## Largest groups in the latest year

_query failed: Catalog Error: Table with name "marts.mart_group_emissions" does not exist because schema "marts" does not exist.

LINE 2:         from marts.mart_group_emissions
                              ^^^^^^^^^^^^^^^^^_
