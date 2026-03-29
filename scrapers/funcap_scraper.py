import logging
from urllib.parse import urljoin

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

        h2 = soup.find("h2", class_="titulo", string=lambda t: t and "aberto" in t.lower())
        if not h2:
            logger.warning("FUNCAP: seção 'Editais Abertos' não encontrada.")
            return []

        container = h2.find_next_sibling("div", class_="SistemasExternos")
        if not container:
            logger.warning("FUNCAP: div.SistemasExternos não encontrada.")
            return []

        opportunities = []
        current: dict | None = None

        for tag in container.find_all(["td", "ul"]):
            if tag.name == "td" and "laranja" in (tag.get("class") or []):
                span = tag.find("span")
                titulo = span.get_text(strip=True) if span else tag.get_text(strip=True)
                current = {"titulo": titulo, "url": self.url, "pdf_links": []}
                opportunities.append(current)

            elif tag.name == "ul" and "ListaDecorada" in (tag.get("class") or []):
                if current is None:
                    continue
                for a in tag.find_all("a", href=True):
                    href = a["href"]
                    if not href.startswith("http"):
                        href = urljoin(self.url, href)
                    if href.lower().endswith(".pdf"):
                        current["pdf_links"].append(href)

        logger.info(f"FUNCAP: {len(opportunities)} editais abertos encontrados.")
        return opportunities

    async def get_documents(self, opportunity: dict) -> list[str]:
        return opportunity.get("pdf_links", [])
