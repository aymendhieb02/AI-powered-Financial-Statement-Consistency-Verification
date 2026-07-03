from __future__ import annotations

from uuid import uuid4

from sicav_checker.models import Evidence, FinancialDocument


class EvidenceTracker:
    def attach(self, document: FinancialDocument) -> FinancialDocument:
        for statement_name, statement in document.statements.items():
            for index, row in enumerate(statement.rows, start=1):
                if row.evidence is None:
                    value = row.current_value if row.current_value is not None else row.previous_value
                    row.evidence = Evidence(line_id=uuid4().hex, source_pdf=document.source_file, page=row.page, row_number=index, column="current/previous", extraction_method=document.extraction_method, raw_text=row.label, normalized_value=value, confidence=row.confidence)
        return document

    def collect(self, documents: list[FinancialDocument]) -> list[Evidence]:
        evidence: list[Evidence] = []
        for document in documents:
            for statement in document.statements.values():
                for row in statement.rows:
                    if row.evidence:
                        evidence.append(row.evidence)
        return evidence
