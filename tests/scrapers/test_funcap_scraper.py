import pytest
import respx
import httpx
from scrapers.funcap_scraper import FUNCAPScraper
from config.sources import SOURCES

BASE_URL = SOURCES["funcap"]["url"]

MOCK_HTML = """
<html><body>
  <h2 class="titulo">Editais Abertos</h2>
  <div class="SistemasExternos">
    <table>
      <tbody>
        <tr><td class="laranja" colspan="2"><span>MULHERES EMPREENDEDORAS - EDITAL 04/2026</span></td></tr>
      </tbody>
      <tr><td><ul class="ListaDecorada">
        <li><a href="../edital/781.pdf">Edital 04/2026</a></li>
      </ul></td></tr>
      <tbody>
        <tr><td class="laranja" colspan="2"><span>Edital Nº 08/2025 - Programa Centelha</span></td></tr>
      </tbody>
      <tr><td><ul class="ListaDecorada">
        <li><a href="../edital/768.pdf">Edital 08/2025</a></li>
      </ul></td></tr>
    </table>
  </div>
</body></html>
"""


@pytest.fixture
def scraper():
    return FUNCAPScraper(SOURCES["funcap"])


@respx.mock
async def test_get_opportunities_returns_open_editais(scraper):
    respx.get(BASE_URL).mock(return_value=httpx.Response(200, text=MOCK_HTML))
    opportunities = await scraper.get_opportunities()
    assert len(opportunities) == 2
    assert all("url" in o and "pdf_links" in o for o in opportunities)
    assert "2026" in opportunities[0]["titulo"]


@respx.mock
async def test_get_opportunities_resolves_pdf_urls(scraper):
    respx.get(BASE_URL).mock(return_value=httpx.Response(200, text=MOCK_HTML))
    opportunities = await scraper.get_opportunities()
    pdfs = opportunities[0]["pdf_links"]
    assert len(pdfs) == 1
    assert pdfs[0].startswith("http")
    assert pdfs[0].endswith(".pdf")


async def test_get_documents_returns_pdf_links(scraper):
    opp = {"titulo": "Edital 2026", "url": BASE_URL, "pdf_links": [
        "https://montenegro.funcap.ce.gov.br/sugba/edital/781.pdf"
    ]}
    docs = await scraper.get_documents(opp)
    assert docs == ["https://montenegro.funcap.ce.gov.br/sugba/edital/781.pdf"]


async def test_get_documents_returns_empty_when_no_pdfs(scraper):
    opp = {"titulo": "Edital sem PDF", "url": BASE_URL, "pdf_links": []}
    docs = await scraper.get_documents(opp)
    assert docs == []
