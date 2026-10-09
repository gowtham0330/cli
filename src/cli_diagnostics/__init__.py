"""Packaged CLI Diagnostics Tool."""

__version__ = "1.0.0"
__author__ = "RabTech Academy Software Engineering Intern"

from cli_diagnostics.diagnostics import run_system_diagnostics
from cli_diagnostics.events import analyze_events, process_events_file
from cli_diagnostics.models import (
    DiagnosticEvent,
    DiagnosticReport,
    DiagnosticStatus,
    EventAnalysisResult,
    ServiceHealth,
    SystemDiagnosticsResult,
)

__all__ = [
    "__version__",
    "run_system_diagnostics",
    "analyze_events",
    "process_events_file",
    "DiagnosticStatus",
    "DiagnosticEvent",
    "DiagnosticReport",
    "ServiceHealth",
    "EventAnalysisResult",
    "SystemDiagnosticsResult",
]
