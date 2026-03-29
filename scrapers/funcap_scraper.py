import logging
import httpx
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class FUNCAPScraper(BaseScraper):
    async def get_opportunities(self) -> list[dict]:
        await self._delay()
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(self.url)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        opportunities = []
        in_open_section = False

        for tag in soup.find_all(["h2", "li"]):
            if tag.name == "h2":
                in_open_section = "aberto" in tag.get_text(strip=True).lower()
                continue

            if not in_open_section:
                continue

            strong = tag.find("strong")
            if not strong:
                continue

            titulo = strong.get_text(strip=True)
            link = tag.find("a", href=True)
            url = link["href"] if link else self.url
            opportunities.append({"titulo": titulo, "url": url})

        logger.info(f"FUNCAP: {len(opportunities)} oportunidades abertas encontradas.")
        return opportunities

    async def get_documents(self, opportunity: dict) -> list[str]:
        url = opportunity["url"]
        if url.lower().endswith(".pdf"):
            return [url]

        await self._delay()
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        content = soup.find("div", class_="entry-content") or soup.body
        if not content:
            return []

        return [
            a["href"]
            for a in content.find_all("a", href=True)
            if a["href"].lower().endswith(".pdf")
        ]
