from __future__ import annotations

import asyncio

from tools.ai_gateway import app as gateway


def test_redact_text_masks_supported_sensitive_patterns():
	text = "qa@example.com +967 777 123 456 USD 120 customer_id: CUST-1 15.12345, 44.98765"
	redacted, count = gateway._redact_text(text)

	assert count >= 5
	assert "[REDACTED_EMAIL]" in redacted
	assert "[REDACTED_PHONE]" in redacted
	assert "[REDACTED_PRICE]" in redacted
	assert "[REDACTED_CUSTOMER_ID]" in redacted
	assert "[REDACTED_GPS]" in redacted


def test_suggest_response_includes_redaction_and_governance_metadata():
	payload = gateway.SuggestRequest(
		task="compliance-check",
		site="SITE-A",
		record_type="Lot",
		record_name="LOT-001",
		context="customer_id: CUST-77 USD 900 contact qa@example.com",
	)

	result = asyncio.run(gateway.suggest(payload))

	assert result.ok is True
	assert result.assistive_only is True
	assert result.decision_required is True
	assert result.redaction_applied is True
	assert result.redaction_count >= 3
	assert result.template_id == "lot_compliance"
	assert result.model in gateway.ALLOWED_MODEL_SET
	assert result.tokens_used > 0
