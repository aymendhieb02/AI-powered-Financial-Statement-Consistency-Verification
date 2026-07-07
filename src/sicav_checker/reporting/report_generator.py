from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from sicav_checker.comparison.coverage import comparison_coverage, is_anomaly_status
from sicav_checker.comparison.metrics import build_metric_breakdown, build_review_items
from sicav_checker.domain.models import ComparisonReport
from sicav_checker.reporting.excel_report import write_excel_report


class ReportGenerator(ABC):
    """Base interface for accountant-facing report generators."""

    @abstractmethod
    def generate(self, report: ComparisonReport, output_dir: Path) -> Path:
        raise NotImplementedError


class ExcelGenerator(ReportGenerator):
    """Generate an accountant-facing Excel workbook from a ComparisonReport."""

    def __init__(self, filename: str = "maxula_consistency_report.xlsx") -> None:
        self.filename = filename

    def generate(self, report: ComparisonReport, output_dir: Path) -> Path:
        output = output_dir / self.filename
        output.parent.mkdir(parents=True, exist_ok=True)
        try:
            import pandas as pd
        except ImportError:
            return write_excel_report(output, report.documents, report.comparisons, report.validations, report.missing_years)

        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            for sheet, rows in _report_tables(report).items():
                pd.DataFrame(rows).to_excel(writer, sheet_name=sheet[:31], index=False)
            workbook = writer.book
            ok = workbook.add_format({"bg_color": "#C6EFCE", "font_color": "#006100"})
            bad = workbook.add_format({"bg_color": "#FFC7CE", "font_color": "#9C0006"})
            warn = workbook.add_format({"bg_color": "#FFEB9C", "font_color": "#9C6500"})
            for worksheet in writer.sheets.values():
                worksheet.freeze_panes(1, 0)
                worksheet.set_column(0, 30, 20)
                worksheet.conditional_format("A1:AZ5000", {"type": "text", "criteria": "containing", "value": "OK", "format": ok})
                worksheet.conditional_format("A1:AZ5000", {"type": "text", "criteria": "containing", "value": "MISMATCH", "format": bad})
                worksheet.conditional_format("A1:AZ5000", {"type": "text", "criteria": "containing", "value": "MISSING", "format": bad})
                worksheet.conditional_format("A1:AZ5000", {"type": "text", "criteria": "containing", "value": "LOW", "format": warn})
        return output


class JsonGenerator(ReportGenerator):
    """Generate a machine-readable JSON report from a ComparisonReport."""

    def __init__(self, filename: str = "maxula_consistency_report.json") -> None:
        self.filename = filename

    def generate(self, report: ComparisonReport, output_dir: Path) -> Path:
        output = output_dir / self.filename
        output.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "summary": _summary(report),
            "metrics": _metrics(report),
            "review_items": _review_items(report),
            "documents": [_dump(item) for item in report.documents],
            "cross_year_checks": [_dump(item) for item in report.comparisons],
            "internal_validation": [_dump(item) for item in report.validations],
            "rule_results": [_dump(item) for item in report.rule_results],
            "evidence": [_dump(item) for item in report.evidence],
            "confidence": _dump(report.confidence) if report.confidence else None,
            "verification_history": [_dump(item) for item in report.verification_history],
            "missing_years": report.missing_years,
        }
        output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return output


def _report_tables(report: ComparisonReport) -> dict[str, list[dict[str, Any]]]:
    review_items = _review_items(report)
    return {
        "Summary": _summary_rows(report),
        "Metrics": _metric_rows(report),
        "Financial Consistency": [item for item in review_items if item["status"] in {"carry_forward_ok", "LABEL_RENAMED", "OK"}],
        "Extraction Issues": [item for item in review_items if item["status"] in {"parse_low_confidence", "LOW_CONFIDENCE_EXTRACTION"} or item.get("evidence_type") in {"low_confidence_parse", "review"}],
        "Actual Mismatches": [item for item in review_items if item["status"] in {"carry_forward_mismatch", "MISMATCH"}],
        "Missing Accounts": [item for item in review_items if item["status"] in {"missing_in_old_current", "missing_in_new_comparative", "MISSING_IN_OLD", "MISSING_IN_NEW"}],
        "Duplicate Labels": [item for item in review_items if item["status"] == "duplicate_label"],
        "Detailed Evidence": review_items,
        "Cross-Year Checks": [_dump(item) for item in report.comparisons],
        "Internal Validation": [_dump(item) for item in report.validations],
        "Rule Results": [_dump(item) for item in report.rule_results or _validation_rule_rows(report)],
        "Extraction Quality": [_document_quality(item) for item in report.documents],
        "Missing Years": [{"missing_year": year} for year in report.missing_years],
        "Confidence Summary": [_dump(report.confidence)] if report.confidence else [],
        "Evidence Trace": [_dump(item) for item in report.evidence],
        "Verification History": [_dump(item) for item in report.verification_history],
        "Matching Summary": [_matching_row(item) for item in report.comparisons],
    }


def _metrics(report: ComparisonReport) -> dict[str, Any]:
    docs = sorted(report.documents, key=lambda document: document.document_year or 0)
    old_document = docs[0] if docs else None
    new_document = docs[-1] if len(docs) > 1 else old_document
    return build_metric_breakdown(old_document, new_document, report.comparisons, report.validations)


def _review_items(report: ComparisonReport) -> list[dict[str, Any]]:
    docs = sorted(report.documents, key=lambda document: document.document_year or 0)
    old_document = docs[0] if docs else None
    new_document = docs[-1] if len(docs) > 1 else old_document
    return build_review_items(report.comparisons, old_document, new_document)


def _metric_rows(report: ComparisonReport) -> list[dict[str, Any]]:
    metrics = _metrics(report)
    keys = [
        "financial_consistency",
        "financial_consistency_numerator",
        "financial_consistency_denominator",
        "extraction_coverage",
        "extraction_coverage_numerator",
        "extraction_coverage_denominator",
        "structural_quality",
        "actual_mismatches",
        "missing_accounts",
        "duplicate_labels",
        "polluted_labels",
        "critical_accounting_errors",
        "extraction_confidence",
    ]
    rows = [{"Metric": key, "Value": metrics.get(key)} for key in keys]
    rows.append({"Metric": "risk_category", "Value": metrics["risk"]["category"]})
    rows.append({"Metric": "risk_rationale", "Value": metrics["risk"]["rationale"]})
    rows.append({"Metric": "verdict", "Value": metrics["verdict"]["label"]})
    rows.append({"Metric": "verdict_reason", "Value": metrics["verdict"]["reason"]})
    return rows


def _summary(report: ComparisonReport) -> dict[str, Any]:
    metrics = _metrics(report)
    return {
        "documents": len(report.documents),
        "cross_year_checks": len(report.comparisons),
        "internal_validation_checks": len(report.validations),
        "rule_checks": len(report.rule_results) or sum(1 for item in report.validations if item.rule_id),
        "anomalies": sum(1 for item in [*report.comparisons, *report.validations] if is_anomaly_status(item.status)),
        "missing_years": report.missing_years,
        "confidence": report.confidence.overall if report.confidence else None,
        **_coverage(report),
        **{key: value for key, value in metrics.items() if key not in {"risk", "verdict", "why_verdict", "metric_debug"}},
        "risk_category": metrics["risk"]["category"],
        "risk_level": metrics["risk"]["level"],
        "risk_rationale": metrics["risk"]["rationale"],
        "verdict": metrics["verdict"]["label"],
        "verdict_reason": metrics["verdict"]["reason"],
    }


def _coverage(report: ComparisonReport) -> dict[str, Any]:
    if len(report.documents) < 2:
        return {
            "old_extracted_lines": 0,
            "new_extracted_lines": 0,
            "comparable_lines": len(report.comparisons),
            "matched_lines": 0,
            "mismatched_lines": 0,
            "missing_in_old": 0,
            "missing_in_new": 0,
            "ignored_lines": 0,
            "comparison_coverage_percentage": 0.0,
        }
    docs = sorted(report.documents, key=lambda document: document.document_year or 0)
    return comparison_coverage(docs[0], docs[-1], report.comparisons)


def _summary_rows(report: ComparisonReport) -> list[dict[str, Any]]:
    return [{"Metric": key, "Value": value} for key, value in _summary(report).items()]


def _document_quality(document: Any) -> dict[str, Any]:
    return {
        "document_year": document.document_year,
        "source_file": document.source_file,
        "extraction_method": document.extraction_method,
        "confidence": document.confidence,
        "statements": ", ".join(document.statements),
    }


def _validation_rule_rows(report: ComparisonReport) -> list[dict[str, Any]]:
    return [_dump(item) for item in report.validations if item.rule_id]


def _matching_row(result: Any) -> dict[str, Any]:
    return {
        "pair": result.pair,
        "year": result.year,
        "statement": result.statement,
        "old_label": result.old_label,
        "new_label": result.new_label,
        "canonical_label": result.canonical_label,
        "matching_method": result.matching_method,
        "confidence": result.confidence,
        "status": result.status,
    }


def _dump(model: Any) -> dict[str, Any]:
    if model is None:
        return {}
    return model.model_dump(mode="json") if hasattr(model, "model_dump") else dict(model)
