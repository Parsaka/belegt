"""The BigQuery store without BigQuery: policies, naming, row encoding and the retriever."""

import pytest

from belegt.documents.chunking import chunk_pages
from belegt.documents.model import Page
from belegt.rag.bigquery import (
    CHUNK_SCHEMA,
    BigQueryRetriever,
    check_tenant,
    chunk_rows,
    row_access_policy_sql,
    tenant_service_account,
)
from belegt.rag.embedding import HashingEmbedder

bigquery = pytest.importorskip("google.cloud.bigquery")


def test_policy_lets_a_tenant_see_its_rows_and_the_shared_corpus_only():
    sql = row_access_policy_sql(
        "p.rag.chunks", "tenant_a", "serviceAccount:rag-tenant-a@p.iam.gserviceaccount.com"
    )
    assert sql.startswith("CREATE OR REPLACE ROW ACCESS POLICY tenant_tenant_a ON `p.rag.chunks`")
    assert 'GRANT TO ("serviceAccount:rag-tenant-a@p.iam.gserviceaccount.com")' in sql
    assert sql.endswith("FILTER USING (tenant_id IN ('tenant_a', 'shared'))")


@pytest.mark.parametrize("tenant", ["shared"])
def test_the_shared_corpus_gets_no_policy_of_its_own(tenant):
    with pytest.raises(ValueError, match="shared"):
        row_access_policy_sql("p.rag.chunks", tenant, "serviceAccount:x@p.iam.gserviceaccount.com")


@pytest.mark.parametrize("bad", ["", "a", "Tenant", "a-b", "a'; DROP", "x" * 22])
def test_tenant_ids_that_could_break_sql_or_iam_names_are_rejected(bad):
    with pytest.raises(ValueError):
        check_tenant(bad)


def test_members_are_validated():
    with pytest.raises(ValueError, match="member"):
        row_access_policy_sql("p.rag.chunks", "tenant_a", 'allUsers") OR ("x')


def test_service_account_names_are_valid_iam_ids():
    email = tenant_service_account("tenant_a", "belegt-pk-2610")
    assert email == "rag-tenant-a@belegt-pk-2610.iam.gserviceaccount.com"
    account_id = email.split("@")[0]
    assert 6 <= len(account_id) <= 30


def test_rows_match_the_table_schema_and_carry_unit_vectors():
    pages = [Page("esrs", 1, "E1-6 Treibhausgasemissionen\n\nScope 1 und Scope 2.")]
    rows = chunk_rows(chunk_pages(pages, "shared"), HashingEmbedder(dim=16))
    assert rows
    assert set(rows[0]) == {f["name"] for f in CHUNK_SCHEMA}
    assert abs(sum(v * v for v in rows[0]["embedding"]) - 1) < 1e-9


class _Job:
    def __init__(self, rows):
        self._rows = rows

    def result(self):
        return self._rows


class _Client:
    def __init__(self, rows):
        self.rows, self.calls = rows, []

    def query(self, sql, job_config):
        self.calls.append((sql, job_config))
        return _Job(self.rows)


def test_retriever_queries_as_the_tenant_with_parameters_not_string_formatting():
    row = {
        "chunk_id": "esrs:1:abc",
        "doc_id": "esrs",
        "tenant_id": "shared",
        "page": 1,
        "heading": None,
        "text": "Scope 1",
        "score": 0.8,
    }
    clients: dict[str, _Client] = {}

    def client_for(tenant):
        return clients.setdefault(tenant, _Client([row]))

    hits = BigQueryRetriever(client_for, "p.rag", HashingEmbedder(dim=16)).search(
        "Scope 1", "tenant_a", k=3
    )
    assert [h.chunk.chunk_id for h in hits] == ["esrs:1:abc"]
    assert list(clients) == ["tenant_a"]  # the query ran under the tenant's own identity
    sql, config = clients["tenant_a"].calls[0]
    assert "tenant_a" not in sql
    params = {p.name: p for p in config.query_parameters}
    assert params["tenant"].value == "tenant_a"
    assert len(params["embedding"].values) == 16
    assert config.maximum_bytes_billed == 100 * 1024 * 1024


def test_retriever_refuses_the_shared_pseudo_tenant():
    with pytest.raises(ValueError):
        BigQueryRetriever(lambda t: _Client([]), "p.rag", HashingEmbedder()).search(
            "x", "shared", k=3
        )


def test_a_question_without_a_company_searches_all_documents_without_an_empty_array_check():
    """BigQuery receives an empty ARRAY parameter as NULL, so the SQL must not rely on
    `ARRAY_LENGTH(@docs) = 0`: that filter removed every row in the first BigQuery run with
    the report corpus, and both memo questions abstained (Pipeline run 41287672974)."""
    client = _Client([])
    BigQueryRetriever(lambda t: client, "p.rag", HashingEmbedder(dim=16)).search(
        "Reduktionsziel?", "tenant_a", k=3
    )
    sql, config = client.calls[0]
    params = {p.name: p for p in config.query_parameters}
    assert params["all_docs"].value is True
    assert "ARRAY_LENGTH" not in sql
    assert "@all_docs OR doc_id IN UNNEST(@docs)" in sql


def test_a_named_company_restricts_the_search_to_its_reports():
    client = _Client([])
    BigQueryRetriever(lambda t: client, "p.rag", HashingEmbedder(dim=16)).search(
        "BASF Scope 1?", "tenant_a", k=12, docs=frozenset({"basf-2024"})
    )
    params = {p.name: p for p in client.calls[0][1].query_parameters}
    assert params["all_docs"].value is False
    assert params["docs"].values == ["basf-2024"]
