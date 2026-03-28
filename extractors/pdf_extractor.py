import io
import logging

import httpx
import pdfplumber

logger = logging.getLogger(__name__)

MAX_PAGES = 15
MAX_CHARS = 80_000 * 4 # ~80k tokens * 4 chars/token

async def extract_text_from_url(url: str) -> tuple[str, bool]:
    """Downloads PDF from a URL and extracts text. Returns (text: str, was_truncated: bool).
    """
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url)
        response.raise_for_status()
    return extract_text_from_bytes(response.content)

def extract_text_from_bytes(pdf_bytes: bytes) -> tuple[str, bool]:
    """Extract  text from PDF bytes. Returns (text: str, was_truncated: bool)."""
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        pages = pdf.pages
        texts: list[str] = []
        truncated = False

        for i, page in enumerate(pages):
            if i >= MAX_PAGES:
                truncated = True
                logger.warning(f"PDF truncado nas primeiras {MAX_PAGES} páginas (total: {len(pages)})")
                break
            
            text = page.extract_text() or ""
            texts.append(text)

            if sum(len(t) for t in texts) > MAX_CHARS:
                truncated = True
                logger.warning(f"PDF truncado nas primeiras {MAX_PAGES} páginas (total: {len(pages)})")
                break
        return ("\n\n".join(texts), truncated)

    