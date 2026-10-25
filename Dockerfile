# Two images from one file, both small, non-root, no build tools at runtime:
#   docker build --target reports .   report extraction tasks (Indexed Job / Cloud Run job)
#   docker build .                    the API (default, last stage)
FROM python:3.12-slim AS build-reports
WORKDIR /src
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir --prefix=/install ".[docs,extract,gcs]"

FROM python:3.12-slim AS reports
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY --from=build-reports /install /usr/local
COPY dbt/seeds/reports.csv /app/reports.csv
RUN useradd --uid 10001 --no-create-home app
USER 10001
WORKDIR /tmp
ENTRYPOINT ["belegt", "reports"]
CMD ["--seed", "/app/reports.csv", "--work", "/tmp/work"]

FROM python:3.12-slim AS build-api
WORKDIR /src
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir --prefix=/install ".[api]"

FROM python:3.12-slim AS api
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 BELEGT_CHUNKS=/data/chunks.jsonl
COPY --from=build-api /install /usr/local
RUN useradd --uid 10001 --no-create-home app
USER 10001
EXPOSE 8080
CMD ["uvicorn", "belegt.api.app:app_from_env", "--factory", "--host", "0.0.0.0", "--port", "8080"]
