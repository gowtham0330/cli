"""Tests for system, environment, and tool diagnostics."""

from collections import namedtuple
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

from cli_diagnostics.diagnostics import (
    check_developer_tools,
    check_disk_space,
    check_os,
    check_python_version,
    check_single_tool,
    inspect_environment_variables,
    is_sensitive_key,
    redact_value,
    run_system_diagnostics,
)
from cli_diagnostics.models import DiagnosticStatus


def test_check_python_version_current():
    """Verify that current runtime python version check returns valid result."""
    result = check_python_version()
    assert result.major == sys.version_info.major
    assert result.minor == sys.version_info.minor
    assert result.is_supported is True
    assert result.status == DiagnosticStatus.HEALTHY
    assert "satisfies runtime requirements" in result.message


def test_check_python_version_unsupported(monkeypatch):
    """Verify that Python versions below 3.10 fail runtime check."""
    fake_version = namedtuple("version_info", ["major", "minor", "micro"])(3, 9, 2)
    monkeypatch.setattr(sys, "version_info", fake_version)
    result = check_python_version()
    assert result.is_supported is False
    assert result.status == DiagnosticStatus.UNHEALTHY
    assert "below the required 3.10+ baseline" in result.message


def test_check_os_structure():
    """Verify operating system details inspection."""
    os_info = check_os()
    assert os_info.system != ""
    assert os_info.machine != ""
    assert os_info.status == DiagnosticStatus.HEALTHY
    d = os_info.to_dict()
    assert "platform" in d
    assert "system" in d


def test_check_disk_space_healthy():
    """Verify disk check when free space is ample."""
    fake_usage = namedtuple("usage", ["total", "used", "free"])(
        total=100 * 1024 * 1024 * 1024,
        used=20 * 1024 * 1024 * 1024,
        free=80 * 1024 * 1024 * 1024,
    )
    with patch("shutil.disk_usage", return_value=fake_usage):
        result = check_disk_space(".", min_disk_mb=1024.0)
        assert result.status == DiagnosticStatus.HEALTHY
        assert result.free_mb > 1024.0
        assert result.used_percent == pytest.approx(20.0, rel=1e-2)


def test_check_disk_space_unhealthy():
    """Verify disk check fails when free space falls below min_disk_mb."""
    fake_usage = namedtuple("usage", ["total", "used", "free"])(
        total=10 * 1024 * 1024 * 1024,
        used=9.8 * 1024 * 1024 * 1024,
        free=200 * 1024 * 1024,  # 200 MB free
    )
    with patch("shutil.disk_usage", return_value=fake_usage):
        result = check_disk_space(".", min_disk_mb=1024.0)
        assert result.status == DiagnosticStatus.UNHEALTHY
        assert "is below the required minimum" in result.message


def test_check_disk_space_warning_near_threshold():
    """Verify disk check generates warning when approaching min threshold."""
    fake_usage = namedtuple("usage", ["total", "used", "free"])(
        total=10 * 1024 * 1024 * 1024,
        used=8.8 * 1024 * 1024 * 1024,
        free=1200 * 1024 * 1024,  # 1200 MB free, between 1024 and 1536 MB
    )
    with patch("shutil.disk_usage", return_value=fake_usage):
        result = check_disk_space(".", min_disk_mb=1024.0)
        assert result.status == DiagnosticStatus.WARNING
        assert "approaching minimum threshold" in result.message


def test_check_disk_space_exception_handling():
    """Verify graceful handling if disk usage querying fails."""
    with patch("shutil.disk_usage", side_effect=OSError("Drive access denied")):
        result = check_disk_space("/invalid/path", min_disk_mb=500.0)
        assert result.status == DiagnosticStatus.UNHEALTHY
        assert "Unable to query disk capacity" in result.message


def test_is_sensitive_key():
    """Verify detection of secret/credential keywords in environment keys."""
    assert is_sensitive_key("AWS_SECRET_ACCESS_KEY") is True
    assert is_sensitive_key("GITHUB_TOKEN") is True
    assert is_sensitive_key("DATABASE_PASSWORD") is True
    assert is_sensitive_key("API_KEY") is True
    assert is_sensitive_key("AUTH_HEADER") is True
    assert is_sensitive_key("PRIVATE_KEY") is True
    assert is_sensitive_key("PATH") is False
    assert is_sensitive_key("USER") is False
    assert is_sensitive_key("HOME") is False


def test_redact_value():
    """Verify sensitive value masking."""
    assert redact_value("AWS_SECRET_KEY", "super-secret-12345") == "***REDACTED***"
    assert redact_value("USER", "intern_user") == "intern_user"
    assert redact_value("EMPTY_VAR", "") == "<empty>"


def test_inspect_environment_variables(monkeypatch):
    """Verify environment variables inspection with automated redaction."""
    fake_env = {
        "PATH": "/usr/bin:/bin",
        "USER": "rabtech_user",
        "STRIPE_API_KEY": "sk_live_981273918237912837192",
        "DATABASE_PASSWORD": "super_secret_pw",
    }
    monkeypatch.setattr(os, "environ", fake_env)
    res = inspect_environment_variables(["PATH", "USER", "STRIPE_API_KEY"])

    assert res["PATH"] == "/usr/bin:/bin"
    assert res["USER"] == "rabtech_user"
    assert res["STRIPE_API_KEY"] == "***REDACTED***"
    # Unlisted sensitive variable from os.environ is also captured and redacted
    assert res["DATABASE_PASSWORD"] == "***REDACTED***"


def test_check_single_tool_installed():
    """Verify tool check when tool is available in PATH."""
    with patch("shutil.which", return_value="/usr/bin/git"):
        fake_proc = MagicMock(stdout="git version 2.34.1\n", stderr="", returncode=0)
        with patch("subprocess.run", return_value=fake_proc):
            res = check_single_tool("git")
            assert res.installed is True
            assert res.status == DiagnosticStatus.HEALTHY
            assert res.path == "/usr/bin/git"
            assert "git version 2.34.1" in (res.version or "")


def test_check_single_tool_missing():
    """Verify tool check when tool is not found in PATH."""
    with patch("shutil.which", return_value=None):
        res = check_single_tool("docker")
        assert res.installed is False
        assert res.status == DiagnosticStatus.WARNING
        assert res.path is None
        assert "was not found in PATH" in res.message


def test_check_developer_tools():
    """Verify batch developer tool chain check."""
    tools = ["git", "pip", "pytest", "node", "npm", "docker"]
    with patch("shutil.which", return_value="/fake/bin/tool"):
        fake_proc = MagicMock(stdout="tool v1.0.0\n", returncode=0)
        with patch("subprocess.run", return_value=fake_proc):
            results = check_developer_tools(tools)
            assert len(results) == 6
            for t in tools:
                assert t in results
                assert results[t].installed is True


def test_run_system_diagnostics_aggregation():
    """Verify end-to-end system diagnostics aggregation."""
    with patch("cli_diagnostics.diagnostics.check_python_version") as mock_py:
        mock_py.return_value = MagicMock(status=DiagnosticStatus.HEALTHY, is_supported=True)
        with patch("cli_diagnostics.diagnostics.check_disk_space") as mock_disk:
            mock_disk.return_value = MagicMock(status=DiagnosticStatus.HEALTHY)
            with patch("cli_diagnostics.diagnostics.check_developer_tools") as mock_tools:
                mock_tools.return_value = {
                    "git": MagicMock(status=DiagnosticStatus.HEALTHY, installed=True),
                    "docker": MagicMock(status=DiagnosticStatus.WARNING, installed=False),
                }
                res = run_system_diagnostics()
                assert res.warnings_count == 1
                assert res.errors_count == 0
                assert res.overall_status == DiagnosticStatus.WARNING
