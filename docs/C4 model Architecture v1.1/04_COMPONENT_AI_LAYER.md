# C4 Level 3 — Component Diagram: AI Layer

> **C4 Level:** 3 — Component  
> **Container:** AI Gateway (FastAPI) + Ollama (Local LLM) + Qdrant (Vector Store)  
> **Version:** 1.1  
> **Date:** 2026-02-23  
> **Related:** [← Component: Core Platform](03_COMPONENT_CORE_PLATFORM.md) | [Component: Service Adapters →](05_COMPONENT_SERVICE_ADAPTERS.md)

---

## Purpose

This diagram zooms into the **AI Layer** — the AI Gateway container and its satellite components (Ollama, Qdrant). It shows how AI requests flow from the Frappe platform through redaction and routing to LLM inference, and how responses are logged and returned.

**Critical constraint: AI is assistive only.** No component in this layer may write to any DocType, submit any workflow action, or take any autonomous decision. AI outputs are text suggestions that a human must explicitly apply.

---

## Diagram

```mermaid
C4Component
    title Component Diagram — AI Layer

    %% ── External callers ───────────────────────────────────────────────────────
    Container(frappe,  "Frappe Backend", "Python / Gunicorn", "Core platform — makes AI suggestion requests")
    ContainerDb(qdrant, "Qdrant Vector Store", "Qdrant OSS", "Vector embeddings for RAG retrieval")
    Container(ollama,  "Ollama", "Local LLM runtime", "Llama 3.2 3B Q4 — offline inference")
    System_Ext(llm_api, "Cloud LLM API\n(OpenAI / Anthropic)", "External LLM endpoints\n(used when online + needed)")

    System_Boundary(ai_layer, "AI Gateway Container (FastAPI)") {

        %% ── API Entry Point ────────────────────────────────────────────────────
        Component(api_router, "API Router",
            "FastAPI — /suggest endpoint\nPOST /suggest",
            "Entry point for all AI suggestion requests.\nAuthenticates caller with internal service token.\nRoutes to the appropriate pipeline component.\nValidates task type against allowed list.\nReturns suggestion text + audit metadata.")

        %% ── Redaction Engine ───────────────────────────────────────────────────
        Component(redactor, "PII Redactor",
            "Python — redaction.py\nRegex + entity detection",
            "Redacts sensitive data before any LLM call:\n• Farmer names/phones → [FARMER_ID]\n• Customer names/IDs → [CUSTOMER_ID]\n• Pricing/margin data → [PRICE_REDACTED]\n• GPS exact coords → rounded to 2dp\n• Employee names → role label\n• Bank account numbers → [BANK_REDACTED]\nReturns redacted_context + redaction_applied flag.\nIf redaction fails: blocks LLM call (fail-safe).")

        %% ── Prompt Builder ─────────────────────────────────────────────────────
        Component(prompt_builder, "Prompt Builder",
            "Python — prompts.py",
            "Constructs minimal, task-specific prompts\nfrom redacted context.\n\nSupported tasks:\n• compliance_check — list gaps for a Lot\n• capa_draft — draft corrective action plan\n• evidence_narrative — summarise EvidencePack\n\nIncludes: system prompt (food safety context),\nRAG-retrieved snippets (from Qdrant),\nredacted lot/NC/cert context.\nOutputs: final_prompt string.")

        %% ── RAG Retriever ──────────────────────────────────────────────────────
        Component(rag, "RAG Retriever",
            "Python — rag.py\nQdrant client",
            "Retrieves relevant document snippets\nfrom Qdrant vector store.\nUsed to augment prompts with:\n• FAO GAP control point descriptions\n• HACCP CCP procedures\n• CAPA best-practice templates\n• ISO 22000 clause references\nSimilarity search on task + context embedding.")

        %% ── LLM Router ─────────────────────────────────────────────────────────
        Component(llm_router, "LLM Router",
            "Python — routing.py",
            "Selects the appropriate LLM backend:\n• Prefer local Ollama (offline / low latency)\n• Fall back to cloud LLM when:\n  - Ollama is unavailable\n  - Task complexity exceeds local model\n  - Cloud explicitly requested\nChecks Ollama health before routing.\nEnforces: never route to cloud if\nredaction_applied = False.")

        %% ── AI Interaction Logger ──────────────────────────────────────────────
        Component(logger, "AI Interaction Logger",
            "Python — audit_log.py\nWrites to MariaDB via Frappe REST",
            "Logs every AI interaction:\n• timestamp, user, record_type, record_name\n• task, model_used\n• SHA-256 of prompt (prompt_hash)\n• SHA-256 of response (response_hash)\n• redaction_applied, tokens_used\n• suggestion_accepted (updated later by Frappe)\nImmutable — no deletions permitted.\nAuditors can review full history.")

        %% ── Response Sanitiser ─────────────────────────────────────────────────
        Component(sanitiser, "Response Sanitiser",
            "Python — sanitise.py",
            "Post-processes LLM response:\n• Strips any PII that may have slipped through\n• Enforces maximum response length\n• Removes any actionable commands\n  (AI must not instruct the system directly)\n• Formats output as structured suggestion text.")
    }

    %% ── Relationships ──────────────────────────────────────────────────────────
    Rel(frappe,    api_router,    "POST /suggest\n{task, lot, context}", "HTTP REST :8001")
    Rel(api_router, redactor,    "Pass context for redaction", "Python function call")
    Rel(api_router, prompt_builder, "Build final prompt", "Python function call")
    Rel(api_router, llm_router,  "Route to LLM", "Python function call")
    Rel(api_router, logger,      "Log interaction", "Python function call")
    Rel(api_router, sanitiser,   "Sanitise LLM response", "Python function call")

    Rel(redactor,      prompt_builder, "Passes redacted_context", "Python return value")
    Rel(prompt_builder, rag,     "Requests relevant snippets\nfor task + context", "Qdrant similarity search")
    Rel(rag,           qdrant,   "Vector similarity search\non task embedding", "gRPC :6333")

    Rel(llm_router, ollama,  "Sends final_prompt\n(prefer offline)", "HTTP REST :11434")
    Rel(llm_router, llm_api, "Sends final_prompt\n(cloud fallback, redacted)", "HTTPS REST")

    Rel(sanitiser,  api_router, "Returns sanitised\nsuggestion text", "Python return value")
    Rel(logger,     frappe,     "Writes AI Interaction Log record\nvia Frappe REST", "Frappe REST API")
```

---

## ASCII Fallback — AI Layer Flow

```
  Frappe Backend
  POST /suggest {task, lot, context}
         │
         ▼
  ┌──────────────────────────────────────────────────────────┐
  │                    AI GATEWAY CONTAINER                   │
  │                                                           │
  │  [API Router]                                             │
  │      │ Authenticate (service token)                       │
  │      │ Validate task type                                  │
  │      ▼                                                     │
  │  [PII Redactor]                                           │
  │      Farmer names → [FARMER_ID]                           │
  │      Customer IDs → [CUSTOMER_ID]                         │
  │      Pricing data → [PRICE_REDACTED]                      │
  │      GPS coords → rounded                                  │
  │      redaction_applied = True                             │
  │      │                                                     │
  │      ▼                                                     │
  │  [RAG Retriever] ──────────────────▶ [Qdrant Vector DB]   │
  │      FAO GAP snippets               similarity search      │
  │      HACCP CCP procedures           gRPC :6333             │
  │      CAPA templates                                        │
  │      │                                                     │
  │      ▼                                                     │
  │  [Prompt Builder]                                         │
  │      System prompt (food safety context)                  │
  │      + RAG snippets                                       │
  │      + Redacted lot/cert/NC context                       │
  │      = final_prompt                                       │
  │      │                                                     │
  │      ▼                                                     │
  │  [LLM Router]                                             │
  │      Is Ollama healthy? ──── YES ──▶ [Ollama :11434]      │
  │                         └── NO  ──▶ [Cloud LLM (HTTPS)]  │
  │      (Only routes to cloud if redaction_applied=True)     │
  │      │                                                     │
  │      ▼ (LLM response text)                                 │
  │  [Response Sanitiser]                                     │
  │      Strip residual PII                                   │
  │      Enforce max length                                   │
  │      Remove actionable commands                           │
  │      │                                                     │
  │      ▼                                                     │
  │  [AI Interaction Logger]                                  │
  │      Log: timestamp, user, record, task, model            │
  │      Log: SHA-256(prompt), SHA-256(response)              │
  │      Log: redaction_applied, tokens_used                  │
  │      Write to AI Interaction Log (via Frappe REST)        │
  │      │                                                     │
  └──────┼──────────────────────────────────────────────────── ┘
         │ Returns: { suggestion, log_hash, model, tokens }
         ▼
  Frappe Backend → stores in DocType read-only field
  Frappe Desk → displays "AI Suggestion — Review Required"
  User → clicks Accept (creates human record) or Dismiss
```

---

## AI Task Reference

| Task key | Input | Output | Side effects |
|----------|-------|--------|-------------|
| `compliance_check` | `lot` name, season policy | List of missing QC tests, expired certs, open NCs for the Lot | None — read-only |
| `capa_draft` | `nonconformance` name, description, root_cause | Suggested corrective action plan text | None — text only; user must submit |
| `evidence_narrative` | `evidence_pack` name, scope | Human-readable audit narrative summarising the evidence pack | None — text only; user must approve before sending |

---

## Approved LLM Models (V1.1)

| Model | Type | Use case | Session persistence? |
|-------|------|---------|---------------------|
| `ollama/llama3.2:3b-q4` | Local | All tasks; offline-first | No |
| `openai/gpt-4o-mini` | Cloud (redacted) | When local model insufficient | No (stateless API calls) |
| `anthropic/claude-3-haiku` | Cloud (redacted) | Alternative to GPT-4o-mini | No |

**Model activation requires:** QA Manager + Owner approval. See `docs/Docs v1.1/11_AI_GOVERNANCE.md §6`.

---

## RAG Knowledge Base (Qdrant)

| Collection | Source documents | Used for |
|-----------|-----------------|---------|
| `fao_gap` | FAO GAP Middle East PDF | compliance_check prompts |
| `haccp_ccp` | HACCP CCP procedure library | capa_draft prompts |
| `iso22000` | ISO 22000:2018 clause summaries | evidence_narrative prompts |
| `capa_templates` | CAPA best-practice templates | capa_draft prompts |
| `codex_mrl` | Codex Alimentarius MRL tables | compliance_check (mycotoxin limits) |

> ⚠️ **Proposed gap:** The Qdrant knowledge base population scripts and embedding pipeline are not yet implemented in V1.1. See [11_PROPOSED_GAPS.md](11_PROPOSED_GAPS.md).

---

## Security Properties

| Property | Implementation |
|----------|---------------|
| **Service authentication** | Internal token via `AI_GATEWAY_TOKEN` env var |
| **PII never reaches external LLM** | Redactor blocks call if `redaction_applied = False` |
| **Immutable audit log** | All interactions logged; no deletions via API |
| **Stateless LLM calls** | No session persistence; each call is independent |
| **No write access to Frappe** | AI Gateway only writes to AI Interaction Log; no DocType mutations |
| **Graceful degradation** | If AI Gateway is down: Frappe continues operating; AI panel shows "AI unavailable" |

---

## Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-02-23 | YasserAKareem | Initial AI layer component diagram — V1.1 |
