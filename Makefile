.PHONY: install lint fmt test warehouse
install:
	pip install -e ".[dev,dbt]"
lint:
	ruff check . && ruff format --check . && mypy
fmt:
	ruff check --fix . && ruff format .
test:
	pytest -m "not live"
warehouse:
	belegt load --source tests/fixtures --db data/belegt.duckdb
	dbt build --project-dir dbt --profiles-dir dbt
