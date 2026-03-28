"""Tests for right configurations of LLMConfig and SOURCES configuration objects"""

from config.settings import LLMConfig
from config.sources import SOURCES 

def test_llm_config_defaults():
    """Asserts that LLMConfig has the right configurations."""
    config = LLMConfig()
    assert config.primary_model == "gpt-4o"
    assert config.fallback_model == "claude-sonnet-4-5"
    assert config.correction_threshold == 0.6

def test_sources_has_three_sources():
    """Asserts that SOURCES dict has all three required sources."""
    assert set(SOURCES.keys()) == {"fapdf", "funcap", "capes"}

def test_sources_has_required_fields():
    """Asserts that the SOURCES dict have required items.
    
    Required items:
        url: website URL
        scraper: the scraper related to the source (URL)
        strategy: scraper's scraping strategy
    """
    for name, source in SOURCES.items():
        assert "url" in source, f"{name} sem URL"
        assert "scraper" in source, f"{name} sem scraper"
        assert "strategy" in source, f"{name} sem strategy"