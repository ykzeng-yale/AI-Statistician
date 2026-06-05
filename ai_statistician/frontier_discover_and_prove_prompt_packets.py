from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .frontier_coverage_audit import FrontierBenchmarkQuestion, load_frontier_benchmark_questions


FRONTIER_DAP_PROMPT_PACKET_SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = "FRONTIER_DAP_PROMPT_PACKETS_NOT_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "Discover-and-prove prompt packets are hard-mode discovery and rewrite work "
    "orders. They are not Lean proof evidence; proof evidence starts only after "
    "a concrete formal theorem or artifact is kernel verified and separately "
    "promoted."
)
WORKER_OUTPUT_JSONL = "frontier_discover_and_prove_worker_outputs.jsonl"


@dataclass(frozen=True)
class FrontierDiscoverAndProvePromptPacket:
    schema_version: int
    prompt_packet_id: str
    question_id: str
    topic: str
    title: str
    hard_mode_input: dict[str, object]
    dap_workflow: tuple[str, ...]
    expected_output_contract: dict[str, object]
    prompt: str
    withheld_reference_hash: str
    expected_results_withheld: bool
    source_identity_withheld: bool
    prompt_expected_result_leak_detected: bool
    prompt_source_identity_leak_detected: bool
    proof_evidence_ready: int
    proof_evidence_status: str
    proof_evidence_boundary: str


def export_frontier_discover_and_prove_prompt_packets(
    out_dir: Path,
    *,
    benchmark_file: Path = Path("docs/frontier_stat_theory_benchmark.md"),
    max_packets: int = 60,
) -> dict[str, object]:
    """Export DAP-style hard-mode frontier-stat discovery/rewrite packets.

    The existing frontier benchmark already has open questions plus withheld
    expected results. This exporter turns those rows into worker packets that
    force the useful DAP separation: discover the estimand/procedure/theorem
    first, self-check it, then rewrite it into an easy-mode formal target for
    downstream provers. The packet deliberately withholds the paper source and
    expected theoretical results.
    """

    if max_packets <= 0:
        raise ValueError("max_packets must be positive")
    questions = load_frontier_benchmark_questions(benchmark_file)
    selected = questions[:max_packets]
    packets = [_packet_for_question(question) for question in selected]
    packet_dicts = [asdict(packet) for packet in packets]

    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "frontier_discover_and_prove_prompt_packets_manifest.json"
    jsonl_path = out_dir / "frontier_discover_and_prove_prompt_packets.jsonl"
    report_path = out_dir / "frontier_discover_and_prove_prompt_packets.md"
    _write_jsonl(jsonl_path, packet_dicts)

    by_topic: dict[str, int] = {}
    for packet in packets:
        by_topic[packet.topic] = by_topic.get(packet.topic, 0) + 1
    payload: dict[str, object] = {
        "schema_version": FRONTIER_DAP_PROMPT_PACKET_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "benchmark_file": str(benchmark_file),
        "n_benchmark_questions": len(questions),
        "max_packets": max_packets,
        "n_prompt_packets": len(packets),
        "n_output_contracts": sum(1 for row in packets if row.expected_output_contract),
        "n_expected_results_withheld": sum(1 for row in packets if row.expected_results_withheld),
        "n_source_identity_withheld": sum(1 for row in packets if row.source_identity_withheld),
        "n_prompt_expected_result_leaks": sum(
            1 for row in packets if row.prompt_expected_result_leak_detected
        ),
        "n_prompt_source_identity_leaks": sum(
            1 for row in packets if row.prompt_source_identity_leak_detected
        ),
        "n_proof_evidence_ready": 0,
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "worker_output_jsonl": WORKER_OUTPUT_JSONL,
        "by_topic": dict(sorted(by_topic.items())),
        "packets_jsonl": str(jsonl_path),
        "report_path": str(report_path),
        "dataset_fingerprint": stable_hash(packet_dicts),
        "all_ok": bool(packets)
        and all(row.expected_output_contract for row in packets)
        and all(row.expected_results_withheld for row in packets)
        and all(row.source_identity_withheld for row in packets)
        and not any(row.prompt_expected_result_leak_detected for row in packets)
        and not any(row.prompt_source_identity_leak_detected for row in packets),
        "limitations": [
            "DAP-style discovery outputs are candidate statistical answers, not proof evidence",
            "the exporter withholds benchmark expected results and source identity, but open questions may still contain domain hints",
            "downstream simulation, formalization, and Lean/kernel checks must validate any hard-to-easy rewrite before promotion",
        ],
        "packets": packet_dicts,
    }
    manifest_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    report_path.write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _packet_for_question(question: FrontierBenchmarkQuestion) -> FrontierDiscoverAndProvePromptPacket:
    hard_mode_input = {
        "question_id": question.id,
        "topic": question.topic,
        "title": question.title,
        "open_question": question.open_question,
        "visible_assumption_hints": question.assumptions,
        "source_identity_withheld": True,
        "expected_results_withheld": True,
    }
    expected_output_contract = {
        "write_jsonl": WORKER_OUTPUT_JSONL,
        "required_fields": [
            "prompt_packet_id",
            "question_id",
            "discovered_answer",
            "proposed_estimand",
            "proposed_estimator_or_procedure",
            "assumptions",
            "asymptotic_regime",
            "candidate_theorem_statement",
            "hard_to_easy_rewrite",
            "self_verification",
            "proof_obligations",
            "simulation_plan",
            "rejected_alternatives",
            "proof_evidence_ready",
            "kernel_verified_theorems",
            "evidence_paths",
            "limitations",
        ],
        "zero_evidence_response": {
            "proof_evidence_ready": 0,
            "kernel_verified_theorems": 0,
            "evidence_paths": [],
        },
        "local_kernel_evidence_rule": (
            "Set proof_evidence_ready > 0 only when the response includes a "
            "local Lean/AXLE verifier manifest for the exact rewritten theorem."
        ),
        "withheld_fields": ["source", "expected_theoretical_results"],
    }
    prompt = _prompt_for_question(question, expected_output_contract)
    return FrontierDiscoverAndProvePromptPacket(
        schema_version=FRONTIER_DAP_PROMPT_PACKET_SCHEMA_VERSION,
        prompt_packet_id=f"frontier_dap_prompt_packet:{question.id}",
        question_id=question.id,
        topic=question.topic,
        title=question.title,
        hard_mode_input=hard_mode_input,
        dap_workflow=(
            "natural_language_answer_discovery",
            "self_verification_and_revision",
            "hard_to_easy_theorem_rewrite",
            "simulation_and_formal_proof_obligation_routing",
        ),
        expected_output_contract=expected_output_contract,
        prompt=prompt,
        withheld_reference_hash=stable_hash(
            {
                "question_id": question.id,
                "source": question.source,
                "expected_results": question.expected_results,
            }
        ),
        expected_results_withheld=bool(question.expected_results)
        and not _contains_any(prompt, question.expected_results),
        source_identity_withheld=bool(question.source)
        and not _source_leaked(prompt, question.source),
        prompt_expected_result_leak_detected=_contains_any(prompt, question.expected_results),
        prompt_source_identity_leak_detected=_source_leaked(prompt, question.source),
        proof_evidence_ready=0,
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
    )


def _prompt_for_question(
    question: FrontierBenchmarkQuestion,
    expected_output_contract: dict[str, object],
) -> str:
    return "\n".join(
        [
            "You are a DAP-style frontier-statistics worker.",
            "Hard Mode: the final statistical answer is not given. First discover the estimand, procedure, assumptions, and theorem target; then rewrite the problem into an Easy Mode formal target for downstream proof workers.",
            "Do not infer or search for the paper identity, DOI, authors, or withheld expected theoretical results. Use only the visible open question and assumption hints below.",
            "Return exactly one JSON object as a JSONL row that satisfies the expected_output_contract.",
            "Discovery output is not proof evidence. Keep proof_evidence_ready=0 unless a local Lean/AXLE kernel verifier manifest for the exact rewritten theorem is attached.",
            "",
            "Visible hard-mode input:",
            json.dumps(
                {
                    "question_id": question.id,
                    "topic": question.topic,
                    "title": question.title,
                    "open_question": question.open_question,
                    "visible_assumption_hints": question.assumptions,
                },
                indent=2,
            ),
            "",
            "Required reasoning phases:",
            "1. Discover the candidate answer: estimand, procedure/estimator, assumptions, asymptotic regime, and theorem claim.",
            "2. Self-verification: list failure modes, missing assumptions, likely counterexamples, and at least one rejected alternative.",
            "3. Hard-to-easy rewrite: state a fully specified theorem target with no answer hole or hidden placeholder.",
            "4. Route proof obligations: separate simulation checks, source retrieval needs, formal primitives, and Lean/kernel proof obligations.",
            "",
            "Expected output contract:",
            json.dumps(expected_output_contract, indent=2),
        ]
    )


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    lower_text = " ".join(text.lower().split())
    for needle in needles:
        normalized = " ".join(str(needle).lower().split())
        if normalized and normalized in lower_text:
            return True
    return False


def _source_leaked(text: str, source: str) -> bool:
    lower_text = text.lower()
    for token in _source_leak_tokens(source):
        if token and token in lower_text:
            return True
    return False


def _source_leak_tokens(source: str) -> tuple[str, ...]:
    tokens: list[str] = []
    lower = source.lower()
    if "doi:" in lower:
        tokens.append(lower.split("doi:", 1)[1].strip())
    for marker in ("jasa", "annals of statistics", "jrssb", "biometrika"):
        if marker in lower:
            tokens.append(marker)
    return tuple(token for token in tokens if token)


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, default=str) + "\n" for row in rows),
        encoding="utf-8",
    )


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Frontier Discover-and-Prove Prompt Packets",
        "",
        "DAP-style hard-mode packets require answer discovery before formal proof routing.",
        "They withhold source identity and expected results from the worker prompt.",
        "",
        f"- Packets: {payload.get('n_prompt_packets')}",
        f"- Output contracts: {payload.get('n_output_contracts')}",
        f"- Expected results withheld: {payload.get('n_expected_results_withheld')}",
        f"- Source identity withheld: {payload.get('n_source_identity_withheld')}",
        f"- Expected-result prompt leaks: {payload.get('n_prompt_expected_result_leaks')}",
        f"- Source-identity prompt leaks: {payload.get('n_prompt_source_identity_leaks')}",
        f"- Proof evidence ready: {payload.get('n_proof_evidence_ready')}",
        f"- Proof status: `{payload.get('proof_evidence_status')}`",
        f"- Worker output JSONL: `{payload.get('worker_output_jsonl')}`",
        f"- Fingerprint: `{payload.get('dataset_fingerprint')}`",
        "",
        "## Packets",
        "",
        "| Packet | Topic | Output | Proof status |",
        "|---|---|---|---|",
    ]
    for row in payload.get("packets", []):
        if not isinstance(row, dict):
            continue
        contract = row.get("expected_output_contract", {})
        if not isinstance(contract, dict):
            contract = {}
        lines.append(
            f"| `{row.get('question_id')}` | `{row.get('topic')}` | "
            f"`{contract.get('write_jsonl', '')}` | `{row.get('proof_evidence_status')}` |"
        )
    return "\n".join(lines) + "\n"
