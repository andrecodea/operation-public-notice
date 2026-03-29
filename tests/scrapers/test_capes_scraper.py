import pytest
from unittest.mock import MagicMock, patch
from scrapers.capes_scraper import CAPESScraper
from config.sources import SOURCES


@pytest.fixture
def scraper():
    return CAPESScraper(SOURCES["capes"])


def _mock_fc_result(links: list[str], markdown: str = "") -> MagicMock:
    result = MagicMock()
    result.links = links
    result.markdown = markdown
    return result


async def test_get_opportunities_returns_internal_capes_links(scraper):
    mock_result = _mock_fc_result(links=[
        "https://www.gov.br/capes/pt-br/acesso-a-informacao/acoes-e-programas/bolsas/edital-2026",
        "https://www.gov.br/capes/pt-br/acesso-a-informacao/acoes-e-programas/bolsas/edital-2025",
        "https://www.gov.br/capes/pt-br/acesso-a-informacao/acoes-e-programas/resultado-2024",
        "https://external.site.com/irrelevante",
    ])
    mock_fc = MagicMock()
    mock_fc.scrape_url.return_value = mock_result
    scraper._fc_client = mock_fc

    opportunities = await scraper.get_opportunities()

    assert len(opportunities) >= 1
    assert all("gov.br/capes" in opp["url"] for opp in opportunities)


async def test_get_documents_finds_pdfs_on_edital_page(scraper):
    mock_result = _mock_fc_result(links=[
        "https://www.gov.br/capes/pt-br/centrais-de-conteudo/documentos/edital-2026.pdf",
        "https://www.gov.br/capes/pt-br/centrais-de-conteudo/documentos/anexo-2026.pdf",
        "https://www.gov.br/capes/pt-br/pagina-interna",
    ])
    mock_fc = MagicMock()
    mock_fc.scrape_url.return_value = mock_result
    scraper._fc_client = mock_fc

    opp = {"titulo": "Edital 2026", "url": "https://www.gov.br/capes/edital-2026"}
    docs = await scraper.get_documents(opp)

    assert len(docs) == 2
    assert all(d.endswith(".pdf") for d in docs)


async def test_get_documents_returns_url_directly_if_pdf(scraper):
    opp = {"titulo": "Edital", "url": "https://gov.br/edital.pdf"}
    docs = await scraper.get_documents(opp)
    assert docs == ["https://gov.br/edital.pdf"]


@pytest.mark.integration
async def test_integration_get_opportunities_real():
    scraper = CAPESScraper(SOURCES["capes"])
    opportunities = await scraper.get_opportunities()
    assert isinstance(opportunities, list)
