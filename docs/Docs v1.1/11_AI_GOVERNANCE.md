# AI Governance — YAM Agri Platform V1.1

> **SDLC Phase:** Compliance / Governance  
> **Version:** 1.1  
> **Status:** ⚠️ Draft  
> **Date:** 2026-02-23  
> **Audience:** All team members, AI developers, external auditors  
> **Related:** [Compliance & Quality](10_COMPLIANCE_AND_QUALITY.md) | [Security & RBAC](06_SECURITY_AND_RBAC.md)  
> **Deep reference:** `docs/SMART_FARM_ARCHITECTURE.md` Layer 7 | `docs/AGENTS_AND_MCP_BLUEPRINT.md` §5

---

## 1. Core Principle: AI is Assistive Only

> **This principle is non-negotiable and applies everywhere in the YAM Agri platform.**

AI is **always assistive — it suggests; humans decide and execute.**

No AI component, workflow, or automation may:

| Prohibited action | Example |
|------------------|---------|
| Automatically accept or reject a grain lot | AI cannot set Lot.status = "Accepted" without a human clicking Submit |
| Initiate a product recall without human confirmation | AI cannot create or submit a recall workflow |
| Send customer communications autonomously | AI-drafted messages must be reviewed and sent by a human |
| Bypass site-level data isolation | AI tools cannot access data beyond the user's assigned sites |
| Commit code or deploy to any environment | AI coding assistants (Copilot) suggest; a human reviews and merges |
| Execute any Frappe DocType write without a human triggering the action | AI suggestions stored as text; user must explicitly apply them |

This applies in:
- Frappe Desk AI suggestion panels
- MCP tool calls in VS Code Copilot sessions
- GitHub Actions workflows
- AI Gateway API calls
- Any future agent or automation built on top of the platform

---

## 2. AI Action Modes

Three AI action modes are permitted in the platform. "Autonomous" is never permitted.

| Mode | Description | V1.1 examples | Human gate |
|------|-------------|--------------|-----------|
| **Read-only** | AI displays information; no system change possible | Compliance dashboard, lot summary, trend analysis | None (display only) |
| **Propose-only** | AI surfaces a recommendation; operator reviews and decides | Compliance gap list, variety recommendation | User clicks Accept/Dismiss |
| **Execute-with-approval** | System prepares an action record; manager must confirm before it runs | AI-drafted CAPA plan → QA Manager approves and submits | Workflow approval required |
| ~~Autonomous~~ | ~~AI executes without confirmation~~ | ~~Never permitted~~ | ~~N/A~~ |

---

## 3. AI Safety Architecture

### 3.1 AI Gateway (Technical Enforcement)

The AI Gateway is the **mandatory gateway** between Frappe and any external LLM. It enforces:

```
Frappe Platform
      │
      │  Internal API call (server-side only)
      ▼
AI Gateway (FastAPI — ai-gateway service)
  ┌──────────────────────────────────────┐
  │ 1. Authenticate caller (service token)│
  │ 2. Validate task type is permitted   │
  │ 3. REDACT: PII, pricing, customer IDs│
  │ 4. Build minimal prompt (context only)│
  │ 5. Call LLM (local Ollama or cloud)  │
  │ 6. Log: hash + record ref + user     │
  │ 7. Return: suggestion text ONLY      │
  └──────────────────────────────────────┘
      │
      │  Suggestion text returned (no DocType writes)
      ▼
Frappe Platform
  ┌──────────────────────────────────────┐
  │ Store suggestion in read-only field  │
  │ Display to user in AI Suggestion Panel│
  │ User: Accept → creates human record  │
  │ User: Dismiss → logged               │
  └──────────────────────────────────────┘
```

### 3.2 Permitted AI Tasks (V1.1)

| Task | Description | Output type |
|------|-------------|-------------|
| `compliance_check` | List missing QC tests, expired certificates, open NCs for a Lot | Suggestion text |
| `capa_draft` | Draft a corrective action plan for a Nonconformance | Suggestion text |
| `evidence_narrative` | Draft a narrative summary for an EvidencePack | Suggestion text (user must approve before sending) |

### 3.3 Blocked AI Calls

The AI Gateway will reject any request that:
- Attempts to write to any DocType directly
- Requests PII without redaction
- Specifies an unpermitted task type
- Originates from an unauthenticated caller

---

## 4. Data Redaction Policy

Before any data leaves the YAM platform to an external LLM, the AI Gateway **must** redact:

| Data category | Redaction action | Example |
|---------------|-----------------|---------|
| Farmer name | Replace with `[FARMER_ID]` | "Ahmed Al-Shaibani" → "[FARMER_ID:F-001]" |
| Farmer phone number | Replace with `[PHONE_REDACTED]` | "+967xxxxxxxx" → "[PHONE_REDACTED]" |
| Customer name | Replace with `[CUSTOMER_ID]` | "Al-Noor Trading" → "[CUSTOMER_ID:C-042]" |
| Pricing / margin data | Replace with `[PRICE_REDACTED]` | "$450/ton" → "[PRICE_REDACTED]" |
| GPS exact coordinates | Round to 2 decimal places | "15.3521, 44.2081" → "15.35, 44.21" |
| Employee name | Replace with role | "Ibrahim Al-Sana'ani" → "[IT_ADMIN]" |
| Bank account numbers | Replace with `[BANK_REDACTED]` | Full redaction |

**Audit of redaction:** A redaction audit record is created before every LLM call. If redaction cannot be confirmed, the LLM call is blocked.

---

## 5. AI Interaction Audit Log

Every AI interaction is logged in the `AI Interaction Log` DocType (or equivalent table) with:

| Field | Description |
|-------|-------------|
| `timestamp` | UTC datetime of the call |
| `user` | Frappe username who triggered the suggestion |
| `record_type` | DocType of the context record (e.g., "Lot") |
| `record_name` | Name of the context record (e.g., "LOT-2026-001") |
| `task` | AI task type (compliance_check / capa_draft / evidence_narrative) |
| `model_used` | LLM model name and version |
| `prompt_hash` | SHA-256 of the redacted prompt sent |
| `response_hash` | SHA-256 of the AI response |
| `redaction_applied` | Boolean — was redaction applied? |
| `tokens_used` | Token count (for cost monitoring) |
| `suggestion_accepted` | Boolean — did user accept or dismiss? |
| `accepted_by` | User who accepted (if different from requester) |
| `accepted_at` | Datetime of acceptance |

This log is **immutable** — no deletions permitted. Auditors can review all AI interactions.

---

## 6. AI Model Governance

### 6.1 Approved Models (V1.1)

| Model | Type | Use case | Approved by |
|-------|------|---------|------------|
| `ollama/llama3.2:3b-q4` | Local (offline) | All V1.1 tasks | Owner + QA Manager |
| `openai/gpt-4o-mini` | Cloud (with redaction) | When local model insufficient | Owner |
| `anthropic/claude-3-haiku` | Cloud (with redaction) | Alternative to GPT-4o-mini | Owner |

**Forbidden models in V1.1:**
- Any model not in the approved list
- Any model that stores conversation history (session persistence)
- Any model with known data retention policies for API calls (check vendor policy before adding)

### 6.2 Model Activation Procedure

New AI models must follow this process before use:

1. **Propose:** Developer adds model to model registry with details (vendor, version, data policy)
2. **Security scan:** Run Garak (LLM red-team tool) against model for prompt injection / data leakage
3. **Review:** QA Manager reviews scan results and approves/rejects
4. **Owner approval:** Platform Owner gives final approval
5. **Add to approved list:** Update this document and AI Gateway configuration
6. **Test:** Run compliance_check task with test data; verify redaction is working
7. **Monitor:** Track tokens_used and response quality for 2 weeks

> ⚠️ **Proposed addition:** An AI Model Card template for each approved model is identified as a gap (captures: intended use, limitations, ethical considerations, performance on YAM tasks). See `00_INDEX.md`.

### 6.3 Model Retirement Procedure

When retiring a model:
1. Remove from AI Gateway approved list
2. Update this document
3. Verify all pending AI Interaction Log entries are closed
4. Archive model weights (if local) or confirm vendor data deletion (if cloud)

---

## 7. AI Copilot Agents (Developer Tools)

The `.github/agents/` folder contains role-specific instruction files for GitHub Copilot. These files govern how Copilot assists in code and documentation tasks — they do not give Copilot any runtime access to the platform.

| Agent file | Role | Key restriction |
|------------|------|----------------|
| `developer.md` | Application developer | Cannot deploy to production or commit secrets |
| `devops.md` | Infrastructure / DevOps | Cannot merge to main without review |
| `qa-manager.md` | QA / compliance | Cannot override compliance rules without approval |
| `owner.md` | Platform owner | Strategic decisions; cannot bypass security controls |

**All agents enforce:** AI is assistive only; humans decide and execute.

---

## 8. Responsible AI Commitments

YAM Agri commits to the following responsible AI practices:

| Commitment | How it is implemented |
|-----------|----------------------|
| Transparency | Every AI suggestion is clearly labelled "AI Suggestion — Review Required" in the UI |
| Explainability | AI suggestions include a brief rationale; no black-box decisions |
| Human oversight | Every AI output requires human review before any action |
| Fairness | Crop variety recommendations are deterministic and explainable (no opaque ML in V1.1) |
| Privacy | PII and financial data never sent to external LLMs |
| Auditability | Full AI interaction log; immutable; auditor-accessible |
| Fallback | If AI is down, all platform functions work without AI (graceful degradation) |
| Minimal data | Only the minimum context needed for the task is sent to the AI |

---

## 9. AI Governance Review Schedule

| Review | Frequency | Who |
|--------|-----------|-----|
| AI interaction log review | Monthly | QA Manager |
| Approved model list review | Quarterly | Owner + QA Manager |
| AI Gateway redaction audit | Quarterly | DevOps + QA Manager |
| AI action prohibition audit | At every release | Developer + QA Manager |
| External AI governance audit | Annually | External Auditor |

---

## 10. Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-02-23 | YasserAKareem | Initial AI governance document — V1.1 |
