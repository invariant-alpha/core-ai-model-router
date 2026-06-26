# Prompt Operativo — CORE_AI_MODEL_ROUTER

## Ruolo nel Sistema
Core Engine (Livello 1). Gateway unificato per qualsiasi chiamata a modelli AI (testo, immagini, audio, video).
Riceve richieste indipendenti dal vendor, seleziona il provider, formatta la chiamata (usando ad es. OpenRouter per il testo e Novita.ai/Prodia per media), gestisce il retry e la validazione della risposta via Pydantic (structured output per il testo).
Emette un evento di `cost_usd` per ogni chiamata in modo che il FinOps Module possa tracciarlo (tramite pub sul bus).

## Lifecycle
Controllabile (RUNNING, PAUSED, STOPPED).
- Se PAUSED, le richieste vengono accodate sul Bus o rifiutate con errore a seconda della configurazione. Per semplicità, possiamo non prelevarle dal Bus o gestire un NACK.

## Configurazione
```python
from pydantic import BaseModel, Field

class AIModelRouterConfig(BaseModel):
    openrouter_api_key: str = Field(default="", description="Key di OpenRouter")
    novita_api_key: str = Field(default="", description="Key di Novita.ai")
    default_text_model: str = Field(default="anthropic/claude-3-sonnet")
    default_image_model: str = Field(default="stable-diffusion-xl")
    max_retries: int = Field(default=3)
```

## Dipendenze
- Moduli già implementati: `core-bus`.
- Librerie esterne: `httpx`.

## Schema Pydantic Completo
```python
from pydantic import BaseModel
from typing import Optional, Literal, Dict, Any

class AIRequest(BaseModel):
    modality: Literal["text", "image", "audio", "video"]
    model_preference: Literal["fast", "smart", "cheap"] = "smart"
    model_override: Optional[str] = None
    prompt: str
    negative_prompt: Optional[str] = None
    system_prompt: Optional[str] = None
    output_schema: Optional[Dict[str, Any]] = None  # JSON schema per structured output
    parameters: dict = {}
    correlation_id: str

class AIResponse(BaseModel):
    modality: str
    content: Optional[str] = None
    asset_base64: Optional[str] = None
    parsed_output: Optional[dict] = None
    model_used: str
    provider_used: str
    cost_usd: float
    correlation_id: str
```

## Contratto Redis Streams
- Stream sottoscritti: `ai.request.created`
- Stream pubblicati: `ai.response.completed`, `ai.response.failed`, `finops.cost.recorded`
- DLQ: `system.dlq.ai`

## Flusso Principale
1. Riceve `AIRequest`.
2. Identifica il provider.
3. Se `modality == "text"`, chiama OpenRouter (`httpx` su `https://openrouter.ai/api/v1/chat/completions`).
4. Estrae risultato e calcola/stima il costo basato sui token ritornati da OpenRouter.
5. Pubblica la `AIResponse` su `ai.response.completed`.
6. Pubblica un evento su `finops.cost.recorded` con il costo stimato.
7. Se la chiamata fallisce, prova il retry; dopo `max_retries` pubblica su `ai.response.failed`.

## Struttura Directory
```
core-ai-model-router/
├── Dockerfile
├── pyproject.toml
├── docs/
│   └── prompts/
│       └── CORE_AI_MODEL_ROUTER.md
├── src/
│   └── core_ai_model_router/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       ├── schemas.py
│       └── router.py
└── tests/
    ├── unit/
    └── integration/
```

## Test Richiesti
- Unit test: Mocking di OpenRouter via `respx`.

## Definition of Done
- [ ] Tutti i test passano
- [ ] Implementazione client HTTP verso OpenRouter
- [ ] Emette eventi di costo
