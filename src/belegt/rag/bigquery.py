"""The retrieval store on BigQuery: chunks with embeddings, row access policies per tenant.

Isolation has two independent layers:

1. **Row access policies** on `rag.chunks`. Tenant `x` reads through its own service account
   `rag-x@<project>`, and the policy for that account only lets rows of `x` and `shared` through.
   Once a table has a row access policy, every principal without one sees no rows at all.
2. **The query itself** filters on the tenant before VECTOR_SEARCH (see `bigquery_search_sql`).

A bug in either layer alone does not leak another tenant's text. VECTOR_SEARCH and row access
policies are both part of BigQuery on-demand pricing; there is no separate vector database.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from typing import Any

from belegt.documents.model import SHARED_TENANT, Chunk
from belegt.rag.embedding import Embedder
from belegt.rag.retrieval import Hit, bigquery_search_sql, visible_tenants

CHUNKS_TABLE = "chunks"
CHUNK_SCHEMA: list[dict[str, str]] = [
    {"name": "chunk_id", "type": "STRING", "mode": "REQUIRED"},
    {"name": "doc_id", "type": "STRING", "mode": "REQUIRED"},
    {"name": "tenant_id", "type": "STRING", "mode": "REQUIRED"},
    {"name": "page", "type": "INT64", "mode": "REQUIRED"},
    {"name": "heading", "type": "STRING", "mode": "NULLABLE"},
    {"name": "text", "type": "STRING", "mode": "REQUIRED"},
    {"name": "embedding", "type": "FLOAT64", "mode": "REPEATED"},
]
_TENANT = re.compile(r"^[a-z][a-z0-9_]{1,20}$")


def check_tenant(tenant_id: str) -> str:
    """Tenant ids end up in policy names and service account ids, so keep them plain."""
    if not _TENANT.fullmatch(tenant_id):
        raise ValueError(f"invalid tenant id {tenant_id!r}: a-z, 0-9 and _, 2 to 21 characters")
    return tenant_id


def tenant_service_account(tenant_id: str, project: str) -> str:
    """rag-tenant-a@<project>.iam.gserviceaccount.com for tenant `tenant_a`."""
    return f"rag-{check_tenant(tenant_id).replace('_', '-')}@{project}.iam.gserviceaccount.com"


def row_access_policy_sql(table: str, tenant_id: str, member: str) -> str:
    """One policy per tenant: its identity sees its own rows and the shared corpus."""
    tenant = check_tenant(tenant_id)
    if tenant == SHARED_TENANT:
        raise ValueError("the shared corpus is visible to every tenant; it has no policy")
    if not re.fullmatch(r"(serviceAccount|user|group):[\w.@-]+", member):
        raise ValueError(f"invalid member {member!r}")
    return (
        f"CREATE OR REPLACE ROW ACCESS POLICY tenant_{tenant} ON `{table}` "
        f'GRANT TO ("{member}") '
        f"FILTER USING (tenant_id IN ('{tenant}', '{SHARED_TENANT}'))"
    )


def chunk_rows(
    chunks: Iterable[Chunk], embedder: Embedder, batch: int = 64
) -> list[dict[str, Any]]:
    """Chunks as BigQuery rows with passage embeddings, in a stable order."""
    ordered = sorted(chunks, key=lambda c: c.chunk_id)
    rows: list[dict[str, Any]] = []
    for start in range(0, len(ordered), batch):
        part = ordered[start : start + batch]
        vectors = embedder.embed([c.text for c in part], query=False)
        for c, vec in zip(part, vectors, strict=True):
            rows.append(
                {
                    "chunk_id": c.chunk_id,
                    "doc_id": c.doc_id,
                    "tenant_id": check_tenant(c.tenant_id),
                    "page": c.page,
                    "heading": c.heading,
                    "text": c.text,
                    "embedding": vec,
                }
            )
    return rows


def load_chunks(client: Any, table: str, rows: list[dict[str, Any]]) -> int:
    """Replace the whole table (WRITE_TRUNCATE keeps re-runs idempotent). Row access policies
    survive a truncating load, so isolation holds while the new rows arrive."""
    from google.cloud import bigquery

    config = bigquery.LoadJobConfig(
        schema=[bigquery.SchemaField.from_api_repr(f) for f in CHUNK_SCHEMA],
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
    )
    client.load_table_from_json(rows, table, job_config=config).result()
    return len(rows)


class BigQueryRetriever:
    """Retriever over `rag.chunks`; every query runs as the tenant's own identity.

    `client_for` returns a BigQuery client authenticated as that tenant's service account
    (see `impersonating_client`), so the row access policy applies to each request.
    """

    def __init__(self, client_for: Callable[[str], Any], dataset: str, embedder: Embedder) -> None:
        self._client_for = client_for
        self._dataset = dataset
        self._embedder = embedder

    def search(self, question: str, tenant_id: str, k: int) -> list[Hit]:
        from google.cloud import bigquery

        visible_tenants(tenant_id)  # rejects the shared pseudo-tenant and empty ids
        (vector,) = self._embedder.embed([question], query=True)
        config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("tenant", "STRING", tenant_id),
                bigquery.ArrayQueryParameter("embedding", "FLOAT64", vector),
            ],
            maximum_bytes_billed=100 * 1024 * 1024,
        )
        job = self._client_for(tenant_id).query(
            bigquery_search_sql(self._dataset, k), job_config=config
        )
        return [
            Hit(
                Chunk(
                    chunk_id=r["chunk_id"],
                    doc_id=r["doc_id"],
                    tenant_id=r["tenant_id"],
                    page=r["page"],
                    text=r["text"],
                    heading=r["heading"],
                ),
                float(r["score"]),
            )
            for r in job.result()
        ]


def impersonating_client(project: str) -> Callable[[str], Any]:
    """Clients that act as `rag-<tenant>@<project>`, cached per tenant.

    The caller (the API's or the pipeline's identity) needs Service Account Token Creator on
    each tenant account. No keys are involved.
    """
    import google.auth
    from google.auth import impersonated_credentials
    from google.cloud import bigquery

    source, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    cache: dict[str, Any] = {}

    def client_for(tenant_id: str) -> Any:
        if tenant_id not in cache:
            creds = impersonated_credentials.Credentials(  # type: ignore[no-untyped-call]
                source_credentials=source,
                target_principal=tenant_service_account(tenant_id, project),
                target_scopes=["https://www.googleapis.com/auth/bigquery"],
                lifetime=900,
            )
            cache[tenant_id] = bigquery.Client(project=project, credentials=creds)
        return cache[tenant_id]

    return client_for
