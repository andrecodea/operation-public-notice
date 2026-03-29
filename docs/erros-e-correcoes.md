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

---

## 10. FAPDF capturava 88 documentos institucionais (loop infinito no pipeline)

**Descoberto em:** smoke test completo do `main.py` (2026-03-29).
**Sintoma:** Pipeline não terminava — 88 documentos processados (Organograma, Plano de Dados Abertos, Contatos Telefônicos...), cada um disparando 2 chamadas LLM (extração + correção).
**Causa:** Filtro `/documents/d/fap/` capturava todos os links da página, incluindo documentos institucionais do sidebar. O slug desses arquivos não contém `edital`.
**Correção:** Adicionado filtro por slug: só aceita hrefs onde `slug.startswith("edital")`.

```python
slug = href.rstrip("/").rsplit("/", 1)[-1]
if not slug.startswith("edital"):
    continue
```

**Resultado:** 8 editais reais encontrados (antes: 88 documentos mistos).

---

## 11. LLM retornava markdown em vez de JSON puro → `json.loads` falhava silenciosamente

**Descoberto em:** smoke test completo do `main.py` (2026-03-29).
**Sintoma:** `Expecting value: line 1 column 1 (char 0)` em 100% das extrações, mesmo com `completion_tokens` > 0 nos logs de observabilidade.
**Causa:** O LLM envolvia a resposta em bloco markdown (` ```json\n{...}\n``` `). O extrator chamava `json.loads(raw)` diretamente sem strip. `json.loads("```json...")` falha com o mesmo erro de string vazia.
**Correção:** Adicionada `_strip_markdown()` em `extractors/llm_extractor.py`, chamada antes de ambos os `json.loads` (extração e correção):

```python
def _strip_markdown(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        text = text.rsplit("```", 1)[0]
    return text.strip()
```

**Padrão estabelecido:** Todo `json.loads` sobre resposta de LLM deve passar por `_strip_markdown()` antes.

---

## 12. FUNCAP — seletores errados (estrutura real é tabela, não ul/li/strong)

**Descoberto em:** smoke test dos scrapers (2026-03-29).
**Sintoma:** `FUNCAP: 0 oportunidades abertas encontradas.`
**Causa:** O scraper buscava `["h2", "li"]` + `tag.find("strong")`, mas a página usa uma tabela dentro de `div.SistemasExternos`:
- Título do edital: `td.laranja > span`
- Links de PDF: `ul.ListaDecorada li a`

**Correção:** Reescrito com seletores corretos. PDFs são resolvidos para URL absoluta com `urljoin` e armazenados em `opportunity["pdf_links"]`. `get_documents` apenas retorna esse campo — sem request adicional.

**Padrão estabelecido:** Quando os documentos de uma oportunidade já são descobertos junto com ela (mesma página), armazená-los diretamente no dict da oportunidade evita um request extra desnecessário.

---

## 13. Firecrawl SDK v4 — API incompatível com uso anterior

**Descoberto em:** smoke test dos scrapers com `load_dotenv` (2026-03-29).
**Sintoma:** `'Firecrawl' object has no attribute 'scrape_url'`
**Causa:** `firecrawl-py` v4.21.0 mudou completamente a API:

| Antes (v1) | Depois (v4) |
|------------|-------------|
| `FirecrawlApp(api_key=...)` | `AsyncFirecrawlApp(api_key=...)` |
| `.scrape_url(url, params={"formats": [...]})` | `await .scrape(url, formats=[...])` |
| Síncrono | Assíncrono |

**Correção:** `CAPESScraper` atualizado para `AsyncFirecrawlApp` e `await self.fc.scrape(url, formats=["links"])`. Testes atualizados para usar `AsyncMock` no método `scrape`.

**Padrão estabelecido:** Ao usar SDKs externos, sempre verificar se há variante async (`AsyncXxx`) disponível e preferir ela em código `async/await`. Não assumir compatibilidade entre major versions.

---

## 14. `load_dotenv()` não chamado em scripts ad-hoc → FIRECRAWL_API_KEY não carregada

**Sintoma:** `No API key provided for cloud service` ao rodar script Python inline com `-c`.
**Causa:** `load_dotenv()` só é chamado em `main.py`. Scripts inline não carregam o `.env` automaticamente.
**Padrão:** Em qualquer script ou teste que precise de variáveis de ambiente, adicionar `from dotenv import load_dotenv; load_dotenv()` antes de instanciar scrapers ou providers. No pipeline, `main.py` é responsável por isso.
