import pytest
from unittest.mock import AsyncMock, MagicMock
from scrapers.capes_scraper import CAPESScraper
from config.sources import SOURCES


@pytest.fixture
def scraper():
    return CAPESScraper(SOURCES["capes"])


def _mock_fc(links: list[str]) -> MagicMock:
    result = MagicMock()
    result.links = links
    fc = MagicMock()
    fc.scrape = AsyncMock(return_value=result)
    return fc


async def test_get_opportunities_returns_internal_capes_links(scraper):
    scraper._fc_client = _mock_fc(links=[
        "https://www.gov.br/capes/pt-br/acesso-a-informacao/acoes-e-programas/bolsas/edital-2026",
        "https://www.gov.br/capes/pt-br/acesso-a-informacao/acoes-e-programas/bolsas/edital-2025",
        "https://external.site.com/irrelevante",
    ])

    opportunities = await scraper.get_opportunities()

    assert len(opportunities) == 2
    assert all("gov.br/capes" in opp["url"] for opp in opportunities)


async def test_get_opportunities_skips_resultados(scraper):
    scraper._fc_client = _mock_fc(links=[
        "https://www.gov.br/capes/pt-br/assuntos/editais-e-resultados-capes/resultados-2026",
        "https://www.gov.br/capes/pt-br/acesso-a-informacao/acoes-e-programas/bolsas/edital-2026",
    ])

    opportunities = await scraper.get_opportunities()

    assert len(opportunities) == 1
    assert "edital-2026" in opportunities[0]["url"]


async def test_get_documents_finds_pdfs_on_edital_page(scraper):
    scraper._fc_client = _mock_fc(links=[
        "https://www.gov.br/capes/pt-br/centrais-de-conteudo/documentos/edital-2026.pdf",
        "https://www.gov.br/capes/pt-br/centrais-de-conteudo/documentos/anexo-2026.pdf",
        "https://www.gov.br/capes/pt-br/pagina-interna",
    ])

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
