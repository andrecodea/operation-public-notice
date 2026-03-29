import logging
import httpx
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

BASE_URL = "https://www.fap.df.gov.br"

class FAPDFScraper(BaseScraper):
    async def get_opportunities(self) -> list[dict]:
        await self._delay()
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(self.url)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        opportunities = []

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/documents/d/fap/" not in href:
                continue
            titulo = a.get_text(strip=True)
            if not titulo:
                prev = a.find_previous("strong")
                titulo = prev.get_text(strip=True) if prev else href
            opportunities.append({"titulo": titulo, "url": href})

        logger.info(f"FAPDF: {len(opportunities)} editais encontrados.")
        return opportunities

    async def get_documents(self, opportunity: dict) -> list[str]:
        url = opportunity["url"]
        if url.startswith("http"):
            return [url]
        return [f"{BASE_URL}{url}"]
