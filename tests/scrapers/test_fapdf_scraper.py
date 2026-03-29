import pytest
import respx
import httpx
from scrapers.fapdf_scraper import FAPDFScraper
from config.sources import SOURCES

MOCK_HTML = """
<html><body>
  <p><strong>EDITAL 01/2026 FAPDF PUBLICA</strong><br>
    <a href="/documents/d/fap/edital-n-01-2026-fapdf-publica-pdf">Baixar PDF</a>
  </p>
  <p><strong>EDITAL 02/2026 FAPDF PARTICIPA</strong><br>
    <a href="/documents/d/fap/edital-n-02-2026-fapdf-participa-pdf">Baixar PDF</a>
  </p>
  <p><a href="/documentos/outros/link-irrelevante">Link irrelevante</a></p>
</body></html>
"""

@pytest.fixture
def scraper():
    return FAPDFScraper(SOURCES["fapdf"])

@respx.mock
async def test_get_opportunities_returns_pdf_links(scraper):
    respx.get(SOURCES["fapdf"]["url"]).mock(
        return_value=httpx.Response(200, text=MOCK_HTML)
    )
    opportunities = await scraper.get_opportunities()
    assert len(opportunities) == 2
    assert all("/documents/d/fap/" in opp["url"] for opp in opportunities)
    assert opportunities[0]["titulo"] != ""

@respx.mock
async def test_get_documents_returns_full_url(scraper):
    opp = {"titulo": "EDITAL 01/2026", "url": "/documents/d/fap/edital-n-01-2026-pdf"}
    docs = await scraper.get_documents(opp)
    assert len(docs) == 1
    assert docs[0].startswith("https://www.fap.df.gov.br")

async def test_get_documents_returns_absolute_url_unchanged(scraper):
    opp = {"titulo": "EDITAL 01/2026", "url": "https://www.fap.df.gov.br/documents/d/fap/edital-n-01-2026-pdf"}
    docs = await scraper.get_documents(opp)
    assert docs[0] == opp["url"]

@pytest.mark.integration
async def test_integration_get_opportunities_real():
    scraper = FAPDFScraper(SOURCES["fapdf"])
    opportunities = await scraper.get_opportunities()
    assert isinstance(opportunities, list)
    assert len(opportunities) > 0
