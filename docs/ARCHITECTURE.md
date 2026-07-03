# FinVerify Architecture

FinVerify is a modular monolith. It runs as one local Python application today, but its internal boundaries are shaped so a future FastAPI, Streamlit, or desktop client can reuse the same business services.

## Canonical Financial Model

The application no longer treats extracted tables as the system contract. Extraction is allowed to be messy, but everything after extraction consumes a canonical FinancialDocument object.

Pipeline contract: PDF -> Extraction -> FinancialDocument -> Validation -> Comparison -> Reporting.

The primary domain models live in sicav_checker.domain.models: FinancialDocument, DocumentMetadata, FinancialStatement, StatementSection, FinancialLine, ComparisonResult, ValidationResult, ComparisonReport, Anomaly, and RiskScore.

Legacy names such as ExtractedDocument, Statement, and StatementRow remain as aliases for compatibility, but new code should use the canonical names.

## Module Responsibilities

Extraction only extracts document content and builds canonical documents. Normalization only normalizes labels, numbers, and document content. Validation only runs deterministic accounting rules. Comparison only compares consecutive canonical documents. Reporting only generates output from ComparisonReport.

AI is optional and never performs calculations. It may explain anomalies or semantic matches; numerical decisions remain deterministic Python.

## Service Layer

Reusable application services live in sicav_checker.services: ExtractionService, NormalizationService, ValidationService, ComparisonService, ReportingService, StorageService, and AIService. Future clients should call these services instead of importing CLI commands.

## Orchestration

PipelineOrchestrator coordinates the workflow: load PDFs, extract, normalize, save canonical JSON, validate, compare, and generate reports. Business flow belongs in the orchestrator, not in the CLI.

## Dependency Boundaries

Storage is behind StorageAdapter, currently implemented by local and optional MinIO adapters. Reporting is behind ReportGenerator, currently implemented by ExcelGenerator and JsonGenerator. Future Azure Blob, S3, PDF, or dashboard adapters can be added without changing business logic.

## Error Handling

Expected application failures use custom exceptions: ExtractionError, NormalizationError, ValidationError, ComparisonError, StorageError, and ReportingError. This makes future API error mapping straightforward.

## Logging and Testability

Pipeline stages use log_stage, which logs start, finish, duration, context, and failures. Services can be unit tested independently, and the orchestrator accepts dependencies in its constructor for fake services or storage in tests.

## Enterprise Verification Modules

The next-generation FinVerify modules extend the canonical model rather than bypassing it. The rule engine, chart of accounts, evidence tracker, confidence engine, and verification history all exchange FinancialDocument, ComparisonResult, ValidationResult, and ComparisonReport objects.

### Configurable Rule Engine

Rules live under config/rules and are loaded at runtime by sicav_checker.rules. The engine separates loading, registration, execution, and result mapping so accountants can add deterministic accounting rules without changing Python code. Rule execution logs timing, status, severity, statement, and confidence for audit review.

### Canonical Chart of Accounts

The chart of accounts configuration maps observed accounting labels to canonical concepts. Normalization now stores original labels, canonical labels, matching confidence, and matching method on each financial line. Comparison uses canonical concepts instead of raw extracted labels, which makes renamed labels auditable rather than fragile.

### Evidence Tracking

Evidence objects are attached to financial lines during extraction and collected into ComparisonReport. Evidence captures source PDF, page, row, column, raw text, normalized value, extraction method, and confidence. Comparison results carry old and new evidence so a future UI can open the source location for an anomaly.

### Confidence Engine

ConfidenceEngine aggregates extraction, normalization, comparison, and rule confidence into an overall verification confidence. The value is exposed through reports, API endpoints, and the React confidence dashboard.

### Version History

Every report generation creates an immutable VerificationRun stored through repository interfaces. The JSON repository is the current implementation, but the business layer depends on repository contracts so SQLite or PostgreSQL can be introduced without rewriting services.

### Reporting and API Surface

ComparisonReport is now the reporting boundary. Excel and JSON reports include rule results, evidence traceability, confidence summary, verification history, and matching summary. FastAPI exposes enterprise endpoints for rules, validation, verification history, confidence, and evidence lookup. React adds pages for Rules, Verification History, Evidence, and Confidence.
