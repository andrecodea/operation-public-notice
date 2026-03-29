import logging
from playwright.async_api import async_playwright
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class FAPDFScraper(BaseScraper):
    async def get_opportunities(self) -> list[dict]:
        year = str(self.filters.get("year", 2026))
        opportunities = []

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(self.url, wait_until="networkidle")

            try:
                year_selector = f"text={year}"
                await page.click(year_selector)
                await page.wait_for_selector(".accordion-content", timeout=5000)
            except Exception:
                logger.warning(f"FAPDF: accordion do ano {year} não encontrado")

            # coletar links de editais visíveis
            items = await page.query_selector_all("a[href*='edital'], a[href*='.pdf']")
            for item in items:
                text = await item.inner_text()
                href = await item.get_attribute("href")
                if href and year in text:
                    opportunities.append({"titulo": text.strip(), "url": href})
                    
            await browser.close()
        
        await self._delay()
        logger.info(f"FAPDF: {len(opportunities)} oportunidades de {year} encontradas")
        return opportunities
    
    async def get_documents(self, opportunity: dict) -> list[str]:
        url = opportunity["url"]

        # pdfs da fapdf geralmente são linkados diretamente
        if url.lower().endswith(".pdf"):
            return [url]

        # caso seja uma página, busca pdfs nela
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(self.url, wait_until="networkidle")
            links = await page.eval_on_selector_all(
                "a[href$='.pdf']",
                "els => els.map(e => e.href)"
            )
            await browser.close()
        
        await self._delay()
        return links