"""Library curation gates for proposed statistical lemmas."""

from __future__ import annotations

from dataclasses import dataclass

from statlean_agent.contracts import (
    BenchmarkTask,
    CuratedLemmaCandidate,
    CuratedLemmaLedgerEntry,
    CurationDecision,
    LemmaNonVacuityReport,
    LemmaProofCostReport,
    LemmaProposal,
    LemmaProposalGateReport,
    VerificationReport,
    VerificationStatus,
)
from statlean_agent.retrieval import PremiseRecord
from statlean_agent.rewards import FORBIDDEN_TOKENS


@dataclass(frozen=True)
class CurationPolicy:
    min_reuse_count: int = 1
    min_generality_score: float = 0.0
    require_semantic_notes: bool = True


DEFAULT_REQUIRED_GATES = (
    "lean_compiles",
    "no_forbidden_tokens",
    "no_duplicate_statement",
    "minimal_imports",
    "non_vacuity_example",
    "downstream_reuse",
    "statistical_semantic_review",
)


def curate_candidate(
    candidate: CuratedLemmaCandidate,
    policy: CurationPolicy = CurationPolicy(),
) -> CurationDecision:
    """Apply static curation gates before a lemma can enter the local library."""

    reasons: list[str] = []
    required_changes: list[str] = []
    joined = f"{candidate.statement}\n{candidate.proof}".lower()

    for token in FORBIDDEN_TOKENS:
        if token in joined:
            reasons.append(f"forbidden token `{token}` appears in statement or proof")

    if candidate.reuse_count < policy.min_reuse_count:
        required_changes.append("show downstream reuse before promotion")

    if candidate.generality_score < policy.min_generality_score:
        required_changes.append("increase generality score or justify task-specific lemma")

    if policy.require_semantic_notes and not candidate.semantic_notes.strip():
        required_changes.append("add statistical semantic notes")

    if not candidate.motivation_tasks:
        required_changes.append("link at least one motivating theorem or benchmark task")

    accepted = not reasons and not required_changes
    return CurationDecision(
        accepted=accepted,
        reasons=tuple(reasons),
        required_changes=tuple(required_changes),
    )


def build_theorem_hole_lemma_ledger(
    tasks: tuple[BenchmarkTask, ...],
    reports: tuple[VerificationReport, ...],
) -> tuple[CuratedLemmaLedgerEntry, ...]:
    """Create seed curation records from theorem-hole benchmark tasks.

    These records are intentionally not promoted into StatInference. The
    theorem-hole source contains scoped `sorry` placeholders, so the curator
    must block each candidate until a future no-sorry proof replaces it.
    """

    reports_by_task = {report.task_id: report for report in reports}
    entries: list[CuratedLemmaLedgerEntry] = []
    for task in tasks:
        if "theorem_hole" not in task.domain_tags:
            continue

        candidate = _candidate_from_theorem_hole(task)
        decision = curate_candidate(candidate)
        entries.append(
            CuratedLemmaLedgerEntry(
                ledger_id=f"ledger::{task.task_id}",
                candidate=candidate,
                decision=decision,
                source_task_ids=(task.task_id,),
                verification_report_ids=(task.task_id,) if task.task_id in reports_by_task else (),
                status="blocked_placeholder" if not decision.accepted else "candidate_ready",
                notes=(
                    "Do not promote this candidate until the theorem-hole placeholder "
                    "is replaced by a verified no-sorry proof."
                ),
            )
        )
    return tuple(entries)


def build_theorem_hole_lemma_proposals(
    tasks: tuple[BenchmarkTask, ...],
    *,
    proposed_by: str = "theorem-hole-miner",
) -> tuple[LemmaProposal, ...]:
    """Create pre-curation proposal records from theorem-hole benchmark tasks."""

    proposals: list[LemmaProposal] = []
    for task in tasks:
        if "theorem_hole" not in task.domain_tags:
            continue
        candidate = _candidate_from_theorem_hole(task)
        proposals.append(
            LemmaProposal(
                proposal_id=f"proposal::{task.task_id}",
                source_kind="benchmark_theorem_hole",
                proposed_by=proposed_by,
                candidate=candidate,
                source_task_ids=(task.task_id,),
                domain_tags=task.domain_tags,
                expected_premises=task.expected_premises,
                required_gates=DEFAULT_REQUIRED_GATES,
                blocked_reasons=(
                    "source benchmark permits scoped placeholder proof",
                    "requires no-sorry proof before ledger promotion",
                ),
                status="needs_no_sorry_proof",
                notes=(
                    "Proposal is a mining record only. It must pass duplicate, "
                    "import-minimality, non-vacuity, downstream-use, and semantic "
                    "review gates before entering StatInference."
                ),
            )
        )
    return tuple(proposals)


def build_lemma_proposal_gate_reports(
    proposals: tuple[LemmaProposal, ...],
    premise_records: tuple[PremiseRecord, ...],
) -> tuple[LemmaProposalGateReport, ...]:
    """Check duplicate names/statements and import-minimality for proposals."""

    names_by_proposal = _proposal_names(proposals)
    statements_by_proposal = _proposal_statements(proposals)
    premise_names = _premise_name_index(premise_records)
    premises_by_name = _premise_records_by_name(premise_records)
    reports: list[LemmaProposalGateReport] = []

    for proposal in proposals:
        duplicate_name_matches = tuple(
            sorted(
                (
                    *names_by_proposal.get(proposal.candidate.name, ()),
                    *premise_names.get(proposal.candidate.name, ()),
                )
            )
        )
        statement_key = _normalized_statement(proposal.candidate.statement)
        duplicate_statement_matches = tuple(
            sorted(
                item
                for item in statements_by_proposal.get(statement_key, ())
                if item != proposal.proposal_id
            )
        )
        required_imports = _required_imports_for_expected_premises(
            proposal.expected_premises,
            premises_by_name,
        )
        imports_added = tuple(sorted(set(proposal.candidate.imports_added)))
        unused_imports = tuple(import_name for import_name in imports_added if import_name not in required_imports)
        missing_imports = tuple(import_name for import_name in required_imports if import_name not in imports_added)
        required_changes = _gate_required_changes(
            duplicate_name_matches=duplicate_name_matches,
            duplicate_statement_matches=duplicate_statement_matches,
            unused_imports=unused_imports,
            missing_imports=missing_imports,
        )
        passed = not required_changes
        reports.append(
            LemmaProposalGateReport(
                proposal_id=proposal.proposal_id,
                candidate_name=proposal.candidate.name,
                duplicate_name_matches=duplicate_name_matches,
                duplicate_statement_matches=duplicate_statement_matches,
                imports_added=imports_added,
                required_imports=required_imports,
                unused_imports=unused_imports,
                missing_imports=missing_imports,
                passed=passed,
                status="passed" if passed else "blocked_static_gate",
                required_changes=required_changes,
                notes=(
                    "Static P7.M2 gate: duplicate names/statements and "
                    "proposal import set are checked before curation promotion."
                ),
            )
        )
    return tuple(reports)


def build_lemma_non_vacuity_reports(
    proposals: tuple[LemmaProposal, ...],
    tasks: tuple[BenchmarkTask, ...],
    reports: tuple[VerificationReport, ...],
) -> tuple[LemmaNonVacuityReport, ...]:
    """Require accepted non-vacuity benchmark evidence for each proposal."""

    reports_by_task = {report.task_id: report for report in reports}
    evidence_by_proposal = _non_vacuity_evidence_by_proposal(proposals, tasks)
    gate_reports: list[LemmaNonVacuityReport] = []

    for proposal in proposals:
        evidence_tasks = evidence_by_proposal.get(proposal.proposal_id, ())
        accepted = tuple(
            task.task_id
            for task in evidence_tasks
            if reports_by_task.get(task.task_id, VerificationReport(task.task_id, VerificationStatus.ERROR)).status
            is VerificationStatus.ACCEPTED
        )
        missing = tuple(
            task.task_id
            for task in evidence_tasks
            if task.task_id not in accepted
        )
        required_changes = _non_vacuity_required_changes(
            evidence_task_ids=tuple(task.task_id for task in evidence_tasks),
            accepted_evidence_task_ids=accepted,
            missing_evidence_task_ids=missing,
        )
        passed = not required_changes
        gate_reports.append(
            LemmaNonVacuityReport(
                proposal_id=proposal.proposal_id,
                candidate_name=proposal.candidate.name,
                proposal_domain_tags=proposal.domain_tags,
                evidence_task_ids=tuple(task.task_id for task in evidence_tasks),
                evidence_domain_tags=_evidence_domain_tags(evidence_tasks),
                accepted_evidence_task_ids=accepted,
                missing_evidence_task_ids=missing,
                passed=passed,
                status="passed" if passed else "blocked_non_vacuity",
                required_changes=required_changes,
                notes=(
                    "P7.M3 gate: a proposal must be backed by at least one "
                    "accepted benchmark tagged non_vacuity that shares a "
                    "domain-specific tag with the proposal."
                ),
            )
        )
    return tuple(gate_reports)


def build_lemma_proof_cost_reports(
    proposals: tuple[LemmaProposal, ...],
    tasks: tuple[BenchmarkTask, ...],
) -> tuple[LemmaProofCostReport, ...]:
    """Estimate whether a proposal reduces downstream proof construction cost.

    The current curation gate is intentionally conservative: a proposal must
    replace a multi-premise proof bundle in at least one downstream benchmark
    with a projected one-step lemma application. This is a deterministic proxy
    until mined no-sorry proofs are available for direct search-cost replay.
    """

    reports: list[LemmaProofCostReport] = []
    for proposal in proposals:
        downstream_task_ids = _downstream_task_ids_for_proposal(proposal, tasks)
        expected_premises = tuple(dict.fromkeys(proposal.expected_premises))
        baseline_step_count = len(expected_premises)
        projected_step_count = 1 if downstream_task_ids else 0
        proof_cost_delta = baseline_step_count - projected_step_count if downstream_task_ids else 0
        relative_cost_reduction = (
            proof_cost_delta / baseline_step_count
            if baseline_step_count > 0 and proof_cost_delta > 0
            else 0.0
        )
        required_changes = _proof_cost_required_changes(
            downstream_task_ids=downstream_task_ids,
            baseline_step_count=baseline_step_count,
            proof_cost_delta=proof_cost_delta,
        )
        passed = not required_changes
        reports.append(
            LemmaProofCostReport(
                proposal_id=proposal.proposal_id,
                candidate_name=proposal.candidate.name,
                source_task_ids=proposal.source_task_ids,
                downstream_task_ids=downstream_task_ids,
                expected_premises=expected_premises,
                baseline_step_count=baseline_step_count,
                projected_step_count=projected_step_count,
                proof_cost_delta=proof_cost_delta,
                relative_cost_reduction=relative_cost_reduction,
                passed=passed,
                status="passed" if passed else "blocked_downstream_cost",
                required_changes=required_changes,
                notes=(
                    "P7.M4 gate: a candidate must replace a multi-premise "
                    "downstream proof bundle with a projected one-step lemma "
                    "application before promotion."
                ),
            )
        )
    return tuple(reports)


def _candidate_name(task: BenchmarkTask) -> str:
    if task.task_id == "ipw_linearization_theorem_hole_seed":
        return "ipw_hajek_linearization_constructor"
    if task.task_id == "aipw_product_rate_theorem_hole_seed":
        return "aipw_product_rate_route_constructor"
    if task.task_id == "if_normality_theorem_hole_seed":
        return "influence_function_normality_route_constructor"
    return f"{task.task_id}_candidate"


def _candidate_from_theorem_hole(task: BenchmarkTask) -> CuratedLemmaCandidate:
    return CuratedLemmaCandidate(
        name=_candidate_name(task),
        statement=task.lean_task.statement,
        proof="pending no-placeholder proof extracted from theorem-hole benchmark",
        motivation_tasks=(task.task_id,),
        imports_added=task.lean_task.imports,
        reuse_count=max(1, len(task.expected_premises)),
        generality_score=0.5,
        semantic_notes=(
            "Theorem-hole-derived reusable lemma candidate. Expected premises: "
            + ", ".join(task.expected_premises)
        ),
    )


def _proposal_names(proposals: tuple[LemmaProposal, ...]) -> dict[str, tuple[str, ...]]:
    names: dict[str, list[str]] = {}
    for proposal in proposals:
        names.setdefault(proposal.candidate.name, []).append(proposal.proposal_id)
    return {
        name: tuple(proposal_ids)
        for name, proposal_ids in names.items()
        if len(proposal_ids) > 1
    }


def _proposal_statements(proposals: tuple[LemmaProposal, ...]) -> dict[str, tuple[str, ...]]:
    statements: dict[str, list[str]] = {}
    for proposal in proposals:
        statements.setdefault(_normalized_statement(proposal.candidate.statement), []).append(proposal.proposal_id)
    return {
        statement: tuple(proposal_ids)
        for statement, proposal_ids in statements.items()
        if len(proposal_ids) > 1
    }


def _premise_name_index(records: tuple[PremiseRecord, ...]) -> dict[str, tuple[str, ...]]:
    index: dict[str, list[str]] = {}
    for record in records:
        candidates = {
            record.name,
            record.full_name,
            _unqualified_name(record.name),
            _unqualified_name(record.full_name),
        }
        for candidate in candidates:
            if candidate:
                index.setdefault(candidate, []).append(record.full_name or record.name)
    return {name: tuple(sorted(set(matches))) for name, matches in index.items()}


def _premise_records_by_name(records: tuple[PremiseRecord, ...]) -> dict[str, tuple[PremiseRecord, ...]]:
    index: dict[str, list[PremiseRecord]] = {}
    for record in records:
        candidates = {
            record.name,
            record.full_name,
            f"StatInference.{record.name}",
            _unqualified_name(record.name),
            _unqualified_name(record.full_name),
        }
        for candidate in candidates:
            if candidate:
                index.setdefault(candidate, []).append(record)
    return {name: tuple(matches) for name, matches in index.items()}


def _required_imports_for_expected_premises(
    expected_premises: tuple[str, ...],
    premise_records_by_name: dict[str, tuple[PremiseRecord, ...]],
) -> tuple[str, ...]:
    required: set[str] = set()
    for premise in expected_premises:
        records = premise_records_by_name.get(premise, ())
        if records:
            required.update(record.module for record in records)
    return tuple(sorted(required))


def _gate_required_changes(
    *,
    duplicate_name_matches: tuple[str, ...],
    duplicate_statement_matches: tuple[str, ...],
    unused_imports: tuple[str, ...],
    missing_imports: tuple[str, ...],
) -> tuple[str, ...]:
    changes: list[str] = []
    if duplicate_name_matches:
        changes.append("rename candidate or justify duplicate declaration name")
    if duplicate_statement_matches:
        changes.append("deduplicate equivalent lemma proposal statement")
    if unused_imports:
        changes.append("remove imports not needed by expected premises")
    if missing_imports:
        changes.append("add imports required by expected premises")
    return tuple(changes)


def _non_vacuity_evidence_by_proposal(
    proposals: tuple[LemmaProposal, ...],
    tasks: tuple[BenchmarkTask, ...],
) -> dict[str, tuple[BenchmarkTask, ...]]:
    evidence_tasks = tuple(task for task in tasks if "non_vacuity" in task.domain_tags)
    by_proposal: dict[str, tuple[BenchmarkTask, ...]] = {}
    for proposal in proposals:
        proposal_tags = _domain_specific_tags(proposal.domain_tags)
        matched = tuple(
            task
            for task in evidence_tasks
            if proposal_tags & _domain_specific_tags(task.domain_tags)
        )
        by_proposal[proposal.proposal_id] = matched
    return by_proposal


def _non_vacuity_required_changes(
    *,
    evidence_task_ids: tuple[str, ...],
    accepted_evidence_task_ids: tuple[str, ...],
    missing_evidence_task_ids: tuple[str, ...],
) -> tuple[str, ...]:
    changes: list[str] = []
    if not evidence_task_ids:
        changes.append("add a benchmark tagged non_vacuity that shares a domain tag with this proposal")
    if evidence_task_ids and not accepted_evidence_task_ids:
        changes.append("verify at least one matching non-vacuity benchmark task")
    if missing_evidence_task_ids:
        changes.append("repair or remove rejected non-vacuity evidence tasks")
    return tuple(changes)


def _evidence_domain_tags(tasks: tuple[BenchmarkTask, ...]) -> tuple[str, ...]:
    return tuple(sorted({tag for task in tasks for tag in task.domain_tags}))


def _downstream_task_ids_for_proposal(
    proposal: LemmaProposal,
    tasks: tuple[BenchmarkTask, ...],
) -> tuple[str, ...]:
    expected = set(proposal.expected_premises)
    source_ids = set(proposal.source_task_ids)
    downstream: list[str] = []
    for task in tasks:
        task_premises = set(task.expected_premises)
        if task.task_id in source_ids or (expected and expected.issubset(task_premises)):
            downstream.append(task.task_id)
    return tuple(dict.fromkeys(downstream))


def _proof_cost_required_changes(
    *,
    downstream_task_ids: tuple[str, ...],
    baseline_step_count: int,
    proof_cost_delta: int,
) -> tuple[str, ...]:
    changes: list[str] = []
    if not downstream_task_ids:
        changes.append("link at least one downstream benchmark task that can use this proposal")
    if baseline_step_count <= 1:
        changes.append("show a multi-premise proof bundle that the proposal replaces")
    if proof_cost_delta <= 0:
        changes.append("demonstrate positive projected proof-cost reduction")
    return tuple(changes)


def _domain_specific_tags(tags: tuple[str, ...]) -> set[str]:
    generic = {
        "multi_goal",
        "non_vacuity",
        "theorem_hole",
        "verified_by_lean",
    }
    return {tag for tag in tags if tag not in generic}


def _normalized_statement(statement: str) -> str:
    return " ".join(statement.split())


def _unqualified_name(name: str) -> str:
    return name.rsplit(".", maxsplit=1)[-1]
