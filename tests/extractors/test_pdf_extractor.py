import io
import pytest 
from unittest.mock import patch, MagicMock
from extractors.pdf_extractor import extract_text_from_bytes, MAX_PAGES

def _mock_pdf(n_pages: int, text_per_page: str = "texto da página") -> bytes:
    """Creates PDF mock with n pages."""
    mock_page = MagicMock()
    mock_page.extract_text.return_value = text_per_page

    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page] * n_pages
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)
    return mock_pdf

def test_extract_text_from_small_pdf():
    """Asserts that mock PDF is generated correctly and that truncation doesn't happen
    before MAX_PAGES."""
    mock_pdf = _mock_pdf(3)
    with patch("extractors.pdf_extractor.pdfplumber.open", return_value=mock_pdf):
        text, truncated = extract_text_from_bytes(b"fake_pdf")
    assert "texto da página" in text
    assert truncated is False

def test_truncates_in_max_pages():
    """Asserts truncation is True if the number of pages is equal to MAX_PAGES, and 
    Asserts that the text count (amount of text blocks) is equal to MAX_PAGES (one per page)."""
    mock_pdf = _mock_pdf(MAX_PAGES + 5)
    with patch("extractors.pdf_extractor.pdfplumber.open", return_value=mock_pdf):
        text, truncated = extract_text_from_bytes(b"fake_pdf")
    assert truncated is True
    assert text.count("texto da página") == MAX_PAGES

def test_page_with_no_text_becomes_empty_str():
    """Assert that pages with no texts become empty strings instead of None."""
    mock_page = MagicMock()
    mock_page.extract_text.return_value = None
    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)
    with patch("extractors.pdf_extractor.pdfplumber.open", return_value=mock_pdf):
        text, truncated = extract_text_from_bytes(b"fake_pdf")
    assert text == ""
    assert truncated is False

# To run: uv run pytest tests/extractors/test_pdf_extractor.py -v
# PASSED: 28/03/2026