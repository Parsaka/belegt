# API image: small, non-root, no build tools at runtime.
FROM python:3.12-slim AS build
WORKDIR /src
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir --prefix=/install ".[api]"

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 BELEGT_CHUNKS=/data/chunks.jsonl
COPY --from=build /install /usr/local
RUN useradd --uid 10001 --no-create-home app
USER 10001
EXPOSE 8080
CMD ["uvicorn", "belegt.api.app:app_from_env", "--factory", "--host", "0.0.0.0", "--port", "8080"]
