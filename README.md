# SICAV Financial Consistency Checker

Local MVP for checking annual MAXULA PLACEMENT SICAV financial statements. It extracts statement rows from annual PDFs, compares each year current values against the comparative values published in the following available PDF, and produces accountant-readable Excel and JSON audit reports.

## Why Modular Monolith

The application is deployed and run locally as one Python project, but the code is separated into extraction, normalization, comparison, validation, storage, AI, and reporting modules. This keeps the accountant workflow simple while leaving clear boundaries for future replacement of OCR, storage, or matching logic.

## Accountant Workflow

1. Put annual SICAV PDFs in `data/raw_pdfs`.
2. Run `python -m sicav_checker.cli all data/raw_pdfs`.
3. Review `data/reports/maxula_consistency_report.xlsx`.
4. Investigate red, orange, and yellow lines before signing off.

## Setup

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Commands

```powershell
python -m sicav_checker.cli extract data/raw_pdfs
python -m sicav_checker.cli compare data/raw_pdfs
python -m sicav_checker.cli report data/raw_pdfs
python -m sicav_checker.cli all data/raw_pdfs
python -m sicav_checker.cli create-test-errors
python -m sicav_checker.cli test
```

## Output

Extraction JSON files are written to `data/extracted_json/<year>.json`.

Reports are written to:

- `data/reports/maxula_consistency_report.xlsx`
- `data/reports/maxula_consistency_report.json`

## Optional MinIO

Local storage is the default and requires no service. To use MinIO, copy `.env.example` to `.env`, set `STORAGE_BACKEND=minio`, and configure:

```env
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=sicav-documents
MINIO_SECURE=false
```

If MinIO is unavailable, the app logs a warning and continues with local storage.

## Optional Ollama

The configured local model is `qwen2.5-coder:7b`. Ollama is used only to explain anomalies or uncertain label matches. Numeric extraction, arithmetic, comparisons, totals, and severity decisions are always deterministic Python code.

## Testing Strategy

The real PDFs may contain no anomalies, so tests use synthetic extracted JSON and corrupted cases. The corrupted generator creates changed amounts, missing rows, wrong signs, swapped columns, renamed labels, wrong totals, and decimal comma/dot issues.

Run:

```powershell
pytest
```

## Limitations

PDF table extraction can be imperfect when source scans are low quality. OCR, Camelot, Ollama, and MinIO are optional and the MVP remains usable without them. Extraction confidence should be reviewed when yellow lines appear in the report.

## Roadmap

- Add accountant-approved ground truth fixtures.
- Improve table extraction with Camelot when available.
- Add OCR for scanned PDFs.
- Add review UI for correcting extracted rows.
- Persist historical audit decisions.

## Architecture Refactor

FinVerify is now centered on a canonical FinancialDocument domain model. Extraction creates this object, and validation, comparison, reporting, storage, and AI services consume it instead of raw dictionaries.

The CLI is only a client. Business workflow lives in PipelineOrchestrator, and reusable application services live in src/sicav_checker/services. This keeps the modular monolith simple today while allowing a future FastAPI, Streamlit, or desktop UI to reuse the same service layer.

See docs/ARCHITECTURE.md for the architectural decisions and extension points.
