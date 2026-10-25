.PHONY: install lint fmt test
install:
	pip install -e ".[dev]"
lint:
	ruff check . && ruff format --check . && mypy
fmt:
	ruff check --fix . && ruff format .
test:
	pytest -m "not live"
