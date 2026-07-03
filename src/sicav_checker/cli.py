from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

try:
    import typer
except ImportError:
    typer = None

try:
    from rich.console import Console
    from rich.table import Table
except ImportError:
    Console = None
    Table = None

from sicav_checker.config import settings
from sicav_checker.domain.models import ComparisonResult, FinancialDocument, ValidationResult
from sicav_checker.pipeline.orchestrator import PipelineOrchestrator
from sicav_checker.testsupport.corrupted_data_generator import create_corrupted_json


class PlainConsole:
    def print(self, message: object) -> None:
        text = str(message).replace("[green]", "").replace("[/green]", "").replace("[yellow]", "").replace("[/yellow]", "")
        print(text)


console = Console() if Console else PlainConsole()
app = typer.Typer(help="FinVerify - SICAV financial consistency checker") if typer else None


def _orchestrator() -> PipelineOrchestrator:
    return PipelineOrchestrator(app_settings=settings)


def _print_summary(documents: list[FinancialDocument], comparisons: list[ComparisonResult], validations: list[ValidationResult]) -> None:
    if Table:
        table = Table(title="FinVerify Pipeline Summary")
        table.add_column("Metric")
        table.add_column("Value", justify="right")
        table.add_row("Documents", str(len(documents)))
        table.add_row("Cross-year checks", str(len(comparisons)))
        table.add_row("Cross-year anomalies", str(sum(1 for item in comparisons if item.status != "OK")))
        table.add_row("Internal validation checks", str(len(validations)))
        table.add_row("Internal anomalies", str(sum(1 for item in validations if item.status != "OK")))
        console.print(table)
    else:
        print(f"Documents: {len(documents)}")
        print(f"Cross-year checks: {len(comparisons)}")
        print(f"Internal validation checks: {len(validations)}")


def extract_command(raw_pdfs: Path) -> None:
    documents = _orchestrator().extract(raw_pdfs)
    if not documents:
        console.print("[yellow]No PDFs found.[/yellow]")
        return
    for document in documents:
        console.print(f"[green]Extracted[/green] {Path(document.source_file).name} ({document.document_year})")


def compare_command(raw_pdfs: Path | None = None) -> None:
    documents, comparisons, validations, _ = _orchestrator().compare()
    _print_summary(documents, comparisons, validations)


def report_command(raw_pdfs: Path | None = None) -> None:
    result = _orchestrator().report()
    _print_summary(result.documents, result.comparisons, result.validations)
    for path in result.report_paths:
        console.print(f"[green]Report:[/green] {path}")


def all_command(raw_pdfs: Path) -> None:
    result = _orchestrator().run_all(raw_pdfs)
    _print_summary(result.documents, result.comparisons, result.validations)
    for path in result.report_paths:
        console.print(f"[green]Report:[/green] {path}")


def create_test_errors_command(output_dir: Path = Path("data/corrupted_tests")) -> None:
    paths = create_corrupted_json(output_dir)
    for path in paths:
        console.print(f"[green]Created[/green] {path}")


def run_tests_command() -> int:
    return subprocess.call([sys.executable, "-m", "pytest"])


if typer:
    @app.command("extract")
    def extract(raw_pdfs: Path = typer.Argument(..., exists=True, file_okay=False)) -> None:
        extract_command(raw_pdfs)

    @app.command("compare")
    def compare(raw_pdfs: Path = typer.Argument(Path("data/raw_pdfs"), exists=True, file_okay=False)) -> None:
        compare_command(raw_pdfs)

    @app.command("report")
    def report(raw_pdfs: Path = typer.Argument(Path("data/raw_pdfs"), exists=True, file_okay=False)) -> None:
        report_command(raw_pdfs)

    @app.command("all")
    def all(raw_pdfs: Path = typer.Argument(..., exists=True, file_okay=False)) -> None:
        all_command(raw_pdfs)

    @app.command("create-test-errors")
    def create_test_errors(output_dir: Path = Path("data/corrupted_tests")) -> None:
        create_test_errors_command(output_dir)

    @app.command("test")
    def run_tests() -> None:
        raise typer.Exit(run_tests_command())


def main(argv: list[str] | None = None) -> int:
    if typer:
        app()
        return 0

    parser = argparse.ArgumentParser(description="FinVerify - SICAV financial consistency checker")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ["extract", "compare", "report", "all"]:
        sub = subparsers.add_parser(name)
        sub.add_argument("raw_pdfs", nargs="?", type=Path, default=Path("data/raw_pdfs"))
    errors = subparsers.add_parser("create-test-errors")
    errors.add_argument("output_dir", nargs="?", type=Path, default=Path("data/corrupted_tests"))
    subparsers.add_parser("test")

    args = parser.parse_args(argv)
    if args.command in {"extract", "compare", "report", "all"} and not args.raw_pdfs.is_dir():
        parser.error(f"{args.raw_pdfs} is not a directory")
    if args.command == "extract":
        extract_command(args.raw_pdfs)
    elif args.command == "compare":
        compare_command(args.raw_pdfs)
    elif args.command == "report":
        report_command(args.raw_pdfs)
    elif args.command == "all":
        all_command(args.raw_pdfs)
    elif args.command == "create-test-errors":
        create_test_errors_command(args.output_dir)
    elif args.command == "test":
        return run_tests_command()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())