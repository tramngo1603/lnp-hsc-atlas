"""Tests for PubMed E-utilities client — all HTTP calls mocked via respx."""

from __future__ import annotations

import httpx
import pytest
import respx

from pubmed_agent.client import PubMedClient

# --- Fixture XML responses mimicking real NCBI E-utilities output ---

ESEARCH_RESPONSE = b"""\
<?xml version="1.0" encoding="UTF-8"?>
<eSearchResult>
  <Count>3</Count>
  <RetMax>3</RetMax>
  <IdList>
    <Id>38547890</Id>
    <Id>38123456</Id>
    <Id>37999999</Id>
  </IdList>
</eSearchResult>
"""

ESEARCH_EMPTY = b"""\
<?xml version="1.0" encoding="UTF-8"?>
<eSearchResult>
  <Count>0</Count>
  <RetMax>0</RetMax>
  <IdList/>
</eSearchResult>
"""

EFETCH_RESPONSE = b"""\
<?xml version="1.0" encoding="UTF-8"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>38547890</PMID>
      <Article>
        <Journal>
          <Title>Nature Biotechnology</Title>
        </Journal>
        <ArticleTitle>In vivo base editing of HSCs via LNP delivery</ArticleTitle>
        <Abstract>
          <AbstractText Label="BACKGROUND">Beta-thalassemia is a blood disorder.</AbstractText>
          <AbstractText Label="RESULTS">We achieved 45% editing in CD34+ HSCs.</AbstractText>
        </Abstract>
        <AuthorList>
          <Author>
            <LastName>Zhang</LastName>
            <ForeName>Yi</ForeName>
          </Author>
          <Author>
            <LastName>Liu</LastName>
            <ForeName>Xiao</ForeName>
          </Author>
        </AuthorList>
      </Article>
      <PubDate>
        <Year>2024</Year>
        <Month>03</Month>
        <Day>15</Day>
      </PubDate>
    </MedlineCitation>
    <PubmedData>
      <ArticleIdList>
        <ArticleId IdType="pubmed">38547890</ArticleId>
        <ArticleId IdType="doi">10.1038/s41587-024-01234-5</ArticleId>
      </ArticleIdList>
    </PubmedData>
  </PubmedArticle>
</PubmedArticleSet>
"""

ELINK_WITH_PMC = b"""\
<?xml version="1.0" encoding="UTF-8"?>
<eLinkResult>
  <LinkSet>
    <LinkSetDb>
      <Link>
        <Id>9876543</Id>
      </Link>
    </LinkSetDb>
  </LinkSet>
</eLinkResult>
"""

ELINK_NO_PMC = b"""\
<?xml version="1.0" encoding="UTF-8"?>
<eLinkResult>
  <LinkSet/>
</eLinkResult>
"""

PMC_FULL_TEXT = b"""\
<?xml version="1.0" encoding="UTF-8"?>
<pmc-articleset>
  <article>
    <front><article-title>Full text article</article-title></front>
    <body><sec><title>Methods</title><p>LNP formulation details...</p></sec></body>
  </article>
</pmc-articleset>
"""


@pytest.fixture()
def client() -> PubMedClient:
    """Create a PubMedClient with a test API key."""
    return PubMedClient(api_key="test-key", email="test@example.com")


class TestSearch:
    """Test PubMed search (esearch)."""

    @respx.mock
    async def test_search_returns_pmids(self, client: PubMedClient) -> None:
        respx.get(f"{client.BASE_URL}/esearch.fcgi").mock(
            return_value=httpx.Response(200, content=ESEARCH_RESPONSE)
        )
        pmids = await client.search('"lipid nanoparticle" AND "HSC"')
        assert pmids == ["38547890", "38123456", "37999999"]

    @respx.mock
    async def test_search_empty_results(self, client: PubMedClient) -> None:
        respx.get(f"{client.BASE_URL}/esearch.fcgi").mock(
            return_value=httpx.Response(200, content=ESEARCH_EMPTY)
        )
        pmids = await client.search("nonexistent query xyz")
        assert pmids == []

    @respx.mock
    async def test_search_sends_correct_params(self, client: PubMedClient) -> None:
        route = respx.get(f"{client.BASE_URL}/esearch.fcgi").mock(
            return_value=httpx.Response(200, content=ESEARCH_EMPTY)
        )
        await client.search('"LNP" AND "beta-thalassemia"', max_results=50)

        request = route.calls.last.request
        assert "term=%22LNP%22" in str(request.url)
        assert "retmax=50" in str(request.url)
        assert "api_key=test-key" in str(request.url)
        assert "email=test%40example.com" in str(request.url)


class TestFetchAbstract:
    """Test abstract/metadata fetching (efetch)."""

    @respx.mock
    async def test_fetch_parses_article(self, client: PubMedClient) -> None:
        respx.get(f"{client.BASE_URL}/efetch.fcgi").mock(
            return_value=httpx.Response(200, content=EFETCH_RESPONSE)
        )
        result = await client.fetch_abstract("38547890")

        assert result["pmid"] == "38547890"
        assert result["title"] == "In vivo base editing of HSCs via LNP delivery"
        assert result["journal"] == "Nature Biotechnology"
        assert result["doi"] == "10.1038/s41587-024-01234-5"
        assert result["authors"] == ["Zhang Yi", "Liu Xiao"]
        assert "BACKGROUND: Beta-thalassemia" in result["abstract"]
        assert "RESULTS: We achieved 45%" in result["abstract"]

    @respx.mock
    async def test_fetch_not_found(self, client: PubMedClient) -> None:
        empty = b'<?xml version="1.0"?><PubmedArticleSet/>'
        respx.get(f"{client.BASE_URL}/efetch.fcgi").mock(
            return_value=httpx.Response(200, content=empty)
        )
        result = await client.fetch_abstract("00000000")
        assert result["error"] == "Article not found"


class TestFetchAbstractsBatch:
    """Test batch abstract fetching."""

    @respx.mock
    async def test_batch_fetch(self, client: PubMedClient) -> None:
        respx.get(f"{client.BASE_URL}/efetch.fcgi").mock(
            return_value=httpx.Response(200, content=EFETCH_RESPONSE)
        )
        results = await client.fetch_abstracts_batch(["38547890"])
        assert len(results) == 1
        assert results[0]["title"] == "In vivo base editing of HSCs via LNP delivery"

    @respx.mock
    async def test_batch_empty_list(self, client: PubMedClient) -> None:
        results = await client.fetch_abstracts_batch([])
        assert results == []


class TestFetchFullText:
    """Test PMC full-text retrieval (elink + efetch)."""

    @respx.mock
    async def test_full_text_available(self, client: PubMedClient) -> None:
        # First call: elink to get PMC ID
        respx.get(f"{client.BASE_URL}/elink.fcgi").mock(
            return_value=httpx.Response(200, content=ELINK_WITH_PMC)
        )
        # Second call: efetch to get full text
        respx.get(f"{client.BASE_URL}/efetch.fcgi").mock(
            return_value=httpx.Response(200, content=PMC_FULL_TEXT)
        )

        text = await client.fetch_full_text("38547890")
        assert text is not None
        assert "LNP formulation details" in text

    @respx.mock
    async def test_full_text_not_in_pmc(self, client: PubMedClient) -> None:
        respx.get(f"{client.BASE_URL}/elink.fcgi").mock(
            return_value=httpx.Response(200, content=ELINK_NO_PMC)
        )

        text = await client.fetch_full_text("38547890")
        assert text is None


class TestRetryAndRateLimit:
    """Test retry logic and rate limiting."""

    @respx.mock
    async def test_retries_on_server_error(self, client: PubMedClient) -> None:
        route = respx.get(f"{client.BASE_URL}/esearch.fcgi")
        route.side_effect = [
            httpx.Response(503),
            httpx.Response(503),
            httpx.Response(200, content=ESEARCH_RESPONSE),
        ]

        pmids = await client.search("test query")
        assert len(pmids) == 3
        assert route.call_count == 3

    @respx.mock
    async def test_raises_after_max_retries(self, client: PubMedClient) -> None:
        respx.get(f"{client.BASE_URL}/esearch.fcgi").mock(
            return_value=httpx.Response(500)
        )

        with pytest.raises(httpx.HTTPStatusError):
            await client.search("test query")

    def test_rate_limit_with_api_key(self) -> None:
        c = PubMedClient(api_key="key")
        assert c._semaphore._value == 10

    def test_rate_limit_without_api_key(self) -> None:
        c = PubMedClient()
        assert c._semaphore._value == 3


class TestQueries:
    """Test the pre-configured search queries module."""

    def test_daily_queries_exist(self) -> None:
        from pubmed_agent.queries import DAILY_QUERIES

        assert len(DAILY_QUERIES) == 5
        assert any("hematopoietic stem cell" in q for q in DAILY_QUERIES)

    def test_weekly_queries_exist(self) -> None:
        from pubmed_agent.queries import WEEKLY_QUERIES

        assert len(WEEKLY_QUERIES) == 5

    def test_all_queries_combined(self) -> None:
        from pubmed_agent.queries import ALL_QUERIES, DAILY_QUERIES, MONTHLY_QUERIES, WEEKLY_QUERIES

        assert len(ALL_QUERIES) == len(DAILY_QUERIES) + len(WEEKLY_QUERIES) + len(MONTHLY_QUERIES)
