# YAM Server + Frappe/ERPNext Integration Guide

> **Purpose:** This document explains how Frappe/ERPNext integrates with YAM Server to connect AI capabilities with real business applications.

---

## The Integration Vision

YAM Server provides powerful local AI capabilities: inference, document understanding, vector search, and agent orchestration. But AI alone is not a business application.

**Frappe + ERPNext bridges that gap.**

Frappe is a full-stack web framework for building business applications. ERPNext is an open-source ERP built on Frappe. Together, they provide:

- **Structured data models** (DocTypes) for business entities
- **Workflows and approvals** for business processes
- **Forms and UIs** for data entry and management
- **Reports and dashboards** for business intelligence
- **Role-based access control** for multi-user environments
- **Audit trails** for compliance and accountability

When you integrate Frappe/ERPNext with YAM Server, you get:

**AI-assisted business applications that stay grounded in real operational workflows.**

---

## Architecture: Side-by-Side, Not Nested

The integration architecture is **side-by-side**, not nested.

```
┌─────────────────────┐       ┌──────────────────────┐
│   YAM Server Core   │       │  Frappe/ERPNext App  │
│                     │       │                      │
│  ┌──────────────┐   │       │  ┌───────────────┐  │
│  │ Open WebUI   │   │       │  │ Frappe Desk   │  │
│  └──────────────┘   │       │  └───────────────┘  │
│  ┌──────────────┐   │       │  ┌───────────────┐  │
│  │  LiteLLM     │◄──┼───────┼──┤ API Calls     │  │
│  └──────────────┘   │       │  └───────────────┘  │
│  ┌──────────────┐   │       │  ┌───────────────┐  │
│  │    vLLM      │   │       │  │ Custom Apps   │  │
│  └──────────────┘   │       │  └───────────────┘  │
└─────────────────────┘       └──────────────────────┘
         │                             │
         └──────────┬──────────────────┘
                    │
            ┌───────▼────────┐
            │  PostgreSQL    │
            │  ┌──────────┐  │
            │  │ Business │  │  ← Frappe tables
            │  │  Tables  │  │
            │  └──────────┘  │
            │  ┌──────────┐  │
            │  │ pgvector │  │  ← AI embeddings
            │  │ Vectors  │  │
            │  └──────────┘  │
            └────────────────┘
```

**Key principles:**

1. **Shared database** - Both systems use PostgreSQL, but in separate schemas or databases
2. **API-based communication** - Frappe calls LiteLLM API for AI features
3. **Assistive AI only** - AI suggests, humans approve, Frappe enforces business rules
4. **Independent deployment** - Each system can be updated independently
5. **Clear boundaries** - AI infrastructure vs. business application logic

---

## Integration Patterns

### Pattern 1: AI-Assisted Document Processing

**Use case:** User uploads an invoice PDF in ERPNext. System extracts data, suggests line items.

**Flow:**
```
1. User uploads PDF in ERPNext Purchase Invoice form
2. Frappe backend sends PDF to Tika (via YAM Server) for text extraction
3. Extracted text is embedded using YAM Server embeddings service
4. Frappe calls LiteLLM API with prompt: "Extract line items from this invoice"
5. LiteLLM routes to vLLM, generates structured response
6. Frappe displays suggestions in form (read-only, editable)
7. User reviews, edits if needed, saves
8. Frappe validates and saves to business tables (no AI in this step)
```

**Implementation:**
```python
# In Frappe custom app: yam_agri_core/api/invoice_assistant.py
import frappe
import requests
from frappe import _

@frappe.whitelist()
def extract_invoice_data(file_url: str) -> dict:
    """AI-assisted invoice data extraction (assistive only)."""

    # 1. Get file from Frappe
    file_doc = frappe.get_doc("File", {"file_url": file_url})
    file_content = file_doc.get_content()

    # 2. Send to YAM Server LiteLLM API
    litellm_url = frappe.conf.get("yam_server_litellm_url")
    api_key = frappe.conf.get("yam_server_api_key")

    response = requests.post(
        f"{litellm_url}/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": "default",
            "messages": [
                {
                    "role": "system",
                    "content": "You are an invoice data extraction assistant. Extract structured data in JSON format."
                },
                {
                    "role": "user",
                    "content": f"Extract invoice data from:\n\n{file_content[:2000]}"
                }
            ],
            "temperature": 0.1
        }
    )

    if response.status_code != 200:
        frappe.throw(_("AI service unavailable"), frappe.ValidationError)

    result = response.json()
    suggestion = result["choices"][0]["message"]["content"]

    # 3. Return as suggestion (not saved directly)
    return {
        "success": True,
        "suggestion": suggestion,
        "message": _("AI suggestion ready. Please review before saving.")
    }
```

**Frontend integration:**
```javascript
// In Frappe custom form script: purchase_invoice.js
frappe.ui.form.on('Purchase Invoice', {
    onload: function(frm) {
        if (frm.doc.file_url && !frm.doc.items.length) {
            frm.add_custom_button(__('Extract with AI'), function() {
                frappe.call({
                    method: 'yam_agri_core.api.invoice_assistant.extract_invoice_data',
                    args: { file_url: frm.doc.file_url },
                    callback: function(r) {
                        if (r.message.success) {
                            // Display suggestion in dialog for user review
                            show_ai_suggestion_dialog(frm, r.message.suggestion);
                        }
                    }
                });
            });
        }
    }
});

function show_ai_suggestion_dialog(frm, suggestion) {
    let d = new frappe.ui.Dialog({
        title: __('AI Suggestion (Review Required)'),
        fields: [
            {
                fieldname: 'suggestion',
                fieldtype: 'Code',
                label: __('Extracted Data'),
                options: 'JSON',
                default: suggestion
            }
        ],
        primary_action_label: __('Apply to Form'),
        primary_action: function(values) {
            // Parse and apply to form (user controls this)
            let data = JSON.parse(values.suggestion);
            apply_invoice_data_to_form(frm, data);
            d.hide();
        }
    });
    d.show();
}
```

---

### Pattern 2: AI-Powered Recommendations

**Use case:** Inventory manager views a stock item. System suggests reorder levels based on historical data.

**Flow:**
```
1. User opens Stock Item form in ERPNext
2. Frappe backend queries historical consumption data
3. Frappe calls LiteLLM API with context: "Based on this data, recommend reorder level"
4. AI analyzes patterns, returns recommendation with reasoning
5. Recommendation displayed in form sidebar (not saved automatically)
6. User can accept, modify, or ignore
```

**Implementation:**
```python
# In yam_agri_core/api/inventory_assistant.py
@frappe.whitelist()
def suggest_reorder_level(item_code: str) -> dict:
    """AI-suggested reorder levels (assistive only)."""

    # 1. Get historical data from ERPNext
    consumption_data = frappe.db.sql("""
        SELECT posting_date, actual_qty, stock_value
        FROM `tabStock Ledger Entry`
        WHERE item_code = %s
        AND posting_date > DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
        ORDER BY posting_date
    """, (item_code,), as_dict=True)

    if not consumption_data:
        return {"success": False, "message": _("Insufficient historical data")}

    # 2. Prepare context for AI
    context = f"Historical consumption for {item_code}:\n"
    context += "\n".join([
        f"{d.posting_date}: {d.actual_qty} units"
        for d in consumption_data[-30:]  # Last 30 records
    ])

    # 3. Call LiteLLM
    litellm_url = frappe.conf.get("yam_server_litellm_url")
    api_key = frappe.conf.get("yam_server_api_key")

    response = requests.post(
        f"{litellm_url}/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": "default",
            "messages": [
                {
                    "role": "system",
                    "content": "You are an inventory optimization assistant. Analyze patterns and suggest reorder levels with reasoning."
                },
                {
                    "role": "user",
                    "content": f"{context}\n\nSuggest optimal reorder level and reorder quantity. Explain your reasoning."
                }
            ],
            "temperature": 0.3
        }
    )

    result = response.json()
    suggestion = result["choices"][0]["message"]["content"]

    return {
        "success": True,
        "suggestion": suggestion,
        "message": _("AI recommendation ready. Review before applying.")
    }
```

---

### Pattern 3: Compliance Report Generation

**Use case:** QA manager needs to generate HACCP compliance report. AI drafts initial report from structured data.

**Flow:**
```
1. User clicks "Generate Report" in Quality Management module
2. Frappe gathers inspection records, test results, NCRs
3. Frappe calls LiteLLM API: "Draft HACCP compliance report from this data"
4. AI generates report following compliance template
5. Report shown in Frappe report builder (editable)
6. User reviews, adds notes, exports to PDF
7. Frappe saves final version with approval workflow
```

---

## Deployment Architecture

### Option A: Separate Containers (Recommended)

```yaml
# docker-compose.yml
services:
  # YAM Server AI Stack
  traefik:
    image: traefik:v2.10
    # ... config

  open-webui:
    image: ghcr.io/open-webui/open-webui:latest
    # ... config

  litellm:
    image: ghcr.io/berriai/litellm:latest
    # ... config

  vllm:
    image: vllm/vllm-openai:latest
    # ... config

  # Frappe/ERPNext Stack
  frappe-backend:
    image: frappe/erpnext:v16
    environment:
      - YAM_SERVER_LITELLM_URL=http://litellm:4000
      - YAM_SERVER_API_KEY=${LITELLM_API_KEY}
    # ... config

  frappe-frontend:
    image: frappe/erpnext:v16
    # ... config

  # Shared Infrastructure
  postgresql:
    image: pgvector/pgvector:pg16
    # ... config

  redis:
    image: redis:7-alpine
    # ... config
```

**Pros:**
- Clean separation of concerns
- Independent scaling
- Easier to debug and monitor
- Can update AI stack without touching ERP

**Cons:**
- More containers to manage
- Network overhead between services

---

### Option B: Frappe App with AI Integration

```yaml
# docker-compose.yml
services:
  # Frappe with integrated AI client
  frappe-backend:
    image: frappe/erpnext:v16
    environment:
      - YAM_SERVER_LITELLM_URL=http://litellm:4000
    # Custom app installed: yam_agri_core

  # YAM Server AI services (external)
  litellm:
    image: ghcr.io/berriai/litellm:latest
    # ... config

  vllm:
    image: vllm/vllm-openai:latest
    # ... config

  postgresql:
    image: pgvector/pgvector:pg16
    # ... config
```

**Pros:**
- Simpler deployment
- Single user interface (Frappe Desk)
- Tighter integration

**Cons:**
- Less modularity
- Frappe updates might affect AI integration

---

## Configuration

### Frappe Configuration (site_config.json)

```json
{
  "db_name": "erpnext_prod",
  "db_password": "***",
  "yam_server_litellm_url": "http://litellm:4000",
  "yam_server_api_key": "***",
  "yam_server_embeddings_url": "http://embeddings:8080",
  "ai_features_enabled": true,
  "ai_max_tokens": 2000,
  "ai_temperature": 0.3
}
```

### Environment Variables

```bash
# .env
FRAPPE_SITE_NAME=erp.yam.local
YAM_SERVER_LITELLM_URL=http://litellm:4000
YAM_SERVER_API_KEY=sk-yam-***
LITELLM_MODEL_ALIAS_DEFAULT=local/llama-3.2-3b-instruct
POSTGRES_DB=erpnext_prod
POSTGRES_USER=frappe
POSTGRES_PASSWORD=***
```

---

## Security Considerations

### 1. API Key Management

- **Never hardcode API keys** - Use environment variables or Frappe config
- **Rotate keys regularly** - LiteLLM supports key rotation
- **Use separate keys per app** - Different keys for different Frappe apps
- **Log all AI calls** - Audit trail for compliance

### 2. Data Privacy

- **PII redaction** - Strip sensitive data before sending to AI
- **Local-first** - Keep sensitive data on-premise with local models
- **Audit logs** - Track who triggered which AI features
- **User consent** - Make AI assistance opt-in where required

### 3. Rate Limiting

```python
# In Frappe custom app
from frappe.rate_limiter import rate_limit

@frappe.whitelist()
@rate_limit(limit=10, seconds=60)  # 10 requests per minute
def ai_assisted_feature():
    # ... call LiteLLM
    pass
```

### 4. Access Control

```python
# In Frappe custom app
@frappe.whitelist()
def ai_feature_requiring_approval():
    if not frappe.has_permission("AI Features", "use"):
        frappe.throw(_("You don't have permission to use AI features"), frappe.PermissionError)

    # ... proceed with AI call
```

---

## Testing Strategy

### Unit Tests (Frappe App)

```python
# In apps/yam_agri_core/tests/test_ai_integration.py
import frappe
import unittest
from unittest.mock import patch, MagicMock

class TestAIIntegration(unittest.TestCase):

    @patch('requests.post')
    def test_invoice_extraction_success(self, mock_post):
        # Mock LiteLLM response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": '{"invoice_number": "INV-001", "total": 1000}'
                }
            }]
        }
        mock_post.return_value = mock_response

        # Test
        from yam_agri_core.api.invoice_assistant import extract_invoice_data
        result = extract_invoice_data("file_url_here")

        self.assertTrue(result["success"])
        self.assertIn("suggestion", result)

    @patch('requests.post')
    def test_ai_service_unavailable(self, mock_post):
        # Mock service failure
        mock_post.return_value = MagicMock(status_code=503)

        # Test
        from yam_agri_core.api.invoice_assistant import extract_invoice_data
        with self.assertRaises(frappe.ValidationError):
            extract_invoice_data("file_url_here")
```

### Integration Tests

```python
# In apps/yam_agri_core/tests/test_ai_workflow.py
def test_full_invoice_workflow():
    """End-to-end test: upload PDF → AI extraction → form population."""

    # 1. Create test invoice PDF
    test_pdf = create_test_invoice_pdf()

    # 2. Upload to Frappe
    file_doc = frappe.get_doc({
        "doctype": "File",
        "file_name": "test_invoice.pdf",
        "content": test_pdf
    })
    file_doc.insert()

    # 3. Call AI extraction
    result = extract_invoice_data(file_doc.file_url)

    # 4. Verify suggestion structure
    assert result["success"]
    suggestion = json.loads(result["suggestion"])
    assert "invoice_number" in suggestion
    assert "total" in suggestion

    # 5. Cleanup
    file_doc.delete()
```

---

## Monitoring and Observability

### Metrics to Track

1. **AI call latency** - Time from Frappe → LiteLLM → response
2. **AI call success rate** - % of successful vs. failed AI calls
3. **User acceptance rate** - % of AI suggestions accepted by users
4. **Token usage** - Track LiteLLM token consumption per feature
5. **Error rates** - Track specific failure modes

### Grafana Dashboard Example

```yaml
# metrics.yaml (for yam-server-observability repo)
- name: frappe_ai_calls_total
  help: Total AI API calls from Frappe
  type: counter
  labels: [feature, model, status]

- name: frappe_ai_latency_seconds
  help: AI API call latency
  type: histogram
  labels: [feature, model]

- name: frappe_ai_suggestions_accepted_total
  help: AI suggestions accepted by users
  type: counter
  labels: [feature, user_role]
```

### Logging Best Practices

```python
# In Frappe custom app
import frappe
import logging

logger = logging.getLogger(__name__)

def ai_feature_with_logging(context: dict):
    """AI feature with comprehensive logging."""

    # Log input (redact PII)
    logger.info("AI feature triggered", extra={
        "user": frappe.session.user,
        "feature": "invoice_extraction",
        "context_size": len(str(context))
    })

    try:
        # Call AI
        result = call_litellm_api(context)

        # Log success
        logger.info("AI call succeeded", extra={
            "tokens_used": result.get("usage", {}).get("total_tokens"),
            "latency_ms": result.get("latency_ms")
        })

        return result

    except Exception as e:
        # Log failure
        logger.error("AI call failed", extra={
            "error": str(e),
            "feature": "invoice_extraction"
        })
        raise
```

---

## Migration Path

### Phase 1: Core Integration (Week 1-2)

- [ ] Set up separate Docker containers for YAM Server + Frappe
- [ ] Configure shared PostgreSQL database
- [ ] Implement basic LiteLLM API client in Frappe
- [ ] Test connectivity and auth

### Phase 2: First AI Feature (Week 3-4)

- [ ] Choose one high-value use case (e.g., invoice extraction)
- [ ] Implement AI-assisted extraction
- [ ] Build user review UI
- [ ] Test with real users
- [ ] Gather feedback

### Phase 3: Expand Features (Week 5-8)

- [ ] Add 2-3 more AI-assisted features
- [ ] Implement rate limiting and access control
- [ ] Add observability (metrics, logs, traces)
- [ ] Document patterns for developers

### Phase 4: Production Hardening (Week 9-12)

- [ ] Security audit
- [ ] Performance optimization
- [ ] Backup and disaster recovery
- [ ] User training and documentation

---

## Example: YAM Agri Use Case

For the YAM Agri Core platform (cereal supply chain quality management):

### AI-Assisted Features

1. **QC Test Analysis**
   - AI reviews moisture, protein, contamination test results
   - Suggests accept/reject decision based on FAO GAP standards
   - QA Manager reviews and approves (human in loop)

2. **CAPA Draft Generation**
   - AI drafts Corrective and Preventive Actions from nonconformance records
   - Follows HACCP templates
   - QA Manager edits and finalizes

3. **Certificate Validity Check**
   - AI monitors certificate expiry dates
   - Alerts when certificates approaching expiration
   - Blocks lot dispatch if certificates expired (enforced by Frappe workflow)

4. **Evidence Pack Summarization**
   - AI summarizes evidence packs for auditors
   - Generates executive summary from inspection records
   - Links to source documents for traceability

### Integration Points

```python
# In yam_agri_core Frappe app
from yam_agri_core.ai_gateway import suggest_qc_decision

@frappe.whitelist()
def suggest_lot_acceptance(lot_name: str) -> dict:
    """AI-suggested lot acceptance decision (assistive only)."""

    lot = frappe.get_doc("Lot", lot_name)

    # Gather test results
    tests = frappe.get_all("QCTest",
        filters={"lot": lot_name},
        fields=["test_type", "result_value", "pass_fail"]
    )

    # Call AI for suggestion
    suggestion = suggest_qc_decision(lot, tests)

    # Return for QA Manager review
    return {
        "suggestion": suggestion,
        "requires_approval": True,
        "approver_role": "QA Manager"
    }
```

---

## Resources

- [Frappe Framework Documentation](https://frappeframework.com/docs)
- [ERPNext Documentation](https://docs.erpnext.com/)
- [Frappe REST API](https://frappeframework.com/docs/user/en/api)
- [LiteLLM Proxy Docs](https://docs.litellm.ai/)
- [YAM Server Architecture](YAM_SERVER_HOW_IT_WORKS.md)
- [YAM Server Repository Blueprint](YAM_SERVER_REPO_BLUEPRINT.md)

---

**Remember:** AI is assistive, not autonomous. The human approves. The Frappe workflow enforces business rules.
