import pytest
import respx
import httpx
from scrapers.funcap_scraper import FUNCAPScraper
from config.sources import SOURCES

MOCK_HTML_LIST = """
<html><body>
  <h2>Editais Abertos</h2>
  <ul class="acesso">
    <li>
      <strong>MULHERES EMPREENDEDORAS - EDITAL 04/2026</strong>
      <ul>
        <li><a href="https://funcap.ce.gov.br/files/edital04-2026.pdf">Edital</a></li>
      </ul>
    </li>
  </ul>
  <h2>Editais Encerrados</h2>
  <ul class="acesso">
    <li>
      <strong>Edital Nº 08/2025 - Programa Centelha</strong>
      <ul>
        <li><a href="https://funcap.ce.gov.br/files/edital08-2025.pdf">Edital</a></li>
      </ul>
    </li>
  </ul>
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
    assert "2026" in opportunities[0]["titulo"]

@respx.mock
async def test_get_document_returns_pdfs(scraper):
    respx.get("https://funcap.ce.gov.br/edital/1").mock(
        return_value=httpx.Response(200, text="""
        <html><body>
          <div class="entry-content">
            <a href="https://funcap.ce.gov.br/files/edital.pdf">Baixar Edital</a>
          </div>
        </body></html>
        """)
    )
    opp = {"titulo": "Edital 2026", "url": "https://funcap.ce.gov.br/edital/1"}
    docs = await scraper.get_documents(opp)
    assert len(docs) == 1
    assert docs[0].endswith(".pdf")
