from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

try:
    import typer
except ImportError:
    typer = None

try:
    from loguru import logger
except ImportError:
    class _Logger:
        def info(self, message: str, *args: object) -> None:
            print(message.format(*args))
    logger = _Logger()

try:
    from rich.console import Console
    from rich.table import Table
except ImportError:
    Console = None
    Table = None

from sicav_checker.comparison.cross_year_comparator import compare_documents
from sicav_checker.comparison.pair_builder import build_valid_pairs
from sicav_checker.extraction.pdf_loader import list_pdfs
from sicav_checker.extraction.statement_extractor import extract_document
from sicav_checker.models import ComparisonResult, ExtractedDocument, InternalValidationResult
from sicav_checker.reporting.excel_report import write_excel_report
from sicav_checker.reporting.json_report import write_json_report
from sicav_checker.testsupport.corrupted_data_generator import create_corrupted_json
from sicav_checker.validation.internal_validator import validate_document


class PlainConsole:
    def print(self, message: object) -> None:
        text = str(message).replace("[green]", "").replace("[/green]", "").replace("[yellow]", "").replace("[/yellow]", "")
        print(text)


console = Console() if Console else PlainConsole()
app = typer.Typer(help="SICAV Financial Consistency Checker") if typer else None


def _dump_model(model: object) -> dict:
    if hasattr(model, "model_dump"):
        return model.model_dump(mode="json")
    return model.dict()


def _project_root(raw_dir: Path) -> Path:
    return raw_dir.parent.parent if raw_dir.name == "raw_pdfs" else Path.cwd()


def _extracted_dir(raw_dir: Path) -> Path:
    return _project_root(raw_dir) / "data" / "extracted_json"


def _reports_dir(raw_dir: Path) -> Path:
    return _project_root(raw_dir) / "data" / "reports"


def _write_document(doc: ExtractedDocument, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{doc.document_year}.json"
    path.write_text(json.dumps(_dump_model(doc), indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def _load_documents(raw_dir: Path) -> list[ExtractedDocument]:
    extracted = _extracted_dir(raw_dir)
    docs: list[ExtractedDocument] = []
    for path in sorted(extracted.glob("*.json")):
        docs.append(ExtractedDocument(**json.loads(path.read_text(encoding="utf-8"))))
    return sorted(docs, key=lambda doc: doc.document_year)


def _missing_years(years: list[int]) -> list[int]:
    if not years:
        return []
    available = set(years)
    return [year for year in range(min(years), max(years) + 1) if year not in available]


def extract_command(raw_pdfs: Path) -> None:
    pdfs = list_pdfs(raw_pdfs)
    out_dir = _extracted_dir(raw_pdfs)
    if not pdfs:
        console.print("[yellow]No PDFs found.[/yellow]")
        return
    for pdf in pdfs:
        doc = extract_document(pdf)
        path = _write_document(doc, out_dir)
        console.print(f"[green]Extracted[/green] {pdf.name} -> {path}")


def compare_command(raw_pdfs: Path) -> None:
    docs = _load_documents(raw_pdfs)
    results, validations = run_checks(docs)
    if Table:
        table = Table(title="SICAV Comparison")
        table.add_column("Type")
        table.add_column("Checks", justify="right")
        table.add_column("Anomalies", justify="right")
        table.add_row("Cross-year", str(len(results)), str(sum(1 for item in results if item.status != "OK")))
        table.add_row("Internal", str(len(validations)), str(sum(1 for item in validations if item.status != "OK")))
        console.print(table)
    else:
        print(f"Cross-year checks: {len(results)}")
        print(f"Internal checks: {len(validations)}")


def report_command(raw_pdfs: Path) -> None:
    docs = _load_documents(raw_pdfs)
    comparisons, validations = run_checks(docs)
    reports = _reports_dir(raw_pdfs)
    years = [doc.document_year for doc in docs]
    missing = _missing_years(years)
    excel_path = write_excel_report(reports / "maxula_consistency_report.xlsx", docs, comparisons, validations, missing)
    json_path = write_json_report(reports / "maxula_consistency_report.json", docs, comparisons, validations, missing)
    console.print(f"[green]Excel report:[/green] {excel_path}")
    console.print(f"[green]JSON report:[/green] {json_path}")


def all_command(raw_pdfs: Path) -> None:
    extract_command(raw_pdfs)
    report_command(raw_pdfs)


def create_test_errors_command(output_dir: Path = Path("data/corrupted_tests")) -> None:
    paths = create_corrupted_json(output_dir)
    for path in paths:
        console.print(f"[green]Created[/green] {path}")


def run_tests_command() -> int:
    return subprocess.call([sys.executable, "-m", "pytest"])


def run_checks(docs: list[ExtractedDocument]) -> tuple[list[ComparisonResult], list[InternalValidationResult]]:
    docs_by_year = {doc.document_year: doc for doc in docs}
    comparisons: list[ComparisonResult] = []
    for old_year, new_year in build_valid_pairs(list(docs_by_year)):
        comparisons.extend(compare_documents(docs_by_year[old_year], docs_by_year[new_year]))
    validations: list[InternalValidationResult] = []
    for doc in docs:
        validations.extend(validate_document(doc))
    logger.info("Completed {} comparisons and {} internal validations", len(comparisons), len(validations))
    return comparisons, validations


if typer:
    @app.command("extract")
    def extract(raw_pdfs: Path = typer.Argument(..., exists=True, file_okay=False)) -> None:
        extract_command(raw_pdfs)

    @app.command("compare")
    def compare(raw_pdfs: Path = typer.Argument(..., exists=True, file_okay=False)) -> None:
        compare_command(raw_pdfs)

    @app.command("report")
    def report(raw_pdfs: Path = typer.Argument(..., exists=True, file_okay=False)) -> None:
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

    parser = argparse.ArgumentParser(description="SICAV Financial Consistency Checker")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ["extract", "compare", "report", "all"]:
        sub = subparsers.add_parser(name)
        sub.add_argument("raw_pdfs", type=Path)
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