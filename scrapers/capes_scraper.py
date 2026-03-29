import logging
import os
from firecrawl import AsyncFirecrawlApp
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

CAPES_BASE = "https://www.gov.br/capes"
SKIP_PATHS = ["/resultados-", "/resultados-anteriores"]


class CAPESScraper(BaseScraper):
    @property
    def fc(self) -> AsyncFirecrawlApp:
        if not hasattr(self, "_fc_client"):
            self._fc_client = AsyncFirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))
        return self._fc_client

    async def get_opportunities(self) -> list[dict]:
        await self._delay()
        result = await self.fc.scrape(self.url, formats=["links"])
        links = result.links or []

        opportunities = []
        seen = set()
        for link in links:
            if CAPES_BASE not in link:
                continue
            if any(skip in link for skip in SKIP_PATHS):
                continue
            if link in seen:
                continue
            seen.add(link)
            titulo = link.rstrip("/").split("/")[-1].replace("-", " ").title()
            opportunities.append({"titulo": titulo, "url": link})

        logger.info(f"CAPES: {len(opportunities)} oportunidades encontradas.")
        return opportunities

    async def get_documents(self, opportunity: dict) -> list[str]:
        url = opportunity["url"]
        if url.lower().endswith(".pdf"):
            return [url]

        await self._delay()
        result = await self.fc.scrape(url, formats=["links"])
        links = result.links or []

        pdfs = [link for link in links if link.lower().endswith(".pdf")]
        logger.info(f"CAPES: {len(pdfs)} PDFs encontrados em {url}")
        return pdfs
