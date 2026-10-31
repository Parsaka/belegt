# Three images from one file, all non-root, no build tools at runtime:
#   docker build --target reports .     report extraction tasks (Indexed Job / Cloud Run job)
#   docker build --target api-cloud .   the API on Cloud Run: BigQuery retrieval, e5 embeddings
#   docker build .                      the API with in-memory chunks (kind tests, default)
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

# The e5 model is baked in, so a cold start loads it from disk instead of downloading it.
FROM python:3.12-slim AS build-api-cloud
RUN python -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH HF_HOME=/opt/models
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
WORKDIR /src
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir ".[api,bigquery,embed]" \
    && python -c "from sentence_transformers import SentenceTransformer as S; S('intfloat/multilingual-e5-small')"

FROM python:3.12-slim AS api-cloud
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH=/opt/venv/bin:$PATH \
    HF_HOME=/opt/models HF_HUB_OFFLINE=1 BELEGT_BACKEND=bigquery BELEGT_SEED=/app/reports.csv
COPY --from=build-api-cloud /opt/venv /opt/venv
COPY --from=build-api-cloud /opt/models /opt/models
COPY dbt/seeds/reports.csv /app/reports.csv
RUN useradd --uid 10001 --no-create-home app
USER 10001
EXPOSE 8080
CMD ["sh", "-c", "exec uvicorn belegt.api.app:app_from_env --factory --host 0.0.0.0 --port ${PORT:-8080}"]

FROM python:3.12-slim AS build-api
WORKDIR /src
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir --prefix=/install ".[api]"

FROM python:3.12-slim AS api
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 BELEGT_CHUNKS=/data/chunks.jsonl \
    BELEGT_SEED=/app/reports.csv
COPY --from=build-api /install /usr/local
COPY dbt/seeds/reports.csv /app/reports.csv
RUN useradd --uid 10001 --no-create-home app
USER 10001
EXPOSE 8080
CMD ["uvicorn", "belegt.api.app:app_from_env", "--factory", "--host", "0.0.0.0", "--port", "8080"]
