# C4 Dynamic Diagram — AI Assistance Flow

> **C4 Type:** Dynamic Diagram  
> **Scenario:** AI compliance check request from Frappe Desk through AI Gateway to LLM and back  
> **Version:** 1.1  
> **Date:** 2026-02-23  
> **Related:** [← Dynamic: Lot Lifecycle](06_DYNAMIC_LOT_LIFECYCLE.md) | [Deployment: Dev →](08_DEPLOYMENT_DEV.md)

---

## Purpose

This dynamic diagram shows how the **AI assistance flow** works in the YAM Agri Platform — from a user requesting an AI compliance check in the Frappe Desk UI, through the AI Gateway's redaction and routing pipeline, to the LLM inference and back to a read-only suggestion displayed to the user. It illustrates the **assistive-only guarantee** enforced at every step.

**Key invariant:** At no point in this flow does any container write to a DocType, change any workflow state, or take any action without an explicit human click.

---

## Diagram — AI Compliance Check Flow

```mermaid
sequenceDiagram
    autonumber
    actor Owner as U6 Agri-Business Owner
    participant Desk as Frappe Desk (Browser)
    participant nginx as nginx
    participant Frappe as Frappe Backend
    participant DB as MariaDB
    participant AIGW as AI Gateway (FastAPI)
    participant Ollama as Ollama (Local LLM)
    participant CloudLLM as Cloud LLM API
    participant Qdrant as Qdrant (Vector Store)
    participant AuditLog as AI Interaction Log (MariaDB)

    Owner->>Desk: Open Lot LOT-2026-001<br/>Click "AI: Check Compliance"

    Desk->>nginx: POST /api/method/yam_agri_core.api.compliance.check_lot<br/>{lot: "LOT-2026-001"}
    nginx->>Frappe: POST (HTTP)

    Frappe->>DB: SELECT lot details, linked QCTests, Certificates,<br/>open Nonconformances for LOT-2026-001
    DB-->>Frappe: {crop: Wheat, season: 2026-Spring, site: SITE-001,<br/>qc_tests: [{type: Moisture, result: Pass}],<br/>certificates: [{type: FAO GAP, expiry: 2027-02-01}],<br/>open_nc_count: 0}

    Note over Frappe: Build AI request context (local data — no PII yet)
    Frappe->>AIGW: POST http://ai-gateway:8001/suggest<br/>{task: "compliance_check",<br/>lot: "LOT-2026-001",<br/>context: {crop: "Wheat", season: "2026-Spring",<br/>qc_tests: [...], certificates: [...],<br/>farmer_name: "Ahmed Al-Shaibani",<br/>farmer_phone: "+967xxxxxxxx",<br/>customer_price_usd: 450}}

    Note over AIGW: Step 1: Authenticate caller
    AIGW->>AIGW: Validate AI_GATEWAY_TOKEN ✓

    Note over AIGW: Step 2: Redact sensitive data
    AIGW->>AIGW: PII Redactor:<br/>farmer_name → [FARMER_ID:F-001]<br/>farmer_phone → [PHONE_REDACTED]<br/>customer_price_usd → [PRICE_REDACTED]<br/>redaction_applied = True

    Note over AIGW: Step 3: RAG retrieval
    AIGW->>Qdrant: Similarity search: "compliance check wheat 2026-spring FAO GAP"
    Qdrant-->>AIGW: [FAO GAP clause 4.2 (storage conditions),<br/>Mycotoxin limit: 5ppb (EU), 10ppb (domestic),<br/>Season policy template: Wheat Spring requires Moisture + Mycotoxin tests]

    Note over AIGW: Step 4: Build prompt
    AIGW->>AIGW: Prompt Builder:<br/>System: "You are a food safety advisor for a cereal grain operator..."<br/>Context: redacted lot data + RAG snippets<br/>Task: "List missing compliance items for this lot"

    Note over AIGW: Step 5: Route to LLM
    AIGW->>Ollama: Check health: GET http://ollama:11434/api/tags
    Ollama-->>AIGW: {models: ["llama3.2:3b-q4"]} → healthy ✓

    AIGW->>Ollama: POST /api/generate<br/>{model: "llama3.2:3b-q4", prompt: final_prompt}
    Ollama-->>AIGW: {response: "Based on the 2026-Spring season policy for Wheat:\n1. Missing: Mycotoxin test (aflatoxin B1 ≤ 5 ppb required)\n2. Missing: Protein content test (recommended)\n3. Certificate status: FAO GAP valid until 2027-02-01 ✓\n4. No open nonconformances.\nRecommended action: Request laboratory mycotoxin test before dispatch."}

    Note over AIGW: Step 6: Sanitise response
    AIGW->>AIGW: Response Sanitiser:<br/>Strip residual PII: none found<br/>Enforce max length: 512 tokens OK<br/>Remove actionable commands: none found ✓

    Note over AIGW: Step 7: Log interaction (immutable)
    AIGW->>AuditLog: POST AI Interaction Log record:<br/>{timestamp, user: "owner@yam.com",<br/>record_type: "Lot", record_name: "LOT-2026-001",<br/>task: "compliance_check",<br/>model: "ollama/llama3.2:3b-q4",<br/>prompt_hash: sha256(...),<br/>response_hash: sha256(...),<br/>redaction_applied: true,<br/>tokens_used: 312,<br/>suggestion_accepted: null}

    AIGW-->>Frappe: 200 OK {suggestion: "...", log_hash: "sha256:abc...",<br/>model: "ollama/llama3.2:3b-q4", tokens_used: 312}

    Frappe->>DB: UPDATE tabLot SET ai_suggestion="..." WHERE name='LOT-2026-001'
    Note right of DB: ai_suggestion is a READ-ONLY display field<br/>No workflow action is triggered

    Frappe-->>Desk: 200 OK {suggestion: "...", log_hash: "..."}

    Desk->>Owner: Display AI Suggestion panel:<br/>"⚠️ AI Suggestion — Review Required<br/>Missing: Mycotoxin test..."
    Note right of Owner: HUMAN DECISION REQUIRED

    alt Owner accepts suggestion
        Owner->>Desk: Click "Accept — Create Task"
        Desk->>Frappe: POST /api/resource/Task<br/>{title: "Run Mycotoxin test for LOT-2026-001",<br/>assigned_to: "inspector@yam.com"}
        Frappe->>DB: INSERT Task (human-authored record)
        Note right of DB: Human created the Task — not AI
        Frappe->>AuditLog: Update AI Interaction Log:<br/>suggestion_accepted = True, accepted_by = "owner@yam.com"
    else Owner dismisses suggestion
        Owner->>Desk: Click "Dismiss"
        Desk->>Frappe: POST update AI log: suggestion_accepted = False
        Frappe->>AuditLog: Update AI Interaction Log: suggestion_accepted = False
    end
```

---

## Diagram — Cloud LLM Fallback Path

```mermaid
sequenceDiagram
    autonumber
    participant AIGW as AI Gateway
    participant Ollama as Ollama (Local LLM)
    participant CloudLLM as Cloud LLM (OpenAI/Anthropic)

    AIGW->>Ollama: GET http://ollama:11434/api/tags (health check)
    Ollama-->>AIGW: Connection refused (Ollama down / overloaded)

    Note over AIGW: Ollama unavailable → fallback to cloud
    AIGW->>AIGW: Check: redaction_applied = True? ✓<br/>(Only cloud route if PII was redacted)

    AIGW->>CloudLLM: POST https://api.openai.com/v1/chat/completions<br/>Authorization: Bearer {OPENAI_API_KEY}<br/>{model: "gpt-4o-mini", messages: [{role: user, content: final_prompt}]}
    CloudLLM-->>AIGW: {choices: [{message: {content: "..."}}],<br/>usage: {total_tokens: 412}}

    Note over AIGW: Log model used = "openai/gpt-4o-mini"
```

---

## ASCII Summary — AI Assist Guarantee Chain

```
  User in Frappe Desk
    "Check compliance for LOT-001"
         │
         ▼
  Frappe Backend (READ-ONLY data gathering)
    • Queries local DB for lot, QC, certs, NCs
    • NO writes at this stage
         │
         ▼
  AI Gateway
    ┌─────────────────────────────────────┐
    │ 1. Authenticate (service token)     │
    │ 2. REDACT: PII, pricing, customer   │ ← blocks if redaction fails
    │ 3. RAG: retrieve relevant snippets  │
    │ 4. Build minimal prompt             │
    │ 5. Route: Ollama first → Cloud LLM  │ ← cloud only if redacted
    │ 6. Sanitise response                │
    │ 7. LOG: hash + record + user        │ ← immutable
    └─────────────────────────────────────┘
         │
         ▼
  Frappe Backend
    • Stores suggestion in READ-ONLY field
    • NO workflow action triggered
         │
         ▼
  Frappe Desk — AI Suggestion Panel
    "⚠️ AI Suggestion — Review Required"
    [Accept → Create Task] [Dismiss]
         │
         ▼
  HUMAN DECISION (mandatory)
    • Accept: HUMAN creates Task/record
    • Dismiss: AI interaction logged as dismissed
    
  ══════════════════════════════════════════
  AI NEVER:
  ✗ Sets Lot.status
  ✗ Approves/rejects Lot
  ✗ Creates Nonconformance automatically
  ✗ Sends customer communication
  ✗ Initiates recall
  ✗ Commits to production
  ══════════════════════════════════════════
```

---

## AI Interaction Audit Log Schema

Every AI interaction is recorded in the immutable AI Interaction Log:

| Field | Type | Description |
|-------|------|-------------|
| `name` | Auto | Document name (auto-generated) |
| `timestamp` | Datetime | UTC time of the AI call |
| `user` | Link → User | Who triggered the suggestion |
| `record_type` | Data | DocType of context record (e.g., "Lot") |
| `record_name` | Data | Record name (e.g., "LOT-2026-001") |
| `task` | Select | compliance_check / capa_draft / evidence_narrative |
| `model_used` | Data | e.g., "ollama/llama3.2:3b-q4" |
| `prompt_hash` | Data | SHA-256 of redacted prompt |
| `response_hash` | Data | SHA-256 of LLM response |
| `redaction_applied` | Check | Was PII redaction applied? |
| `tokens_used` | Int | Token count (for cost monitoring) |
| `suggestion_accepted` | Check | Did user accept or dismiss? (null until decided) |
| `accepted_by` | Link → User | User who accepted (if different from requester) |
| `accepted_at` | Datetime | When suggestion was accepted |

> ⚠️ **Proposed gap:** The `AI Interaction Log` DocType is not yet implemented as a Frappe DocType in `yam_agri_core`. See [11_PROPOSED_GAPS.md](11_PROPOSED_GAPS.md).

---

## Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-02-23 | YasserAKareem | Initial AI assist dynamic diagram — V1.1 |
