"""Host system and runtime diagnostic checks."""

from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
import sys
from typing import Dict, List, Optional

from cli_diagnostics.models import (
    DiagnosticStatus,
    DiskCheckResult,
    OSCheckResult,
    PythonCheckResult,
    SystemDiagnosticsResult,
    ToolCheckResult,
)

# Standard developer tools to check
TARGET_DEV_TOOLS = ["git", "pip", "pytest", "node", "npm", "docker"]

# Standard environment variables to inspect safely
SELECTED_ENV_VARS = [
    "PATH",
    "SHELL",
    "USER",
    "LOGNAME",
    "HOME",
    "LANG",
    "LC_ALL",
    "TERM",
    "PYTHONPATH",
    "VIRTUAL_ENV",
    "CONDA_DEFAULT_ENV",
    "TEMP",
    "TMP",
]

# Case-insensitive patterns indicating sensitive environment variables
SENSITIVE_KEY_PATTERNS = [
    r"KEY",
    r"SECRET",
    r"TOKEN",
    r"PASSW(OR)?D",
    r"AUTH",
    r"CRED(ENTIAL)?",
    r"PRIVATE",
    r"SIGNATURE",
    r"CERT",
    r"API",
]
SENSITIVE_REGEX = re.compile("|".join(SENSITIVE_KEY_PATTERNS), re.IGNORECASE)


def is_sensitive_key(key: str) -> bool:
    """Determine if an environment variable key is likely sensitive."""
    return bool(SENSITIVE_REGEX.search(key))


def redact_value(key: str, value: str) -> str:
    """Redact sensitive environment variable values."""
    if not value:
        return "<empty>"
    if is_sensitive_key(key):
        return "***REDACTED***"
    # Basic heuristic for values that look like secrets (e.g. bearer, hex/b64 tokens > 28 chars)
    if len(value) > 32 and re.match(r"^[A-Za-z0-9_\-\.]{32,}$", value):
        return f"{value[:4]}***[REDACTED]***{value[-3:]}"
    return value


def check_python_version() -> PythonCheckResult:
    """Inspect current Python interpreter version and capability."""
    version_tuple = sys.version_info
    major, minor, micro = version_tuple.major, version_tuple.minor, version_tuple.micro
    version_str = f"{major}.{minor}.{micro}"
    is_supported = (major, minor) >= (3, 10)

    if not is_supported:
        status = DiagnosticStatus.UNHEALTHY
        msg = f"Python {version_str} is below the required 3.10+ baseline."
    else:
        status = DiagnosticStatus.HEALTHY
        msg = f"Python {version_str} satisfies runtime requirements."

    return PythonCheckResult(
        version=version_str,
        major=major,
        minor=minor,
        micro=micro,
        implementation=platform.python_implementation(),
        executable=sys.executable,
        is_supported=is_supported,
        status=status,
        message=msg,
    )


def check_os() -> OSCheckResult:
    """Gather host operating system metadata."""
    return OSCheckResult(
        system=platform.system(),
        release=platform.release(),
        version=platform.version(),
        machine=platform.machine(),
        platform_string=platform.platform(),
        status=DiagnosticStatus.HEALTHY,
    )


def check_disk_space(
    target_path: str = ".", min_disk_mb: float = 1024.0
) -> DiskCheckResult:
    """Inspect disk space for target path against required minimum threshold."""
    resolved_path = os.path.abspath(target_path)
    # Ensure checking against an existing directory
    check_dir = resolved_path if os.path.isdir(resolved_path) else os.path.dirname(resolved_path)
    if not os.path.exists(check_dir):
        check_dir = "."

    try:
        usage = shutil.disk_usage(check_dir)
        total_mb = usage.total / (1024 * 1024)
        used_mb = usage.used / (1024 * 1024)
        free_mb = usage.free / (1024 * 1024)
        used_percent = (usage.used / usage.total) * 100.0 if usage.total > 0 else 0.0

        if free_mb < min_disk_mb:
            status = DiagnosticStatus.UNHEALTHY
            msg = (
                f"Free disk space ({free_mb:.1f} MB) is below the "
                f"required minimum of {min_disk_mb:.1f} MB."
            )
        elif free_mb < (min_disk_mb * 1.5):
            status = DiagnosticStatus.WARNING
            msg = (
                f"Free disk space ({free_mb:.1f} MB) is approaching minimum threshold "
                f"({min_disk_mb:.1f} MB)."
            )
        else:
            status = DiagnosticStatus.HEALTHY
            msg = (
                f"Disk space adequate: {free_mb:.1f} MB free ({100.0 - used_percent:.1f}% available)."
            )

        return DiskCheckResult(
            total_mb=total_mb,
            used_mb=used_mb,
            free_mb=free_mb,
            used_percent=used_percent,
            min_required_mb=min_disk_mb,
            status=status,
            message=msg,
        )
    except Exception as exc:
        return DiskCheckResult(
            total_mb=0.0,
            used_mb=0.0,
            free_mb=0.0,
            used_percent=0.0,
            min_required_mb=min_disk_mb,
            status=DiagnosticStatus.UNHEALTHY,
            message=f"Unable to query disk capacity on '{check_dir}': {exc}",
        )


def inspect_environment_variables(
    keys_to_inspect: Optional[List[str]] = None,
) -> Dict[str, str]:
    """Inspect selected environment variables with automated secret redaction."""
    keys = keys_to_inspect or SELECTED_ENV_VARS
    result: Dict[str, str] = {}

    for key in keys:
        if key in os.environ:
            val = os.environ[key]
            result[key] = redact_value(key, val)
        else:
            result[key] = "<not set>"

    # Check for any other explicitly set environment variables that might be leaked
    for key, val in os.environ.items():
        if is_sensitive_key(key) and key not in result:
            result[key] = "***REDACTED***"

    return result


def check_single_tool(tool_name: str) -> ToolCheckResult:
    """Inspect presence and version of a single developer command-line tool."""
    tool_path = shutil.which(tool_name)
    if not tool_path:
        return ToolCheckResult(
            tool=tool_name,
            installed=False,
            version=None,
            path=None,
            status=DiagnosticStatus.WARNING,
            message=f"Tool '{tool_name}' was not found in PATH.",
        )

    version_str: Optional[str] = None
    try:
        # Safe subprocess execution: direct executable path, explicit arguments, no shell
        proc = subprocess.run(
            [tool_path, "--version"],
            capture_output=True,
            text=True,
            timeout=3.0,
            check=False,
        )
        output = (proc.stdout or proc.stderr or "").strip()
        if output:
            first_line = output.splitlines()[0].strip()
            # Truncate if unusually verbose
            version_str = first_line[:80]
        else:
            version_str = "detected (no version string)"
    except Exception as exc:
        version_str = f"detected (version query error: {exc})"

    return ToolCheckResult(
        tool=tool_name,
        installed=True,
        version=version_str,
        path=tool_path,
        status=DiagnosticStatus.HEALTHY,
        message=f"Tool '{tool_name}' available at {tool_path}.",
    )


def check_developer_tools(
    tools: Optional[List[str]] = None,
) -> Dict[str, ToolCheckResult]:
    """Inspect specified developer tools in system PATH."""
    target_tools = tools or TARGET_DEV_TOOLS
    return {tool: check_single_tool(tool) for tool in target_tools}


def run_system_diagnostics(
    target_disk_path: str = ".", min_disk_mb: float = 1024.0
) -> SystemDiagnosticsResult:
    """Execute complete host system diagnostic assessment."""
    py_result = check_python_version()
    os_result = check_os()
    disk_result = check_disk_space(target_disk_path, min_disk_mb)
    env_vars = inspect_environment_variables()
    dev_tools = check_developer_tools()

    warnings_count = 0
    errors_count = 0

    if py_result.status == DiagnosticStatus.UNHEALTHY:
        errors_count += 1
    elif py_result.status == DiagnosticStatus.WARNING:
        warnings_count += 1

    if disk_result.status == DiagnosticStatus.UNHEALTHY:
        errors_count += 1
    elif disk_result.status == DiagnosticStatus.WARNING:
        warnings_count += 1

    for tool_res in dev_tools.values():
        if tool_res.status == DiagnosticStatus.UNHEALTHY:
            errors_count += 1
        elif tool_res.status == DiagnosticStatus.WARNING:
            warnings_count += 1

    if errors_count > 0:
        overall = DiagnosticStatus.UNHEALTHY
    elif warnings_count > 0:
        overall = DiagnosticStatus.WARNING
    else:
        overall = DiagnosticStatus.HEALTHY

    return SystemDiagnosticsResult(
        python_info=py_result,
        os_info=os_result,
        disk_info=disk_result,
        env_vars=env_vars,
        developer_tools=dev_tools,
        overall_status=overall,
        warnings_count=warnings_count,
        errors_count=errors_count,
    )
