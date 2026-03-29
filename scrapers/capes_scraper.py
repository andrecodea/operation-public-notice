import logging
from playwright.async_api import async_playwright
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class CAPESScraper(BaseScraper):
    async def get_opportunities(self) -> list[dict]:
        years = [str(y) for y in self.filters.get("years", [2025, 2026])]
        opportunities = []

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(self.url, wait_until="networkidle")

            links = await page.query_selector_all("a[href]")
            for link in links:
                text = await link.inner_text()
                href = await link.get_attribute("href") or ""
                if any(year in text or year in href for year in years):
                    opportunities.append({"titulo": text.strip(), "url": href})
                

            await browser.close()

    async def get_documents(self, opportunity: dict) -> list[str]:
        url = opportunity["url"]
        if url.lower().endswith(".pdf"):
            return [url]
        
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(self.url, wait_until="networkidle")
            pdf_links = await page.eval_on_selector_all(
                "a[href$='.pdf']",
                "els => els.map(e => e.href)"
            )
            await browser.close()

        await self._delay()
        return pdf_links

        