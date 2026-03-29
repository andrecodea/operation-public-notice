import pytest 
from unittest.mock import AsyncMock, MagicMock, patch
from scrapers.capes_scraper import CAPESScraper
from config.sources import SOURCES

@pytest.fixture
def scraper():
    return CAPESScraper(SOURCES["capes"])

async def test_get_opportunities_filters_by_year(scraper):
    # edital mock de 2026
    mock_link_2026 = MagicMock()
    mock_link_2026.inner_text = AsyncMock(return_value="Edital CAPES 2026")
    mock_link_2026.get_attribute = AsyncMock(return_value="https://gov.br/capes/edital/2026/1")

    # edital mock de 2024
    mock_link_2024 = MagicMock()
    mock_link_2026.inner_text = AsyncMock(return_value="Edital CAPES 2024")
    mock_link_2026.get_attribute = AsyncMock(return_value="https://gov.br/capes/edital/2024/1")

    # web page mock
    mock_page = AsyncMock()
    mock_page.query_selector_all = AsyncMock(return_value=[mock_link_2026, mock_link_2024])

    with patch("scrapers.capes_scraper.async_playwright") as mock_pw:
        mock_pw.return_value.__aenter__ = AsyncMock(
            return_value=MagicMock(
                chromium=MagicMock(launch=AsyncMock(return_value=MagicMock(
                    new_page = AsyncMock(return_value(mock_page), close=AsyncMock())
                )))
            )
        )
        opportunities = await scraper.get_opportunities()

    years = scraper.filters["years"]
    for opp in opportunities:
        assert any(str(y) in opp["titulo"] or str(y) in opp["url"] for y in years)

    @pytest.mark.integration
    async def test_integration_get_opportunities_real():
        scraper = CAPESScraper(SOURCES["capes"])
        opportunities = await scraper.get_opportunities()
        assert isinstance(opportunities, list)