import logging

from app.telemetry import RedactionFilter, redact_sensitive_value


def test_redact_sensitive_value_masks_known_keys_in_dict():
    redact_fields = {"access_token", "authorization"}
    payload = {
        "access_token": "secret-token",
        "nested": {"authorization": "Bearer abc.def.ghi"},
        "ok": "hello",
    }
    redacted = redact_sensitive_value(payload, None, redact_fields)
    assert redacted["access_token"] == "[REDACTED]"
    assert redacted["nested"]["authorization"] == "[REDACTED]"
    assert redacted["ok"] == "hello"


def test_redaction_filter_masks_bearer_and_extra_fields():
    redact_fields = {"access_token"}
    log_filter = RedactionFilter(redact_fields)
    record = logging.makeLogRecord(
        {
            "msg": "auth header: Bearer abc.def",
            "args": (),
            "access_token": "secret",
        }
    )
    allowed = log_filter.filter(record)
    assert allowed is True
    assert "Bearer [REDACTED]" in str(record.msg)
    assert record.access_token == "[REDACTED]"
