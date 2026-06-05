from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


STAT_CLAIM_CERTIFICATE_PLAN_SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = "STAT_CLAIM_CERTIFICATE_PLAN_NOT_PROOF_EVIDENCE"


@dataclass(frozen=True)
class StatClaimCertificateTarget:
    schema_version: int
    target_id: str
    source_claim_id: str
    question_id: str
    problem_class: str
    claim_status: str
    certificate_family: str
    checker_name: str
    priority: str
    statement: str
    witness_schema: tuple[str, ...]
    checker_contract: str
    checker_theorem_shape: str
    generator_contract: str
    required_gate: str
    proof_evidence_status: str
    evidence_boundary: str
    evidence_paths: tuple[str, ...]
    ok: bool
    errors: tuple[str, ...] = ()


CERTIFICATE_BLUEPRINTS: tuple[dict[str, object], ...] = (
    {
        "family": "conformal_coverage_certificate",
        "checker": "ConformalCoverageCertificateChecker",
        "keywords": (
            "conformal",
            "exchangeability",
            "prediction interval",
            "coverage",
            "rank",
            "quantile",
        ),
        "witness_schema": (
            "exchangeable_score_indices",
            "calibration_score_multiset",
            "rank_threshold",
            "coverage_level_alpha",
            "rank_count_certificate",
        ),
        "checker_contract": (
            "check exchangeability/rank-count witness and threshold arithmetic for split "
            "conformal marginal coverage"
        ),
        "checker_theorem_shape": (
            "checker cert = true -> finite-sample marginal coverage of the encoded "
            "split-conformal prediction set"
        ),
    },
    {
        "family": "randomization_variance_certificate",
        "checker": "RandomizationVarianceCertificateChecker",
        "keywords": (
            "randomization",
            "design-based",
            "variance",
            "neyman",
            "conservative variance",
            "difference-in-means",
        ),
        "witness_schema": (
            "finite_population_size",
            "treatment_count",
            "assignment_probability_table",
            "balance_constraints",
            "variance_bound_terms",
            "nonnegative_slack_certificate",
        ),
        "checker_contract": (
            "check assignment probabilities, balance identities, and nonnegative slack "
            "for a conservative design-based variance bound"
        ),
        "checker_theorem_shape": (
            "checker cert = true -> encoded variance estimator upper-bounds the "
            "randomization variance claim"
        ),
    },
    {
        "family": "privacy_accountant_certificate",
        "checker": "PrivacyAccountantCertificateChecker",
        "keywords": (
            "privacy",
            "differential privacy",
            "privacy accountant",
            "composition",
            "privacy-loss",
        ),
        "witness_schema": (
            "mechanism_ledger",
            "epsilon_delta_entries",
            "composition_rule_ids",
            "advanced_composition_terms",
            "budget_bound_certificate",
        ),
        "checker_contract": (
            "check that a mechanism ledger and composition certificate imply the "
            "advertised privacy budget"
        ),
        "checker_theorem_shape": (
            "checker cert = true -> encoded composed mechanism satisfies the stated "
            "epsilon-delta privacy bound"
        ),
    },
    {
        "family": "kkt_optimality_certificate",
        "checker": "KktOptimalityCertificateChecker",
        "keywords": (
            "kkt",
            "convex",
            "dual",
            "optimization",
            "lasso",
            "estimator optimality",
        ),
        "witness_schema": (
            "primal_candidate",
            "dual_candidate",
            "convexity_certificate",
            "stationarity_residuals",
            "complementary_slackness_terms",
            "dual_bound_certificate",
        ),
        "checker_contract": (
            "check convexity, stationarity, feasibility, complementary slackness, and "
            "dual-bound arithmetic for estimator optimality"
        ),
        "checker_theorem_shape": (
            "checker cert = true -> encoded estimator candidate is optimal or within "
            "the certified objective gap"
        ),
    },
    {
        "family": "multiple_testing_threshold_certificate",
        "checker": "MultipleTestingThresholdCertificateChecker",
        "keywords": (
            "multiple testing",
            "fdr",
            "false discovery",
            "benjamini",
            "hochberg",
            "bh",
            "threshold",
        ),
        "witness_schema": (
            "p_value_validity_rows",
            "sorted_p_values",
            "threshold_index",
            "monotone_stepup_certificate",
            "fdr_bound_terms",
        ),
        "checker_contract": (
            "check p-value validity assumptions, sorted threshold arithmetic, and "
            "step-up monotonicity for FDR/FWER control claims"
        ),
        "checker_theorem_shape": (
            "checker cert = true -> encoded threshold rule satisfies the advertised "
            "multiple-testing error bound"
        ),
    },
    {
        "family": "empirical_process_bound_certificate",
        "checker": "EmpiricalProcessBoundCertificateChecker",
        "keywords": (
            "empirical process",
            "entropy",
            "bracketing",
            "covering number",
            "symmetrization",
            "rademacher",
            "weak convergence",
        ),
        "witness_schema": (
            "function_class_id",
            "envelope_bound",
            "entropy_integral_bound",
            "symmetrization_step",
            "tail_bound_parameters",
        ),
        "checker_contract": (
            "check reusable entropy/bracketing/symmetrization witness data for an "
            "encoded empirical-process bound"
        ),
        "checker_theorem_shape": (
            "checker cert = true -> encoded empirical-process deviation or tightness "
            "bound follows from registered assumptions"
        ),
    },
)


def export_stat_claim_certificate_plan(
    claim_ledger_dir: Path,
    out_dir: Path | None = None,
    *,
    max_targets: int = 40,
) -> dict[str, object]:
    """Export Axon-style statistical certificate-checker planning targets.

    The emitted rows are not proof evidence. They identify claims where an
    untrusted generator could emit a compact witness and a small Lean checker
    could eventually validate a reusable statistical claim.
    """

    errors: list[str] = []
    manifest_path = claim_ledger_dir / "claim_ledger_manifest.json"
    rows_path = claim_ledger_dir / "claim_ledger.jsonl"
    manifest = _read_json(manifest_path, errors)
    ledger_rows = _read_jsonl(rows_path, errors)
    targets = tuple(_targets_from_ledger_rows(ledger_rows, max_targets=max_targets))
    by_family = Counter(target.certificate_family for target in targets)
    by_priority = Counter(target.priority for target in targets)
    payload: dict[str, object] = {
        "schema_version": STAT_CLAIM_CERTIFICATE_PLAN_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "claim_ledger_dir": str(claim_ledger_dir),
        "claim_ledger_manifest": str(manifest_path),
        "claim_ledger_jsonl": str(rows_path),
        "ledger_claims": manifest.get("n_claims", len(ledger_rows)),
        "ledger_all_ok": manifest.get("all_ok", False),
        "n_targets": len(targets),
        "n_ok": sum(1 for target in targets if target.ok),
        "n_checker_families": len(by_family),
        "n_proof_evidence_ready": 0,
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "all_ok": not errors and bool(manifest.get("all_ok", True)) and bool(targets) and all(
            target.ok for target in targets
        ),
        "errors": errors,
        "by_family": dict(sorted(by_family.items())),
        "by_priority": dict(sorted(by_priority.items())),
        "targets": [asdict(target) for target in targets],
        "target_fingerprint": stable_hash([asdict(target) for target in targets]),
        "limitations": [
            "Certificate plans are checker design and worker-routing artifacts, not Lean proof evidence.",
            "A certificate proves only the encoded claim after a Lean/AXLE checker theorem is kernel verified.",
            "Paper semantic faithfulness still requires source-span extraction and round-trip review.",
            "Untrusted witness generation may speed proof search but cannot replace local kernel verification.",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "stat_claim_certificate_plan_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "stat_claim_certificate_targets.jsonl").write_text(
            "\n".join(json.dumps(asdict(target), sort_keys=True) for target in targets)
            + ("\n" if targets else ""),
            encoding="utf-8",
        )
        (out_dir / "stat_claim_certificate_plan.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _targets_from_ledger_rows(
    rows: list[dict[str, Any]],
    *,
    max_targets: int,
) -> list[StatClaimCertificateTarget]:
    targets: list[StatClaimCertificateTarget] = []
    seen: set[tuple[str, str]] = set()
    candidate_statuses = {
        "THEOREM_GOAL_CONJECTURED",
        "FORMAL_GAP",
        "PROOF_FAILED",
        "SIMULATION_SUPPORTED",
        "SIMULATION_FLAGGED",
        "REVISION_QUEUED",
    }
    for row in rows:
        if len(targets) >= max_targets:
            break
        if not isinstance(row, dict):
            continue
        if str(row.get("status", "")) not in candidate_statuses:
            continue
        blueprint, score = _best_blueprint(row)
        if blueprint is None:
            continue
        key = (str(row.get("claim_id", "")), str(blueprint["family"]))
        if key in seen:
            continue
        seen.add(key)
        targets.append(_target_from_ledger_row(row, blueprint, score))
    return targets


def _best_blueprint(row: dict[str, Any]) -> tuple[dict[str, object] | None, int]:
    haystack = " ".join(
        [
            str(row.get("claim_id", "")),
            str(row.get("question_id", "")),
            str(row.get("problem_class", "")),
            str(row.get("kind", "")),
            str(row.get("statement", "")),
            " ".join(str(item) for item in row.get("required_primitives", []) or []),
            " ".join(str(item) for item in row.get("formal_source_hits", []) or []),
            " ".join(str(item) for item in row.get("paper_source_ids", []) or []),
            " ".join(str(item) for item in row.get("knowledge_ids", []) or []),
        ]
    ).lower()
    best: dict[str, object] | None = None
    best_score = 0
    for blueprint in CERTIFICATE_BLUEPRINTS:
        score = sum(1 for keyword in blueprint["keywords"] if str(keyword).lower() in haystack)
        if score > best_score:
            best = blueprint
            best_score = score
    return best, best_score


def _target_from_ledger_row(
    row: dict[str, Any],
    blueprint: dict[str, object],
    score: int,
) -> StatClaimCertificateTarget:
    errors: list[str] = []
    source_claim_id = str(row.get("claim_id", ""))
    evidence_paths = tuple(str(path) for path in row.get("evidence_paths", []) or [] if str(path))
    if not source_claim_id:
        errors.append("source claim_id missing")
    if not evidence_paths:
        errors.append("evidence_paths missing")
    family = str(blueprint["family"])
    status = str(row.get("status", ""))
    priority = _priority_for_row(status, score)
    return StatClaimCertificateTarget(
        schema_version=STAT_CLAIM_CERTIFICATE_PLAN_SCHEMA_VERSION,
        target_id=f"stat_claim_certificate:{stable_hash([source_claim_id, family])[:16]}",
        source_claim_id=source_claim_id,
        question_id=str(row.get("question_id", "")),
        problem_class=str(row.get("problem_class", "")),
        claim_status=status,
        certificate_family=family,
        checker_name=str(blueprint["checker"]),
        priority=priority,
        statement=str(row.get("statement", "")),
        witness_schema=tuple(str(item) for item in blueprint["witness_schema"]),
        checker_contract=str(blueprint["checker_contract"]),
        checker_theorem_shape=str(blueprint["checker_theorem_shape"]),
        generator_contract=(
            "untrusted agent may propose witness JSON only; it must not add assumptions, "
            "weaken the claim, or mark proof_evidence_ready without a kernel-verified checker theorem"
        ),
        required_gate=(
            "Lean/AXLE kernel verifies a small checker theorem of the form "
            "`checker cert = true -> encoded statistical claim`; promotion also requires "
            "claim-ledger linkage to the original theorem statement"
        ),
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        evidence_boundary=(
            "This target identifies a possible certificate-checker route. It is not proof "
            "evidence for the source claim, and witness generation alone is not verifier evidence."
        ),
        evidence_paths=evidence_paths,
        ok=not errors,
        errors=tuple(errors),
    )


def _priority_for_row(status: str, score: int) -> str:
    if status in {"FORMAL_GAP", "PROOF_FAILED"} and score >= 2:
        return "high"
    if status in {"THEOREM_GOAL_CONJECTURED", "REVISION_QUEUED"}:
        return "medium"
    return "low"


def _read_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing JSON file: {path}")
        return {}
    except Exception as exc:
        errors.append(f"failed to parse {path}: {type(exc).__name__}: {exc}")
        return {}
    return payload if isinstance(payload, dict) else {}


def _read_jsonl(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        errors.append(f"missing JSONL file: {path}")
        return []
    rows: list[dict[str, Any]] = []
    for idx, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"failed to parse JSONL {path}:{idx}: {exc}")
            continue
        if isinstance(payload, dict):
            rows.append(payload)
        else:
            errors.append(f"JSONL row is not an object: {path}:{idx}")
    return rows


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Statistical Claim Certificate Plan",
        "",
        f"- Claim ledger: `{payload.get('claim_ledger_manifest')}`",
        f"- Targets: {payload.get('n_ok')}/{payload.get('n_targets')} audit-clean",
        f"- Checker families: {payload.get('n_checker_families')}",
        f"- Proof status: `{payload.get('proof_evidence_status')}`",
        "",
        "These targets apply the certificate-checking pattern to statistical claims.",
        "They are planning artifacts, not Lean proof evidence.",
        "",
        "## Families",
        "",
    ]
    by_family = payload.get("by_family", {})
    if isinstance(by_family, dict) and by_family:
        for family, count in sorted(by_family.items()):
            lines.append(f"- `{family}`: {count}")
    else:
        lines.append("- none")
    lines.extend(["", "## Targets", ""])
    targets = payload.get("targets", [])
    if not isinstance(targets, list) or not targets:
        lines.append("No certificate targets were exported.")
    else:
        for row in targets[:30]:
            if not isinstance(row, dict):
                continue
            lines.extend(
                [
                    f"### `{row.get('target_id')}`",
                    "",
                    f"- Source claim: `{row.get('source_claim_id')}`",
                    f"- Family: `{row.get('certificate_family')}`",
                    f"- Checker: `{row.get('checker_name')}`",
                    f"- Priority: `{row.get('priority')}`",
                    f"- Required gate: {row.get('required_gate')}",
                    "",
                ]
            )
    lines.extend(["", "## Honesty Boundary", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"
