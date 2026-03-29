import pytest 
from unittest.mock import AsyncMock, MagicMock, patch
from scrapers.fapdf_scraper import FAPDFScraper 
from config.sources import SOURCES

@pytest.fixture
def scraper():
    return FAPDFScraper(SOURCES["fapdf"])

async def test_get_opportunity_year_filter(scraper):
    """Playwright mock that returns two items, only one from 2026."""

    # edital mock de 2026
    mock_item_2026 = MagicMock()
    mock_item_2026.inner_text = AsyncMock(return_value="Edital FAPDF 2026")
    mock_item_2026.get_attribute = AsyncMock(return_value="https://fap.df.gov.br/edital/1")

    # edital mock de 2025
    mock_item_2025 = MagicMock()
    mock_item_2025.inner_text = AsyncMock(return_value="Edital FAPDF 2025")
    mock_item_2025.get_attribute = AsyncMock(return_value="https://fap.df.gov.br/edital/2")

    # página web mock
    mock_page = AsyncMock()
    mock_page.query_selector_all = AsyncMock(return_value=[mock_item_2026, mock_item_2025])
    mock_page.click = AsyncMock()
    mock_page.wait_for_selector = AsyncMock()

    with patch("scrapers.fapdf_scraper.async_playwright") as mock_pw:
        mock_pw.return_value.__aenter__ = AsyncMock(
            return_value=MagicMock(
                chromium=MagicMock(
                    launch=AsyncMock(
                        return_value=MagicMock(
                            new_page=AsyncMock(
                                return_value=mock_page), close=AsyncMock())
                                )
                            )
                        )
                    )
        opportunities = await scraper.get_opportunities()

    assert all("2026" in o["titulo"] for o in opportunities)

@pytest.mark.integration
async def test_integration_get_opportunities_real():
    """Real test against FAPDF. Run with: pytest -m integration"""
    scraper = FAPDFScraper(SOURCES["fapdf"])
    opportunities = await scraper.get_opportunities()
    assert isinstance(opportunities, list)
    assert len(opportunities) > 0
