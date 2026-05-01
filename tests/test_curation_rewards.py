import json
from pathlib import Path

from statlean_agent.contracts import (
    CuratedLemmaCandidate,
    CuratedLemmaLedgerEntry,
    LemmaNonVacuityReport,
    LemmaProposal,
    LemmaProposalGateReport,
    ProofAttempt,
    VerificationReport,
    VerificationStatus,
)
from statlean_agent.benchmarks import SEED_BENCHMARKS
from statlean_agent.curation import (
    DEFAULT_REQUIRED_GATES,
    build_lemma_non_vacuity_reports,
    build_lemma_proposal_gate_reports,
    build_theorem_hole_lemma_ledger,
    build_theorem_hole_lemma_proposals,
    curate_candidate,
)
from statlean_agent.retrieval import PremiseRecord, build_premise_index
from statlean_agent.rewards import aggregate_reward_breakdowns, find_forbidden_tokens, score_attempt
from statlean_agent.serialization import dataclass_from_dict, read_jsonl


def test_curator_rejects_sorry() -> None:
    candidate = CuratedLemmaCandidate(
        name="bad",
        statement="theorem bad : True := by",
        proof="sorry",
        motivation_tasks=("task",),
        reuse_count=1,
        semantic_notes="bad example",
    )
    decision = curate_candidate(candidate)
    assert not decision.accepted
    assert any("sorry" in reason for reason in decision.reasons)


def test_reward_penalizes_forbidden_tokens() -> None:
    attempt = ProofAttempt(
        task_id="task",
        agent_key="whole_proof_generator",
        lean_code="theorem bad : True := by\n  sorry\n  sorry",
        verifier_status=VerificationStatus.REJECTED,
    )
    report = VerificationReport(task_id="task", status=VerificationStatus.REJECTED)
    reward = score_attempt(attempt, report)
    assert reward.total < 0
    assert reward.components["forbidden_sorry"] == -20.0


def test_reward_accepts_verified_progress() -> None:
    attempt = ProofAttempt(
        task_id="task",
        agent_key="tactic_synthesizer",
        lean_code="theorem ok : True := by trivial",
        premises_used=("True.intro",),
        verifier_status=VerificationStatus.ACCEPTED,
    )
    report = VerificationReport(
        task_id="task",
        status=VerificationStatus.ACCEPTED,
        locally_valid_steps=1,
        closed_goals=1,
    )
    reward = score_attempt(attempt, report)
    assert reward.total > 10


def test_reward_allows_configured_placeholder_without_policy_penalty() -> None:
    attempt = ProofAttempt(
        task_id="draft",
        agent_key="formalizer",
        lean_code="theorem draft : True := by\n  sorry",
        verifier_status=VerificationStatus.ACCEPTED,
    )
    report = VerificationReport(task_id="draft", status=VerificationStatus.ACCEPTED)
    reward = score_attempt(attempt, report, allowed_placeholders=("sorry",))
    assert reward.total == 10.0
    assert "forbidden_sorry" not in reward.components


def test_reward_does_not_allow_admit_placeholder() -> None:
    attempt = ProofAttempt(
        task_id="draft",
        agent_key="formalizer",
        lean_code="theorem draft : True := by\n  admit",
        verifier_status=VerificationStatus.ACCEPTED,
    )
    report = VerificationReport(task_id="draft", status=VerificationStatus.ACCEPTED)
    reward = score_attempt(attempt, report, allowed_placeholders=("admit",))
    assert reward.components["forbidden_admit"] == -10.0


def test_reward_keeps_timeout_penalty_with_policy_violation() -> None:
    attempt = ProofAttempt(
        task_id="timeout",
        agent_key="formalizer",
        lean_code="theorem timeout : True := by\n  sorry",
        verifier_status=VerificationStatus.TIMEOUT,
    )
    report = VerificationReport(task_id="timeout", status=VerificationStatus.TIMEOUT)
    reward = score_attempt(attempt, report)
    assert reward.components["timeout"] == -2.0
    assert reward.components["forbidden_sorry"] == -10.0


def test_policy_scan_ignores_comments_and_strings() -> None:
    source = 'theorem ok : True := by\n  -- sorry in a comment\n  have h := "admit in a string"\n  trivial'
    assert find_forbidden_tokens(source) == ()


def test_aggregate_reward_breakdowns_sums_components() -> None:
    accepted = score_attempt(
        ProofAttempt("ok", "agent", "theorem ok : True := by trivial"),
        VerificationReport("ok", VerificationStatus.ACCEPTED),
    )
    rejected = score_attempt(
        ProofAttempt("bad", "agent", "theorem bad : True := by sorry"),
        VerificationReport("bad", VerificationStatus.REJECTED),
    )

    aggregate = aggregate_reward_breakdowns((accepted, rejected))

    assert aggregate.total == accepted.total + rejected.total
    assert aggregate.components["proof_complete"] == 10.0
    assert aggregate.components["forbidden_sorry"] == -10.0


def test_theorem_hole_lemma_ledger_blocks_placeholder_candidates() -> None:
    theorem_hole_tasks = tuple(task for task in SEED_BENCHMARKS if "theorem_hole" in task.domain_tags)
    reports = tuple(VerificationReport(task.task_id, VerificationStatus.ACCEPTED) for task in theorem_hole_tasks)

    entries = build_theorem_hole_lemma_ledger(theorem_hole_tasks, reports)

    assert len(entries) == 3
    assert {entry.status for entry in entries} == {"blocked_placeholder"}
    assert all(not entry.decision.accepted for entry in entries)
    assert all(any("sorry" in reason for reason in entry.decision.reasons) for entry in entries)
    assert {entry.candidate.name for entry in entries} == {
        "ipw_hajek_linearization_constructor",
        "aipw_product_rate_route_constructor",
        "influence_function_normality_route_constructor",
    }


def test_theorem_hole_lemma_proposals_record_required_gates() -> None:
    theorem_hole_tasks = tuple(task for task in SEED_BENCHMARKS if "theorem_hole" in task.domain_tags)

    proposals = build_theorem_hole_lemma_proposals(theorem_hole_tasks)

    assert len(proposals) == 3
    assert {proposal.status for proposal in proposals} == {"needs_no_sorry_proof"}
    assert all(proposal.required_gates == DEFAULT_REQUIRED_GATES for proposal in proposals)
    assert all(proposal.blocked_reasons for proposal in proposals)
    assert all(proposal.source_kind == "benchmark_theorem_hole" for proposal in proposals)
    assert all(proposal.candidate.motivation_tasks == proposal.source_task_ids for proposal in proposals)
    assert {proposal.candidate.name for proposal in proposals} == {
        "ipw_hajek_linearization_constructor",
        "aipw_product_rate_route_constructor",
        "influence_function_normality_route_constructor",
    }


def test_lemma_proposal_gate_reports_detect_duplicate_name_and_imports() -> None:
    proposal = LemmaProposal(
        proposal_id="proposal::dup",
        source_kind="unit",
        proposed_by="test",
        candidate=CuratedLemmaCandidate(
            name="existingLemma",
            statement="example : True := by trivial",
            proof="by trivial",
            motivation_tasks=("task",),
            imports_added=("StatInference.Unused",),
            semantic_notes="unit test",
        ),
        source_task_ids=("task",),
        expected_premises=("StatInference.existingPremise",),
    )
    duplicate_statement = LemmaProposal(
        proposal_id="proposal::same_statement",
        source_kind="unit",
        proposed_by="test",
        candidate=CuratedLemmaCandidate(
            name="freshLemma",
            statement="example   :   True := by\n  trivial",
            proof="by trivial",
            motivation_tasks=("task",),
            imports_added=("StatInference.Required",),
            semantic_notes="unit test",
        ),
        source_task_ids=("task",),
        expected_premises=("StatInference.existingPremise",),
    )
    premises = (
        PremiseRecord(
            name="existingLemma",
            kind="theorem",
            module="StatInference.Required",
            file="StatInference/Required.lean",
            line=1,
            full_name="StatInference.existingLemma",
        ),
        PremiseRecord(
            name="existingPremise",
            kind="theorem",
            module="StatInference.Required",
            file="StatInference/Required.lean",
            line=2,
            full_name="StatInference.existingPremise",
        ),
    )

    reports = build_lemma_proposal_gate_reports((proposal, duplicate_statement), premises)
    by_id = {report.proposal_id: report for report in reports}

    assert by_id["proposal::dup"].status == "blocked_static_gate"
    assert by_id["proposal::dup"].duplicate_name_matches == ("StatInference.existingLemma",)
    assert by_id["proposal::dup"].missing_imports == ("StatInference.Required",)
    assert by_id["proposal::dup"].unused_imports == ("StatInference.Unused",)
    assert "rename candidate or justify duplicate declaration name" in by_id["proposal::dup"].required_changes
    assert by_id["proposal::same_statement"].duplicate_statement_matches == ("proposal::dup",)


def test_current_lemma_proposal_gate_reports_pass_static_checks() -> None:
    proposals = build_theorem_hole_lemma_proposals(SEED_BENCHMARKS)
    premises = build_premise_index(Path("."), source_dir="StatInference")

    reports = build_lemma_proposal_gate_reports(proposals, premises)

    assert len(reports) == 3
    assert all(report.passed for report in reports)
    assert {report.status for report in reports} == {"passed"}
    assert all(not report.duplicate_name_matches for report in reports)
    assert all(not report.duplicate_statement_matches for report in reports)
    assert all(not report.unused_imports for report in reports)
    assert all(not report.missing_imports for report in reports)
    assert {
        "StatInference.Causal.IPW",
        "StatInference.Causal.AIPW",
        "StatInference.Semiparametric.Normality",
    } == {report.required_imports[0] for report in reports}


def test_lemma_non_vacuity_reports_require_accepted_evidence() -> None:
    proposals = build_theorem_hole_lemma_proposals(SEED_BENCHMARKS)
    accepted_reports = tuple(
        VerificationReport(task.task_id, VerificationStatus.ACCEPTED)
        for task in SEED_BENCHMARKS
    )

    reports = build_lemma_non_vacuity_reports(proposals, SEED_BENCHMARKS, accepted_reports)

    assert len(reports) == 3
    assert all(report.passed for report in reports)
    assert {report.status for report in reports} == {"passed"}
    by_id = {report.proposal_id: report for report in reports}
    assert "constant_ipw_hajek_route_seed" in by_id["proposal::ipw_linearization_theorem_hole_seed"].evidence_task_ids
    assert "trivial_aipw_product_rate_route_seed" in by_id["proposal::aipw_product_rate_theorem_hole_seed"].evidence_task_ids
    assert (
        "trivial_influence_function_normality_seed"
        in by_id["proposal::if_normality_theorem_hole_seed"].evidence_task_ids
    )
    assert all("non_vacuity" in report.evidence_domain_tags for report in reports)


def test_lemma_non_vacuity_reports_block_missing_or_rejected_evidence() -> None:
    proposal = LemmaProposal(
        proposal_id="proposal::missing",
        source_kind="unit",
        proposed_by="test",
        candidate=CuratedLemmaCandidate(
            name="missing",
            statement="example : True := by trivial",
            proof="by trivial",
            motivation_tasks=("task",),
            semantic_notes="unit test",
        ),
        source_task_ids=("task",),
        domain_tags=("new_domain",),
    )
    rejected = LemmaProposal(
        proposal_id="proposal::rejected",
        source_kind="unit",
        proposed_by="test",
        candidate=CuratedLemmaCandidate(
            name="rejected",
            statement="example : True := by trivial",
            proof="by trivial",
            motivation_tasks=("task",),
            semantic_notes="unit test",
        ),
        source_task_ids=("task",),
        domain_tags=("ipw",),
    )
    rejected_reports = tuple(
        VerificationReport(task.task_id, VerificationStatus.REJECTED)
        for task in SEED_BENCHMARKS
        if "non_vacuity" in task.domain_tags
    )

    reports = build_lemma_non_vacuity_reports((proposal, rejected), SEED_BENCHMARKS, rejected_reports)
    by_id = {report.proposal_id: report for report in reports}

    assert by_id["proposal::missing"].status == "blocked_non_vacuity"
    assert by_id["proposal::missing"].required_changes == (
        "add a benchmark tagged non_vacuity that shares a domain tag with this proposal",
    )
    assert by_id["proposal::rejected"].status == "blocked_non_vacuity"
    assert "verify at least one matching non-vacuity benchmark task" in by_id["proposal::rejected"].required_changes
    assert by_id["proposal::rejected"].missing_evidence_task_ids


def test_checked_in_theorem_hole_ledger_is_curator_blocked() -> None:
    records = read_jsonl(Path("artifacts/curation/theorem-hole-ledger.jsonl"))
    entries = tuple(dataclass_from_dict(CuratedLemmaLedgerEntry, record) for record in records)

    assert len(entries) == 3
    assert {entry.status for entry in entries} == {"blocked_placeholder"}
    assert all(not entry.decision.accepted for entry in entries)
    assert all(entry.verification_report_ids == entry.source_task_ids for entry in entries)


def test_checked_in_lemma_proposals_are_precuration_records() -> None:
    records = read_jsonl(Path("artifacts/curation/lemma-proposals.jsonl"))
    proposals = tuple(dataclass_from_dict(LemmaProposal, record) for record in records)
    schema = json.loads(Path("schemas/lemma_proposal.schema.json").read_text(encoding="utf-8"))

    assert len(proposals) == 3
    assert {proposal.status for proposal in proposals} == {"needs_no_sorry_proof"}
    assert all(proposal.required_gates == DEFAULT_REQUIRED_GATES for proposal in proposals)
    assert all(proposal.blocked_reasons for proposal in proposals)
    assert all(proposal.candidate.semantic_notes for proposal in proposals)
    assert schema["title"] == "LemmaProposal"
    assert all(set(record) <= set(schema["properties"]) for record in records)


def test_checked_in_lemma_proposal_gate_reports_pass() -> None:
    records = read_jsonl(Path("artifacts/curation/lemma-proposal-gates.jsonl"))
    reports = tuple(dataclass_from_dict(LemmaProposalGateReport, record) for record in records)
    schema = json.loads(Path("schemas/lemma_proposal_gate_report.schema.json").read_text(encoding="utf-8"))

    assert len(reports) == 3
    assert all(report.passed for report in reports)
    assert {report.status for report in reports} == {"passed"}
    assert all(not report.required_changes for report in reports)
    assert all(not report.duplicate_name_matches for report in reports)
    assert all(not report.duplicate_statement_matches for report in reports)
    assert all(not report.unused_imports for report in reports)
    assert all(not report.missing_imports for report in reports)
    assert schema["title"] == "LemmaProposalGateReport"
    assert all(set(record) <= set(schema["properties"]) for record in records)


def test_checked_in_lemma_non_vacuity_reports_pass() -> None:
    records = read_jsonl(Path("artifacts/curation/lemma-non-vacuity.jsonl"))
    reports = tuple(dataclass_from_dict(LemmaNonVacuityReport, record) for record in records)
    schema = json.loads(Path("schemas/lemma_non_vacuity_report.schema.json").read_text(encoding="utf-8"))

    assert len(reports) == 3
    assert all(report.passed for report in reports)
    assert {report.status for report in reports} == {"passed"}
    assert all(report.evidence_task_ids for report in reports)
    assert all(report.accepted_evidence_task_ids for report in reports)
    assert all(not report.required_changes for report in reports)
    assert all(not report.missing_evidence_task_ids for report in reports)
    assert schema["title"] == "LemmaNonVacuityReport"
    assert all(set(record) <= set(schema["properties"]) for record in records)
