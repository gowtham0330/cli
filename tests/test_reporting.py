"""Tests for diagnostic report generation and output serialization."""

import json
from pathlib import Path

from cli_diagnostics.models import (
    DiagnosticReport,
    DiagnosticStatus,
    DiskCheckResult,
    OSCheckResult,
    PythonCheckResult,
    SystemDiagnosticsResult,
    ToolCheckResult,
)
from cli_diagnostics.reporting import (
    format_json_report,
    format_terminal_report,
    write_reports,
)


def _make_sample_report(with_events: bool = False) -> DiagnosticReport:
    """Helper fixture to construct mock DiagnosticReport."""
    py_res = PythonCheckResult(
        version="3.10.12",
        major=3,
        minor=10,
        micro=12,
        implementation="CPython",
        executable="/usr/bin/python3",
        is_supported=True,
        status=DiagnosticStatus.HEALTHY,
        message="Python 3.10.12 satisfies runtime requirements.",
    )
    os_res = OSCheckResult(
        system="Linux",
        release="6.1.0",
        version="#1 SMP",
        machine="x86_64",
        platform_string="Linux-6.1.0-x86_64",
        status=DiagnosticStatus.HEALTHY,
    )
    disk_res = DiskCheckResult(
        total_mb=50000.0,
        used_mb=10000.0,
        free_mb=40000.0,
        used_percent=20.0,
        min_required_mb=1024.0,
        status=DiagnosticStatus.HEALTHY,
        message="Adequate storage available.",
    )
    dev_tools = {
        "git": ToolCheckResult(
            tool="git",
            installed=True,
            version="git version 2.34.1",
            path="/usr/bin/git",
            status=DiagnosticStatus.HEALTHY,
        ),
        "docker": ToolCheckResult(
            tool="docker",
            installed=False,
            version=None,
            path=None,
            status=DiagnosticStatus.WARNING,
            message="Tool 'docker' was not found in PATH.",
        ),
    }
    sys_diag = SystemDiagnosticsResult(
        python_info=py_res,
        os_info=os_res,
        disk_info=disk_res,
        env_vars={"PATH": "/usr/bin:/bin", "USER": "tester"},
        developer_tools=dev_tools,
        overall_status=DiagnosticStatus.WARNING,
        warnings_count=1,
        errors_count=0,
    )

    event_analysis = None
    if with_events:
        from cli_diagnostics.events import process_events_file

        event_analysis = process_events_file(Path("samples/diagnostic-events.json"))

    return DiagnosticReport(
        timestamp="2026-10-09T14:00:00Z",
        tool_name="cli-diagnostics",
        tool_version="1.0.0",
        system_diagnostics=sys_diag,
        event_analysis=event_analysis,
        overall_status="attention required" if with_events else "warning",
        exit_code=1 if with_events else 0,
        strict_mode=False,
    )


def test_format_terminal_report_sections():
    """Verify standard sections appear in terminal report."""
    report = _make_sample_report(with_events=False)
    output = format_terminal_report(report, pretty=True)

    assert "CLI-DIAGNOSTICS REPORT" in output
    assert "1. SYSTEM & RUNTIME ENVIRONMENT" in output
    assert "2. DEVELOPER TOOLCHAIN DIAGNOSTICS" in output
    assert "3. ENVIRONMENT VARIABLES (REDACTED AUDIT)" in output
    assert "git" in output
    assert "docker" in output
    assert "EXECUTION RESULT: SUCCESS (Exit Code 0)" in output


def test_format_terminal_report_with_events():
    """Verify events section in terminal report."""
    report = _make_sample_report(with_events=True)
    output = format_terminal_report(report, pretty=True)

    assert "4. DIAGNOSTIC EVENTS & SERVICE HEALTH" in output
    assert "billing-api" in output
    assert "profile-api" in output
    assert "UNHEALTHY" in output
    assert "HEALTHY" in output
    assert "EXECUTION RESULT: DIAGNOSTIC FAILURE" in output


def test_format_json_report_schema():
    """Verify JSON report serializes valid schema with all key fields."""
    report = _make_sample_report(with_events=True)
    json_str = format_json_report(report)
    data = json.loads(json_str)

    assert data["tool_name"] == "cli-diagnostics"
    assert data["tool_version"] == "1.0.0"
    assert data["overall_status"] == "attention required"
    assert "system_diagnostics" in data
    assert "event_analysis" in data
    assert data["event_analysis"]["total_events"] == 5
    assert data["event_analysis"]["services"]["billing-api"]["health"] == "UNHEALTHY"


def test_write_reports_to_files(tmp_path):
    """Verify writing text and JSON reports to disk."""
    report = _make_sample_report(with_events=True)
    text_out = tmp_path / "reports" / "report.txt"
    json_out = tmp_path / "reports" / "report.json"

    write_reports(
        report=report,
        text_path=str(text_out),
        json_path=str(json_out),
        pretty=True,
    )

    assert text_out.exists()
    assert json_out.exists()
    assert text_out.read_text(encoding="utf-8").startswith("=======")
    loaded_json = json.loads(json_out.read_text(encoding="utf-8"))
    assert loaded_json["tool_name"] == "cli-diagnostics"
