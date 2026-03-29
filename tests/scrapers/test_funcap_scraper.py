import pytest 
import respx
import httpx
from scrapers.funcap_scraper import FUNCAPScraper
from config.sources import SOURCES

MOCK_HTML_LIST = """
<html>
<body>
    <article class="post">
        <h2><a href="https://funcap.ce.gov.br/edital/1">Chamada Universal 2026</a></h2>
        <span class="status">aberto</span>
    </article>
    <article class="post">
        <h2><a href="https://funcap.ce.gov.br/edital/2">Edital Fechado</a></h2>
        <span class="status">encerrado</span>
    </article>
</body></html>
"""

MOCK_HTML_EDITAL = """
<html><body>
    <div class="entry-content">
        <a href="https://funcap.ce.gov.br/files/edital.pdf">Baixar Edital</a>
    </div>
</body></html>
"""

@pytest.fixture
def scraper():
    return FUNCAPScraper(SOURCES["funcap"])

@respx.mock 
async def test_get_opportunities_only_open_ones(scraper):
    respx.get(SOURCES["funcap"]["url"]).mock(
        return_value=httpx.Response(200, text=MOCK_HTML_LIST)
    )
    opportunities = await scraper.get_opportunities()
    assert len(opportunities) == 1
    assert opportunities[0]["titulo"] == "Chamada Universal 2026"

@respx.mock
async def test_get_document_returns_pdfs(scraper):
    respx.get("https://funcap.ce.gov.br/edital/1").mock(
        return_value=httpx.Response(200, text=MOCK_HTML_EDITAL)
    )
    opp = {"titulo": "Chamada Universal 2026", "url": "https://funcap.ce.gov.br/edital/1"}
    docs = await scraper.get_documents(opp)
    assert len(docs) == 1
    assert docs[0].endswith(".pdf")

# Pra rodar: uv run pytest tests/scrapers/test_funcap_scraper.py -v