"""Defines data source configurations."""

SOURCES: dict[str, dict] = {
    "fapdf": {
        "url": "https://www.fap.df.gov.br/",
        "scraper": "FAPDFScraper",
        "strategy": "playwright",
        "filters": {"year": 2026}
    },
    "funcap": {
        "url": "https://montenegro.funcap.ce.gov.br/sugba/editais-site-wordpress/",
        "scraper": "FUNCAPScraper",
        "strategy": "httpx",
        "filters": {"status": "aberto"}
    },
    "capes": {
        "url": "https://www.gov.br/capes/pt-br/assuntos/editais-e-resultados-capes",
        "scraper": "CAPESScraper",
        "strategy": "playwright",
        "filters": {"years": [2025, 2026]}
    }
}