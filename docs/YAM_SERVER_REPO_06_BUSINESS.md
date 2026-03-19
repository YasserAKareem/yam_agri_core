# YAM Server Business - Repository Creation Guide

> **Repository:** `yam-server-business`
> **Purpose:** Frappe/ERPNext business application layer with AI-assisted features
> **Owner:** Business Application Developers, Domain Experts
> **Release Cadence:** Moderate - follows business requirements cycle

---

## GitHub Repository Form

### Repository Name
```
yam-server-business
```

### Description
```
Frappe/ERPNext business applications for YAM Server. Custom DocTypes, workflows, and AI-assisted business features. Where AI meets operations.
```

### Topics
```
frappe, erpnext, business-apps, erp, ai-assisted, workflows,
doctypes, business-logic, yam-server
```

---

## File Structure

```
yam-server-business/
├── apps/
│   ├── yam_agriculture/               # Agriculture domain
│   │   ├── yam_agriculture/
│   │   │   ├── doctype/
│   │   │   │   ├── farm/
│   │   │   │   ├── crop_cycle/
│   │   │   │   ├── harvest/
│   │   │   │   └── quality_test/
│   │   │   ├── api/
│   │   │   │   ├── ai_crop_advisor.py
│   │   │   │   └── yield_prediction.py
│   │   │   ├── workflows/
│   │   │   │   └── harvest_approval.json
│   │   │   └── reports/
│   │   └── hooks.py
│   ├── yam_inventory/                 # Inventory management
│   │   └── yam_inventory/
│   │       ├── doctype/
│   │       │   ├── storage_location/
│   │       │   ├── stock_movement/
│   │       │   └── quality_check/
│   │       └── api/
│   │           ├── ai_demand_forecast.py
│   │           └── reorder_suggestions.py
│   └── yam_sales/                     # Sales & distribution
│       └── yam_sales/
│           ├── doctype/
│           │   ├── customer_inquiry/
│           │   ├── quotation/
│           │   └── sales_order/
│           └── api/
│               ├── ai_pricing_advisor.py
│               └── lead_scoring.py
├── integrations/
│   ├── litellm/
│   │   ├── client.py                  # LiteLLM API client
│   │   └── prompts.py                 # Prompt templates
│   ├── embeddings/
│   │   └── vector_search.py           # Document similarity
│   └── agents/
│       └── agent_caller.py            # Call YAM agents
├── fixtures/
│   ├── workflows/
│   │   └── harvest_workflow.json
│   ├── roles/
│   │   └── role_profiles.json
│   └── custom_fields/
│       └── site_fields.json
├── tests/
│   ├── test_crop_advisor.py
│   ├── test_demand_forecast.py
│   └── test_integrations.py
└── docs/
    ├── ARCHITECTURE.md
    ├── AI_INTEGRATION.md
    └── DEVELOPMENT.md
```

---

## Key Concepts

### AI-Assisted DocType

Example: Crop Advisory with AI suggestions

```python
# apps/yam_agriculture/yam_agriculture/doctype/crop_cycle/crop_cycle.py
import frappe
from frappe.model.document import Document
from yam_agriculture.api.ai_crop_advisor import get_recommendations

class CropCycle(Document):
    def validate(self):
        # Standard business logic
        if not self.expected_harvest_date:
            frappe.throw("Expected harvest date is required")

        # AI-assisted validation (advisory only)
        if self.get("request_ai_advice"):
            self.generate_ai_recommendations()

    def generate_ai_recommendations(self):
        """
        Get AI recommendations for crop management.
        AI suggests, human approves, Frappe enforces.
        """
        context = {
            "crop": self.crop,
            "location": self.farm_location,
            "soil_type": self.soil_type,
            "planting_date": self.planting_date,
            "current_stage": self.growth_stage
        }

        # Call LiteLLM via YAM Server
        recommendations = get_recommendations(context)

        # Store as read-only field for review
        self.ai_recommendations = frappe.as_json(recommendations)

        # Human must explicitly accept to apply
        frappe.msgprint(
            f"AI Recommendations ready. Review and accept to apply.",
            indicator="blue"
        )
```

### LiteLLM Integration

```python
# integrations/litellm/client.py
import httpx
import frappe

class LiteLLMClient:
    def __init__(self):
        self.base_url = frappe.conf.get("yam_server_litellm_url")
        self.api_key = frappe.conf.get("yam_server_api_key")

    async def chat_completion(
        self,
        messages: list,
        model: str = "default",
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> dict:
        """
        Call LiteLLM chat completion API.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def embeddings(self, text: str) -> list:
        """
        Generate embeddings for text.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/embeddings",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": "embeddings",
                    "input": text
                }
            )
            response.raise_for_status()
            return response.json()["data"][0]["embedding"]
```

### AI Crop Advisor

```python
# apps/yam_agriculture/yam_agriculture/api/ai_crop_advisor.py
import frappe
from integrations.litellm.client import LiteLLMClient
from integrations.litellm.prompts import CROP_ADVISOR_PROMPT

@frappe.whitelist()
async def get_recommendations(context: dict) -> dict:
    """
    Get AI-powered crop management recommendations.

    This is ASSISTIVE ONLY - recommendations must be reviewed
    and approved by agronomist before implementation.
    """
    client = LiteLLMClient()

    messages = [
        {
            "role": "system",
            "content": CROP_ADVISOR_PROMPT
        },
        {
            "role": "user",
            "content": f"""
Provide recommendations for crop cycle:
- Crop: {context['crop']}
- Location: {context['location']}
- Soil Type: {context['soil_type']}
- Growth Stage: {context['current_stage']}
- Days Since Planting: {context.get('days_since_planting', 'unknown')}

Focus on: irrigation, fertilization, pest management, harvest timing.
            """
        }
    ]

    response = await client.chat_completion(
        messages=messages,
        model="agricultural-advisor",  # Routes to appropriate model
        temperature=0.3  # Lower for factual recommendations
    )

    recommendations = response["choices"][0]["message"]["content"]

    return {
        "recommendations": recommendations,
        "confidence": "advisory",  # Always advisory, never authoritative
        "requires_review": True,
        "reviewed_by": None,
        "applied": False
    }
```

---

## README

```markdown
# YAM Server Business

> Where AI meets real operational workflows.

## What This Repository Contains

Frappe/ERPNext business applications that integrate with YAM Server AI infrastructure.

**Key Principle:** AI suggests, humans approve, Frappe enforces business rules.

## Applications

### yam_agriculture
- Farm management
- Crop cycle tracking
- Quality testing
- AI-powered crop advisory

### yam_inventory
- Multi-location inventory
- Stock movements
- Quality checks
- AI demand forecasting

### yam_sales
- Customer inquiries
- Quotations
- Sales orders
- AI pricing optimization

## AI Integration Pattern

```python
# 1. User requests AI assistance
crop_cycle.request_ai_advice = 1

# 2. System calls LiteLLM
recommendations = get_ai_recommendations(context)

# 3. Results stored in read-only field
crop_cycle.ai_recommendations = recommendations

# 4. Human reviews and decides
if agronomist_approves:
    apply_recommendations(crop_cycle, recommendations)

# 5. Frappe enforces business rules
crop_cycle.validate()  # Standard validation applies
```

## Architecture

### Side-by-Side Deployment

```
┌─────────────────┐         ┌──────────────────┐
│  Frappe/ERPNext │◄───────►│  YAM Server AI   │
│  Business Logic │  API    │  LiteLLM Gateway │
│  Port 8000      │  Calls  │  Port 8080       │
└─────────────────┘         └──────────────────┘
       │                            │
       ▼                            ▼
┌─────────────────┐         ┌──────────────────┐
│   PostgreSQL    │         │   vLLM Inference │
│   Business DB   │         │   GPU Models     │
└─────────────────┘         └──────────────────┘
```

### Integration Points

1. **API Calls:** Frappe calls LiteLLM REST API
2. **Shared Database:** Optional - read-only vector tables
3. **Webhooks:** n8n workflows trigger on Frappe events
4. **Common Auth:** OIDC via Authentik (optional)

## Development Setup

```bash
# Install Frappe/ERPNext
bench init yam-frappe --frappe-branch version-16
cd yam-frappe

# Get business apps
bench get-app https://github.com/YasserAKareem/yam-server-business.git

# Install apps
bench --site mysite install-app yam_agriculture
bench --site mysite install-app yam_inventory
bench --site mysite install-app yam_sales

# Configure YAM Server connection
# In site_config.json:
{
  "yam_server_litellm_url": "http://localhost:8080",
  "yam_server_api_key": "your-api-key"
}

# Start development
bench start
```

## AI Features

### Document Analysis
Upload invoices, contracts → Extract data → Suggest entries

### Demand Forecasting
Historical sales + seasonality → Predict demand → Reorder suggestions

### Pricing Optimization
Market rates + costs + competition → Optimal pricing → Review and approve

### Quality Prediction
Sensor data + past results → Quality forecast → Early intervention

## Safety & Governance

- **No Autonomous Actions:** AI never writes to business tables
- **Audit Trail:** All AI suggestions logged with timestamps
- **Human Approval:** Critical decisions require role-based approval
- **Explainability:** AI provides reasoning for suggestions
- **Fallback:** System works fully without AI integration

## Testing

```bash
# Run tests
cd apps/yam_agriculture
pytest

# Test AI integration
pytest tests/test_crop_advisor.py

# Test without AI (fallback)
YAM_SERVER_DISABLED=1 pytest
```
```

---

## Copilot Instructions

```markdown
## Critical Rules

1. **AI is Assistive Only** - Never write directly to business tables from AI
2. **Human Approval Required** - High-risk decisions need explicit approval
3. **Frappe Enforces Rules** - Business validation happens in Python controllers
4. **Fallback Must Work** - Platform works fully without AI integration
5. **Side-by-Side Deployment** - Don't embed YAM Server inside Frappe

## Integration Pattern

```python
# ✅ CORRECT: Assistive pattern
ai_suggestion = get_ai_recommendation(context)
crop_cycle.ai_recommendation = ai_suggestion  # Read-only field
# Human reviews and decides whether to apply

# ❌ WRONG: Autonomous action
ai_suggestion = get_ai_recommendation(context)
crop_cycle.apply_fertilizer_amount = ai_suggestion["amount"]
crop_cycle.save()  # AI directly modified business data
```

## Never Do This

- ❌ Let AI write directly to DocTypes
- ❌ Embed LiteLLM inside Frappe container
- ❌ Skip business validation for AI suggestions
- ❌ Store API keys in DocTypes or database
- ❌ Make platform dependent on AI availability
```

---

**Status:** Ready for creation
