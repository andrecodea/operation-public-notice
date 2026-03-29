# Scraper Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Corrigir os três scrapers para funcionar com as páginas reais de produção, substituindo Playwright por httpx+BS4 no FAPDF e por Firecrawl no CAPES.

**Architecture:** Cada scraper é reescrito de forma independente. A interface `BaseScraper` (`get_opportunities` / `get_documents`) não muda — só a implementação interna. `config/sources.py` recebe URLs e parâmetros atualizados.

**Tech Stack:** httpx, BeautifulSoup4 (FAPDF + FUNCAP), firecrawl-py (CAPES), pydantic, pytest, respx, openai streaming, anthropic streaming

---

## Contexto e Motivação

Detectado na primeira execução com URLs reais (2026-03-29):

| Fonte  | Problema                                                              | Decisão                    |
|--------|-----------------------------------------------------------------------|----------------------------|
| FAPDF  | Accordion JS inexistente; URL real é `/editais-fapdf-20261`           | httpx + BS4, URL corrigida |
| FUNCAP | Seletores errados (`article.post` vs `ul/li.acesso`)                  | httpx + BS4, seletores fixos |
| CAPES  | `get_documents()` navegava para `self.url`; JS pesado dificulta seletores | Firecrawl                  |

Detalhes em `docs/erros-e-correcoes.md` itens 8 e 9.

---

## Estrutura de Arquivos

```
config/
└── sources.py              ← MODIFICAR: URLs e filtros atualizados

scrapers/
├── fapdf_scraper.py        ← REESCREVER: httpx + BS4
├── funcap_scraper.py       ← MODIFICAR: corrigir seletores
└── capes_scraper.py        ← REESCREVER: Firecrawl

tests/scrapers/
├── test_fapdf_scraper.py   ← REESCREVER: adaptar mocks ao novo scraper
├── test_funcap_scraper.py  ← MODIFICAR: ajustar HTML mock
└── test_capes_scraper.py   ← REESCREVER: mockar Firecrawl

pyproject.toml              ← MODIFICAR: adicionar firecrawl-py
```

---

## Task 1 — Atualizar `config/sources.py` e adicionar `firecrawl-py`

**Files:**
- Modify: `config/sources.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Atualizar sources.py**

```python
SOURCES: dict[str, dict] = {
    "fapdf": {
        "url": "https://www.fap.df.gov.br/editais-fapdf-20261",
        "scraper": "FAPDFScraper",
        "strategy": "httpx",
        "filters": {"year": "2026"}
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
        "strategy": "firecrawl",
        "filters": {}
    }
}
```

- [ ] **Step 2: Adicionar firecrawl-py ao pyproject.toml**

Adicionar em `dependencies`:
```toml
"firecrawl-py>=1.0.0",
```

- [ ] **Step 3: Instalar**

```bash
uv sync
```

Expected: firecrawl-py instalado sem erros.

- [ ] **Step 4: Verificar que testes de config ainda passam**

```bash
uv run pytest tests/test_config.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add config/sources.py pyproject.toml uv.lock
git commit -m "feat: update sources config and add firecrawl-py dependency"
```

---

## Task 2 — Reescrever `FAPDFScraper`

**Files:**
- Modify: `scrapers/fapdf_scraper.py`
- Modify: `tests/scrapers/test_fapdf_scraper.py`

A página `https://www.fap.df.gov.br/editais-fapdf-20261` lista editais como links `<a>` com href no padrão `/documents/d/fap/`. Esses links são os PDFs diretamente.

- [ ] **Step 1: Escrever o teste**

```python
# tests/scrapers/test_fapdf_scraper.py
import pytest
import respx
import httpx
from scrapers.fapdf_scraper import FAPDFScraper
from config.sources import SOURCES

MOCK_HTML = """
<html><body>
  <p><strong>EDITAL 01/2026 FAPDF PUBLICA</strong><br>
    <a href="/documents/d/fap/edital-n-01-2026-fapdf-publica-pdf">Baixar PDF</a>
  </p>
  <p><strong>EDITAL 02/2026 FAPDF PARTICIPA</strong><br>
    <a href="/documents/d/fap/edital-n-02-2026-fapdf-participa-pdf">Baixar PDF</a>
  </p>
  <p><a href="/documentos/outros/link-irrelevante">Link irrelevante</a></p>
</body></html>
"""

@pytest.fixture
def scraper():
    return FAPDFScraper(SOURCES["fapdf"])

@respx.mock
async def test_get_opportunities_returns_pdf_links(scraper):
    respx.get(SOURCES["fapdf"]["url"]).mock(
        return_value=httpx.Response(200, text=MOCK_HTML)
    )
    opportunities = await scraper.get_opportunities()
    assert len(opportunities) == 2
    assert all("/documents/d/fap/" in opp["url"] for opp in opportunities)
    assert opportunities[0]["titulo"] != ""

@respx.mock
async def test_get_documents_returns_full_url(scraper):
    opp = {"titulo": "EDITAL 01/2026", "url": "/documents/d/fap/edital-n-01-2026-pdf"}
    docs = await scraper.get_documents(opp)
    assert len(docs) == 1
    assert docs[0].startswith("https://www.fap.df.gov.br")

@respx.mock
async def test_get_documents_returns_absolute_url_unchanged(scraper):
    opp = {"titulo": "EDITAL 01/2026", "url": "https://www.fap.df.gov.br/documents/d/fap/edital-n-01-2026-pdf"}
    docs = await scraper.get_documents(opp)
    assert docs[0] == opp["url"]
```

- [ ] **Step 2: Rodar para confirmar falha**

```bash
uv run pytest tests/scrapers/test_fapdf_scraper.py -v
```

Expected: FAIL (ImportError ou AssertionError).

- [ ] **Step 3: Reescrever `fapdf_scraper.py`**

```python
import logging
import httpx
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

BASE_URL = "https://www.fap.df.gov.br"

class FAPDFScraper(BaseScraper):
    async def get_opportunities(self) -> list[dict]:
        await self._delay()
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(self.url)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        opportunities = []

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/documents/d/fap/" not in href:
                continue
            titulo = a.get_text(strip=True) or a.find_previous("strong", string=True)
            if hasattr(titulo, "get_text"):
                titulo = titulo.get_text(strip=True)
            opportunities.append({"titulo": str(titulo), "url": href})

        logger.info(f"FAPDF: {len(opportunities)} editais encontrados.")
        return opportunities

    async def get_documents(self, opportunity: dict) -> list[str]:
        url = opportunity["url"]
        if url.startswith("http"):
            return [url]
        return [f"{BASE_URL}{url}"]
```

- [ ] **Step 4: Rodar para confirmar aprovação**

```bash
uv run pytest tests/scrapers/test_fapdf_scraper.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add scrapers/fapdf_scraper.py tests/scrapers/test_fapdf_scraper.py
git commit -m "fix: rewrite FAPDFScraper with httpx+BS4 and correct URL"
```

---

## Task 3 — Corrigir seletores do `FUNCAPScraper`

**Files:**
- Modify: `scrapers/funcap_scraper.py`
- Modify: `tests/scrapers/test_funcap_scraper.py`

A página usa `<ul>/<li>` com seções "Editais Abertos" e "Editais Encerrados". Links apontam para PDFs ou para Plataforma Montenegro.

- [ ] **Step 1: Atualizar HTML mock do teste**

```python
# tests/scrapers/test_funcap_scraper.py
import pytest
import respx
import httpx
from scrapers.funcap_scraper import FUNCAPScraper
from config.sources import SOURCES

MOCK_HTML_LIST = """
<html><body>
  <h2>Editais Abertos</h2>
  <ul class="acesso">
    <li>
      <strong>MULHERES EMPREENDEDORAS - EDITAL 04/2026</strong>
      <ul>
        <li><a href="https://funcap.ce.gov.br/files/edital04-2026.pdf">Edital</a></li>
      </ul>
    </li>
  </ul>
  <h2>Editais Encerrados</h2>
  <ul class="acesso">
    <li>
      <strong>Edital Nº 08/2025 - Programa Centelha</strong>
      <ul>
        <li><a href="https://funcap.ce.gov.br/files/edital08-2025.pdf">Edital</a></li>
      </ul>
    </li>
  </ul>
</body></html>
"""

@pytest.fixture
def scraper():
    return FUNCAPScraper(SOURCES["funcap"])

@respx.mock
async def test_get_opportunities_only_open_ones(scraper):
    respx.get(SOURCES["funcap"]["url"]).mock(
        return_value=httpx.Response(200, text=MOCK_HTML_LIST)
    )
    opportunities = await scraper.get_opportunities()
    assert len(opportunities) == 1
    assert "2026" in opportunities[0]["titulo"]

@respx.mock
async def test_get_document_returns_pdfs(scraper):
    respx.get("https://funcap.ce.gov.br/edital/1").mock(
        return_value=httpx.Response(200, text="""
        <html><body>
          <div class="entry-content">
            <a href="https://funcap.ce.gov.br/files/edital.pdf">Baixar Edital</a>
          </div>
        </body></html>
        """)
    )
    opp = {"titulo": "Edital 2026", "url": "https://funcap.ce.gov.br/edital/1"}
    docs = await scraper.get_documents(opp)
    assert len(docs) == 1
    assert docs[0].endswith(".pdf")
```

- [ ] **Step 2: Rodar para confirmar falha**

```bash
uv run pytest tests/scrapers/test_funcap_scraper.py -v
```

Expected: `test_get_opportunities_only_open_ones` FAIL (0 oportunidades com seletores atuais).

- [ ] **Step 3: Corrigir `funcap_scraper.py`**

```python
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
        in_open_section = False

        for tag in soup.find_all(["h2", "li"]):
            if tag.name == "h2":
                text = tag.get_text(strip=True).lower()
                in_open_section = "aberto" in text
                continue

            if not in_open_section:
                continue

            strong = tag.find("strong")
            if not strong:
                continue

            titulo = strong.get_text(strip=True)
            link = tag.find("a", href=True)
            url = link["href"] if link else self.url
            opportunities.append({"titulo": titulo, "url": url})

        logger.info(f"FUNCAP: {len(opportunities)} oportunidades abertas encontradas.")
        return opportunities

    async def get_documents(self, opportunity: dict) -> list[str]:
        url = opportunity["url"]
        if url.lower().endswith(".pdf"):
            return [url]

        await self._delay()
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        content = soup.find("div", class_="entry-content") or soup.body
        if not content:
            return []

        return [
            a["href"]
            for a in content.find_all("a", href=True)
            if a["href"].lower().endswith(".pdf")
        ]
```

- [ ] **Step 4: Rodar para confirmar aprovação**

```bash
uv run pytest tests/scrapers/test_funcap_scraper.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add scrapers/funcap_scraper.py tests/scrapers/test_funcap_scraper.py
git commit -m "fix: update FUNCAPScraper selectors to match current HTML structure"
```

---

## Task 4 — Reescrever `CAPESScraper` com Firecrawl

**Files:**
- Modify: `scrapers/capes_scraper.py`
- Modify: `tests/scrapers/test_capes_scraper.py`

Firecrawl retorna `markdown` (texto limpo) e `links` (lista de todos os hrefs da página). `get_opportunities()` usa o listing principal. `get_documents()` usa Firecrawl em cada página de edital para encontrar PDFs.

- [ ] **Step 1: Escrever o teste**

```python
# tests/scrapers/test_capes_scraper.py
import pytest
from unittest.mock import MagicMock, patch
from scrapers.capes_scraper import CAPESScraper
from config.sources import SOURCES

@pytest.fixture
def scraper():
    return CAPESScraper(SOURCES["capes"])

def _mock_fc_result(links: list[str], markdown: str = "") -> MagicMock:
    result = MagicMock()
    result.links = links
    result.markdown = markdown
    return result

async def test_get_opportunities_returns_internal_capes_links(scraper):
    mock_result = _mock_fc_result(links=[
        "https://www.gov.br/capes/pt-br/acesso-a-informacao/acoes-e-programas/bolsas/edital-2026",
        "https://www.gov.br/capes/pt-br/acesso-a-informacao/acoes-e-programas/bolsas/edital-2025",
        "https://www.gov.br/capes/pt-br/acesso-a-informacao/acoes-e-programas/resultado-2024",
        "https://external.site.com/irrelevante",
    ])

    with patch("scrapers.capes_scraper.FirecrawlApp") as MockFC:
        MockFC.return_value.scrape_url.return_value = mock_result
        opportunities = await scraper.get_opportunities()

    assert len(opportunities) == 2
    assert all("gov.br/capes" in opp["url"] for opp in opportunities)

async def test_get_documents_finds_pdfs_on_edital_page(scraper):
    mock_result = _mock_fc_result(links=[
        "https://www.gov.br/capes/pt-br/centrais-de-conteudo/documentos/edital-2026.pdf",
        "https://www.gov.br/capes/pt-br/centrais-de-conteudo/documentos/anexo-2026.pdf",
        "https://www.gov.br/capes/pt-br/pagina-interna",
    ])

    with patch("scrapers.capes_scraper.FirecrawlApp") as MockFC:
        MockFC.return_value.scrape_url.return_value = mock_result
        opp = {"titulo": "Edital 2026", "url": "https://www.gov.br/capes/edital-2026"}
        docs = await scraper.get_documents(opp)

    assert len(docs) == 2
    assert all(d.endswith(".pdf") for d in docs)

async def test_get_documents_returns_url_directly_if_pdf(scraper):
    opp = {"titulo": "Edital", "url": "https://gov.br/edital.pdf"}
    docs = await scraper.get_documents(opp)
    assert docs == ["https://gov.br/edital.pdf"]

@pytest.mark.integration
async def test_integration_get_opportunities_real():
    scraper = CAPESScraper(SOURCES["capes"])
    opportunities = await scraper.get_opportunities()
    assert isinstance(opportunities, list)
```

- [ ] **Step 2: Rodar para confirmar falha**

```bash
uv run pytest tests/scrapers/test_capes_scraper.py -v -m "not integration"
```

Expected: FAIL (ImportError — FirecrawlApp não existe no scraper atual).

- [ ] **Step 3: Reescrever `capes_scraper.py`**

```python
import logging
import os
from firecrawl import FirecrawlApp
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

CAPES_BASE = "https://www.gov.br/capes"

class CAPESScraper(BaseScraper):
    def __init__(self, config: dict):
        super().__init__(config)
        self._fc = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))

    async def get_opportunities(self) -> list[dict]:
        await self._delay()
        result = self._fc.scrape_url(self.url, params={"formats": ["links"]})
        links = result.links or []

        opportunities = []
        for link in links:
            if CAPES_BASE not in link:
                continue
            if any(skip in link for skip in ["/pt-br/assuntos/editais", "/acesso-a-informacao/institucional"]):
                continue
            titulo = link.rstrip("/").split("/")[-1].replace("-", " ").title()
            opportunities.append({"titulo": titulo, "url": link})

        logger.info(f"CAPES: {len(opportunities)} oportunidades encontradas.")
        return opportunities

    async def get_documents(self, opportunity: dict) -> list[str]:
        url = opportunity["url"]
        if url.lower().endswith(".pdf"):
            return [url]

        await self._delay()
        result = self._fc.scrape_url(url, params={"formats": ["links"]})
        links = result.links or []

        pdfs = [link for link in links if link.lower().endswith(".pdf")]
        logger.info(f"CAPES: {len(pdfs)} PDFs encontrados em {url}")
        return pdfs
```

- [ ] **Step 4: Rodar para confirmar aprovação**

```bash
uv run pytest tests/scrapers/test_capes_scraper.py -v -m "not integration"
```

Expected: 3 passed, 1 deselected.

- [ ] **Step 5: Commit**

```bash
git add scrapers/capes_scraper.py tests/scrapers/test_capes_scraper.py
git commit -m "fix: rewrite CAPESScraper using Firecrawl instead of Playwright"
```

---

## Task 5 — Observabilidade LLM: tokens, latência e TTFT

**Files:**
- Create: `providers/metrics.py`
- Modify: `providers/openai_provider.py`
- Modify: `providers/claude_provider.py`
- Modify: `tests/providers/test_providers.py`

**Motivação:** Cada chamada LLM agora emite um log estruturado com tokens consumidos, latência total e TTFT (time to first token). TTFT exige streaming — ambos os providers são migrados de completion síncrona para streaming interno; a interface `complete(messages) -> str` não muda.

**Por que TTFT importa:** TTFT mede o tempo até o modelo começar a responder — indica qualidade de alocação de GPU no provider. Latência total inclui geração completa. Juntos permitem diagnosticar se o gargalo é enfileiramento ou geração.

**Formato do log:**
```
INFO llm_metrics {"provider": "openai", "model": "gpt-4o", "prompt_tokens": 1234,
  "completion_tokens": 312, "total_tokens": 1546, "latency_ms": 4210.3, "ttft_ms": 890.1}
```

- [ ] **Step 1: Criar `providers/metrics.py`**

```python
import json
from dataclasses import dataclass

@dataclass
class LLMCallMetrics:
    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: float = 0.0
    ttft_ms: float | None = None

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def to_log_dict(self) -> dict:
        return {
            "provider": self.provider,
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "latency_ms": round(self.latency_ms, 1),
            "ttft_ms": round(self.ttft_ms, 1) if self.ttft_ms is not None else None,
        }
```

- [ ] **Step 2: Escrever testes de métricas**

```python
# acrescentar em tests/providers/test_providers.py
from providers.metrics import LLMCallMetrics

def test_metrics_total_tokens():
    m = LLMCallMetrics(provider="openai", model="gpt-4o", prompt_tokens=100, completion_tokens=50)
    assert m.total_tokens == 150

def test_metrics_to_log_dict_rounds_floats():
    m = LLMCallMetrics(provider="openai", model="gpt-4o",
                       latency_ms=1234.5678, ttft_ms=432.1)
    d = m.to_log_dict()
    assert d["latency_ms"] == 1234.6
    assert d["ttft_ms"] == 432.1

def test_metrics_ttft_none_stays_none():
    m = LLMCallMetrics(provider="openai", model="gpt-4o")
    assert m.to_log_dict()["ttft_ms"] is None
```

- [ ] **Step 3: Rodar para confirmar falha**

```bash
uv run pytest tests/providers/test_providers.py -v -k "metrics"
```

Expected: FAIL (`ModuleNotFoundError` ou similar).

- [ ] **Step 4: Criar o arquivo e confirmar aprovação**

```bash
uv run pytest tests/providers/test_providers.py -v -k "metrics"
```

Expected: 3 passed.

- [ ] **Step 5: Migrar `openai_provider.py` para streaming com métricas**

```python
import time
import json
import logging
from openai import AsyncOpenAI
from providers.base import LLMProvider
from providers.metrics import LLMCallMetrics
from config.settings import LLMConfig

logger = logging.getLogger(__name__)

class OpenAIProvider(LLMProvider):
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = AsyncOpenAI()

    async def complete(self, messages: list[dict]) -> str:
        start = time.perf_counter()
        ttft_ms = None
        chunks: list[str] = []
        prompt_tokens = 0
        completion_tokens = 0

        stream = await self.client.chat.completions.create(
            model=self.config.primary_model,
            messages=messages,
            timeout=self.config.timeout_seconds,
            stream=True,
            stream_options={"include_usage": True},
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                if ttft_ms is None:
                    ttft_ms = (time.perf_counter() - start) * 1000
                chunks.append(chunk.choices[0].delta.content)
            if chunk.usage:
                prompt_tokens = chunk.usage.prompt_tokens
                completion_tokens = chunk.usage.completion_tokens

        metrics = LLMCallMetrics(
            provider="openai",
            model=self.config.primary_model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=(time.perf_counter() - start) * 1000,
            ttft_ms=ttft_ms,
        )
        logger.info("llm_metrics %s", json.dumps(metrics.to_log_dict()))
        return "".join(chunks)
```

- [ ] **Step 6: Migrar `claude_provider.py` para streaming com métricas**

```python
import time
import json
import logging
from anthropic import AsyncAnthropic
from providers.base import LLMProvider
from providers.metrics import LLMCallMetrics
from config.settings import LLMConfig

logger = logging.getLogger(__name__)

class ClaudeProvider(LLMProvider):
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = AsyncAnthropic()

    async def complete(self, messages: list[dict]) -> str:
        system = next((m["content"] for m in messages if m["role"] == "system"), None)
        user_messages = [m for m in messages if m["role"] != "system"]

        kwargs: dict = {
            "model": self.config.fallback_model,
            "max_tokens": 4096,
            "messages": user_messages,
        }
        if system:
            kwargs["system"] = system

        start = time.perf_counter()
        ttft_ms = None
        chunks: list[str] = []

        async with self.client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                if ttft_ms is None and text:
                    ttft_ms = (time.perf_counter() - start) * 1000
                chunks.append(text)
            final = await stream.get_final_message()

        metrics = LLMCallMetrics(
            provider="anthropic",
            model=self.config.fallback_model,
            prompt_tokens=final.usage.input_tokens,
            completion_tokens=final.usage.output_tokens,
            latency_ms=(time.perf_counter() - start) * 1000,
            ttft_ms=ttft_ms,
        )
        logger.info("llm_metrics %s", json.dumps(metrics.to_log_dict()))
        return "".join(chunks)
```

- [ ] **Step 7: Atualizar mocks dos testes de providers existentes**

Os testes existentes mockam `client.chat.completions.create` para retornar um objeto síncrono. Com streaming precisam retornar um async iterator. Substituir o mock de `complete()` diretamente é mais simples:

```python
# tests/providers/test_providers.py — atualizar os testes existentes
# Mockar complete() diretamente em vez do client interno

async def test_use_openai_when_available(mocker):
    mocker.patch("providers.openai_provider.OpenAIProvider.complete",
                 new=AsyncMock(return_value="resposta openai"))
    result = await complete_with_fallback([{"role": "user", "content": "teste"}], LLMConfig())
    assert result == "resposta openai"

async def test_fallback_to_claude(mocker):
    mocker.patch("providers.openai_provider.OpenAIProvider.complete",
                 new=AsyncMock(side_effect=Exception("rate limit")))
    mocker.patch("providers.claude_provider.ClaudeProvider.complete",
                 new=AsyncMock(return_value="resposta claude"))
    result = await complete_with_fallback([{"role": "user", "content": "teste"}], LLMConfig())
    assert result == "resposta claude"

async def test_openai_provider_uses_primary_model(mocker):
    mocker.patch("providers.openai_provider.OpenAIProvider.complete",
                 new=AsyncMock(return_value="ok"))
    config = LLMConfig(primary_model="gpt-4o-mini")
    provider = OpenAIProvider(config)
    assert provider.config.primary_model == "gpt-4o-mini"

async def test_claude_uses_fallback_model(mocker):
    mocker.patch("providers.claude_provider.ClaudeProvider.complete",
                 new=AsyncMock(return_value="ok"))
    config = LLMConfig(fallback_model="claude-haiku-4-5-20251001")
    provider = ClaudeProvider(config)
    assert provider.config.fallback_model == "claude-haiku-4-5-20251001"
```

- [ ] **Step 8: Rodar suite de providers completa**

```bash
uv run pytest tests/providers/test_providers.py -v
```

Expected: 7 passed (4 originais + 3 de métricas).

- [ ] **Step 9: Commit**

```bash
git add providers/metrics.py providers/openai_provider.py providers/claude_provider.py tests/providers/test_providers.py
git commit -m "feat: add LLM observability — tokens, latency and TTFT via streaming"
```

---

## Task 6 — Verificação final: todos os testes passando

- [ ] **Step 1: Rodar suite completa**

```bash
uv run pytest -m "not integration" -v
```

Expected: 33 passed (ou mais, se novos testes foram adicionados), 0 failed.

- [ ] **Step 2: Smoke test em produção**

```bash
uv run python main.py
```

Expected: pelo menos CAPES ou FUNCAP com ≥1 edital processado e `output/editais.json` com conteúdo.

- [ ] **Step 3: Commit final**

```bash
git add docs/erros-e-correcoes.md DESIGN.md
git commit -m "docs: update scraper strategy decisions and error log"
```

---

## Notas de Implementação

- `FirecrawlApp.scrape_url()` é síncrono na SDK Python atual (v1.x). O `await self._delay()` antes da chamada é suficiente para respeitar rate limits.
- O filtro de URLs no `CAPESScraper.get_opportunities()` é heurístico — pode precisar de ajuste fino após o smoke test de produção.
- Se `result.links` vier `None` (página sem links), o `or []` garante que o código não quebra.
