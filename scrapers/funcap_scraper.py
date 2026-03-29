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

        for article in soup.find_all("article", class_="post"):
            status_tag = article.find("span", class_="status")
            status = status_tag.get_text(strip=True).lower() if status_tag else ""

            if self.filters.get("status") and status != self.filters["status"]:
                continue

            link_tag = article.find("a", href=True)
            title_tag = article.find("h2")
            if link_tag and title_tag:
                opportunities.append({
                    "titulo": title_tag.get_text(strip=True),
                    "url": link_tag["href"],
                })

        logger.info(f"FUNCAP: {len(opportunities)} opportunidades abertas encontradas.")
        return opportunities

    async def get_documents(self, opportunity: dict) -> list[str]:
        await self._delay()
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(opportunity["url"])
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        content = soup.find("div", class_="entry-content")
        if not content:
            return []

        pdf_links = [
            a["href"]
            for a in content.find_all("a", href=True)
            if a["href"].lower().endswith(".pdf")
        ]
        return pdf_links