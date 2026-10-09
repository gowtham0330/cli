"""Report formatting and persistence for terminal and JSON outputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from cli_diagnostics.models import (
    DiagnosticReport,
    DiagnosticStatus,
)


def _status_badge(status: DiagnosticStatus) -> str:
    """Format status indicator badge for terminal output."""
    if status == DiagnosticStatus.HEALTHY:
        return "[PASS] "
    elif status == DiagnosticStatus.WARNING:
        return "[WARN] "
    elif status == DiagnosticStatus.UNHEALTHY:
        return "[FAIL] "
    return "[INFO] "


def format_terminal_report(report: DiagnosticReport, pretty: bool = True) -> str:
    """Generate a clean, professional, readable terminal diagnostics report."""
    lines: list[str] = []
    width = 78
    divider = "=" * width
    sub_divider = "-" * width

    # Header
    lines.append(divider)
    lines.append(f"  {report.tool_name.upper()} REPORT  -  v{report.tool_version}")
    lines.append(divider)
    lines.append(f"Generated At : {report.timestamp}")
    lines.append(f"Strict Mode  : {'ENABLED' if report.strict_mode else 'DISABLED'}")
    lines.append(f"Exit Code    : {report.exit_code}")
    lines.append(f"Final Status : {report.overall_status.upper()}")
    lines.append("")

    # 1. Host System Runtime Diagnostics
    sys_diag = report.system_diagnostics
    lines.append("1. SYSTEM & RUNTIME ENVIRONMENT")
    lines.append(sub_divider)

    py = sys_diag.python_info
    lines.append(
        f"{_status_badge(py.status)} Python Runtime : {py.implementation} {py.version} ({py.executable})"
    )
    if not py.is_supported:
        lines.append(f"        -> {py.message}")

    os_info = sys_diag.os_info
    lines.append(
        f"{_status_badge(os_info.status)} Operating System: {os_info.system} {os_info.release} ({os_info.machine})"
    )
    lines.append(f"        Platform Details: {os_info.platform_string}")

    disk = sys_diag.disk_info
    lines.append(
        f"{_status_badge(disk.status)} Disk Capacity   : {disk.free_mb:.1f} MB Free / {disk.total_mb:.1f} MB Total "
        f"({disk.used_percent:.1f}% used, required: {disk.min_required_mb:.1f} MB)"
    )
    lines.append(f"        Storage Status  : {disk.message}")
    lines.append("")

    # 2. Developer Toolchain Check
    lines.append("2. DEVELOPER TOOLCHAIN DIAGNOSTICS")
    lines.append(sub_divider)
    lines.append(f"{'TOOL':<10} {'STATUS':<10} {'VERSION / DETAILS':<40} {'PATH'}")
    lines.append("-" * 78)

    for tool_name, tool_res in sys_diag.developer_tools.items():
        status_label = "INSTALLED" if tool_res.installed else "MISSING"
        ver = (tool_res.version or "N/A")[:38]
        path_str = tool_res.path or "-"
        lines.append(f"{tool_name:<10} {status_label:<10} {ver:<40} {path_str}")
    lines.append("")

    # 3. Environment Variables (Redacted)
    lines.append("3. ENVIRONMENT VARIABLES (REDACTED AUDIT)")
    lines.append(sub_divider)
    for env_k, env_v in sorted(sys_diag.env_vars.items()):
        lines.append(f"  {env_k:<20} = {env_v}")
    lines.append("")

    # 4. Telemetry Event Analysis
    if report.event_analysis:
        evt = report.event_analysis
        lines.append("4. DIAGNOSTIC EVENTS & SERVICE HEALTH")
        lines.append(sub_divider)
        lines.append(f"Target / Context    : {evt.generated_for}")
        lines.append(f"Total Events Loaded : {evt.total_events}")
        lines.append(
            f"Severity Breakdown  : INFO: {evt.info_count}  |  WARN: {evt.warn_count}  |  ERROR: {evt.error_count}"
        )
        lines.append(
            f"Failure Metrics     : HTTP 5xx: {evt.http_5xx_count}  |  Missing Latency: {evt.missing_latency_count}"
        )
        lines.append("")
        lines.append("Service Health Breakdown:")
        lines.append(
            f"{'SERVICE':<16} {'EVENTS':<8} {'ERR':<6} {'WARN':<6} {'5XX':<6} {'NO_LAT':<8} {'AVG_LAT':<12} {'HEALTH'}"
        )
        lines.append("-" * 78)

        for s_name, s_health in evt.services.items():
            avg_str = (
                f"{s_health.avg_latency_ms:.1f} ms"
                if s_health.avg_latency_ms is not None
                else "N/A"
            )
            lines.append(
                f"{s_name:<16} {s_health.total_events:<8} {s_health.error_count:<6} "
                f"{s_health.warn_count:<6} {s_health.http_5xx_count:<6} "
                f"{s_health.missing_latency_count:<8} {avg_str:<12} {s_health.health.value}"
            )
            for reason in s_health.reasons:
                lines.append(f"    * {reason}")

        lines.append("")
        lines.append(f"Service Evaluation : {evt.overall_status.upper()}")
        for msg in evt.summary_messages:
            lines.append(f"  -> {msg}")
        lines.append("")

    # Footer
    lines.append(divider)
    if report.exit_code == 0:
        lines.append("  EXECUTION RESULT: SUCCESS (Exit Code 0)")
    elif report.exit_code == 1:
        lines.append("  EXECUTION RESULT: DIAGNOSTIC FAILURE / ATTENTION REQUIRED (Exit Code 1)")
    elif report.exit_code == 2:
        lines.append("  EXECUTION RESULT: USAGE OR INPUT ERROR (Exit Code 2)")
    else:
        lines.append("  EXECUTION RESULT: INTERNAL ERROR (Exit Code 3)")
    lines.append(divider)

    return "\n".join(lines)


def format_json_report(report: DiagnosticReport, indent: int = 2) -> str:
    """Serialize the complete diagnostic report to structured JSON."""
    return json.dumps(report.to_dict(), indent=indent, ensure_ascii=False)


def write_reports(
    report: DiagnosticReport,
    text_path: Optional[str] = None,
    json_path: Optional[str] = None,
    pretty: bool = True,
) -> None:
    """Save formatted report to disk if destination paths were specified."""
    if text_path:
        out_p = Path(text_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            f.write(format_terminal_report(report, pretty=pretty))

    if json_path:
        out_j = Path(json_path)
        out_j.parent.mkdir(parents=True, exist_ok=True)
        with open(out_j, "w", encoding="utf-8") as f:
            f.write(format_json_report(report, indent=2 if pretty else None))
