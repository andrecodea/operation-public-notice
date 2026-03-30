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

---

## 15. LLM judge sem `_strip_markdown` → `Expecting value: line 1 column 1 (char 0)`

**Descoberto em:** smoke test completo com pipeline rodando via API (2026-03-29).
**Sintoma:** 3 de 4 editais processados falhavam com `Expecting value: line 1 column 1 (char 0)` no judge, mesmo com `completion_tokens > 0` nos logs. O extrator funcionava normalmente.
**Causa:** `llm_extractor.py` tinha `_strip_markdown()` antes de cada `json.loads`, mas `llm_judge.py` chamava `json.loads(raw)` diretamente. Sob carga de 429 + retries, o modelo voltava a envolver o JSON em bloco markdown (` ```json\n{...}\n``` `). `json.loads("```json...")` falha com `char 0` porque a backtick não é um valor JSON válido.
**Correção:** `_strip_markdown` importada de `llm_extractor` e aplicada no judge antes do `json.loads`. Adicionado `logger.error` com os primeiros 200 chars do raw em caso de falha para facilitar debugging futuro.

```python
# llm_judge.py
from extractors.llm_extractor import _strip_markdown
...
scores_raw = json.loads(_strip_markdown(raw))
```

**Padrão reforçado:** Todo `json.loads` sobre resposta de LLM deve passar por `_strip_markdown()`. Sem exceções, mesmo com system prompt explícito pedindo JSON puro — o modelo ignora sob pressão de rate limiting.

---

## 16. Rate limiting por TPM, não por RPM — limiter proativo não resolve

**Descoberto em:** execução real do pipeline (2026-03-29).
**Sintoma:** 429s frequentes mesmo com pipeline sequencial (sem paralelismo). O `_RateLimiter` baseado em RPM adicionado anteriormente não reduzia os erros.
**Causa:** Cada edital consome ~35k tokens em dois disparos (extração ~17k + judge ~17k). O limite de TPM do OpenAI Tier 1 para `gpt-4o` é 30k tokens/minuto. Dois disparos em sequência rápida excedem a janela.
**Solução aplicada:** `inter_call_delay: float = 3.0` adicionado ao `LLMConfig` — sleep proativo antes de cada chamada LLM em `complete_with_fallback`. Reduz bursts mas não elimina 429 completamente com Tier 1.
**Solução definitiva:** Fazer upgrade para Tier 2 da OpenAI ($50 gastos) → 450k TPM → sem 429 para este volume. Ou usar Claude como primário (limites de Anthropic são mais generosos no Tier equivalente).
**Padrão:** Para pipelines sequenciais com PDFs grandes, o gargalo é TPM, não RPM. Rate limiters baseados em contagem de requests não ajudam — o correto é rastrear tokens consumidos por janela.

---

## 17. Pipeline não expunha resultados parciais ao frontend

**Descoberto em:** uso real do frontend durante execução do pipeline (2026-03-29).
**Sintoma:** Frontend mostrava lista vazia durante toda a execução. Editais apareciam só após o pipeline encerrar completamente.
**Causa:** `main.py` acumulava todos os resultados em memória e escrevia os JSONs apenas no final do loop de todas as fontes.
**Correção:** Flush parcial após cada edital concluído — `output/editais.json` e `output/evaluation.json` são sobrescritos com os dados acumulados até aquele momento. A API lê os arquivos a cada request, então o frontend passa a ver resultados incrementais.

```python
# Após cada edital concluído em main.py
with open(out / "editais.json", "w", encoding="utf-8") as f:
    json.dump(all_editais, f, ensure_ascii=False, indent=2)
with open(out / "evaluation.json", "w", encoding="utf-8") as f:
    json.dump(all_evaluations, f, ensure_ascii=False, indent=2)
```

**Trade-off:** A cada edital há uma escrita de arquivo completa (não append). Aceitável para o volume atual (< 50 editais). Para volumes maiores, substituir por banco ou por append com reescrita eventual.

---

## 18. Decisões de design adicionadas nesta sessão (2026-03-29)

### 18a. Tracking de modelo LLM na avaliação

**Motivação:** Saber se uma extração usou o modelo primário (gpt-4o) ou o fallback (Claude) é útil para diagnosticar diferenças de qualidade e rastrear custos por fonte.

**Implementação:**
- `complete_with_fallback` passou a retornar `tuple[str, str]` — texto e nome do modelo usado
- `EvaluationResult` ganhou `extraction_model: str | None` e `judge_model: str | None`
- `llm_extractor.extract_edital` e `correct_edital` retornam o modelo junto com o edital
- `llm_judge.evaluate` recebe `extraction_model` como parâmetro e registra `judge_model` internamente
- `/evaluation/summary` expõe `model_usage: dict[str, int]` — contagem por modelo

**Padrão:** Qualquer chamada LLM deve ser rastreável — qual modelo, qual etapa, qual edital.

### 18b. Pipeline status endpoint + polling no frontend

**Motivação:** `POST /pipeline/run` retorna 202 imediatamente (BackgroundTasks). Sem polling, o frontend não sabe quando o pipeline termina.

**Implementação:**
- `GET /pipeline/status` → `{"running": bool}` — usa a variável `_pipeline_running` já existente no módulo
- `PipelineButton` faz polling a cada 3s enquanto `running: true`
- Ao detectar `running: false`, dispara `onDone()` → App recarrega lista e dashboard
- `onStart()` inicia polling de editais a cada 10s para exibir resultados incrementais

**Padrão:** Para operações longas em background, sempre expor endpoint de status separado. Não bloquear o request original nem usar WebSocket para POC — polling simples é suficiente.

### 18c. `_RateLimiter` baseado em token bucket

**Motivação:** Evitar 429s proativamente em vez de só tratar reativamente via retry.

**Implementação:** Classe `_RateLimiter` em `providers/base.py` com janela deslizante de `period` segundos e teto de `max_calls`. Instâncias separadas por provider, inicializadas lazily a partir de `LLMConfig.rpm_openai` e `LLMConfig.rpm_claude`.

**Limitação conhecida:** Limita por RPM, não por TPM. Para o problema atual (TPM), o `inter_call_delay` é mais efetivo. O limiter de RPM protege cenários futuros com concorrência.

### 18d. Empacotamento como `.exe` via PyInstaller

**Motivação:** Entregar a solução como executável standalone sem exigir Python instalado.

**Implementação:**
- `run_app.py` — entry point: carrega `.env`, abre browser automaticamente, inicia uvicorn
- `app.spec` — spec PyInstaller com `hiddenimports` para FastAPI/uvicorn/pydantic e `datas` incluindo `frontend/dist/`
- `api/main.py` — serve `frontend/dist/` como static files quando o diretório existe (modo produção)
- Build: `cd frontend && npm run build && cd .. && pyinstaller app.spec`
- Saída: `dist/operacao-edital/operacao-edital.exe`

**Limitação:** Playwright não funciona dentro do bundle PyInstaller — browsers precisam ser instalados separadamente via `playwright install chromium` na máquina destino. Distribuição é a pasta `dist/operacao-edital/`, não um único `.exe`.
