import asyncio
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    def __init__(self, config: dict):
        self.config = config
        self.url = config["url"]
        self.filters = config.get("filters", {})
    
    # implementações abstratas
    @abstractmethod
    async def get_opportunities(self) -> list[dict]:
        """Returns list of opportunities with `titulo` and `url`."""
        ...

    @abstractmethod
    async def get_documents(self, opportunity: dict) -> list[str]:
        """Returns an opportunity's relevant PDF URLs"""
        ...
    
    # implementação concreta
    async def _delay(self):
        """Respects robots.txt with request delay"""
        await asyncio.sleep(1.5)