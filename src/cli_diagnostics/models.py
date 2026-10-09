"""Data models and type definitions for cli-diagnostics."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class DiagnosticStatus(str, Enum):
    """Health classification status."""
    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    UNHEALTHY = "UNHEALTHY"
    UNKNOWN = "UNKNOWN"

    def __str__(self) -> str:
        return self.value


class EventSeverity(str, Enum):
    """Log or diagnostic event severity level."""
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"

    def __str__(self) -> str:
        return self.value


@dataclass
class ToolCheckResult:
    """Result of inspecting an individual developer CLI tool."""
    tool: str
    installed: bool
    version: Optional[str] = None
    path: Optional[str] = None
    status: DiagnosticStatus = DiagnosticStatus.HEALTHY
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool": self.tool,
            "installed": self.installed,
            "version": self.version,
            "path": self.path,
            "status": self.status.value,
            "message": self.message,
        }


@dataclass
class DiskCheckResult:
    """Result of disk storage capacity inspection."""
    total_mb: float
    used_mb: float
    free_mb: float
    used_percent: float
    min_required_mb: float
    status: DiagnosticStatus
    message: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_mb": round(self.total_mb, 2),
            "used_mb": round(self.used_mb, 2),
            "free_mb": round(self.free_mb, 2),
            "used_percent": round(self.used_percent, 2),
            "min_required_mb": round(self.min_required_mb, 2),
            "status": self.status.value,
            "message": self.message,
        }


@dataclass
class PythonCheckResult:
    """Result of Python runtime diagnostics."""
    version: str
    major: int
    minor: int
    micro: int
    implementation: str
    executable: str
    is_supported: bool
    status: DiagnosticStatus
    message: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "major": self.major,
            "minor": self.minor,
            "micro": self.micro,
            "implementation": self.implementation,
            "executable": self.executable,
            "is_supported": self.is_supported,
            "status": self.status.value,
            "message": self.message,
        }


@dataclass
class OSCheckResult:
    """Result of host operating system inspection."""
    system: str
    release: str
    version: str
    machine: str
    platform_string: str
    status: DiagnosticStatus = DiagnosticStatus.HEALTHY

    def to_dict(self) -> Dict[str, Any]:
        return {
            "system": self.system,
            "release": self.release,
            "version": self.version,
            "machine": self.machine,
            "platform": self.platform_string,
            "status": self.status.value,
        }


@dataclass
class SystemDiagnosticsResult:
    """Consolidated host system diagnostics."""
    python_info: PythonCheckResult
    os_info: OSCheckResult
    disk_info: DiskCheckResult
    env_vars: Dict[str, str]
    developer_tools: Dict[str, ToolCheckResult]
    overall_status: DiagnosticStatus
    warnings_count: int
    errors_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "python": self.python_info.to_dict(),
            "os": self.os_info.to_dict(),
            "disk": self.disk_info.to_dict(),
            "env_vars": self.env_vars,
            "developer_tools": {
                k: v.to_dict() for k, v in self.developer_tools.items()
            },
            "overall_status": self.overall_status.value,
            "warnings_count": self.warnings_count,
            "errors_count": self.errors_count,
        }


@dataclass
class DiagnosticEvent:
    """Validated single diagnostic event."""
    timestamp: str
    service: str
    severity: EventSeverity
    latency_ms: Optional[float]
    http_status: Optional[int]
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "service": self.service,
            "severity": self.severity.value,
            "latency_ms": self.latency_ms,
            "http_status": self.http_status,
            "message": self.message,
        }


@dataclass
class ServiceHealth:
    """Aggregated health classification metrics for an individual service."""
    service_name: str
    total_events: int
    info_count: int
    warn_count: int
    error_count: int
    http_5xx_count: int
    missing_latency_count: int
    avg_latency_ms: Optional[float]
    health: DiagnosticStatus
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "service_name": self.service_name,
            "total_events": self.total_events,
            "info_count": self.info_count,
            "warn_count": self.warn_count,
            "error_count": self.error_count,
            "http_5xx_count": self.http_5xx_count,
            "missing_latency_count": self.missing_latency_count,
            "avg_latency_ms": (
                round(self.avg_latency_ms, 2)
                if self.avg_latency_ms is not None
                else None
            ),
            "health": self.health.value,
            "reasons": self.reasons,
        }


@dataclass
class EventAnalysisResult:
    """Aggregate diagnostic events analysis and health summary."""
    generated_for: str
    total_events: int
    info_count: int
    warn_count: int
    error_count: int
    http_5xx_count: int
    missing_latency_count: int
    services: Dict[str, ServiceHealth]
    overall_status: str
    is_healthy: bool
    summary_messages: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "generated_for": self.generated_for,
            "total_events": self.total_events,
            "info_count": self.info_count,
            "warn_count": self.warn_count,
            "error_count": self.error_count,
            "http_5xx_count": self.http_5xx_count,
            "missing_latency_count": self.missing_latency_count,
            "services": {k: v.to_dict() for k, v in self.services.items()},
            "overall_status": self.overall_status,
            "is_healthy": self.is_healthy,
            "summary_messages": self.summary_messages,
        }


@dataclass
class DiagnosticReport:
    """Consolidated diagnostic report combining system and event checks."""
    timestamp: str
    tool_name: str
    tool_version: str
    system_diagnostics: SystemDiagnosticsResult
    event_analysis: Optional[EventAnalysisResult]
    overall_status: str
    exit_code: int
    strict_mode: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "tool_version": self.tool_version,
            "timestamp": self.timestamp,
            "strict_mode": self.strict_mode,
            "exit_code": self.exit_code,
            "overall_status": self.overall_status,
            "system_diagnostics": self.system_diagnostics.to_dict(),
            "event_analysis": (
                self.event_analysis.to_dict()
                if self.event_analysis is not None
                else None
            ),
        }
