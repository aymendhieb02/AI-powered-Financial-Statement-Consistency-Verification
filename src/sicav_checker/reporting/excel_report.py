from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
from xml.sax.saxutils import escape

from sicav_checker.models import ComparisonResult, ExtractedDocument, InternalValidationResult

SHEETS = ["Summary", "Cross-Year Checks", "Internal Validation", "Extraction Quality", "Missing Years"]


def _dump(model: object) -> dict:
    return model.model_dump(mode="json") if hasattr(model, "model_dump") else model.dict()


def write_excel_report(path: str | Path, documents: list[ExtractedDocument], comparisons: list[ComparisonResult], validations: list[InternalValidationResult], missing_years: list[int]) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        return _write_with_pandas(output, documents, comparisons, validations, missing_years)
    except ImportError:
        return _write_basic_xlsx(output, documents, comparisons, validations, missing_years)


def _data(documents: list[ExtractedDocument], comparisons: list[ComparisonResult], validations: list[InternalValidationResult], missing_years: list[int]) -> dict[str, list[dict]]:
    return {
        "Summary": [
            {"Metric": "Documents extracted", "Value": len(documents)},
            {"Metric": "Cross-year checks", "Value": len(comparisons)},
            {"Metric": "Internal validation checks", "Value": len(validations)},
            {"Metric": "Cross-year anomalies", "Value": sum(1 for i in comparisons if i.status != "OK")},
            {"Metric": "Internal anomalies", "Value": sum(1 for i in validations if i.status != "OK")},
        ],
        "Cross-Year Checks": [_dump(i) for i in comparisons],
        "Internal Validation": [_dump(i) for i in validations],
        "Extraction Quality": [{"document_year": d.document_year, "source_file": d.source_file, "extraction_method": d.extraction_method, "confidence": d.confidence, "statements": ", ".join(d.statements)} for d in documents],
        "Missing Years": [{"missing_year": y} for y in missing_years],
    }


def _write_with_pandas(output: Path, documents: list[ExtractedDocument], comparisons: list[ComparisonResult], validations: list[InternalValidationResult], missing_years: list[int]) -> Path:
    import pandas as pd
    data = _data(documents, comparisons, validations, missing_years)
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        for sheet, rows in data.items():
            pd.DataFrame(rows).to_excel(writer, sheet_name=sheet, index=False)
        workbook = writer.book
        ok = workbook.add_format({"bg_color": "#C6EFCE", "font_color": "#006100"})
        bad = workbook.add_format({"bg_color": "#FFC7CE", "font_color": "#9C0006"})
        miss = workbook.add_format({"bg_color": "#FCE4D6", "font_color": "#9C6500"})
        low = workbook.add_format({"bg_color": "#FFEB9C", "font_color": "#9C6500"})
        for sheet in ("Cross-Year Checks", "Internal Validation"):
            ws = writer.sheets[sheet]
            ws.freeze_panes(1, 0)
            ws.set_column(0, 20, 18)
            ws.conditional_format("A1:Z5000", {"type": "text", "criteria": "containing", "value": "OK", "format": ok})
            ws.conditional_format("A1:Z5000", {"type": "text", "criteria": "containing", "value": "MISMATCH", "format": bad})
            ws.conditional_format("A1:Z5000", {"type": "text", "criteria": "containing", "value": "MISSING", "format": miss})
            ws.conditional_format("A1:Z5000", {"type": "text", "criteria": "containing", "value": "LOW_CONFIDENCE_EXTRACTION", "format": low})
    return output

def _write_basic_xlsx(output: Path, documents: list[ExtractedDocument], comparisons: list[ComparisonResult], validations: list[InternalValidationResult], missing_years: list[int]) -> Path:
    data = _data(documents, comparisons, validations, missing_years)
    with ZipFile(output, "w", ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _content_types())
        z.writestr("_rels/.rels", "<?xml version='1.0'?><Relationships xmlns='http://schemas.openxmlformats.org/package/2006/relationships'><Relationship Id='rId1' Type='http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument' Target='xl/workbook.xml'/></Relationships>")
        z.writestr("xl/workbook.xml", _workbook())
        z.writestr("xl/_rels/workbook.xml.rels", _rels())
        z.writestr("xl/styles.xml", _styles())
        for i, sheet in enumerate(SHEETS, 1):
            z.writestr(f"xl/worksheets/sheet{i}.xml", _sheet(data.get(sheet, [])))
    return output


def _headers(rows: list[dict]) -> list[str]:
    headers: list[str] = []
    for row in rows:
        for key in row:
            if key not in headers:
                headers.append(key)
    return headers or ["No data"]


def _style(row: dict, header: bool = False) -> int:
    if header:
        return 1
    status = str(row.get("status", ""))
    if status == "OK":
        return 2
    if status == "MISMATCH":
        return 3
    if "MISSING" in status:
        return 4
    if status == "LOW_CONFIDENCE_EXTRACTION":
        return 5
    return 0


def _sheet(rows: list[dict]) -> str:
    headers = _headers(rows)
    xml_rows = [_row(1, {h: h for h in headers}, headers, 1)]
    for idx, row in enumerate(rows or [{headers[0]: ""}], 2):
        xml_rows.append(_row(idx, row, headers, _style(row)))
    return "<?xml version='1.0' encoding='UTF-8'?><worksheet xmlns='http://schemas.openxmlformats.org/spreadsheetml/2006/main'><sheetViews><sheetView workbookViewId='0'><pane ySplit='1' topLeftCell='A2' activePane='bottomLeft' state='frozen'/></sheetView></sheetViews><sheetData>" + "".join(xml_rows) + "</sheetData></worksheet>"


def _row(num: int, row: dict, headers: list[str], style: int) -> str:
    cells = []
    for col, header in enumerate(headers, 1):
        ref = f"{_col(col)}{num}"
        value = escape(str(row.get(header, "")))
        cells.append(f"<c r='{ref}' t='inlineStr' s='{style}'><is><t>{value}</t></is></c>")
    return f"<row r='{num}'>" + "".join(cells) + "</row>"


def _col(index: int) -> str:
    name = ""
    while index:
        index, rem = divmod(index - 1, 26)
        name = chr(65 + rem) + name
    return name


def _content_types() -> str:
    sheets = "".join(f"<Override PartName='/xl/worksheets/sheet{i}.xml' ContentType='application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml'/>" for i in range(1, len(SHEETS) + 1))
    return "<?xml version='1.0'?><Types xmlns='http://schemas.openxmlformats.org/package/2006/content-types'><Default Extension='rels' ContentType='application/vnd.openxmlformats-package.relationships+xml'/><Default Extension='xml' ContentType='application/xml'/><Override PartName='/xl/workbook.xml' ContentType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml'/><Override PartName='/xl/styles.xml' ContentType='application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml'/>" + sheets + "</Types>"


def _workbook() -> str:
    sheets = "".join(f"<sheet name='{escape(name)}' sheetId='{i}' r:id='rId{i}'/>" for i, name in enumerate(SHEETS, 1))
    return "<?xml version='1.0'?><workbook xmlns='http://schemas.openxmlformats.org/spreadsheetml/2006/main' xmlns:r='http://schemas.openxmlformats.org/officeDocument/2006/relationships'><sheets>" + sheets + "</sheets></workbook>"


def _rels() -> str:
    rels = "".join(f"<Relationship Id='rId{i}' Type='http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet' Target='worksheets/sheet{i}.xml'/>" for i in range(1, len(SHEETS) + 1))
    rels += f"<Relationship Id='rId{len(SHEETS) + 1}' Type='http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles' Target='styles.xml'/>"
    return "<?xml version='1.0'?><Relationships xmlns='http://schemas.openxmlformats.org/package/2006/relationships'>" + rels + "</Relationships>"


def _styles() -> str:
    fills = "<fill><patternFill patternType='none'/></fill><fill><patternFill patternType='gray125'/></fill>"
    fills += "<fill><patternFill patternType='solid'><fgColor rgb='FFD9EAF7'/></patternFill></fill>"
    fills += "<fill><patternFill patternType='solid'><fgColor rgb='FFC6EFCE'/></patternFill></fill>"
    fills += "<fill><patternFill patternType='solid'><fgColor rgb='FFFFC7CE'/></patternFill></fill>"
    fills += "<fill><patternFill patternType='solid'><fgColor rgb='FFFCE4D6'/></patternFill></fill>"
    fills += "<fill><patternFill patternType='solid'><fgColor rgb='FFFFEB9C'/></patternFill></fill>"
    xfs = "<xf numFmtId='0' fontId='0' fillId='0' borderId='0' xfId='0'/>"
    xfs += "<xf numFmtId='0' fontId='1' fillId='2' borderId='0' xfId='0' applyFont='1' applyFill='1'/>"
    xfs += "<xf numFmtId='0' fontId='0' fillId='3' borderId='0' xfId='0' applyFill='1'/>"
    xfs += "<xf numFmtId='0' fontId='0' fillId='4' borderId='0' xfId='0' applyFill='1'/>"
    xfs += "<xf numFmtId='0' fontId='0' fillId='5' borderId='0' xfId='0' applyFill='1'/>"
    xfs += "<xf numFmtId='0' fontId='0' fillId='6' borderId='0' xfId='0' applyFill='1'/>"
    return "<?xml version='1.0'?><styleSheet xmlns='http://schemas.openxmlformats.org/spreadsheetml/2006/main'><fonts count='2'><font><sz val='11'/><name val='Calibri'/></font><font><b/><sz val='11'/><name val='Calibri'/></font></fonts><fills count='7'>" + fills + "</fills><borders count='1'><border><left/><right/><top/><bottom/><diagonal/></border></borders><cellStyleXfs count='1'><xf numFmtId='0' fontId='0' fillId='0' borderId='0'/></cellStyleXfs><cellXfs count='6'>" + xfs + "</cellXfs></styleSheet>"
