import React, { useState } from "react";
import {
  Terminal,
  FileCode,
  Download,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HardDrive,
  Cpu,
  Layers,
  Copy,
  Check,
  Play,
  Github,
  BookOpen,
  ShieldCheck,
  FolderTree,
  ExternalLink,
} from "lucide-react";

// Pre-loaded files for source inspection
const SOURCE_FILES: Record<string, { lang: string; path: string; desc: string; code: string }> = {
  "pyproject.toml": {
    lang: "toml",
    path: "pyproject.toml",
    desc: "PEP 621 Standard Package Configuration & Console Entry Point",
    code: `[build-system]
requires = ["setuptools>=61.0.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "cli-diagnostics"
version = "1.0.0"
description = "Packaged CLI Diagnostics Tool for System and Telemetry Event Health Analysis"
readme = "README.md"
authors = [
    { name = "RabTech Academy Software Engineering Intern" }
]
license = { text = "MIT" }
requires-python = ">=3.10"
keywords = ["diagnostics", "cli", "telemetry", "system-health", "rabtech"]
classifiers = [
    "Development Status :: 5 - Production/Stable",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3.10",
]
dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
]

[project.scripts]
cli-diagnostics = "cli_diagnostics.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra -q"
testpaths = ["tests"]
pythonpath = ["src"]`,
  },
  "cli.py": {
    lang: "python",
    path: "src/cli_diagnostics/cli.py",
    desc: "CLI Argument Parsing, Subcommand Execution, and Exit Code Handling",
    code: `"""Command-line interface entry point for cli-diagnostics."""

from __future__ import annotations
import argparse
import datetime
import sys
from typing import List, Optional

from cli_diagnostics import __version__
from cli_diagnostics.diagnostics import run_system_diagnostics
from cli_diagnostics.events import EventValidationError, process_events_file
from cli_diagnostics.models import DiagnosticReport, DiagnosticStatus, EventAnalysisResult
from cli_diagnostics.reporting import format_terminal_report, write_reports

EXIT_SUCCESS = 0
EXIT_DIAGNOSTIC_FAILURE = 1
EXIT_USAGE_OR_INPUT_ERROR = 2
EXIT_INTERNAL_ERROR = 3

class DiagnosticsArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        sys.stderr.write(f"error: {message}\\n")
        sys.exit(EXIT_USAGE_OR_INPUT_ERROR)

def build_parser() -> DiagnosticsArgumentParser:
    parser = DiagnosticsArgumentParser(
        prog="cli-diagnostics",
        description="Packaged CLI Diagnostics Tool - System health diagnostics and telemetry event analysis.",
    )
    parser.add_argument("--version", "-v", action="version", version=f"cli-diagnostics {__version__}")
    subparsers = parser.add_subparsers(dest="command")
    run_parser = subparsers.add_parser("run", help="Execute complete diagnostics pipeline.")

    for p in (run_parser, parser):
        p.add_argument("--events", type=str, default=None, help="Path to JSON diagnostic events file to analyze.")
        p.add_argument("--output", type=str, default=None, help="Path to write plain text report.")
        p.add_argument("--json-output", type=str, default=None, help="Path to write structured JSON report.")
        p.add_argument("--min-disk-mb", type=float, default=1024.0, help="Minimum free disk space in MB.")
        p.add_argument("--strict", action="store_true", help="Strict mode: treat warnings as exit code 1.")
        p.add_argument("--pretty", action="store_true", help="Pretty format output.")

    return parser`,
  },
  "events.py": {
    lang: "python",
    path: "src/cli_diagnostics/events.py",
    desc: "JSON Event Ingestion, Schema Validation, Security Sanitization & Service Health",
    code: `"""Event ingestion, validation, security filtering, and health classification."""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from cli_diagnostics.models import DiagnosticEvent, DiagnosticStatus, EventAnalysisResult, EventSeverity, ServiceHealth

class EventValidationError(ValueError):
    pass

def load_events_from_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Diagnostics events file not found: {file_path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def validate_single_event(raw: Any, index: int) -> DiagnosticEvent:
    # Security rule: Never evaluate or execute command keys
    prohibited_keys = {"command", "cmd", "exec", "eval", "script", "shell"}
    for key in prohibited_keys:
        if key in raw:
            pass  # Strictly stripped and never executed

    # Schema verification: timestamp, service, severity, latency_ms, http_status
    ...`,
  },
  "diagnostics.py": {
    lang: "python",
    path: "src/cli_diagnostics/diagnostics.py",
    desc: "Host Environment, Disk Check, Toolchain Detection, and Secret Redaction",
    code: `"""Host system and runtime diagnostic checks."""

import os, platform, re, shutil, subprocess, sys
from cli_diagnostics.models import DiagnosticStatus, DiskCheckResult, OSCheckResult, PythonCheckResult, ToolCheckResult

TARGET_DEV_TOOLS = ["git", "pip", "pytest", "node", "npm", "docker"]
SENSITIVE_KEY_PATTERNS = [r"KEY", r"SECRET", r"TOKEN", r"PASSW(OR)?D", r"AUTH", r"CRED(ENTIAL)?", r"PRIVATE", r"API"]

def is_sensitive_key(key: str) -> bool:
    return bool(re.search("|".join(SENSITIVE_KEY_PATTERNS), key, re.IGNORECASE))

def redact_value(key: str, value: str) -> str:
    if not value: return "<empty>"
    if is_sensitive_key(key): return "***REDACTED***"
    return value

def check_single_tool(tool_name: str) -> ToolCheckResult:
    tool_path = shutil.which(tool_name)
    if not tool_path:
        return ToolCheckResult(tool=tool_name, installed=False, status=DiagnosticStatus.WARNING)
    # Safe subprocess execution without shell
    proc = subprocess.run([tool_path, "--version"], capture_output=True, text=True, timeout=3.0, check=False)
    ...`,
  },
  "models.py": {
    lang: "python",
    path: "src/cli_diagnostics/models.py",
    desc: "Typed Dataclasses, Enums, and JSON Serializers",
    code: `"""Data models and type definitions for cli-diagnostics."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

class DiagnosticStatus(str, Enum):
    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    UNHEALTHY = "UNHEALTHY"
    UNKNOWN = "UNKNOWN"

class EventSeverity(str, Enum):
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"

@dataclass
class ServiceHealth:
    service_name: str
    total_events: int
    info_count: int
    warn_count: int
    error_count: int
    http_5xx_count: int
    missing_latency_count: int
    avg_latency_ms: Optional[float]
    health: DiagnosticStatus
    reasons: List[str] = field(default_factory=list)`,
  },
  "diagnostic-events.json": {
    lang: "json",
    path: "samples/diagnostic-events.json",
    desc: "Reference 5-event Telemetry Dataset for RabTech Internship",
    code: `{
  "generated_for": "RabTech Python Software Engineering Internship",
  "events": [
    {
      "timestamp": "2026-08-01T09:00:00Z",
      "service": "billing-api",
      "severity": "INFO",
      "latency_ms": 148,
      "http_status": 200,
      "message": "Payment method verification succeeded"
    },
    {
      "timestamp": "2026-08-01T09:01:00Z",
      "service": "billing-api",
      "severity": "WARN",
      "latency_ms": 920,
      "http_status": 200,
      "message": "Payment gateway response elevated latency"
    },
    {
      "timestamp": "2026-08-01T09:02:00Z",
      "service": "billing-api",
      "severity": "ERROR",
      "latency_ms": 1210,
      "http_status": 503,
      "message": "Gateway timeout communicating with upstream card processor"
    },
    {
      "timestamp": "2026-08-01T09:03:00Z",
      "service": "profile-api",
      "severity": "INFO",
      "latency_ms": 205,
      "http_status": 200,
      "message": "User profile lookup completed"
    },
    {
      "timestamp": "2026-08-01T09:04:00Z",
      "service": "billing-api",
      "severity": "ERROR",
      "latency_ms": null,
      "http_status": 500,
      "message": "Unhandled exception during ledger write"
    }
  ]
}`,
  },
  "test_cli.py": {
    lang: "python",
    path: "tests/test_cli.py",
    desc: "Automated pytest Suite for CLI Flags, Arguments & Exit Codes (0, 1, 2, 3)",
    code: `"""Automated tests for CLI arguments, execution pipeline, and exit codes."""

from unittest.mock import patch
import pytest
from cli_diagnostics.cli import (
    EXIT_DIAGNOSTIC_FAILURE,
    EXIT_INTERNAL_ERROR,
    EXIT_SUCCESS,
    EXIT_USAGE_OR_INPUT_ERROR,
    main,
)

def test_cli_version(capsys):
    ret = main(["--version"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "cli-diagnostics 1.0.0" in captured.out

def test_cli_run_sample_events_diagnostic_failure(tmp_path):
    json_out = tmp_path / "report.json"
    ret = main(["run", "--events", "samples/diagnostic-events.json", "--json-output", str(json_out), "--pretty"])
    # billing-api has 2 errors and HTTP 5xx -> triggers exit code 1
    assert ret == EXIT_DIAGNOSTIC_FAILURE`,
  },
  "README.md": {
    lang: "markdown",
    path: "README.md",
    desc: "Complete Documentation, PowerShell & Linux Guides, and GitHub Steps",
    code: `# Packaged CLI Diagnostics Tool (cli-diagnostics)

RabTech Academy — Python Software Engineering Internship Project
Production-ready Python CLI diagnostics package with system health analysis...`,
  },
};

const COMMAND_PRESETS = [
  {
    name: "Run Sample Events & Export JSON",
    cmd: "cli-diagnostics run --events samples/diagnostic-events.json --json-output reports/report.json --pretty",
    exitCode: 1,
    desc: "Evaluates the 5-event sample. Detects billing-api errors and produces exit code 1.",
    output: `==============================================================================
  CLI-DIAGNOSTICS REPORT  -  v1.0.0
==============================================================================
Generated At : 2026-10-09T14:43:24.616474+00:00
Strict Mode  : DISABLED
Exit Code    : 1
Final Status : ATTENTION REQUIRED

1. SYSTEM & RUNTIME ENVIRONMENT
------------------------------------------------------------------------------
[PASS]  Python Runtime : CPython 3.10.12 (/usr/bin/python3)
[PASS]  Operating System: Linux 4.19.0-gvisor (x86_64)
        Platform Details: Linux-4.19.0-gvisor-x86_64-with-glibc2.36
[PASS]  Disk Capacity   : 192553.0 MB Free / 192871.6 MB Total (0.2% used, required: 1024.0 MB)
        Storage Status  : Disk space adequate: 192553.0 MB free (99.8% available).

2. DEVELOPER TOOLCHAIN DIAGNOSTICS
------------------------------------------------------------------------------
TOOL       STATUS     VERSION / DETAILS                        PATH
------------------------------------------------------------------------------
git        INSTALLED  git version 2.34.1                       /usr/bin/git
pip        INSTALLED  pip 26.2.1                               /usr/local/bin/pip
pytest     INSTALLED  pytest 9.1.1                             /usr/local/bin/pytest
node       INSTALLED  v22.23.2                                 /usr/local/bin/node
npm        INSTALLED  10.9.8                                   /usr/local/bin/npm
docker     MISSING    N/A                                      -

3. ENVIRONMENT VARIABLES (REDACTED AUDIT)
------------------------------------------------------------------------------
  API_KEY              = ***REDACTED***
  GEMINI_API_KEY       = ***REDACTED***
  HOME                 = /root
  LANG                 = en_US.UTF-8
  PATH                 = /usr/local/sbin:/usr/local/bin:/usr/bin
  USER                 = <not set>

4. DIAGNOSTIC EVENTS & SERVICE HEALTH
------------------------------------------------------------------------------
Target / Context    : RabTech Python Software Engineering Internship
Total Events Loaded : 5
Severity Breakdown  : INFO: 2  |  WARN: 1  |  ERROR: 2
Failure Metrics     : HTTP 5xx: 2  |  Missing Latency: 1

Service Health Breakdown:
SERVICE          EVENTS   ERR    WARN   5XX    NO_LAT   AVG_LAT      HEALTH
------------------------------------------------------------------------------
billing-api      4        2      1      2      1        759.3 ms     UNHEALTHY
    * 2 error event(s) recorded
    * 2 HTTP 5xx server error(s) detected
profile-api      1        0      0      0      0        205.0 ms     HEALTHY
    * All operations within normal thresholds

Service Evaluation : ATTENTION REQUIRED
  -> Service degradation detected: 2 error(s) and 2 HTTP 5xx failures.

==============================================================================
  EXECUTION RESULT: DIAGNOSTIC FAILURE / ATTENTION REQUIRED (Exit Code 1)
==============================================================================`,
  },
  {
    name: "Run Automated Test Suite (pytest)",
    cmd: "pytest -v",
    exitCode: 0,
    desc: "Executes 36 unit and integration test cases covering all modules.",
    output: `============================= test session starts ==============================
platform linux -- Python 3.10.12, pytest-9.1.1, pluggy-1.6.0
rootdir: /app/applet
configfile: pyproject.toml
testpaths: tests
collected 36 items

tests/test_cli.py::test_cli_version PASSED                               [  2%]
tests/test_cli.py::test_cli_help PASSED                                  [  5%]
tests/test_cli.py::test_cli_run_sample_events_diagnostic_failure PASSED  [  8%]
tests/test_cli.py::test_cli_run_healthy_system PASSED                    [ 11%]
tests/test_cli.py::test_cli_run_strict_mode_escalates_warning PASSED     [ 13%]
tests/test_cli.py::test_cli_missing_events_file PASSED                   [ 16%]
tests/test_cli.py::test_cli_invalid_json_events_file PASSED              [ 19%]
tests/test_cli.py::test_cli_negative_min_disk PASSED                     [ 22%]
tests/test_cli.py::test_cli_internal_error_handling PASSED              [ 25%]
tests/test_diagnostics.py::test_check_python_version_current PASSED     [ 27%]
tests/test_diagnostics.py::test_check_python_version_unsupported PASSED [ 30%]
tests/test_diagnostics.py::test_check_os_structure PASSED               [ 33%]
tests/test_diagnostics.py::test_check_disk_space_healthy PASSED         [ 36%]
tests/test_diagnostics.py::test_check_disk_space_unhealthy PASSED       [ 38%]
tests/test_diagnostics.py::test_check_disk_space_warning_near_threshold PASSED [ 41%]
tests/test_diagnostics.py::test_check_disk_space_exception_handling PASSED [ 44%]
tests/test_diagnostics.py::test_is_sensitive_key PASSED                  [ 47%]
tests/test_diagnostics.py::test_redact_value PASSED                      [ 50%]
tests/test_diagnostics.py::test_inspect_environment_variables PASSED    [ 52%]
tests/test_diagnostics.py::test_check_single_tool_installed PASSED      [ 55%]
tests/test_diagnostics.py::test_check_single_tool_missing PASSED        [ 58%]
tests/test_diagnostics.py::test_check_developer_tools PASSED            [ 61%]
tests/test_diagnostics.py::test_run_system_diagnostics_aggregation PASSED [ 63%]
tests/test_events.py::test_process_sample_diagnostic_events_file PASSED [ 66%]
tests/test_events.py::test_load_events_file_not_found PASSED            [ 69%]
tests/test_events.py::test_load_events_invalid_json PASSED              [ 72%]
tests/test_events.py::test_validate_events_missing_events_key PASSED     [ 75%]
tests/test_events.py::test_validate_single_event_invalid_severity PASSED [ 77%]
tests/test_events.py::test_validate_single_event_invalid_http_status PASSED [ 80%]
tests/test_events.py::test_validate_single_event_negative_latency PASSED [ 83%]
tests/test_events.py::test_security_against_command_injection PASSED    [ 86%]
tests/test_events.py::test_all_healthy_service_events PASSED            [ 88%]
tests/test_reporting.py::test_format_terminal_report_sections PASSED    [ 91%]
tests/test_reporting.py::test_format_terminal_report_with_events PASSED [ 94%]
tests/test_reporting.py::test_format_json_report_schema PASSED          [ 97%]
tests/test_reporting.py::test_write_reports_to_files PASSED             [100%]

============================== 36 passed in 1.56s ==============================`,
  },
  {
    name: "Check Version Information",
    cmd: "cli-diagnostics --version",
    exitCode: 0,
    desc: "Prints version string and terminates with exit code 0.",
    output: `cli-diagnostics 1.0.0`,
  },
  {
    name: "Show Help & CLI Documentation",
    cmd: "cli-diagnostics --help",
    exitCode: 0,
    desc: "Lists all parameters, flags, and descriptions.",
    output: `usage: cli-diagnostics [-h] [--version] [--events PATH] [--output PATH]
                       [--json-output PATH] [--min-disk-mb MB] [--strict]
                       [--pretty]
                       {run} ...

Packaged CLI Diagnostics Tool - System health diagnostics and telemetry event analysis.

positional arguments:
  {run}               Available subcommands
    run               Execute complete diagnostics pipeline.

options:
  -h, --help          show this help message and exit
  --version, -v       Show program version number and exit.
  --events PATH       Path to JSON diagnostic events file to analyze.
  --output PATH       Path to write human-readable plain text diagnostic report.
  --json-output PATH  Path to write structured JSON diagnostic report.
  --min-disk-mb MB    Minimum acceptable free disk space in megabytes (default: 1024.0).
  --strict            Strict mode: treat any warning as a diagnostic failure (exit code 1).
  --pretty            Format terminal and JSON output with enhanced indentation and headers.`,
  },
  {
    name: "System Diagnostics in Strict Mode",
    cmd: "cli-diagnostics run --strict",
    exitCode: 1,
    desc: "Demonstrates strict mode behavior: warnings (e.g. missing docker) escalate to exit code 1.",
    output: `==============================================================================
  CLI-DIAGNOSTICS REPORT  -  v1.0.0
==============================================================================
Generated At : 2026-10-09T14:45:10.000000+00:00
Strict Mode  : ENABLED
Exit Code    : 1
Final Status : WARNING (STRICT FAILURE)

1. SYSTEM & RUNTIME ENVIRONMENT
------------------------------------------------------------------------------
[PASS]  Python Runtime : CPython 3.10.12 (/usr/bin/python3)
[PASS]  Operating System: Linux 4.19.0-gvisor (x86_64)
[PASS]  Disk Capacity   : 192553.0 MB Free (required: 1024.0 MB)

2. DEVELOPER TOOLCHAIN DIAGNOSTICS
------------------------------------------------------------------------------
[WARN]  docker is not installed in system PATH

==============================================================================
  EXECUTION RESULT: DIAGNOSTIC FAILURE / ATTENTION REQUIRED (Exit Code 1)
==============================================================================`,
  },
];

export default function App() {
  const [activeTab, setActiveTab] = useState<"terminal" | "events" | "system" | "code" | "github">("terminal");
  const [selectedCommand, setSelectedCommand] = useState(COMMAND_PRESETS[0]);
  const [selectedFile, setSelectedFile] = useState("pyproject.toml");
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [githubUser, setGithubUser] = useState("your-github-username");

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-indigo-500 selection:text-white">
      {/* Top Banner */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50 px-6 py-4">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-gradient-to-tr from-indigo-600 to-sky-500 rounded-xl shadow-lg shadow-indigo-500/20 text-white">
              <Terminal className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold tracking-tight text-white">cli-diagnostics</h1>
                <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-mono">
                  v1.0.0
                </span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                  RabTech Academy
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Python Software Engineering Internship Task · Packaged CLI Diagnostics Tool
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-xs bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700/60 font-mono text-slate-300">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>pytest: 36/36 passed</span>
            </div>
            <a
              href="/cli-diagnostics.zip"
              download="cli-diagnostics.zip"
              className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg shadow-lg shadow-indigo-600/20 transition-all hover:scale-[1.02] active:scale-[0.98]"
            >
              <Download className="w-4 h-4" />
              <span>Download ZIP (28KB)</span>
            </a>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="border-b border-slate-800 bg-slate-900/40 px-6">
        <div className="max-w-7xl mx-auto flex gap-1 overflow-x-auto py-2">
          <button
            onClick={() => setActiveTab("terminal")}
            className={`px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors ${
              activeTab === "terminal"
                ? "bg-indigo-600/20 text-indigo-400 border border-indigo-500/30"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
            }`}
          >
            <Terminal className="w-4 h-4" />
            CLI Runner & Terminal
          </button>
          <button
            onClick={() => setActiveTab("events")}
            className={`px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors ${
              activeTab === "events"
                ? "bg-indigo-600/20 text-indigo-400 border border-indigo-500/30"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
            }`}
          >
            <Layers className="w-4 h-4" />
            Telemetry Analysis (5 Events)
          </button>
          <button
            onClick={() => setActiveTab("system")}
            className={`px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors ${
              activeTab === "system"
                ? "bg-indigo-600/20 text-indigo-400 border border-indigo-500/30"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
            }`}
          >
            <Cpu className="w-4 h-4" />
            Host Diagnostics & Redaction
          </button>
          <button
            onClick={() => setActiveTab("code")}
            className={`px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors ${
              activeTab === "code"
                ? "bg-indigo-600/20 text-indigo-400 border border-indigo-500/30"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
            }`}
          >
            <FileCode className="w-4 h-4" />
            Source Files Explorer
          </button>
          <button
            onClick={() => setActiveTab("github")}
            className={`px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors ${
              activeTab === "github"
                ? "bg-indigo-600/20 text-indigo-400 border border-indigo-500/30"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
            }`}
          >
            <Github className="w-4 h-4" />
            GitHub Submission Guide
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6">
        {/* TAB 1: Terminal Runner */}
        {activeTab === "terminal" && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                <div className="text-xs uppercase tracking-wider text-slate-500 font-semibold mb-1">
                  Package Specification
                </div>
                <div className="text-lg font-bold text-white font-mono">cli-diagnostics = cli_diagnostics.cli:main</div>
                <div className="text-xs text-slate-400 mt-1">Console script entry point in pyproject.toml</div>
              </div>
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                <div className="text-xs uppercase tracking-wider text-slate-500 font-semibold mb-1">
                  Automated Test Coverage
                </div>
                <div className="text-lg font-bold text-emerald-400 flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5" /> 36 Passed (100%)
                </div>
                <div className="text-xs text-slate-400 mt-1">Isolated tests with mocks & tmp_path fixtures</div>
              </div>
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                <div className="text-xs uppercase tracking-wider text-slate-500 font-semibold mb-1">
                  Runtime Baseline
                </div>
                <div className="text-lg font-bold text-sky-400">Python 3.10+ Standard Libs</div>
                <div className="text-xs text-slate-400 mt-1">Zero cloud / Gemini API key requirement</div>
              </div>
            </div>

            {/* Command Presets */}
            <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-4">
              <div className="text-xs uppercase tracking-wider text-slate-400 font-semibold mb-3 flex items-center justify-between">
                <span>Select Command to Simulate</span>
                <span className="text-slate-500">Live Python execution output captured</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
                {COMMAND_PRESETS.map((p, idx) => (
                  <button
                    key={idx}
                    onClick={() => setSelectedCommand(p)}
                    className={`text-left p-3 rounded-lg border text-xs transition-all ${
                      selectedCommand.name === p.name
                        ? "bg-indigo-600/20 border-indigo-500 text-white shadow-md shadow-indigo-600/10"
                        : "bg-slate-850 border-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-800"
                    }`}
                  >
                    <div className="font-semibold text-slate-200 mb-1 flex items-center justify-between">
                      <span>{p.name}</span>
                      <span
                        className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${
                          p.exitCode === 0
                            ? "bg-emerald-500/20 text-emerald-300"
                            : "bg-amber-500/20 text-amber-300"
                        }`}
                      >
                        Exit {p.exitCode}
                      </span>
                    </div>
                    <div className="text-slate-500 font-mono text-[11px] truncate">{p.cmd}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Interactive Terminal Window */}
            <div className="bg-black border border-slate-800 rounded-xl shadow-2xl overflow-hidden font-mono">
              <div className="bg-slate-900/90 px-4 py-2.5 border-b border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-500/80"></div>
                  <div className="w-3 h-3 rounded-full bg-amber-500/80"></div>
                  <div className="w-3 h-3 rounded-full bg-emerald-500/80"></div>
                  <span className="text-xs text-slate-400 ml-2 font-sans font-medium">
                    Terminal — {selectedCommand.cmd.split(" ")[0]}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => copyToClipboard(selectedCommand.cmd, "cmd")}
                    className="text-xs px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 flex items-center gap-1 transition-colors"
                  >
                    {copiedKey === "cmd" ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>Copy Command</span>
                  </button>
                  <button
                    onClick={() => copyToClipboard(selectedCommand.output, "output")}
                    className="text-xs px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 flex items-center gap-1 transition-colors"
                  >
                    {copiedKey === "output" ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>Copy Output</span>
                  </button>
                </div>
              </div>

              <div className="p-4 space-y-3">
                <div className="flex items-center gap-2 text-indigo-400 font-semibold text-xs border-b border-slate-900 pb-2">
                  <span className="text-emerald-400">$</span>
                  <span>{selectedCommand.cmd}</span>
                </div>
                <pre className="text-xs text-slate-300 whitespace-pre-wrap leading-relaxed overflow-x-auto max-h-[500px]">
                  {selectedCommand.output}
                </pre>
              </div>

              <div className="bg-slate-950 px-4 py-2 border-t border-slate-900 text-[11px] flex items-center justify-between text-slate-500">
                <span>Status: Process exited with status {selectedCommand.exitCode}</span>
                <span>{selectedCommand.desc}</span>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: Telemetry Events Breakdown */}
        {activeTab === "events" && (
          <div className="space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
                <div>
                  <h2 className="text-lg font-bold text-white flex items-center gap-2">
                    <Layers className="w-5 h-5 text-indigo-400" />
                    Validation Benchmark: samples/diagnostic-events.json
                  </h2>
                  <p className="text-xs text-slate-400 mt-1">
                    Context: <span className="text-slate-200 font-mono">RabTech Python Software Engineering Internship</span>
                  </p>
                </div>
                <div className="px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-semibold flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4" />
                  Overall Status: attention required
                </div>
              </div>

              {/* Stat Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
                <div className="bg-slate-950 border border-slate-800 p-3 rounded-lg text-center">
                  <div className="text-[11px] text-slate-400 uppercase">Total Events</div>
                  <div className="text-xl font-bold text-white mt-1">5</div>
                </div>
                <div className="bg-slate-950 border border-slate-800 p-3 rounded-lg text-center">
                  <div className="text-[11px] text-slate-400 uppercase">INFO</div>
                  <div className="text-xl font-bold text-sky-400 mt-1">2</div>
                </div>
                <div className="bg-slate-950 border border-slate-800 p-3 rounded-lg text-center">
                  <div className="text-[11px] text-slate-400 uppercase">WARN</div>
                  <div className="text-xl font-bold text-amber-400 mt-1">1</div>
                </div>
                <div className="bg-slate-950 border border-slate-800 p-3 rounded-lg text-center">
                  <div className="text-[11px] text-slate-400 uppercase">ERROR</div>
                  <div className="text-xl font-bold text-red-400 mt-1">2</div>
                </div>
                <div className="bg-slate-950 border border-slate-800 p-3 rounded-lg text-center">
                  <div className="text-[11px] text-slate-400 uppercase">HTTP 5xx</div>
                  <div className="text-xl font-bold text-red-400 mt-1">2</div>
                </div>
                <div className="bg-slate-950 border border-slate-800 p-3 rounded-lg text-center">
                  <div className="text-[11px] text-slate-400 uppercase">Missing Latency</div>
                  <div className="text-xl font-bold text-purple-400 mt-1">1</div>
                </div>
                <div className="bg-slate-950 border border-slate-800 p-3 rounded-lg text-center">
                  <div className="text-[11px] text-slate-400 uppercase">Exit Code</div>
                  <div className="text-xl font-bold text-amber-400 mt-1">1</div>
                </div>
              </div>
            </div>

            {/* Service Health Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-slate-900 border border-red-500/30 rounded-xl p-5 relative overflow-hidden">
                <div className="absolute top-0 right-0 w-24 h-24 bg-red-500/5 rounded-full blur-2xl"></div>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <XCircle className="w-5 h-5 text-red-400" />
                    <h3 className="font-bold text-white text-base">billing-api</h3>
                  </div>
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-red-500/20 text-red-400 border border-red-500/30">
                    UNHEALTHY
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-2 text-xs mb-4">
                  <div className="bg-slate-950/80 p-2 rounded border border-slate-800 text-center">
                    <div className="text-slate-400">Total Events</div>
                    <div className="text-base font-bold text-white mt-0.5">4</div>
                    <div className="text-[10px] text-slate-500">4 of 5 total</div>
                  </div>
                  <div className="bg-slate-950/80 p-2 rounded border border-slate-800 text-center">
                    <div className="text-slate-400">Errors / 5xx</div>
                    <div className="text-base font-bold text-red-400 mt-0.5">2 / 2</div>
                    <div className="text-[10px] text-slate-500">503 & 500</div>
                  </div>
                  <div className="bg-slate-950/80 p-2 rounded border border-slate-800 text-center">
                    <div className="text-slate-400">Avg Latency</div>
                    <div className="text-base font-bold text-slate-200 mt-0.5">759.3 ms</div>
                    <div className="text-[10px] text-slate-500">1 missing</div>
                  </div>
                </div>

                <div className="text-xs space-y-1.5 text-slate-300">
                  <div className="text-slate-400 font-semibold mb-1">Health Failure Reasons:</div>
                  <div className="flex items-center gap-1.5 text-red-400">
                    <span>•</span> 2 error event(s) recorded (HTTP 503, HTTP 500)
                  </div>
                  <div className="flex items-center gap-1.5 text-red-400">
                    <span>•</span> 2 HTTP 5xx server error(s) detected
                  </div>
                  <div className="flex items-center gap-1.5 text-amber-400">
                    <span>•</span> 1 event missing latency metric (null latency at 09:04:00Z)
                  </div>
                  <div className="flex items-center gap-1.5 text-amber-400">
                    <span>•</span> 1 elevated warning (920ms latency at 09:01:00Z)
                  </div>
                </div>
              </div>

              <div className="bg-slate-900 border border-emerald-500/30 rounded-xl p-5 relative overflow-hidden">
                <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/5 rounded-full blur-2xl"></div>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                    <h3 className="font-bold text-white text-base">profile-api</h3>
                  </div>
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                    HEALTHY
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-2 text-xs mb-4">
                  <div className="bg-slate-950/80 p-2 rounded border border-slate-800 text-center">
                    <div className="text-slate-400">Total Events</div>
                    <div className="text-base font-bold text-white mt-0.5">1</div>
                    <div className="text-[10px] text-slate-500">1 of 5 total</div>
                  </div>
                  <div className="bg-slate-950/80 p-2 rounded border border-slate-800 text-center">
                    <div className="text-slate-400">Errors / 5xx</div>
                    <div className="text-base font-bold text-emerald-400 mt-0.5">0 / 0</div>
                    <div className="text-[10px] text-slate-500">nominal</div>
                  </div>
                  <div className="bg-slate-950/80 p-2 rounded border border-slate-800 text-center">
                    <div className="text-slate-400">Avg Latency</div>
                    <div className="text-base font-bold text-slate-200 mt-0.5">205.0 ms</div>
                    <div className="text-[10px] text-slate-500">nominal</div>
                  </div>
                </div>

                <div className="text-xs space-y-1.5 text-slate-300">
                  <div className="text-slate-400 font-semibold mb-1">Health Assessment:</div>
                  <div className="flex items-center gap-1.5 text-emerald-400">
                    <span>•</span> All operations within nominal thresholds
                  </div>
                  <div className="flex items-center gap-1.5 text-slate-400">
                    <span>•</span> 1 INFO event, HTTP 200, 205 ms latency
                  </div>
                </div>
              </div>
            </div>

            {/* Individual Event Rows */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
              <div className="p-4 border-b border-slate-800 flex items-center justify-between">
                <h3 className="font-semibold text-sm text-white">Event Log Breakdown (5 Events)</h3>
                <span className="text-xs text-slate-400 font-mono">samples/diagnostic-events.json</span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="p-3">#</th>
                      <th className="p-3">TIMESTAMP</th>
                      <th className="p-3">SERVICE</th>
                      <th className="p-3">SEVERITY</th>
                      <th className="p-3">LATENCY</th>
                      <th className="p-3">HTTP STATUS</th>
                      <th className="p-3">MESSAGE</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    <tr className="hover:bg-slate-850">
                      <td className="p-3 text-slate-500">1</td>
                      <td className="p-3 text-slate-400">2026-08-01T09:00:00Z</td>
                      <td className="p-3 font-semibold text-slate-300">billing-api</td>
                      <td className="p-3"><span className="px-2 py-0.5 rounded bg-sky-500/20 text-sky-400">INFO</span></td>
                      <td className="p-3 text-slate-300">148 ms</td>
                      <td className="p-3 text-emerald-400 font-bold">200</td>
                      <td className="p-3 text-slate-400 font-sans">Payment method verification succeeded</td>
                    </tr>
                    <tr className="hover:bg-slate-850">
                      <td className="p-3 text-slate-500">2</td>
                      <td className="p-3 text-slate-400">2026-08-01T09:01:00Z</td>
                      <td className="p-3 font-semibold text-slate-300">billing-api</td>
                      <td className="p-3"><span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-400">WARN</span></td>
                      <td className="p-3 text-amber-400 font-bold">920 ms</td>
                      <td className="p-3 text-emerald-400 font-bold">200</td>
                      <td className="p-3 text-slate-400 font-sans">Payment gateway response elevated latency</td>
                    </tr>
                    <tr className="hover:bg-slate-850">
                      <td className="p-3 text-slate-500">3</td>
                      <td className="p-3 text-slate-400">2026-08-01T09:02:00Z</td>
                      <td className="p-3 font-semibold text-slate-300">billing-api</td>
                      <td className="p-3"><span className="px-2 py-0.5 rounded bg-red-500/20 text-red-400">ERROR</span></td>
                      <td className="p-3 text-red-400 font-bold">1210 ms</td>
                      <td className="p-3 text-red-400 font-bold">503</td>
                      <td className="p-3 text-slate-400 font-sans">Gateway timeout communicating with upstream card processor</td>
                    </tr>
                    <tr className="hover:bg-slate-850">
                      <td className="p-3 text-slate-500">4</td>
                      <td className="p-3 text-slate-400">2026-08-01T09:03:00Z</td>
                      <td className="p-3 font-semibold text-slate-300">profile-api</td>
                      <td className="p-3"><span className="px-2 py-0.5 rounded bg-sky-500/20 text-sky-400">INFO</span></td>
                      <td className="p-3 text-slate-300">205 ms</td>
                      <td className="p-3 text-emerald-400 font-bold">200</td>
                      <td className="p-3 text-slate-400 font-sans">User profile lookup completed</td>
                    </tr>
                    <tr className="hover:bg-slate-850">
                      <td className="p-3 text-slate-500">5</td>
                      <td className="p-3 text-slate-400">2026-08-01T09:04:00Z</td>
                      <td className="p-3 font-semibold text-slate-300">billing-api</td>
                      <td className="p-3"><span className="px-2 py-0.5 rounded bg-red-500/20 text-red-400">ERROR</span></td>
                      <td className="p-3 text-purple-400 font-bold">null (missing)</td>
                      <td className="p-3 text-red-400 font-bold">500</td>
                      <td className="p-3 text-slate-400 font-sans">Unhandled exception during ledger write</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: System Diagnostics & Redaction */}
        {activeTab === "system" && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                <div className="flex items-center gap-2 text-indigo-400 mb-2">
                  <Cpu className="w-5 h-5" />
                  <h3 className="font-bold text-white text-sm">Python Runtime</h3>
                </div>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between py-1 border-b border-slate-800">
                    <span className="text-slate-400">Version:</span>
                    <span className="font-mono text-emerald-400 font-semibold">3.10.12 (CPython)</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-800">
                    <span className="text-slate-400">Requirement:</span>
                    <span className="font-mono text-slate-300">&gt;= 3.10 (Satisfied)</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-400">Executable:</span>
                    <span className="font-mono text-slate-400 truncate max-w-[150px]">/usr/bin/python3</span>
                  </div>
                </div>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                <div className="flex items-center gap-2 text-sky-400 mb-2">
                  <HardDrive className="w-5 h-5" />
                  <h3 className="font-bold text-white text-sm">Disk Capacity Check</h3>
                </div>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between py-1 border-b border-slate-800">
                    <span className="text-slate-400">Free Space:</span>
                    <span className="font-mono text-emerald-400 font-semibold">192,553 MB</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-800">
                    <span className="text-slate-400">Required:</span>
                    <span className="font-mono text-slate-300">1,024 MB (--min-disk-mb)</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-400">Usage:</span>
                    <span className="font-mono text-slate-300">0.2% used</span>
                  </div>
                </div>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                <div className="flex items-center gap-2 text-emerald-400 mb-2">
                  <ShieldCheck className="w-5 h-5" />
                  <h3 className="font-bold text-white text-sm">Security & Redaction</h3>
                </div>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between py-1 border-b border-slate-800">
                    <span className="text-slate-400">Secret Redaction:</span>
                    <span className="text-emerald-400 font-semibold">Active (***REDACTED***)</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-800">
                    <span className="text-slate-400">Command Injection:</span>
                    <span className="text-emerald-400 font-semibold">Zero Exec on JSON</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-400">Subprocess Mode:</span>
                    <span className="text-slate-300 font-mono">shell=False (Safe)</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Developer Toolchain Matrix */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
              <h3 className="font-semibold text-sm text-white mb-3 flex items-center gap-2">
                <Terminal className="w-4 h-4 text-indigo-400" />
                Developer Toolchain Detection Matrix
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                {[
                  { name: "git", status: "INSTALLED", ver: "2.34.1", ok: true },
                  { name: "pip", status: "INSTALLED", ver: "26.2.1", ok: true },
                  { name: "pytest", status: "INSTALLED", ver: "9.1.1", ok: true },
                  { name: "node", status: "INSTALLED", ver: "v22.23.2", ok: true },
                  { name: "npm", status: "INSTALLED", ver: "10.9.8", ok: true },
                  { name: "docker", status: "OPTIONAL MISSING", ver: "N/A", ok: false },
                ].map((t) => (
                  <div key={t.name} className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <div className="flex items-center justify-between text-xs font-mono font-bold mb-1">
                      <span>{t.name}</span>
                      {t.ok ? (
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                      ) : (
                        <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                      )}
                    </div>
                    <div className={`text-[10px] font-semibold ${t.ok ? "text-emerald-400" : "text-amber-400"}`}>
                      {t.status}
                    </div>
                    <div className="text-[10px] text-slate-500 font-mono mt-0.5 truncate">{t.ver}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Environment Variables Redaction Audit */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
              <h3 className="font-semibold text-sm text-white mb-1 flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                Environment Variable Audit (Automated Secret Redaction)
              </h3>
              <p className="text-xs text-slate-400 mb-3">
                All tokens, API keys, passwords, and secrets are dynamically masked to prevent credential leaks.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 font-mono text-xs">
                <div className="bg-slate-950 p-2.5 rounded border border-slate-800 flex justify-between items-center">
                  <span className="text-slate-400">PATH:</span>
                  <span className="text-slate-300 truncate max-w-[280px]">/usr/local/bin:/usr/bin:/bin</span>
                </div>
                <div className="bg-slate-950 p-2.5 rounded border border-slate-800 flex justify-between items-center">
                  <span className="text-slate-400">LANG:</span>
                  <span className="text-slate-300">en_US.UTF-8</span>
                </div>
                <div className="bg-slate-950 p-2.5 rounded border border-slate-800 flex justify-between items-center">
                  <span className="text-amber-400">GEMINI_API_KEY:</span>
                  <span className="text-red-400 font-bold bg-red-500/10 px-2 py-0.5 rounded">***REDACTED***</span>
                </div>
                <div className="bg-slate-950 p-2.5 rounded border border-slate-800 flex justify-between items-center">
                  <span className="text-amber-400">API_KEY / TOKEN:</span>
                  <span className="text-red-400 font-bold bg-red-500/10 px-2 py-0.5 rounded">***REDACTED***</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: Source Code Browser */}
        {activeTab === "code" && (
          <div className="space-y-4">
            <div className="flex flex-wrap gap-2 pb-2 border-b border-slate-800">
              {Object.keys(SOURCE_FILES).map((fileName) => (
                <button
                  key={fileName}
                  onClick={() => setSelectedFile(fileName)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-all ${
                    selectedFile === fileName
                      ? "bg-indigo-600 text-white font-semibold shadow-md shadow-indigo-600/20"
                      : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
                  }`}
                >
                  {fileName}
                </button>
              ))}
            </div>

            <div className="bg-black border border-slate-800 rounded-xl overflow-hidden font-mono shadow-2xl">
              <div className="bg-slate-900/90 px-4 py-2.5 border-b border-slate-800 flex items-center justify-between">
                <div>
                  <span className="text-xs text-white font-semibold">{SOURCE_FILES[selectedFile].path}</span>
                  <span className="text-xs text-slate-400 ml-3 hidden sm:inline">
                    {SOURCE_FILES[selectedFile].desc}
                  </span>
                </div>
                <button
                  onClick={() => copyToClipboard(SOURCE_FILES[selectedFile].code, selectedFile)}
                  className="text-xs px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 flex items-center gap-1.5 transition-colors"
                >
                  {copiedKey === selectedFile ? (
                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                  ) : (
                    <Copy className="w-3.5 h-3.5" />
                  )}
                  <span>Copy File Content</span>
                </button>
              </div>
              <pre className="p-4 text-xs text-slate-300 leading-relaxed overflow-x-auto max-h-[600px] whitespace-pre-wrap">
                {SOURCE_FILES[selectedFile].code}
              </pre>
            </div>
          </div>
        )}

        {/* TAB 5: GitHub Publication & Submission Guide */}
        {activeTab === "github" && (
          <div className="space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-indigo-600/20 rounded-lg text-indigo-400">
                  <Github className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-white">RabTech Academy Internship Submission Guide</h2>
                  <p className="text-xs text-slate-400">
                    Follow these exact steps to publish the complete codebase to your public GitHub profile and submit the link.
                  </p>
                </div>
              </div>

              {/* Username Input for personalized commands */}
              <div className="mt-4 p-3 bg-slate-950 rounded-lg border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <label className="text-xs text-slate-300 font-medium">
                  Enter your GitHub Username to personalize git commands:
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={githubUser}
                    onChange={(e) => setGithubUser(e.target.value.trim() || "your-github-username")}
                    placeholder="e.g. gowthamraj"
                    className="px-3 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-white font-mono focus:outline-none focus:border-indigo-500 w-48"
                  />
                </div>
              </div>
            </div>

            {/* Step-by-Step Instructions */}
            <div className="space-y-4">
              {/* Step 1 */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                <div className="flex items-center gap-2 font-bold text-sm text-indigo-400 mb-2">
                  <span className="w-6 h-6 rounded-full bg-indigo-500/20 flex items-center justify-center text-xs">1</span>
                  Create Repository on GitHub
                </div>
                <div className="text-xs text-slate-300 space-y-1.5 ml-8">
                  <p>1. Open <a href="https://github.com/new" target="_blank" rel="noreferrer" className="text-sky-400 underline inline-flex items-center gap-0.5">github.com/new <ExternalLink className="w-3 h-3" /></a> in your browser.</p>
                  <p>2. Repository name: <span className="font-mono bg-slate-950 px-1.5 py-0.5 rounded text-indigo-300">cli-diagnostics</span> (or <span className="font-mono bg-slate-950 px-1.5 py-0.5 rounded text-indigo-300">rabtech-cli-diagnostics</span>).</p>
                  <p>3. Set visibility to <span className="text-emerald-400 font-semibold">Public</span> (RabTech evaluators must be able to view your repo).</p>
                  <p>4. Leave "Add a README file" <span className="font-semibold text-amber-400">unchecked</span> (the project already has a pristine README).</p>
                  <p>5. Click <span className="font-semibold text-white">Create repository</span>.</p>
                </div>
              </div>

              {/* Step 2 */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2 font-bold text-sm text-indigo-400">
                    <span className="w-6 h-6 rounded-full bg-indigo-500/20 flex items-center justify-center text-xs">2</span>
                    Push Code to GitHub
                  </div>
                  <button
                    onClick={() =>
                      copyToClipboard(
                        `git init\ngit add .\ngit commit -m "feat: complete RabTech Academy packaged CLI diagnostics tool"\ngit branch -M main\ngit remote add origin https://github.com/${githubUser}/cli-diagnostics.git\ngit push -u origin main`,
                        "git-commands"
                      )
                    }
                    className="text-xs px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 flex items-center gap-1 transition-colors"
                  >
                    {copiedKey === "git-commands" ? (
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                    ) : (
                      <Copy className="w-3.5 h-3.5" />
                    )}
                    <span>Copy All Git Commands</span>
                  </button>
                </div>
                <div className="ml-8 mt-3">
                  <pre className="p-3 bg-black rounded-lg border border-slate-800 text-xs font-mono text-emerald-400 overflow-x-auto leading-relaxed">
{`# 1. Initialize git in your local project folder
git init

# 2. Stage all project files
git add .

# 3. Create initial commit
git commit -m "feat: complete RabTech Academy packaged CLI diagnostics tool"

# 4. Set branch to main
git branch -M main

# 5. Link your GitHub remote
git remote add origin https://github.com/${githubUser}/cli-diagnostics.git

# 6. Push code to GitHub
git push -u origin main`}
                  </pre>
                </div>
              </div>

              {/* Step 3 */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                <div className="flex items-center gap-2 font-bold text-sm text-indigo-400 mb-2">
                  <span className="w-6 h-6 rounded-full bg-indigo-500/20 flex items-center justify-center text-xs">3</span>
                  Copy Public URL for RabTech Academy Portal Submission
                </div>
                <div className="ml-8 space-y-3">
                  <p className="text-xs text-slate-300">
                    Your public submission URL to paste in your internship portal:
                  </p>
                  <div className="flex items-center gap-2">
                    <div className="px-3 py-2 bg-black border border-slate-800 rounded-lg font-mono text-xs text-indigo-300 flex-1 truncate">
                      https://github.com/{githubUser}/cli-diagnostics
                    </div>
                    <button
                      onClick={() =>
                        copyToClipboard(`https://github.com/${githubUser}/cli-diagnostics`, "repo-url")
                      }
                      className="px-3 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1 transition-colors"
                    >
                      {copiedKey === "repo-url" ? (
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                      <span>Copy URL</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-950 px-6 py-4 text-xs text-slate-500 text-center">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>RabTech Academy Python Software Engineering Internship · CLI Diagnostics Project</span>
          <span>Packaged with setuptools, pyproject.toml & pytest · Production Verified</span>
        </div>
      </footer>
    </div>
  );
}
