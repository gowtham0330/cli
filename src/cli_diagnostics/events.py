"""Event ingestion, validation, security filtering, and health classification."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from cli_diagnostics.models import (
    DiagnosticEvent,
    DiagnosticStatus,
    EventAnalysisResult,
    EventSeverity,
    ServiceHealth,
)


class EventValidationError(ValueError):
    """Raised when diagnostic event JSON structure or values fail validation."""
    pass


def load_events_from_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Safely load and parse raw JSON diagnostic events from a file.

    Guarantees no arbitrary command execution or evaluation is performed.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Diagnostics events file not found: {file_path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise EventValidationError(f"Invalid JSON syntax in '{file_path}': {exc}") from exc
    except Exception as exc:
        raise EventValidationError(f"Failed to read events file '{file_path}': {exc}") from exc

    if not isinstance(data, dict):
        raise EventValidationError("Root JSON document must be an object with 'events'.")

    return data


def validate_single_event(raw: Any, index: int) -> DiagnosticEvent:
    """Validate a single event object according to the schema.

    Security rule: never execute or evaluate command keys.
    """
    if not isinstance(raw, dict):
        raise EventValidationError(f"Event at index {index} must be a JSON object.")

    # Explicit check for prohibited command payload fields to guard against injection
    prohibited_keys = {"command", "cmd", "exec", "eval", "script", "shell"}
    for key in prohibited_keys:
        if key in raw:
            # We strictly ignore/strip any command payload and never execute it
            pass

    # Validate timestamp
    timestamp = raw.get("timestamp")
    if not timestamp or not isinstance(timestamp, str):
        raise EventValidationError(
            f"Event at index {index} missing required 'timestamp' string."
        )

    # Validate service
    service = raw.get("service")
    if not service or not isinstance(service, str) or not service.strip():
        raise EventValidationError(
            f"Event at index {index} missing required 'service' string."
        )
    service = service.strip()

    # Validate severity
    severity_raw = raw.get("severity")
    if not severity_raw or not isinstance(severity_raw, str):
        raise EventValidationError(
            f"Event at index {index} missing required 'severity' string (INFO, WARN, ERROR)."
        )
    severity_clean = severity_raw.strip().upper()
    try:
        severity = EventSeverity(severity_clean)
    except ValueError as exc:
        raise EventValidationError(
            f"Event at index {index} has invalid severity '{severity_raw}'. "
            f"Allowed values: {[s.value for s in EventSeverity]}."
        ) from exc

    # Validate latency_ms
    latency_raw = raw.get("latency_ms")
    latency_ms: Optional[float] = None
    if latency_raw is not None:
        if not isinstance(latency_raw, (int, float)):
            raise EventValidationError(
                f"Event at index {index} has non-numeric latency_ms: {latency_raw}."
            )
        if latency_raw < 0:
            raise EventValidationError(
                f"Event at index {index} has negative latency_ms: {latency_raw}."
            )
        latency_ms = float(latency_raw)

    # Validate http_status
    http_status_raw = raw.get("http_status")
    http_status: Optional[int] = None
    if http_status_raw is not None:
        if not isinstance(http_status_raw, int):
            raise EventValidationError(
                f"Event at index {index} has non-integer http_status: {http_status_raw}."
            )
        if not (100 <= http_status_raw <= 599):
            raise EventValidationError(
                f"Event at index {index} has invalid HTTP status code: {http_status_raw}."
            )
        http_status = http_status_raw

    message = str(raw.get("message", ""))

    return DiagnosticEvent(
        timestamp=timestamp,
        service=service,
        severity=severity,
        latency_ms=latency_ms,
        http_status=http_status,
        message=message,
    )


def validate_events_payload(data: Dict[str, Any]) -> Tuple[str, List[DiagnosticEvent]]:
    """Validate top-level payload structure and all enclosed events."""
    if "events" not in data or not isinstance(data["events"], list):
        raise EventValidationError(
            "Event payload must contain an 'events' list."
        )

    generated_for = str(data.get("generated_for", "CLI Diagnostics Analysis"))
    raw_events = data["events"]

    validated_events: List[DiagnosticEvent] = []
    for idx, raw_evt in enumerate(raw_events):
        validated_events.append(validate_single_event(raw_evt, idx))

    return generated_for, validated_events


def classify_service_health(service_name: str, events: List[DiagnosticEvent]) -> ServiceHealth:
    """Analyze events for a specific service and classify its operational health."""
    total = len(events)
    info_cnt = sum(1 for e in events if e.severity == EventSeverity.INFO)
    warn_cnt = sum(1 for e in events if e.severity == EventSeverity.WARN)
    err_cnt = sum(1 for e in events if e.severity == EventSeverity.ERROR)
    http_5xx_cnt = sum(
        1 for e in events if e.http_status is not None and 500 <= e.http_status <= 599
    )
    missing_latency_cnt = sum(1 for e in events if e.latency_ms is None)

    latencies = [e.latency_ms for e in events if e.latency_ms is not None]
    avg_latency = sum(latencies) / len(latencies) if latencies else None

    reasons: List[str] = []
    health = DiagnosticStatus.HEALTHY

    if err_cnt > 0:
        health = DiagnosticStatus.UNHEALTHY
        reasons.append(f"{err_cnt} error event(s) recorded")

    if http_5xx_cnt > 0:
        health = DiagnosticStatus.UNHEALTHY
        reasons.append(f"{http_5xx_cnt} HTTP 5xx server error(s) detected")

    if health != DiagnosticStatus.UNHEALTHY:
        if warn_cnt > 0:
            health = DiagnosticStatus.WARNING
            reasons.append(f"{warn_cnt} warning event(s) recorded")
        if missing_latency_cnt > 0:
            health = DiagnosticStatus.WARNING
            reasons.append(f"{missing_latency_cnt} event(s) missing latency metric")
        if avg_latency is not None and avg_latency > 800.0:
            health = DiagnosticStatus.WARNING
            reasons.append(f"Elevated average latency: {avg_latency:.1f}ms")

    if health == DiagnosticStatus.HEALTHY:
        reasons.append("All operations within normal thresholds")

    return ServiceHealth(
        service_name=service_name,
        total_events=total,
        info_count=info_cnt,
        warn_count=warn_cnt,
        error_count=err_cnt,
        http_5xx_count=http_5xx_cnt,
        missing_latency_count=missing_latency_cnt,
        avg_latency_ms=avg_latency,
        health=health,
        reasons=reasons,
    )


def analyze_events(
    generated_for: str, events: List[DiagnosticEvent]
) -> EventAnalysisResult:
    """Consolidate, group, and analyze event metrics and service health."""
    total_events = len(events)
    info_count = sum(1 for e in events if e.severity == EventSeverity.INFO)
    warn_count = sum(1 for e in events if e.severity == EventSeverity.WARN)
    error_count = sum(1 for e in events if e.severity == EventSeverity.ERROR)
    http_5xx_count = sum(
        1 for e in events if e.http_status is not None and 500 <= e.http_status <= 599
    )
    missing_latency_count = sum(1 for e in events if e.latency_ms is None)

    # Group events by service
    grouped_services: Dict[str, List[DiagnosticEvent]] = {}
    for event in events:
        grouped_services.setdefault(event.service, []).append(event)

    services_health: Dict[str, ServiceHealth] = {}
    for service_name, service_events in sorted(grouped_services.items()):
        services_health[service_name] = classify_service_health(
            service_name, service_events
        )

    # Determine overall status string
    has_unhealthy = any(
        s.health == DiagnosticStatus.UNHEALTHY for s in services_health.values()
    )
    has_warning = any(
        s.health == DiagnosticStatus.WARNING for s in services_health.values()
    )

    summary_messages: List[str] = []
    if has_unhealthy or error_count > 0:
        overall_status = "attention required"
        is_healthy = False
        summary_messages.append(
            f"Service degradation detected: {error_count} error(s) and {http_5xx_count} HTTP 5xx failures."
        )
    elif has_warning or warn_count > 0:
        overall_status = "warning"
        is_healthy = True
        summary_messages.append(
            f"Service warnings detected: {warn_count} warning(s) and {missing_latency_count} missing latencies."
        )
    else:
        overall_status = "healthy"
        is_healthy = True
        summary_messages.append("All monitored services reporting nominal health.")

    return EventAnalysisResult(
        generated_for=generated_for,
        total_events=total_events,
        info_count=info_count,
        warn_count=warn_count,
        error_count=error_count,
        http_5xx_count=http_5xx_count,
        missing_latency_count=missing_latency_count,
        services=services_health,
        overall_status=overall_status,
        is_healthy=is_healthy,
        summary_messages=summary_messages,
    )


def process_events_file(file_path: Union[str, Path]) -> EventAnalysisResult:
    """Complete pipeline: load, validate, classify, and analyze an events file."""
    data = load_events_from_file(file_path)
    generated_for, events = validate_events_payload(data)
    return analyze_events(generated_for, events)
