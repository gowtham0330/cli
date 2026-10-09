"""Module alias for package initialization."""

from cli_diagnostics import (
    DiagnosticEvent,
    DiagnosticReport,
    DiagnosticStatus,
    EventAnalysisResult,
    ServiceHealth,
    SystemDiagnosticsResult,
    __author__,
    __version__,
    analyze_events,
    process_events_file,
    run_system_diagnostics,
)

__all__ = [
    "__version__",
    "__author__",
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
