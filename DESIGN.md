# DESIGN.md — Decisões e Padrões do Projeto

Documento vivo. Atualizar sempre que uma decisão de design for tomada ou revisada.

---

## Arquitetura

### Padrão central: Pipeline linear sem estado compartilhado

```
scrape → extrai PDF → LLM estrutura → valida Pydantic → LLM judge avalia → JSON
```

Cada etapa é independente. Falha em uma oportunidade não afeta as demais.
O orquestrador (`main.py`) é o único ponto que conecta as etapas.

Dois arquivos de saída gerados ao final:
- `output/editais.json` — array de objetos `Edital`
- `output/evaluation.json` — array de objetos `EvaluationResult` com scores do judge

### Template Method via classe abstrata

`BaseScraper` define o contrato com dois métodos abstratos:

```python
async def get_opportunities(self) -> list[dict]  # descobre oportunidades
async def get_documents(self, opportunity: dict) -> list[str]  # resolve PDFs
```

A lógica de orquestração (download, extração, LLM, avaliação, salvamento) fica em `main.py`, não nos scrapers. Scrapers só sabem navegar — não sabem extrair nem salvar.

**Motivo:** Adicionar nova fonte = criar um arquivo + uma linha em `config/sources.py`. Zero alteração em `main.py`.

### Configuration Object com Pydantic

Toda configuração de runtime (providers, modelos, timeouts, filtros) é tipada com Pydantic
e carregada a partir de variáveis de ambiente ou valores default.
Nunca usar dicts soltos para configuração — sempre um model validado.

```python
class LLMConfig(BaseModel):
    primary_provider: str = "openai"
    primary_model: str = "gpt-4o"
    fallback_provider: str = "claude"
    fallback_model: str = "claude-sonnet-4-20250514"
    max_retries: int = 2
    timeout_seconds: int = 60
```

**Motivo:** Configuração tipada é auto-documentada, validada na inicialização e
auditável — elimina bugs de typo em strings de config.

---

## Decisões técnicas

### Fallback Chain: OpenAI primário → Claude secundário

O stack primário de LLM segue o da empresa-alvo (OpenAI API). Claude atua como fallback
automático em caso de falha (rate limit, timeout, erro de API).

```python
class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, prompt: str) -> str: ...

class OpenAIProvider(LLMProvider): ...   # gpt-4o — primário
class ClaudeProvider(LLMProvider): ...   # claude-sonnet-4-20250514 — fallback

async def complete_with_fallback(prompt: str, config: LLMConfig) -> str:
    try:
        return await OpenAIProvider(config).complete(prompt)
    except Exception as e:
        logger.warning(f"OpenAI falhou ({e}), usando Claude como fallback")
        return await ClaudeProvider(config).complete(prompt)
```

O fallback se aplica tanto ao extrator quanto ao judge — ambos usam `complete_with_fallback`.
O pipeline não sabe qual provider respondeu; recebe texto puro.

**Motivo:** Alinhamento com o stack real da empresa. Resiliência operacional.
Demonstra que o código não tem acoplamento duro com um único provider.

### LLM-as-a-Judge: avaliação por campo

Após cada extração, um segundo LLM call avalia o resultado campo a campo.
O judge recebe: texto bruto do PDF + JSON extraído.

```python
class FieldScore(BaseModel):
    fidelidade: float     # 0–1 · o valor extraído existe no documento?
    completude: float     # 0–1 · havia info disponível que foi ignorada?
    justificativa: str    # explicação do judge

class EvaluationResult(BaseModel):
    edital_id: str                          # link_edital como chave
    fonte: str
    scores_por_campo: dict[str, FieldScore]
    score_geral: float                      # média ponderada dos campos críticos
    # métricas determinísticas:
    campos_preenchidos: int                 # de 18 campos do model Edital
    campos_nulos: int
    json_valido: bool                       # Pydantic passou sem erros?
    texto_truncado: bool                    # PDF truncado nas 15 páginas?
    avaliado_em: datetime
```

**Motivo:** Fidelidade + completude por campo é mais granular e explicável do que
um score único. Permite identificar quais campos são sistematicamente problemáticos
por fonte ou tipo de documento.

### Correção automática: multi-turn correction

Se `score_geral < 0.6` após a avaliação do judge, o pipeline tenta uma correção
via **multi-turn**: o histórico de mensagens original é reaproveitado, adicionando
uma mensagem de usuário com o feedback específico do judge para cada campo problemático.

```python
messages = [
    {"role": "system",    "content": SYSTEM_PROMPT},
    {"role": "user",      "content": f"Texto do PDF:\n{texto_pdf}"},
    {"role": "assistant", "content": json_extraido},        # output original
    {"role": "user",      "content": build_correction_prompt(scores_baixos)},
]
# build_correction_prompt inclui o trecho exato do PDF para cada campo problemático
# (extraído da justificativa do judge) para evitar ancoragem na resposta anterior
```

A correção é feita uma única vez — sem loops. O resultado substituí o `Edital`
original e é reavaliado pelo judge, com `corrigido: bool` no `EvaluationResult`.

**Motivo:** O modelo já tem o PDF no contexto e vê o próprio output — só precisa
corrigir campos específicos. Mais simples e viável do que re-extração completa.
Incluir o trecho exato do PDF no prompt de correção mitiga ancoragem na resposta anterior.

### Métricas determinísticas (sem LLM)

Complementam o judge com contagens binárias e percentuais auditáveis:

| Métrica | Descrição |
|---|---|
| `json_valido` | O output passou em `Edital.model_validate()` sem erros? |
| `campos_preenchidos` | Quantos dos 18 campos têm valor não-nulo? |
| `texto_truncado` | O PDF foi cortado nas 15 primeiras páginas? |
| `taxa_preenchimento` | `campos_preenchidos / 18` como percentual |

**Motivo:** Métricas determinísticas são auditáveis e não dependem de outro LLM call.
Combinadas com o judge, oferecem duas camadas de evidência independentes.

### Estratégia de scraping por fonte (revisada em 2026-03-29)

| Fonte  | Estratégia   | Motivo                                                          |
|--------|--------------|-----------------------------------------------------------------|
| FUNCAP | httpx + BS4  | WordPress estático, sem JS. Seletores: `<ul>/<li>` + `.acesso` |
| FAPDF  | httpx + BS4  | URL direta `/editais-fapdf-20261`, links PDF já expostos no HTML, sem JS |
| CAPES  | Firecrawl    | Portal gov.br com JS pesado; Firecrawl retorna markdown + links sem seletores frágeis |

**Decisão original (Playwright no FAPDF/CAPES) foi revisada** após teste com URLs reais:
- FAPDF não usa accordion — tem URL própria por ano com links diretos para PDFs.
- CAPES exige visita por-edital para encontrar PDFs; Firecrawl é mais robusto que Playwright para este padrão.

Playwright permanece instalado como dependência (pode ser necessário futuramente), mas não é usado em nenhum scraper ativo.

**Configuração:** `FIRECRAWL_API_KEY` obrigatória no `.env` para o `CAPESScraper`.

### Configuração centralizada em `config/sources.py`

URLs, seletores e filtros nunca ficam dentro dos scrapers.
Scrapers recebem a config como parâmetro de inicialização.

**Motivo:** Mudança de URL ou filtro não exige toque no código do scraper.

### Estratégia para PDFs grandes

- Extrair texto página por página com `pdfplumber`
- Limite: ~80k tokens (~300 páginas densas)
- Se ultrapassar: usar apenas as primeiras 15 páginas
- Sempre logar quando truncamento ocorrer (nunca silencioso)

**Motivo:** Editais concentram informações estruturais no início. Truncar com log é
melhor do que falhar ou explodir o contexto do LLM.

### Output do LLM: JSON puro, validado com Pydantic

O prompt instrui o modelo a retornar **somente JSON válido**, sem markdown.
O JSON é parseado e validado com `Edital.model_validate()` antes de qualquer salvamento.
Campos ausentes → `None`. Nunca string vazia.

---

## API (FastAPI)

FastAPI serve os resultados do pipeline ao frontend e expõe um endpoint para disparar o pipeline.
Localizado em `/api`. Usa `uvicorn` como servidor ASGI.

### Endpoints

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/editais` | Lista editais com filtros opcionais (`fonte`, `min_score`) |
| `GET` | `/editais/{id}` | Retorna um edital com seu `EvaluationResult` |
| `GET` | `/evaluation` | Lista todos os `EvaluationResult` |
| `GET` | `/evaluation/summary` | Métricas agregadas para o dashboard (KPIs + por fonte + campos problemáticos) |
| `POST` | `/pipeline/run` | Dispara o pipeline de scraping em background (`BackgroundTasks`) |

### Estrutura

```
api/
├── main.py          ← FastAPI app, CORS, registro de routers
└── routes/
    ├── editais.py   ← GET /editais, GET /editais/{id}
    ├── evaluation.py← GET /evaluation, GET /evaluation/summary
    └── pipeline.py  ← POST /pipeline/run
```

Os dados são lidos de `output/editais.json` e `output/evaluation.json` em cada request.
Sem banco de dados — os JSONs são a fonte de verdade.

**Motivo:** FastAPI elimina o `copy_output.sh`, torna a integração frontend→dados limpa e
demonstra capacidade de construir APIs reais. O endpoint `/pipeline/run` mostra que o
sistema pode ser operado via interface, não só via CLI.

## Frontend

React + Vite + Tailwind. Localizado em `/frontend`. Consome dados via FastAPI (`http://localhost:8000`).

### Layout: Split view + Dashboard

**Tela principal — Split view:**
- Coluna esquerda: lista de editais com filtros (fonte, score geral, área temática)
- Coluna direita: ao selecionar um edital, exibe todos os campos + scores do judge por campo

**Tela secundária — Dashboard de confiabilidade:**
- Score médio por fonte (FAPDF / FUNCAP / CAPES)
- Campos com maior taxa de alucinação (fidelidade baixa sistematicamente)
- Campos com maior taxa de omissão (completude baixa sistematicamente)
- Métricas determinísticas agregadas (% JSON válido, % truncados, taxa de preenchimento média)

**Motivo:** A tela de split serve o usuário final (visualizar editais). O dashboard
serve a engenheira de IA que avalia a qualidade do pipeline.

---

## Tratamento de erros

### Por oportunidade, nunca por fonte

```python
for opportunity in opportunities:
    try:
        # pipeline completo
    except Exception as e:
        logger.error(f"[{source}] Falha em '{opportunity['titulo']}': {e}")
        errors += 1
        continue  # próxima oportunidade
```

**Motivo:** Um PDF corrompido ou fora do ar não deve derrubar a execução inteira.

### Logging estruturado com `logging` padrão

- Nunca usar `print()` no código de produção
- Level `INFO` para progresso normal
- Level `WARNING` para truncamentos, fallbacks de provider e situações recuperáveis
- Level `ERROR` para falhas por oportunidade

---

## Padrões de código

### Async consistente

Todo o código usa `async/await`. Playwright exige isso; httpx suporta nativamente.
Delays entre requisições: `await asyncio.sleep(1)` a `asyncio.sleep(2)`.

### Sem lógica de fonte em `main.py`

`main.py` só conhece a interface `BaseScraper`. Qualquer `if source == "fapdf"` em
`main.py` é um sinal de design errado.

### Sem RAG, embeddings ou busca vetorial

O problema é extração estruturada de documento conhecido, não recuperação de informação.
RAGAS foi considerado e descartado: foi criado para pipelines RAG/Q&A, não para extração
estruturada — aplicá-lo aqui seria uso impreciso da ferramenta.

---

## O que está fora do escopo

- Banco de dados (JSONs em `output/` são a fonte de verdade)
- Autenticação ou login em fontes
- Monitoramento contínuo / agendamento
- Deduplicação entre fontes
- RAGAS (descartado — fit impreciso para extração estruturada)
