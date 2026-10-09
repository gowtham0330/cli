# Packaged CLI Diagnostics Tool (`cli-diagnostics`)

**RabTech Academy — Python Software Engineering Internship Project**  
*Production-ready Python CLI diagnostics package with system health analysis, developer tool auditing, secret-redacted environment inspection, and JSON telemetry event stream classification.*

---

## 1. Project Overview

`cli-diagnostics` is a professional, installable Python command-line utility built for reliability engineering, system triage, and telemetry health classification. It is engineered following standard Python packaging specifications (`pyproject.toml`, standard library emphasis, setuptools build backend, and pytest automated testing).

### Core Capabilities

- **Python Runtime Inspection**: Checks Python version (enforcing `>= 3.10`), implementation (CPython/PyPy), and executable path.
- **Host Operating System Diagnostics**: Queries OS kernel, release, machine architecture, and platform strings across Windows, Linux, and macOS.
- **Disk Capacity Auditing**: Measures total, used, and free disk space against customizable thresholds (`--min-disk-mb`), issuing proactive warnings when approaching limits.
- **Developer Toolchain Verification**: Audits presence, system paths, and version strings for essential developer tools: `git`, `pip`, `pytest`, `node`, `npm`, and `docker`.
- **Automated Secret Redaction**: Inspects key environment variables while redacting sensitive tokens, passwords, and API keys.
- **Telemetry Event Analysis & Health Classification**: Ingests JSON event streams (such as `samples/diagnostic-events.json`), aggregates latency and error distributions, computes HTTP 5xx occurrences, identifies missing latency metrics, and classifies service health (`HEALTHY`, `WARNING`, `UNHEALTHY`).
- **Dual Reporting Engines**: Outputs clean, high-legibility terminal dashboards and structured, machine-parsable JSON reports.
- **Strict Exit Codes**: Complies with standard CLI exit code contracts for CI/CD integration, with customizable warning escalation via `--strict`.

---

## 2. Repository Layout

```text
cli-diagnostics/
├── pyproject.toml                     # PEP 621 package metadata & entry points
├── README.md                          # Complete project documentation & guide
├── LICENSE                            # MIT License
├── .gitignore                         # Python, environment & cache ignore rules
├── src/
│   └── cli_diagnostics/
│       ├── __init__.py                # Package root & public exports
│       ├── __main__.py                # python -m cli_diagnostics runner
│       ├── init.py                    # Module initialization alias
│       ├── main.py                    # Module main execution alias
│       ├── cli.py                     # CLI argument parsing & workflow orchestration
│       ├── diagnostics.py             # Host system, disk & toolchain audits
│       ├── events.py                  # JSON event validation & health classification
│       ├── models.py                  # Dataclasses & typed enumerations
│       └── reporting.py               # Terminal & JSON report formatters
├── tests/
│   ├── test_cli.py                    # CLI argument parsing, flags & exit code tests
│   ├── test_diagnostics.py            # Unit tests for OS, disk, python & redaction
│   ├── test_events.py                 # Telemetry ingestion, validation & security tests
│   └── test_reporting.py              # Report generation & persistence tests
├── samples/
│   └── diagnostic-events.json         # Reference 5-event sample dataset
└── reports/
    ├── .gitkeep
    ├── report.json                    # Sample generated JSON report
    └── report.txt                     # Sample generated terminal text report
```

---

## 3. Installation Guide

This package requires **Python 3.10 or higher**.

### On Linux & macOS

1. **Clone the repository and enter the directory**:
   ```bash
   git clone <YOUR_GITHUB_REPOSITORY_URL>
   cd cli-diagnostics
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install the package in editable mode with development dependencies**:
   ```bash
   python3 -m pip install -e ".[dev]"
   ```

4. **Verify the console entry point**:
   ```bash
   cli-diagnostics --version
   ```

---

### On Windows (PowerShell)

1. **Clone the repository and enter the directory**:
   ```powershell
   git clone <YOUR_GITHUB_REPOSITORY_URL>
   cd cli-diagnostics
   ```

2. **Create and activate a virtual environment**:
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```
   *(If script execution is restricted, run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process` before activating).*

3. **Install the package in editable mode with development dependencies**:
   ```powershell
   python -m pip install -e ".[dev]"
   ```

4. **Verify installation**:
   ```powershell
   cli-diagnostics --version
   ```

---

## 4. Usage & Command-Line Arguments

The console script entry point is registered as `cli-diagnostics`. You can run diagnostics directly or using the `run` subcommand:

```bash
cli-diagnostics [OPTIONS]
# or
cli-diagnostics run [OPTIONS]
```

### Supported Arguments

| Flag | Parameter | Description |
| :--- | :--- | :--- |
| `-h`, `--help` | None | Display usage information and exit |
| `-v`, `--version` | None | Display installed package version and exit |
| `run` | Subcommand | Execute the full diagnostic pipeline |
| `--events` | `PATH` | Path to JSON diagnostic events file to evaluate |
| `--output` | `PATH` | Destination file path for plain-text human-readable report |
| `--json-output` | `PATH` | Destination file path for structured JSON report |
| `--min-disk-mb` | `MB` | Minimum required free disk space in megabytes (default: `1024.0`) |
| `--strict` | Flag | Strict mode: treats warnings as diagnostic failures (`exit 1`) |
| `--pretty` | Flag | Pretty-formats terminal tables and indents JSON output |

---

## 5. Exit Code Specification

| Exit Code | Meaning | Condition |
| :---: | :--- | :--- |
| **`0`** | **Success** | All system diagnostics passed; events healthy (or warnings present in non-strict mode). |
| **`1`** | **Diagnostic Failure** | Free disk space below `--min-disk-mb`, unsupported Python version, degraded telemetry services (`UNHEALTHY` / `attention required`), or any warning when `--strict` is enabled. |
| **`2`** | **Usage or Input Error** | Missing events file, malformed JSON, schema validation failure, negative `--min-disk-mb`, or unrecognized CLI arguments. |
| **`3`** | **Internal Error** | Unhandled system exception, file permission write error, or fatal OS error. |

### Warning Behavior & Strict Mode

- **Normal Mode (default)**: When a check produces a warning (e.g. missing optional developer tools such as `docker` or `pytest`, or disk space approaching threshold), the CLI displays `[WARN]` and exits with code `0`, allowing non-blocking workflow progression.
- **Strict Mode (`--strict`)**: Any detected warning elevates the final status to `warning (strict failure)` and terminates with exit code `1`. Use this in strict CI/CD environments.

---

## 6. Telemetry Event Validation & Expected Results

The package includes sample telemetry data at `samples/diagnostic-events.json` generated for the RabTech Python Software Engineering Internship:

```json
{
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
}
```

### Analysis Classification Results

When executing:
```bash
cli-diagnostics run --events samples/diagnostic-events.json --json-output reports/report.json --pretty
```

The pipeline produces the exact expected validation metrics:
- **Total events**: `5`
- **INFO**: `2`
- **WARN**: `1`
- **ERROR**: `2`
- **HTTP 5xx events**: `2` (HTTP 503 and HTTP 500)
- **billing-api events**: `4` (1 INFO, 1 WARN, 2 ERROR)
- **profile-api events**: `1` (1 INFO)
- **Missing latency events**: `1` (event index 4 has `null` latency)
- **billing-api health**: `UNHEALTHY` (due to ERROR events and 5xx failures)
- **profile-api health**: `HEALTHY` (all operations nominal)
- **Overall status**: `attention required`
- **Exit code**: `1` (diagnostic failure triggered by unhealthy service)

---

## 7. Security & Redaction Safeguards

1. **Zero Execution of JSON Inputs**: The event parser uses static JSON parsing and validates fields against typed schemas. Even if a payload contains fields like `command`, `exec`, or `shell`, they are never passed to an execution environment (`eval`, `exec`, or shell subprocesses).
2. **Automated Secret Redaction**: Environment audit routines inspect sensitive keywords (`KEY`, `SECRET`, `TOKEN`, `PASSWORD`, `AUTH`, `CREDENTIAL`, `API`) and replace them with `***REDACTED***` in both terminal and JSON outputs.

---

## 8. Running Automated Tests

Run the full pytest suite with verbose or quiet flags:

```bash
# Quiet mode
pytest -q

# Verbose mode
pytest -v
```

All 36 test cases cover:
- Host runtime checks and Python version thresholds
- Disk space limits and exception handling
- Toolchain discovery and subprocess isolation via mocks
- Environment variable inspection and secret masking
- JSON schema validation, error states, and injection safety
- Aggregated service classification and latency math
- CLI argument parsing, flags, subcommands, and exit codes 0, 1, 2, and 3

---

## 9. Steps to Publish to GitHub for RabTech Submission

Follow these exact steps to publish your completed project to GitHub:

### Step 1: Create a New GitHub Repository
1. Log into your GitHub account at [https://github.com](https://github.com).
2. Click the **+** icon in the upper-right corner and select **New repository**.
3. Name your repository: `cli-diagnostics` (or `rabtech-cli-diagnostics`).
4. Set visibility to **Public** (required so RabTech evaluators can inspect your code).
5. **Do NOT** initialize with a README, .gitignore, or license (we already have pristine versions).
6. Click **Create repository**.

### Step 2: Initialize Git and Push from Local Directory

Open your terminal or PowerShell in the project directory:

```bash
# 1. Initialize git
git init

# 2. Stage all files
git add .

# 3. Create your initial commit
git commit -m "feat: complete RabTech Academy packaged CLI diagnostics tool"

# 4. Set default branch to main
git branch -M main

# 5. Link your GitHub remote (replace with your actual username and repo name)
git remote add origin https://github.com/<YOUR-GITHUB-USERNAME>/cli-diagnostics.git

# 6. Push to GitHub
git push -u origin main
```

### Step 3: Verify and Submit

1. Open your browser and navigate to:
   `https://github.com/<YOUR-GITHUB-USERNAME>/cli-diagnostics`
2. Confirm all files (`pyproject.toml`, `README.md`, `LICENSE`, `src/`, `tests/`, `samples/`, `reports/`) are visible and the README renders cleanly.
3. Copy your repository URL:
   `https://github.com/<YOUR-GITHUB-USERNAME>/cli-diagnostics`
4. Paste this public GitHub URL into your **RabTech Academy Python Software Engineering Internship Portal** submission form.

---

## 10. License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
