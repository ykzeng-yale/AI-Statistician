import json
from pathlib import Path

from statlean_agent.contracts import (
    CuratedLemmaCandidate,
    CuratedLemmaLedgerEntry,
    LemmaProposal,
    ProofAttempt,
    VerificationReport,
    VerificationStatus,
)
from statlean_agent.benchmarks import SEED_BENCHMARKS
from statlean_agent.curation import (
    DEFAULT_REQUIRED_GATES,
    build_theorem_hole_lemma_ledger,
    build_theorem_hole_lemma_proposals,
    curate_candidate,
)
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
