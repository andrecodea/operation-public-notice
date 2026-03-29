# ROADMAP — Operação Edital (POC)

Início: 2026-03-25 | Término previsto: 2026-03-30

---

## Plano 1 — Pipeline Python

### ✅ Task 1 — Setup do Projeto
- Configurar `pyproject.toml` com todas as dependências
- Criar estrutura de diretórios e `__init__.py` em cada pacote
- Configurar `pytest.ini` (`asyncio_mode = auto`, `pythonpath = .`, marcador `integration`)

### ✅ Task 2 — Config: `LLMConfig` e `SOURCES`
- `config/settings.py` — `LLMConfig(BaseModel)` com defaults e validação Pydantic
- `config/sources.py` — `SOURCES: dict[str, dict]` com fapdf, funcap, capes

### ✅ Task 3 — Model `Edital`
- `models/edital.py` — Pydantic model com 18 campos e `id` determinístico via SHA-256

### ✅ Task 4 — Models `FieldScore` e `EvaluationResult`
- `models/evaluation.py` — contrato de dados do LLM judge

### ✅ Task 5 — Providers: Fallback Chain OpenAI → Claude
- `providers/base.py` — `LLMProvider(ABC)` + `complete_with_fallback` com lazy imports
- `providers/openai_provider.py` e `providers/claude_provider.py`

### ✅ Task 6 — PDF Extractor
- `extractors/pdf_extractor.py` — truncamento em 15 páginas / ~80k tokens

### ✅ Task 7 — LLM Extractor + Multi-turn Correction
- `extractors/llm_extractor.py` — `extract_edital`, `correct_edital`, `build_correction_prompt`

### ✅ Task 8 — LLM Judge
- `extractors/llm_judge.py` — `evaluate`, score ponderado por campo crítico/secundário

### ✅ Task 9 — Base Scraper + FUNCAP
- `scrapers/base_scraper.py` — ABC com `get_opportunities` e `get_documents`
- `scrapers/funcap_scraper.py` — httpx + BeautifulSoup, filtro status "aberto"

### ✅ Task 10 — FAPDF Scraper
- `scrapers/fapdf_scraper.py` — Playwright, accordion por ano, filtro 2026

### ✅ Task 11 — CAPES Scraper
- `scrapers/capes_scraper.py` — Playwright, portal gov.br, filtro anos 2025/2026

### ✅ Task 12 — `main.py` — Orquestrador
- Pipeline completo: scrape → PDF → extração → judge → correção → JSON de saída

---

## Plano 2 — FastAPI

### ⬜ API REST
- `api/main.py` — rotas para servir `editais.json` e `evaluation.json` ao frontend
- Endpoint para disparar o pipeline manualmente

---

## Plano 3 — Frontend React

### ⬜ Interface
- Vite + Tailwind, sem Next.js
- Lista de editais com filtros (fonte, área temática)
- Card/modal com todos os campos do `Edital`
- Dashboard de scores do LLM judge

---

## Dependências

```
Plano 1 (pipeline)
    └── Plano 2 (FastAPI serve os JSONs)
            └── Plano 3 (frontend consome a API)
```
