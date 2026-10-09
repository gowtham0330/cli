"""Automated tests for CLI arguments, execution pipeline, and exit codes."""

from pathlib import Path
from unittest.mock import patch

import pytest

from cli_diagnostics.cli import (
    EXIT_DIAGNOSTIC_FAILURE,
    EXIT_INTERNAL_ERROR,
    EXIT_SUCCESS,
    EXIT_USAGE_OR_INPUT_ERROR,
    main,
)
from cli_diagnostics.models import (
    DiagnosticStatus,
    DiskCheckResult,
    OSCheckResult,
    PythonCheckResult,
    SystemDiagnosticsResult,
    ToolCheckResult,
)


def _mock_healthy_system():
    """Return mock system diagnostics with 0 errors and 0 warnings."""
    return SystemDiagnosticsResult(
        python_info=PythonCheckResult(
            version="3.10.12",
            major=3,
            minor=10,
            micro=12,
            implementation="CPython",
            executable="/usr/bin/python3",
            is_supported=True,
            status=DiagnosticStatus.HEALTHY,
            message="Python supported",
        ),
        os_info=OSCheckResult(
            system="Linux",
            release="6.1.0",
            version="1",
            machine="x86_64",
            platform_string="Linux-x86_64",
            status=DiagnosticStatus.HEALTHY,
        ),
        disk_info=DiskCheckResult(
            total_mb=50000.0,
            used_mb=10000.0,
            free_mb=40000.0,
            used_percent=20.0,
            min_required_mb=1024.0,
            status=DiagnosticStatus.HEALTHY,
            message="Disk healthy",
        ),
        env_vars={"PATH": "/usr/bin"},
        developer_tools={
            "git": ToolCheckResult(
                tool="git",
                installed=True,
                version="git 2.34",
                path="/usr/bin/git",
                status=DiagnosticStatus.HEALTHY,
            )
        },
        overall_status=DiagnosticStatus.HEALTHY,
        warnings_count=0,
        errors_count=0,
    )


def test_cli_version(capsys):
    """Verify cli-diagnostics --version output and exit code."""
    ret = main(["--version"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "cli-diagnostics 1.0.0" in captured.out


def test_cli_help(capsys):
    """Verify cli-diagnostics --help output and exit code."""
    ret = main(["--help"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "Packaged CLI Diagnostics Tool" in captured.out
    assert "--events" in captured.out
    assert "--strict" in captured.out
    assert "--json-output" in captured.out


def test_cli_run_sample_events_diagnostic_failure(tmp_path):
    """Verify exit code 1 when evaluating sample diagnostic events with unhealthy service."""
    json_out = tmp_path / "report.json"
    ret = main(
        [
            "run",
            "--events",
            "samples/diagnostic-events.json",
            "--json-output",
            str(json_out),
            "--pretty",
        ]
    )
    # Since billing-api has 2 errors and HTTP 5xx, exit code must be 1 (DIAGNOSTIC FAILURE)
    assert ret == EXIT_DIAGNOSTIC_FAILURE
    assert json_out.exists()


def test_cli_run_healthy_system():
    """Verify exit code 0 when all diagnostics pass."""
    with patch("cli_diagnostics.cli.run_system_diagnostics", return_value=_mock_healthy_system()):
        ret = main([])
        assert ret == EXIT_SUCCESS


def test_cli_run_strict_mode_escalates_warning():
    """Verify strict mode causes exit code 1 on system warnings."""
    mock_sys = _mock_healthy_system()
    mock_sys.overall_status = DiagnosticStatus.WARNING
    mock_sys.warnings_count = 1

    with patch("cli_diagnostics.cli.run_system_diagnostics", return_value=mock_sys):
        # Without strict: should exit 0
        ret_normal = main([])
        assert ret_normal == EXIT_SUCCESS

        # With strict: should exit 1
        ret_strict = main(["--strict"])
        assert ret_strict == EXIT_DIAGNOSTIC_FAILURE


def test_cli_missing_events_file():
    """Verify exit code 2 when specified events file does not exist."""
    ret = main(["run", "--events", "nonexistent-events-file-12345.json"])
    assert ret == EXIT_USAGE_OR_INPUT_ERROR


def test_cli_invalid_json_events_file(tmp_path):
    """Verify exit code 2 when events file contains malformed JSON."""
    bad_file = tmp_path / "broken.json"
    bad_file.write_text("{ broken: json", encoding="utf-8")
    ret = main(["--events", str(bad_file)])
    assert ret == EXIT_USAGE_OR_INPUT_ERROR


def test_cli_negative_min_disk():
    """Verify exit code 2 when negative min-disk-mb is supplied."""
    ret = main(["--min-disk-mb", "-500"])
    assert ret == EXIT_USAGE_OR_INPUT_ERROR


def test_cli_internal_error_handling():
    """Verify exit code 3 on unexpected internal system failure."""
    with patch(
        "cli_diagnostics.cli.run_system_diagnostics",
        side_effect=RuntimeError("Hardware fault"),
    ):
        ret = main([])
        assert ret == EXIT_INTERNAL_ERROR
