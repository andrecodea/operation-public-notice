# Erros e Correções — Histórico de Debugging

Registro dos bugs encontrados durante o desenvolvimento. Útil para evitar repetição nos próximos planos.

---

## 1. `CAPESScraper.get_opportunities()` sem `return`

**Arquivo:** `scrapers/capes_scraper.py`
**Sintoma:** Scraper retornava `None` implicitamente, causando `TypeError` no orquestrador ao tentar iterar.
**Causa:** `return opportunities` ausente no final do método.
**Correção:** Adicionado `return opportunities` + `await self._delay()` + `logger.info(...)` (consistente com os demais scrapers).

---

## 2. `test_main.py` — múltiplos bugs

**Arquivo:** `tests/test_main.py`

| Bug | Linha original | Correção |
|-----|---------------|----------|
| Import com `Patch` maiúsculo | `from unittest.mock import ..., Patch` | `patch` (minúsculo) |
| Typo no nome da variável | `source=edutal.fonte` | `edital.fonte` |
| Nome de helper inconsistente | `_mocK_evaluation` (K maiúsculo) | `_mock_evaluation` |
| `run_pipeline` chamado sem `config` | `await run_pipeline(output_dir=...)` | `config` tornou-se opcional com default `LLMConfig()` |

---

## 3. `SCRAPER_REGISTRY` construído na importação (patches não funcionavam)

**Arquivo:** `main.py`
**Sintoma:** Testes patcheavam `main.FAPDFScraper` e `main.CAPESScraper`, mas o pipeline continuava usando as classes reais — Playwright tentava abrir browsers e falhava.
**Causa:** `SCRAPER_REGISTRY` era um dict no escopo do módulo, populado no momento da importação com referências às classes originais. Patches aplicados depois não afetavam o dict já criado.
**Correção:** `scraper_registry` movido para dentro de `run_pipeline()`. Assim, a cada execução, o dict é construído com as classes que estiverem no namespace do módulo naquele momento — inclusive mocks.

---

## 4. `test_capes_scraper.py` — bugs no mock de Playwright

**Arquivo:** `tests/scrapers/test_capes_scraper.py`

| Bug | Detalhe |
|-----|---------|
| Sintaxe inválida | `new_page = AsyncMock(return_value(mock_page))` — `return_value` usado como chamada de função |
| Atributos configurados no objeto errado | Linhas 18-19 sobrescreviam `mock_link_2026` em vez de configurar `mock_link_2024` |
| `__aexit__` ausente | Mock do context manager do Playwright sem `__aexit__`, causando erro ao sair do `async with` |
| Teste de integração indentado dentro de função | `@pytest.mark.integration` estava dentro do corpo de outro teste (código morto) |

**Correção:** Mock do Playwright reescrito com estrutura correta (`mock_browser`, `mock_playwright`, `__aenter__`/`__aexit__` explícitos). Teste de integração movido para escopo correto.

---

## 5. Dependências de dev não instaladas

**Arquivo:** `pyproject.toml`
**Sintoma:** `ModuleNotFoundError: No module named 'respx'` e `asyncio_mode` não reconhecido pelo pytest.
**Causa:** `pytest-asyncio`, `pytest-mock` e `respx` estavam em `[project.optional-dependencies] dev` mas não foram instalados com `uv sync`.
**Correção:** `uv sync --extra dev`

---

## 6. Playwright sem browsers instalados

**Sintoma:** `BrowserType.launch: Executable doesn't exist at .../chrome-headless-shell.exe`
**Causa:** `playwright install` não foi executado após instalar o pacote.
**Correção:** `uv run playwright install chromium`

---

## 7. `load_dotenv()` ausente — chaves de API não carregadas

**Arquivo:** `main.py`
**Sintoma:** Providers OpenAI/Claude falhariam com erro de autenticação em produção pois as variáveis de ambiente do `.env` não eram carregadas.
**Causa:** `python-dotenv` estava nas dependências mas `load_dotenv()` nunca era chamado.
**Correção:** Adicionado `from dotenv import load_dotenv; load_dotenv()` no topo de `main.py`, antes dos imports de config.

---

## 8. Scrapers desalinhados com estrutura real das páginas — detectado em teste de produção

**Descoberto em:** primeira execução de `main.py` com URLs reais (2026-03-29).

### 8a. FAPDF — URL e estrutura erradas

**Sintoma:** `FAPDF: accordion do ano 2026 não encontrado` → 0 oportunidades.
**Causa:** O scraper tentava navegar para `https://www.fap.df.gov.br/` e clicar num accordion `text=2026`. A página real de editais 2026 é uma URL própria (`/editais-fapdf-20261`) e os editais já são links diretos para PDFs — sem accordion, sem JS necessário.
**Decisão:** Reescrever como httpx + BS4 apontando para a URL correta. Playwright removido desta fonte.

### 8b. CAPES — `get_documents()` navegava para `self.url` em vez de `opportunity["url"]`

**Sintoma:** Todas as 12 oportunidades baixavam o mesmo PDF (`manual-cartao-pesquisador`), não relacionado a editais. LLM retornava string vazia → `json.loads("")` → `Expecting value: line 1 column 1 (char 0)`.
**Causa:** Bug no `get_documents()`: `await page.goto(self.url, ...)` em vez de `await page.goto(url, ...)`.
**Decisão:** Reescrever com Firecrawl (ver decisão de design abaixo). O bug de `self.url` some com a reescrita.

### 8c. FUNCAP — 0 oportunidades (possível falso negativo)

**Sintoma:** 0 editais abertos encontrados.
**Causa provável:** A estrutura HTML do WordPress mudou — o scraper buscava `article.post` + `span.status`, mas a página usa `<ul>/<li>` com classe `.acesso` e seções "Editais Abertos" / "Editais Encerrados".
**Decisão:** Reescrever seletores com base na estrutura real observada.

---

## 9. Decisão de design: substituição de Playwright por Firecrawl no CAPES

**Contexto:** CAPES é um portal gov.br com renderização JS pesada. Cada edital linka para páginas internas onde os PDFs estão. O Playwright exige manutenção de seletores frágeis e é lento.
**Decisão:** Usar Firecrawl API no `CAPESScraper` para listing e por-edital PDF discovery.
**Motivo:** Firecrawl retorna markdown limpo + lista de links sem necessidade de seletores CSS. Mais robusto a mudanças de layout. Usuário já possui créditos.
**Consequência:** `firecrawl-py` adicionado às dependências. `FIRECRAWL_API_KEY` necessária no `.env`. Playwright removido do CAPES.
