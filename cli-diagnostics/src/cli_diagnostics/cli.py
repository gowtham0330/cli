"""Command-line interface entry point for cli-diagnostics."""

from __future__ import annotations

import argparse
import datetime
import sys
from typing import List, Optional

from cli_diagnostics import __version__
from cli_diagnostics.diagnostics import run_system_diagnostics
from cli_diagnostics.events import EventValidationError, process_events_file
from cli_diagnostics.models import (
    DiagnosticReport,
    DiagnosticStatus,
    EventAnalysisResult,
)
from cli_diagnostics.reporting import (
    format_terminal_report,
    write_reports,
)

# Standard Exit Codes
EXIT_SUCCESS = 0
EXIT_DIAGNOSTIC_FAILURE = 1
EXIT_USAGE_OR_INPUT_ERROR = 2
EXIT_INTERNAL_ERROR = 3


class DiagnosticsArgumentParser(argparse.ArgumentParser):
    """Custom ArgumentParser to exit with code 2 on syntax/usage errors."""

    def error(self, message: str) -> None:
        sys.stderr.write(f"error: {message}\n")
        sys.exit(EXIT_USAGE_OR_INPUT_ERROR)


def build_parser() -> DiagnosticsArgumentParser:
    """Build command-line parser supporting flags and 'run' subcommand."""
    parser = DiagnosticsArgumentParser(
        prog="cli-diagnostics",
        description=(
            "Packaged CLI Diagnostics Tool - System health diagnostics and "
            "telemetry event analysis."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=f"cli-diagnostics {__version__}",
        help="Show program version number and exit.",
    )

    # Subparsers to cleanly support `cli-diagnostics run ...`
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")
    run_parser = subparsers.add_parser(
        "run",
        help="Execute diagnostics and event analysis.",
        description="Execute complete diagnostics pipeline.",
    )

    # Attach diagnostic options to both run_parser and root parser for convenience
    for p in (run_parser, parser):
        p.add_argument(
            "--events",
            type=str,
            default=None,
            metavar="PATH",
            help="Path to JSON diagnostic events file to analyze.",
        )
        p.add_argument(
            "--output",
            type=str,
            default=None,
            metavar="PATH",
            help="Path to write human-readable plain text diagnostic report.",
        )
        p.add_argument(
            "--json-output",
            type=str,
            default=None,
            metavar="PATH",
            help="Path to write structured JSON diagnostic report.",
        )
        p.add_argument(
            "--min-disk-mb",
            type=float,
            default=1024.0,
            metavar="MB",
            help="Minimum acceptable free disk space in megabytes (default: 1024.0).",
        )
        p.add_argument(
            "--strict",
            action="store_true",
            help="Strict mode: treat any warning as a diagnostic failure (exit code 1).",
        )
        p.add_argument(
            "--pretty",
            action="store_true",
            default=False,
            help="Format terminal and JSON output with enhanced indentation and headers.",
        )

    return parser


def run_pipeline(
    events_path: Optional[str] = None,
    output_path: Optional[str] = None,
    json_output_path: Optional[str] = None,
    min_disk_mb: float = 1024.0,
    strict: bool = False,
    pretty: bool = False,
) -> int:
    """Execute the core diagnostics and reporting workflow."""
    # 1. System diagnostics
    system_results = run_system_diagnostics(min_disk_mb=min_disk_mb)

    # 2. Event analysis if requested
    event_results: Optional[EventAnalysisResult] = None
    if events_path:
        try:
            event_results = process_events_file(events_path)
        except (FileNotFoundError, EventValidationError) as exc:
            sys.stderr.write(f"Input Error: {exc}\n")
            return EXIT_USAGE_OR_INPUT_ERROR
        except Exception as exc:
            sys.stderr.write(f"Unexpected error parsing events: {exc}\n")
            return EXIT_INTERNAL_ERROR

    # 3. Determine Overall Status & Exit Code
    # Diagnostic failures:
    # - System diagnostics is UNHEALTHY
    # - Event analysis is unhealthy or status == "attention required"
    # - Strict mode is enabled and warnings exist
    has_system_failure = system_results.overall_status == DiagnosticStatus.UNHEALTHY
    has_event_failure = bool(event_results and not event_results.is_healthy)

    has_system_warning = system_results.overall_status == DiagnosticStatus.WARNING
    has_event_warning = bool(
        event_results and event_results.overall_status == "warning"
    )

    if has_system_failure or has_event_failure:
        exit_code = EXIT_DIAGNOSTIC_FAILURE
        overall_status = "attention required"
    elif strict and (has_system_warning or has_event_warning):
        exit_code = EXIT_DIAGNOSTIC_FAILURE
        overall_status = "warning (strict failure)"
    elif has_system_warning or has_event_warning:
        exit_code = EXIT_SUCCESS
        overall_status = "warning"
    else:
        exit_code = EXIT_SUCCESS
        overall_status = "healthy"

    # 4. Compile final report
    report = DiagnosticReport(
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        tool_name="cli-diagnostics",
        tool_version=__version__,
        system_diagnostics=system_results,
        event_analysis=event_results,
        overall_status=overall_status,
        exit_code=exit_code,
        strict_mode=strict,
    )

    # 5. Output rendering
    terminal_report = format_terminal_report(report, pretty=pretty)
    sys.stdout.write(terminal_report + "\n")

    # 6. File persistence
    if output_path or json_output_path:
        try:
            write_reports(
                report=report,
                text_path=output_path,
                json_path=json_output_path,
                pretty=pretty,
            )
        except Exception as exc:
            sys.stderr.write(f"Internal Error writing report files: {exc}\n")
            return EXIT_INTERNAL_ERROR

    return exit_code


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point for cli-diagnostics."""
    if argv is None:
        argv = sys.argv[1:]

    parser = build_parser()

    # Pre-parse validation for min-disk-mb negative check
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return exc.code

    if args.min_disk_mb is not None and args.min_disk_mb < 0:
        sys.stderr.write("error: --min-disk-mb must be a non-negative number.\n")
        return EXIT_USAGE_OR_INPUT_ERROR

    try:
        return run_pipeline(
            events_path=args.events,
            output_path=args.output,
            json_output_path=args.json_output,
            min_disk_mb=args.min_disk_mb,
            strict=args.strict,
            pretty=args.pretty,
        )
    except Exception as exc:
        sys.stderr.write(f"Unexpected internal fatal error: {exc}\n")
        return EXIT_INTERNAL_ERROR


if __name__ == "__main__":
    sys.exit(main())
