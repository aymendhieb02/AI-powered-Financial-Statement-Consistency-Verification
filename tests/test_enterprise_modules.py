from pathlib import Path

from sicav_checker.chart_of_accounts.canonical_mapper import CanonicalMapper
from sicav_checker.confidence.confidence_engine import ConfidenceEngine
from sicav_checker.evidence.evidence_tracker import EvidenceTracker
from sicav_checker.history.verification_history import VerificationHistoryService
from sicav_checker.repositories.json_repositories import JsonVerificationRepository
from sicav_checker.rules.rule_engine import RuleEngine
from sicav_checker.testsupport.corrupted_data_generator import base_documents, corrupted_documents
from sicav_checker.comparison.cross_year_comparator import compare_documents
from sicav_checker.models import Status


def test_rule_engine_loads_external_rules() -> None:
    engine = RuleEngine()
    rules = engine.list_rules()
    assert any(rule.id == "BS001" for rule in rules)


def test_rule_engine_executes_balance_sheet_rule() -> None:
    old, _ = base_documents()
    results = RuleEngine().execute(old)
    assert any(result.rule_id == "BS001" and result.status == Status.OK for result in results)


def test_canonical_mapper_uses_alias_dictionary() -> None:
    match = CanonicalMapper().map_label("Total des actifs")
    assert match.canonical_label == "total_actif"
    assert match.method == "alias_dictionary"


def test_evidence_tracker_attaches_traceability() -> None:
    old, _ = base_documents()
    tracked = EvidenceTracker().attach(old)
    row = tracked.statements["bilan"].rows[0]
    assert row.evidence is not None
    assert row.evidence.source_pdf == "2024.pdf"


def test_confidence_engine_aggregates_scores() -> None:
    old, new = base_documents()
    comparisons = compare_documents(old, new)
    confidence = ConfidenceEngine().aggregate([old, new], comparisons, [])
    assert 0 <= confidence.overall <= 1


def test_verification_history_tracks_changes(tmp_path: Path) -> None:
    repo = JsonVerificationRepository(tmp_path)
    service = VerificationHistoryService(repo)
    old, new = base_documents()
    first = service.create_run("project", [old, new], compare_documents(old, new), [], [])
    bad_old, bad_new = corrupted_documents("changed_amount")
    second = service.create_run("project", [bad_old, bad_new], compare_documents(bad_old, bad_new), [], [])
    assert first.run_id != second.run_id
    assert second.new_anomalies
    assert service.get_run(second.run_id) is not None
