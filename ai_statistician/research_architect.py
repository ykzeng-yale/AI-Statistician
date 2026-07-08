from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Protocol

from .fingerprint import stable_hash
from .model_backend import (
    AnthropicGeneratorBackend,
    GeneratorBackend,
    GeneratorRequest,
    StaticJSONGeneratorBackend,
    resolve_generator_model,
)
from .llm_json_repair import extract_json_object, generate_validated_json_packet
from .research_schema import OpenResearchQuestion, ResearchReport


ARCHITECT_SCHEMA_VERSION = 1
THEORY_DERIVATION_NOT_PROOF_EVIDENCE = "LLM_THEORY_DERIVATION_NOT_PROOF_EVIDENCE"
THEORY_MIN_DERIVATION_STEPS = 3
THEORY_MIN_EQUATION_CHAIN_STEPS = 2
KERNEL_PROOF_BOUNDARY = (
    "LLM derivations, retrieval hits, and simulation predictions are proposal "
    "or diagnostic evidence only. Formal proof evidence requires AXLE/local "
    "Lean kernel verification of the intended formal claim."
)


class ArchitectLLMProvider(GeneratorBackend, Protocol):
    """Compatibility alias for the older Architect provider boundary."""


class StaticArchitectLLMProvider(StaticJSONGeneratorBackend):
    """Offline provider for deterministic tests and reviewed response replay."""

    def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        return self.generate(
            GeneratorRequest(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        ).text


class AnthropicArchitectLLMProvider(AnthropicGeneratorBackend):
    def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        return self.generate(
            GeneratorRequest(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        ).text


@dataclass(frozen=True)
class ResearchArchitectConfig:
    model: str = ""
    model_tier: str = "sonnet"
    max_tokens: int = 4500
    temperature: float = 0.2
    provider_name: str = "anthropic"
    max_repair_attempts: int = 2


@dataclass(frozen=True)
class EvidenceLedgerRow:
    evidence_id: str
    question_id: str
    artifact_id: str
    artifact_kind: str
    source_agent: str
    evidence_status: str
    proof_evidence_status: str
    boundary: str
    created_at: str


class LLMTheoryDeveloperAgent:
    """LLM-backed statistical theory developer.

    This is the first runtime layer for the canonical Architect goal: it asks a
    frontier model to derive statistical theory artifacts, then validates and
    records them without promoting them to proof evidence.
    """

    def __init__(
        self,
        *,
        provider: GeneratorBackend | None = None,
        config: ResearchArchitectConfig = ResearchArchitectConfig(),
    ) -> None:
        self.provider = provider or AnthropicArchitectLLMProvider()
        self.config = config

    def derive(
        self,
        question: OpenResearchQuestion,
        *,
        architect_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        user_prompt = build_theory_developer_prompt(
            question,
            architect_context=architect_context or {},
        )
        request_model = resolve_generator_model(
            provider_name=self.config.provider_name,
            requested_model=self.config.model,
            model_tier=self.config.model_tier,
        )
        request = GeneratorRequest(
            system_prompt=THEORY_DEVELOPER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            model=request_model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            schema=THEORY_DEVELOPER_JSON_SCHEMA,
            metadata={
                "subsystem": "TheoryDeveloper",
                "agent": "LLMTheoryDeveloperAgent",
                "provider_name": self.config.provider_name,
                "model_tier": self.config.model_tier,
                "resolved_model": request_model,
            },
        )

        def build_packet(raw_payload: Mapping[str, Any], response: Any, raw_text: str) -> dict[str, Any]:
            return _normalize_theory_packet(
                raw_payload,
                question=question,
                model=response.model or request_model,
                model_tier=self.config.model_tier,
                provider_name=self.config.provider_name or response.provider,
                raw_response=raw_text,
            )

        return generate_validated_json_packet(
            provider=self.provider,
            request=request,
            extract_payload=_extract_json_object,
            build_packet=build_packet,
            validate_packet=validate_theory_packet,
            validation_label="LLM TheoryDeveloper packet",
            max_repair_attempts=self.config.max_repair_attempts,
            repair_context_builder=_theory_developer_json_repair_context,
        )


class ResearchArchitectAgent:
    """First runtime slice for Architect-dispatched theory artifacts.

    This records LLM TheoryDeveloper output and evidence boundaries. It is not
    the complete plan-act-observe-revise AgentRuntime described in the project
    goal document.
    """

    def __init__(
        self,
        *,
        theory_developer: LLMTheoryDeveloperAgent,
        out_dir: Path,
    ) -> None:
        self.theory_developer = theory_developer
        self.out_dir = out_dir

    def run_theory_development(
        self,
        questions: list[OpenResearchQuestion],
        *,
        architect_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        packets: list[dict[str, Any]] = []
        ledger_rows: list[EvidenceLedgerRow] = []
        for question in questions:
            packet = self.theory_developer.derive(
                question,
                architect_context=architect_context or {},
            )
            packets.append(packet)
            ledger_rows.append(_ledger_row_for_packet(packet, question))

        packet_path = self.out_dir / "theory_derivation_packets.jsonl"
        ledger_path = self.out_dir / "evidence_ledger.jsonl"
        project_state_path = self.out_dir / "architect_project_state.json"
        manifest_path = self.out_dir / "research_architect_manifest.json"
        report_path = self.out_dir / "research_architect.md"
        _write_jsonl(packet_path, packets)
        _write_jsonl(ledger_path, [asdict(row) for row in ledger_rows])
        project_state = _project_state(questions, packets, ledger_rows)
        project_state_path.write_text(json.dumps(project_state, indent=2, default=str), encoding="utf-8")
        manifest: dict[str, Any] = {
            "schema_version": ARCHITECT_SCHEMA_VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "architect_stage": "llm_theory_development",
            "n_questions": len(questions),
            "n_theory_derivation_packets": len(packets),
            "n_evidence_ledger_rows": len(ledger_rows),
            "all_packets_ok": all(bool(packet.get("ok")) for packet in packets),
            "proof_evidence_status": THEORY_DERIVATION_NOT_PROOF_EVIDENCE,
            "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
            "artifacts": {
                "project_state": str(project_state_path),
                "theory_derivation_packets": str(packet_path),
                "evidence_ledger": str(ledger_path),
                "report": str(report_path),
            },
        }
        manifest_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
        report_path.write_text(_markdown_report(manifest, packets), encoding="utf-8")
        return manifest


class LLMTheoryDeveloperRepairHandler:
    """Research-loop live repair handler backed by the LLM TheoryDeveloper."""

    def __init__(
        self,
        *,
        theory_developer: LLMTheoryDeveloperAgent,
        out_dir: Path | None = None,
    ) -> None:
        self.theory_developer = theory_developer
        self.out_dir = out_dir

    def __call__(self, item: Mapping[str, Any], report: ResearchReport) -> dict[str, Any]:
        context = research_loop_theory_repair_context(item, report)
        packet = self.theory_developer.derive(report.question, architect_context=context)
        artifact = theory_revision_artifact_from_packet(packet, item=item, report=report)
        artifact_paths: dict[str, str] = {}
        if self.out_dir is not None:
            artifact_paths = write_theory_repair_artifacts(
                packet,
                artifact,
                out_dir=self.out_dir / stable_hash([report.question.id, item, packet.get("packet_id", "")])[:16],
                question=report.question,
            )
        return {
            "execution_status": "EXECUTED_LLM_THEORY_DEVELOPER_REPAIR",
            "task_type": "theory_revision_from_simulation_failure",
            "result": (
                "LLM TheoryDeveloper produced a derivation-backed theory revision. "
                "The revision is a proposal and must still pass simulation, semantic, "
                "source-grounding, and Lean/kernel gates."
            ),
            "rerun_requested": True,
            "repair_artifact": artifact,
            "live_repair_handler": "LLMTheoryDeveloperRepairHandler",
            "llm_theory_derivation_packet_id": packet.get("packet_id", ""),
            "llm_theory_artifacts": artifact_paths,
            "proof_evidence_status": THEORY_DERIVATION_NOT_PROOF_EVIDENCE,
            "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
        }


def build_theory_developer_prompt(
    question: OpenResearchQuestion,
    *,
    architect_context: Mapping[str, Any],
) -> str:
    compact_context = _compact_architect_context_for_prompt(architect_context)
    exact_semantic_instruction = (
        _theory_developer_downstream_exact_semantic_instruction(compact_context)
    )
    payload = {
        "question": {
            "id": question.id,
            "title": question.title,
            "description": question.description,
            "tags": list(question.tags),
        },
        "prompt_mode": {
            "mode": "compact_theory_discovery_packet",
            "purpose": "derive the core statistical object, procedure, theorem goals, and proof obligations without replaying full retrieval artifacts",
            "do_not_expand_full_retrieval_or_architect_json": True,
        },
        "architect_context": compact_context,
        "required_output_contract": THEORY_DEVELOPER_OUTPUT_CONTRACT,
        "validator_required_key_checklist": THEORY_DEVELOPER_VALIDATOR_CHECKLIST,
        "concise_output_budget": {
            "min_derivation_steps": THEORY_MIN_DERIVATION_STEPS,
            "max_derivation_steps": 5,
            "min_equation_chain_steps": THEORY_MIN_EQUATION_CHAIN_STEPS,
            "max_candidate_procedures": 1,
            "max_theorem_goals": 1,
            "max_lemma_cards": 1,
            "max_formalization_requests": 1,
            "max_critic_findings": 1,
            "max_simulation_predictions": 1,
            "max_next_actions": 1,
            "max_string_chars": 180,
            "instruction": (
                "Return a complete valid JSON object within this budget. Use exactly "
                "one item in estimator_specs, theorem_cards, lemma_cards, "
                "formalization_requests, critic_findings, and next_actions. Use at "
                "least three and at most five derivation_steps, plus at least two "
                "equation_chain rows and an assumption_ledger. Keep every string one "
                "sentence or one equation fragment. Do not include essays, tables, "
                "Markdown, or long simulation instructions."
            ),
        },
        "proof_boundary": KERNEL_PROOF_BOUNDARY,
    }
    if exact_semantic_instruction:
        payload["downstream_exact_semantic_formalizer_instruction"] = (
            exact_semantic_instruction
        )
    return (
        "Derive statistical theory artifacts for the Architect loop. Return ONLY "
        "JSON matching required_output_contract. Do not classify and stop. Do not "
        "claim Lean/kernel proof evidence. Build a compact derivation trace that a "
        "Formalizer/ProofEngineer can consume: name assumptions, write a short "
        "equation chain, expose lemma dependencies, and state exactly which semantic "
        "alignment constraints must survive formalization. Before returning, check "
        "validator_required_key_checklist exactly, including "
        "all top_level_required_fields, theorem_cards[0].informal_statement, "
        "theorem_cards[0].proof_strategy, proof_plan, and simulation_ademp_spec. "
        "This is a focused first-pass "
        "discovery packet: exactly one primary procedure, one theorem card, one lemma "
        "card, one formalization request, one critic finding, and one next action, "
        "but at least three derivation steps and two equation-chain rows. Keep the "
        "packet concise enough to finish as one valid JSON object; do not trade JSON "
        "completeness for detail.\n\n"
        + json.dumps(payload, separators=(",", ":"), default=str, ensure_ascii=False)
    )


THEORY_DEVELOPER_VALIDATOR_CHECKLIST: dict[str, Any] = {
    "top_level_required_fields": [
        "problem_card",
        "theory_derivation_packet",
        "estimator_specs",
        "theorem_cards",
        "lemma_cards",
        "proof_plan",
        "formalization_requests",
        "simulation_ademp_spec",
        "critic_findings",
        "next_actions",
    ],
    "problem_card": [
        "observed_data",
        "dgp",
        "estimand",
        "assumptions",
        "desired_theorem_type",
    ],
    "theory_derivation_packet": [
        "derivation_steps[0..2].id",
        "derivation_steps[0..2].claim",
        "derivation_steps[0..2].equation_or_argument",
        "equation_chain[0..1].lhs",
        "equation_chain[0..1].rhs",
        "equation_chain[0..1].justification",
        "assumption_ledger[0].assumption",
        "assumption_ledger[0].used_in",
        "formalization_handoff.semantic_alignment_constraints",
    ],
    "theorem_cards[0]": [
        "id",
        "informal_statement",
        "assumptions_used",
        "conclusion",
        "rate_or_limit_law",
        "proof_strategy",
        "semantic_risks",
    ],
    "required_arrays": [
        "estimator_specs",
        "theorem_cards",
        "lemma_cards",
        "formalization_requests",
        "critic_findings",
        "next_actions",
    ],
    "proof_plan": [
        "proof_dependency_dag",
        "required_primitives",
        "acceptable_strengthening",
        "unacceptable_changes",
    ],
    "simulation_ademp_spec": [
        "aim",
        "dgps",
        "methods",
        "performance_measures",
        "stress_tests",
        "expected_theoretical_behavior",
    ],
    "evidence_boundary": [
        f"proof_evidence_status={THEORY_DERIVATION_NOT_PROOF_EVIDENCE}",
        "kernel_verified=false",
    ],
}


def _theory_developer_json_repair_context(
    *,
    original_user_prompt: str,
    bad_response: str,
    errors: list[str],
    validation_label: str,
    truncation_detected: bool,
) -> dict[str, Any]:
    del original_user_prompt, bad_response, validation_label
    return {
        "subsystem": "TheoryDeveloper",
        "truncation_detected": bool(truncation_detected),
        "validator_required_key_checklist": THEORY_DEVELOPER_VALIDATOR_CHECKLIST,
        "last_validation_errors": [str(error) for error in errors[:8]],
        "repair_prompt_priority_instructions": [
            (
                "The corrected JSON must include every field listed in "
                "top_level_required_fields exactly; do not omit proof_plan or "
                "simulation_ademp_spec in compact mode, and keep both as "
                "non-empty objects with short scalar/list values."
            ),
            (
                "Use exact required key names from validator_required_key_checklist; "
                "do not replace theorem_cards[0].informal_statement with statement "
                "or theorem_cards[0].proof_strategy with proof_idea."
            ),
            (
                "theorem_cards[0] must include id, informal_statement, "
                "assumptions_used, conclusion, rate_or_limit_law, proof_strategy, "
                "and semantic_risks."
            ),
            (
                "theory_derivation_packet must include at least three "
                "derivation_steps, two equation_chain rows with lhs/rhs/justification, "
                "one assumption_ledger row, and formalization_handoff."
            ),
            (
                "Use exactly one item for estimator_specs, theorem_cards, "
                "lemma_cards, formalization_requests, critic_findings, and "
                "next_actions."
            ),
            (
                f"Preserve proof_evidence_status as {THEORY_DERIVATION_NOT_PROOF_EVIDENCE} "
                "and set kernel_verified to false."
            ),
        ],
    }


def _compact_architect_context_for_prompt(context: Mapping[str, Any]) -> dict[str, Any]:
    compact: dict[str, Any] = {
        "compaction_note": (
            "This is a bounded TheoryDeveloper prompt view. Full Architect, "
            "retrieval, and trace artifacts remain in runtime outputs."
        )
    }
    for key in (
        "architect_coordinator_proposal_id",
        "retrieval_memory_manifest_id",
        "previous_theory_packet_id",
        "simulation_manifest_id",
        "formalization_manifest_id",
        "proof_state_feedback_manifest_id",
    ):
        if context.get(key) not in (None, "", [], {}):
            compact[key] = _truncate_text(context.get(key), 180)

    architect_plan = context.get("architect_runtime_plan")
    if isinstance(architect_plan, Mapping):
        compact["architect_runtime_plan_summary"] = _compact_architect_runtime_plan_for_prompt(architect_plan)

    retrieval_context = context.get("retrieval_context")
    if isinstance(retrieval_context, Mapping):
        compact["retrieval_context"] = _compact_retrieval_context_for_prompt(retrieval_context)

    runtime_task = context.get("runtime_task")
    if isinstance(runtime_task, Mapping):
        compact["runtime_task"] = {
            key: runtime_task.get(key)
            for key in (
                "task_id",
                "owner_subsystem",
                "objective",
                "allowed_tools",
                "expected_artifacts",
                "acceptance_gate",
                "stop_condition",
            )
            if key in runtime_task
        }

    environment_feedback = context.get("environment_feedback")
    if isinstance(environment_feedback, Mapping):
        compact["environment_feedback"] = _compact_environment_feedback_for_prompt(environment_feedback)

    runtime_learning_memory = context.get("runtime_learning_memory")
    if isinstance(runtime_learning_memory, Mapping):
        compact["runtime_learning_memory"] = _compact_runtime_learning_memory_for_prompt(runtime_learning_memory)
    return compact


def _compact_architect_runtime_plan_for_prompt(plan: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "problem_analysis": _compact_prompt_mapping(
            plan.get("problem_analysis", {}),
            keys=(
                "theorem_family",
                "statistical_objects",
                "key_obstacles",
                "missing_information",
            ),
            list_limit=4,
            text_limit=240,
        ),
        "retrieval_strategy": _compact_prompt_mapping(
            plan.get("retrieval_strategy", {}),
            keys=("paper_queries", "formal_source_queries", "lean_rag_priorities"),
            list_limit=3,
            text_limit=180,
        ),
        "stat_knowledge_bank_plan": _compact_prompt_mapping(
            plan.get("stat_knowledge_bank_plan", {}),
            keys=("source_families_to_collect", "assumption_dimensions", "proof_skeletons_to_track"),
            list_limit=3,
            text_limit=220,
        ),
        "literature_fair_comparison_plan": _compact_prompt_rows(
            plan.get("literature_fair_comparison_plan", []),
            keys=("candidate_source_family", "must_match", "likely_mismatches", "unsafe_transfer_risks"),
            limit=2,
            list_limit=3,
            text_limit=180,
        ),
        "evidence_contract": _compact_prompt_mapping(
            plan.get("evidence_contract", {}),
            keys=(
                "formal_verification_policy",
                "recommended_research_path",
                "formal_required_for_final",
                "formal_targets",
                "simulation_targets",
                "acceptance_modes",
                "disclosure_requirements",
            ),
            list_limit=3,
            text_limit=220,
        ),
        "subsystem_execution_plan": _compact_prompt_rows(
            plan.get("subsystem_execution_plan", []),
            keys=("subsystem", "objective", "expected_artifacts", "acceptance_gate"),
            limit=3,
            list_limit=3,
            text_limit=220,
        ),
        "evidence_gates": _compact_prompt_rows(
            plan.get("evidence_gates", []),
            keys=("artifact_kind", "required_evidence", "not_evidence"),
            limit=3,
            list_limit=3,
            text_limit=220,
        ),
        "iteration_policy": _compact_prompt_mapping(
            plan.get("iteration_policy", {}),
            keys=("reroute_triggers", "stop_conditions", "max_repair_rounds"),
            list_limit=3,
            text_limit=220,
        ),
        "boundary": _truncate_text(plan.get("boundary", ""), 360),
    }


def _compact_retrieval_context_for_prompt(retrieval_context: Mapping[str, Any]) -> dict[str, Any]:
    knowledge_cards = list(retrieval_context.get("knowledge_cards", []) or [])
    paper_sources = list(retrieval_context.get("paper_sources", []) or [])
    formal_source_hits = list(retrieval_context.get("formal_source_hits", []) or [])
    return {
        "counts": {
            "knowledge_cards": len(knowledge_cards),
            "paper_sources": len(paper_sources),
            "formal_source_hit_groups": len(formal_source_hits),
            "formal_source_hits": sum(
                len(row.get("hits", []) or [])
                for row in formal_source_hits
                if isinstance(row, Mapping)
            ),
        },
        "knowledge_cards": [_compact_knowledge_card(row) for row in knowledge_cards[:3]],
        "paper_sources": [_compact_paper_source(row) for row in paper_sources[:3]],
        "formal_source_hits": [_compact_formal_hit_group(row) for row in formal_source_hits[:2]],
        "boundary": retrieval_context.get("boundary", ""),
        "compaction_note": (
            "Full retrieval artifacts remain in runtime outputs; this prompt view "
            "is bounded to reduce API cost and connection fragility."
        ),
    }


def _compact_knowledge_card(row: Any) -> dict[str, Any]:
    if not isinstance(row, Mapping):
        return {"summary": _truncate_text(row, 240)}
    return {
        "id": row.get("id", ""),
        "title": row.get("title", ""),
        "source_type": row.get("source_type", ""),
        "summary": _truncate_text(row.get("summary", ""), 240),
        "tags": list(row.get("tags", []) or [])[:6],
    }


def _compact_paper_source(row: Any) -> dict[str, Any]:
    if not isinstance(row, Mapping):
        return {"summary": _truncate_text(row, 240)}
    return {
        "id": row.get("id", ""),
        "title": row.get("title", ""),
        "journal": row.get("journal", ""),
        "topic": row.get("topic", ""),
        "publication_date": row.get("publication_date", ""),
        "summary": _truncate_text(row.get("summary", ""), 240),
        "matched_terms": list(row.get("matched_terms", []) or [])[:8],
    }


def _compact_formal_hit_group(row: Any) -> dict[str, Any]:
    if not isinstance(row, Mapping):
        return {"summary": _truncate_text(row, 240), "hits": []}
    hits = list(row.get("hits", []) or [])
    return {
        "theorem_goal_id": row.get("theorem_goal_id", ""),
        "n_hits": len(hits),
        "hits": [_compact_formal_hit(hit) for hit in hits[:2]],
    }


def _compact_formal_hit(hit: Any) -> dict[str, Any]:
    if not isinstance(hit, Mapping):
        return {"summary": _truncate_text(hit, 240)}
    return {
        "source_id": hit.get("source_id", ""),
        "path": hit.get("path", ""),
        "line": hit.get("line", ""),
        "kind": hit.get("kind", ""),
        "name": _truncate_text(hit.get("name", ""), 140),
        "score": hit.get("score", ""),
        "matched_terms": list(hit.get("matched_terms", []) or [])[:8],
        "signature_omitted": bool(hit.get("signature")),
    }


def _compact_prompt_rows(
    rows: Any,
    *,
    keys: tuple[str, ...],
    limit: int,
    list_limit: int,
    text_limit: int,
) -> list[dict[str, Any]]:
    if not isinstance(rows, (list, tuple)):
        return []
    return [
        _compact_prompt_mapping(row, keys=keys, list_limit=list_limit, text_limit=text_limit)
        if isinstance(row, Mapping)
        else {"summary": _truncate_text(row, text_limit)}
        for row in list(rows)[:limit]
    ]


def _compact_prompt_mapping(
    row: Any,
    *,
    keys: tuple[str, ...],
    list_limit: int,
    text_limit: int,
) -> dict[str, Any]:
    if not isinstance(row, Mapping):
        return {}
    return {
        key: _compact_prompt_value(row.get(key), list_limit=list_limit, text_limit=text_limit)
        for key in keys
        if row.get(key) not in (None, "", [], {})
    }


def _compact_prompt_value(value: Any, *, list_limit: int, text_limit: int) -> Any:
    if isinstance(value, str):
        return _truncate_text(value, text_limit)
    if isinstance(value, Mapping):
        return {
            str(key): _compact_prompt_value(child, list_limit=list_limit, text_limit=text_limit)
            for key, child in list(value.items())[:list_limit]
            if child not in (None, "", [], {})
        }
    if isinstance(value, (list, tuple)):
        return [
            _compact_prompt_value(child, list_limit=list_limit, text_limit=text_limit)
            for child in list(value)[:list_limit]
        ]
    return value


def _compact_environment_feedback_for_prompt(feedback: Mapping[str, Any]) -> dict[str, Any]:
    high_priority_agenda = list(feedback.get("high_priority_agenda", []) or [])
    formal_subclaims = list(feedback.get("formal_subclaim_feedback", []) or [])
    failed_simulations = list(feedback.get("failed_simulations", []) or [])
    implementation_gaps = list(feedback.get("implementation_gaps", []) or [])
    compact = {
        "feedback_source": feedback.get("feedback_source", ""),
        "feedback_type": feedback.get("feedback_type", ""),
        "trigger": feedback.get("trigger", ""),
        "failure_classification": feedback.get("failure_classification", ""),
        "failure_classifications": _compact_learning_memory_value(
            feedback.get("failure_classifications", [])
        ),
        "question_id": feedback.get("question_id", ""),
        "source_task_id": feedback.get("source_task_id", ""),
        "source_owner_subsystem": feedback.get("source_owner_subsystem", ""),
        "source_theory_packet_id": feedback.get("source_theory_packet_id", ""),
        "target_consumer_subsystem": feedback.get("target_consumer_subsystem", ""),
        "critic_repair_round": feedback.get("critic_repair_round", ""),
        "next_critic_repair_round": feedback.get("next_critic_repair_round", ""),
        "max_critic_repair_rounds": feedback.get("max_critic_repair_rounds", ""),
        "theory_packet_id": feedback.get("theory_packet_id", ""),
        "simulation_manifest_id": feedback.get("simulation_manifest_id", ""),
        "formalization_manifest_id": feedback.get("formalization_manifest_id", ""),
        "proof_state_feedback_manifest_id": feedback.get("proof_state_feedback_manifest_id", ""),
        "formalization_counts": feedback.get("formalization_counts", {}),
        "simulation_passed": feedback.get("simulation_passed", ""),
        "high_priority_agenda": [_compact_feedback_row(row) for row in high_priority_agenda[:5]],
        "formal_subclaim_feedback": [_compact_feedback_row(row) for row in formal_subclaims[:8]],
        "failed_simulations": [_compact_feedback_row(row) for row in failed_simulations[:5]],
        "implementation_gaps": [_compact_feedback_row(row) for row in implementation_gaps[:5]],
        "required_repair": _truncate_text(feedback.get("required_repair", ""), 720),
        "required_revision": _truncate_text(feedback.get("required_revision", ""), 600),
        "acceptance_gate": _truncate_text(feedback.get("acceptance_gate", ""), 720),
        "proof_evidence_status": _truncate_text(
            feedback.get("proof_evidence_status", ""), 240
        ),
        "proof_evidence_boundary": _truncate_text(feedback.get("proof_evidence_boundary", ""), 400),
        "boundary": _truncate_text(feedback.get("boundary", ""), 400),
    }
    theory_alignment_feedback = feedback.get("theory_trace_downstream_alignment_feedback")
    if isinstance(theory_alignment_feedback, Mapping) and theory_alignment_feedback:
        compact["theory_trace_downstream_alignment_feedback"] = _compact_feedback_row(
            theory_alignment_feedback
        )
    theory_alignment_contract = feedback.get("theory_trace_downstream_alignment_contract")
    if isinstance(theory_alignment_contract, Mapping) and theory_alignment_contract:
        compact["theory_trace_downstream_alignment_contract"] = _compact_feedback_row(
            theory_alignment_contract
        )
    formal_blocker_resource_requests = feedback.get("formal_blocker_resource_requests")
    has_exact_semantic_blocker_rows = (
        isinstance(formal_blocker_resource_requests, (list, tuple))
        and bool(formal_blocker_resource_requests)
    )
    if has_exact_semantic_blocker_rows:
        compact["formal_blocker_resource_requests"] = (
            _compact_exact_semantic_feedback_rows(formal_blocker_resource_requests)
        )
    for exact_semantic_feedback_key in (
        "source_theorem_exact_semantic_definition_repair_feedback",
        "runtime_exact_semantic_definition_work_order_feedback",
        "source_theorem_exact_semantic_definition_work_order_feedback",
    ):
        exact_semantic_feedback = feedback.get(exact_semantic_feedback_key)
        if isinstance(exact_semantic_feedback, Mapping) and exact_semantic_feedback:
            compact[exact_semantic_feedback_key] = (
                _compact_exact_semantic_feedback_mapping(
                    exact_semantic_feedback,
                    include_row_containers=not has_exact_semantic_blocker_rows,
                )
            )
    additional_feedback = feedback.get("additional_runtime_feedback", [])
    if isinstance(additional_feedback, list) and additional_feedback:
        compact["additional_runtime_feedback"] = [
            _compact_feedback_row(row) for row in additional_feedback[:4]
        ]
    return {
        key: value
        for key, value in compact.items()
        if value not in (None, "", [], {})
    }


def _compact_runtime_learning_memory_for_prompt(memory: Mapping[str, Any]) -> dict[str, Any]:
    rows = list(memory.get("rows", []) or [])
    return {
        "schema_version": memory.get("schema_version", 1),
        "source_paths": list(memory.get("source_paths", []) or [])[:5],
        "counts": {
            "rows": len(rows),
            "rows_prompted": min(len(rows), 8),
            "rows_loaded": memory.get("counts", {}).get("rows_loaded", len(rows))
            if isinstance(memory.get("counts", {}), Mapping)
            else len(rows),
        },
        "rows": [_compact_learning_memory_row(row) for row in rows[:8]],
        "boundary": _truncate_text(memory.get("boundary", ""), 500),
    }


def _compact_learning_memory_row(row: Any) -> dict[str, Any]:
    if not isinstance(row, Mapping):
        return {"summary": _truncate_text(row, 240)}
    compact = {
        "learning_task": _truncate_text(row.get("learning_task", ""), 120),
        "question_id": _truncate_text(row.get("question_id", ""), 120),
        "work_order_id": _truncate_text(row.get("work_order_id", ""), 120),
        "next_owner_subsystem": _truncate_text(
            row.get("next_owner_subsystem", ""), 120
        ),
        "target_consumer_subsystem": _truncate_text(
            row.get("target_consumer_subsystem", ""), 120
        ),
        "target_theorem_name": _truncate_text(row.get("target_theorem_name", ""), 160),
        "failure_classification": _truncate_text(
            row.get("failure_classification", ""), 160
        ),
        "failure_classifications": _compact_learning_memory_value(
            row.get("failure_classifications", [])
        ),
        "target_behavior": _truncate_text(row.get("target_behavior", ""), 360),
        "required_repair": _truncate_text(row.get("required_repair", ""), 360),
        "acceptance_gate": _truncate_text(row.get("acceptance_gate", ""), 240),
        "proof_evidence_status": _truncate_text(
            row.get("proof_evidence_status", ""), 180
        ),
        "input_summary": _compact_learning_memory_input_summary(
            row.get("input_summary", {})
        ),
    }
    return {
        key: value
        for key, value in compact.items()
        if value not in (None, "", [], {})
    }


def _compact_learning_memory_input_summary(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    keep_keys = (
        "trigger",
        "owner_subsystem",
        "agenda_id",
        "work_order_id",
        "semantic_primitive_id",
        "target_theorem_name",
        "placeholder_symbol",
        "runtime_queue_status",
        "verification_status",
        "execution_status",
        "failure_classification",
        "route_planner_contract_feedback_id",
        "contract_counts",
        "provider_token_counts",
        "staged_followup_assembly_error_summary",
        "staged_followup_assembly_error_preview",
        "source_manifest_id",
        "source_manifest_path",
        "source_rows_path",
        "formalization_gap_planner_bridge_id",
        "formalization_gap_planner_handoff_id",
        "standalone_seed_path",
        "source_theorem_kernel_verified",
        "artifact_kernel_verified",
        "local_lean_checked",
        "local_lean_compiled",
        "proof_body_attempted",
        "proof_body_attempt_success",
        "premise_name",
        "premise_target_status",
        "premise_target_matched_binder",
        "premise_target_type",
        "premise_derivation_gap_kind",
        "premise_derivation_gap_summary",
        "target_ids",
        "target_theorem_goal_ids",
        "kernel_verified_proof_obligation_ids",
        "kernel_verified_source_theorem_semantic_primitive_ids",
        "kernel_verified_source_theorem_semantic_support_obligation_ids",
        "source_theorem_semantic_primitive_work_order_ids",
        "semantic_primitive_ids",
        "formal_environment_placeholder_symbols",
        "missing_formal_symbols",
        "formal_environment_typeclass_blockers",
        "typeclass_blockers",
        "formal_gap_target_ids",
        "recommended_proof_obligation_ids",
        "diagnostics",
        "proof_body_goal_excerpt",
        "proof_body_attempt_summaries",
        "proof_body_gate_status",
        "formalization_counts",
        "retrieval_counts",
        "candidate_artifact_path",
        "definition_only_candidate_artifact_path",
        "source_candidate_artifact_path",
        "adapter_candidate_artifact_path",
        "adapter_candidate_artifact_paths",
        "premise_candidate_artifact_path",
        "proof_body_candidate_artifact_path",
        "source_theorem_exact_semantic_definition_typechecked_candidate",
        "n_theory_derivation_packets",
        "n_theory_derivation_packets_with_contract",
        "n_theory_derivation_packets_with_min_derivation_steps",
        "n_theory_derivation_packets_with_equation_chain",
        "n_theory_derivation_packets_with_assumption_ledger",
        "n_theory_derivation_packets_with_formalization_handoff",
        "required_theory_trace_consumers",
        "theory_trace_consuming_subsystems",
        "structured_theory_trace_consuming_subsystems",
        "structured_theory_trace_aligned_subsystems",
        "all_required_theory_trace_consumers_observed",
        "all_required_theory_trace_alignment_consumers_observed",
        "target_consumer_subsystem",
        "n_theory_trace_consumption_contracts",
        "n_theory_trace_alignment_contracts",
        "n_theory_trace_alignment_contracts_with_llm_alignment",
        "n_structured_theory_trace_alignment_contracts",
        "n_theory_trace_alignment_contracts_with_unsupported_anchors",
        "failure_classifications",
    )
    compact: dict[str, Any] = {}
    for key in keep_keys:
        if key not in value or value[key] in (None, "", [], {}):
            continue
        child = value[key]
        if _prompt_key_is_path_like(key):
            compact[key] = _compact_prompt_value_for_key(
                key,
                child,
                list_limit=8,
                mapping_limit=8,
                text_limit=320,
                path_limit=1024,
            )
        elif isinstance(child, list):
            limit = (
                4
                if key
                in {"diagnostics", "proof_body_goal_excerpt", "proof_body_attempt_summaries"}
                else 8
            )
            compact[key] = [
                _compact_learning_memory_value(item) for item in child[:limit]
            ]
        elif isinstance(child, Mapping):
            compact[key] = {
                str(child_key): _compact_learning_memory_value(child_value)
                for child_key, child_value in list(child.items())[:8]
                if child_value not in (None, "", [], {})
            }
        else:
            compact[key] = _compact_learning_memory_value(child)
    return compact


def _compact_learning_memory_value(value: Any) -> Any:
    if isinstance(value, str):
        return _truncate_text(value, 320)
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    if isinstance(value, list):
        return [_compact_learning_memory_value(item) for item in value[:6]]
    if isinstance(value, Mapping):
        return {
            str(key): _compact_learning_memory_value(child)
            for key, child in list(value.items())[:6]
            if child not in (None, "", [], {})
        }
    return _truncate_text(value, 320)


_EXACT_SEMANTIC_FEEDBACK_MAPPING_KEYS = (
    "artifact_kind",
    "feedback_type",
    "trigger",
    "question_id",
    "source_task_id",
    "source_owner_subsystem",
    "target_consumer_subsystem",
    "target_theorem_name",
    "target_lean_declaration",
    "failure_classification",
    "required_repair",
    "required_revision",
    "acceptance_gate",
    "proof_body_gate_status",
    "proof_body_goal_reached",
    "source_theorem_kernel_verified",
    "source_theorem_kernel_evidence_eligible",
    "proof_evidence_status",
    "proof_evidence_boundary",
    "boundary",
)


_EXACT_SEMANTIC_FEEDBACK_ROW_KEYS = (
    "work_order_id",
    "repair_feedback_id",
    "diagnostic_id",
    "placeholder_symbol",
    "semantic_primitive_id",
    "target_theorem_name",
    "target_lean_declaration",
    "target_ids",
    "target_lane",
    "lane",
    "action_type",
    "request_type",
    "replacement_strategy",
    "search_targets",
    "semantic_primitives",
    "semantic_primitive_requirements",
    "failure_classification",
    "required_repair",
    "required_revision",
    "runtime_queue_status",
    "verification_status",
    "proof_body_gate_status",
    "proof_body_goal_reached",
    "candidate_artifact_path",
    "definition_only_candidate_artifact_path",
    "source_candidate_artifact_path",
    "adapter_candidate_artifact_path",
    "adapter_candidate_artifact_paths",
    "premise_candidate_artifact_path",
    "proof_body_candidate_artifact_path",
    "source_theorem_exact_semantic_definition_typechecked_candidate",
    "source_theorem_kernel_verified",
    "source_theorem_kernel_evidence_eligible",
    "proof_evidence_status",
    "boundary",
)


_EXACT_SEMANTIC_FEEDBACK_ROW_CONTAINER_KEYS = (
    "formal_blocker_resource_requests",
    "diagnostics",
    "work_orders",
    "rows",
    "source_theorem_exact_semantic_definition_typechecked_candidates",
)


def _theory_developer_downstream_exact_semantic_instruction(
    compact_context: Mapping[str, Any],
) -> dict[str, Any]:
    environment_feedback = compact_context.get("environment_feedback")
    if not isinstance(environment_feedback, Mapping):
        return {}
    if not _contains_exact_semantic_feedback(environment_feedback):
        return {}
    return {
        "status": "ACTIVE_DOWNSTREAM_FORMALIZER_CONSTRAINT",
        "required_behavior": (
            "When refreshing theory_derivation_packet, theorem_cards, and "
            "formalization_handoff, preserve exact source semantic primitive "
            "names, placeholder symbols, target theorem names, "
            "candidate_artifact_path/definition_only_candidate_artifact_path, "
            "and proof_body_gate_status from architect_context.environment_feedback."
        ),
        "proof_body_gate": (
            "If proof_body_gate_status=SEMANTIC_REVIEW_REQUIRED_BEFORE_PROOF_BODY, "
            "do not open source-theorem proof-body search. Route the next handoff "
            "to Formalizer/ProofEngineer exact semantic-definition review or repair."
        ),
        "proof_boundary": (
            "Rows tagged FORMAL_BLOCKER_RESOURCE_REQUEST_NOT_PROOF_EVIDENCE or "
            "*_NOT_PROOF_EVIDENCE are blocker/review context only; do not describe "
            "them as Lean proof, source theorem proof, or kernel evidence."
        ),
    }


def _contains_exact_semantic_feedback(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if "source_theorem_exact_semantic_definition" in key_text:
                return True
            if _contains_exact_semantic_feedback(child):
                return True
        return False
    if isinstance(value, (list, tuple)):
        return any(_contains_exact_semantic_feedback(child) for child in value[:12])
    if isinstance(value, str):
        return (
            "source_theorem_exact_semantic_definition" in value
            or "SEMANTIC_REVIEW_REQUIRED_BEFORE_PROOF_BODY" in value
        )
    return False


def _prompt_key_is_path_like(key: Any) -> bool:
    key_text = str(key).lower()
    return (
        key_text.endswith("_path")
        or key_text.endswith("_paths")
        or key_text.endswith("_jsonl")
        or key_text.endswith("_manifest")
        or "artifact_path" in key_text
    )


def _compact_prompt_value_for_key(
    key: Any,
    value: Any,
    *,
    list_limit: int = 8,
    mapping_limit: int = 10,
    text_limit: int = 320,
    path_limit: int = 1024,
) -> Any:
    string_limit = path_limit if _prompt_key_is_path_like(key) else text_limit
    if isinstance(value, str):
        return _truncate_text(value, string_limit)
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    if isinstance(value, list):
        return [
            _compact_prompt_value_for_key(
                key,
                item,
                list_limit=list_limit,
                mapping_limit=mapping_limit,
                text_limit=text_limit,
                path_limit=path_limit,
            )
            for item in value[:list_limit]
        ]
    if isinstance(value, Mapping):
        return {
            str(child_key): _compact_prompt_value_for_key(
                child_key,
                child_value,
                list_limit=list_limit,
                mapping_limit=mapping_limit,
                text_limit=text_limit,
                path_limit=path_limit,
            )
            for child_key, child_value in list(value.items())[:mapping_limit]
            if child_value not in (None, "", [], {})
        }
    return _truncate_text(value, string_limit)


def _compact_exact_semantic_feedback_mapping(
    value: Any,
    *,
    include_row_containers: bool = True,
) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    compact: dict[str, Any] = {}
    for key in _EXACT_SEMANTIC_FEEDBACK_MAPPING_KEYS:
        if value.get(key) not in (None, "", [], {}):
            compact[key] = _compact_prompt_value_for_key(key, value.get(key))
    if include_row_containers:
        for key in _EXACT_SEMANTIC_FEEDBACK_ROW_CONTAINER_KEYS:
            rows = value.get(key)
            if isinstance(rows, (list, tuple)) and rows:
                compact[key] = _compact_exact_semantic_feedback_rows(rows)
            elif isinstance(rows, Mapping) and rows:
                compact[key] = _compact_exact_semantic_feedback_row(rows)
    else:
        for key in _EXACT_SEMANTIC_FEEDBACK_ROW_CONTAINER_KEYS:
            rows = value.get(key)
            if isinstance(rows, (list, tuple)) and rows:
                compact[f"n_{key}"] = len(rows)
            elif isinstance(rows, Mapping) and rows:
                compact[f"{key}_present"] = True
    return {
        key: row_value
        for key, row_value in compact.items()
        if row_value not in (None, "", [], {})
    }


def _compact_exact_semantic_feedback_rows(rows: Any) -> list[dict[str, Any]]:
    if not isinstance(rows, (list, tuple)):
        return []
    return [_compact_exact_semantic_feedback_row(row) for row in list(rows)[:6]]


def _compact_exact_semantic_feedback_row(row: Any) -> dict[str, Any]:
    if not isinstance(row, Mapping):
        return {"summary": _truncate_text(row, 240)}
    compact: dict[str, Any] = {}
    for key in _EXACT_SEMANTIC_FEEDBACK_ROW_KEYS:
        if row.get(key) not in (None, "", [], {}):
            compact[key] = _compact_prompt_value_for_key(key, row.get(key))
    for key, value in row.items():
        key_text = str(key)
        if key_text in compact or value in (None, "", [], {}):
            continue
        if _prompt_key_is_path_like(key_text) or (
            "source_theorem_exact_semantic_definition" in key_text
        ):
            compact[key_text] = _compact_prompt_value_for_key(key_text, value)
    return compact


def _compact_feedback_row(row: Any) -> dict[str, Any]:
    if not isinstance(row, Mapping):
        return {"summary": _truncate_text(row, 240)}
    compact: dict[str, Any] = {}
    for key, value in row.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            compact[str(key)] = _compact_prompt_value_for_key(key, value)
        elif isinstance(value, list):
            compact[str(key)] = [
                _compact_prompt_value_for_key(key, item)
                for item in value[:8]
            ]
        elif isinstance(value, Mapping):
            compact[str(key)] = {
                str(k): _compact_prompt_value_for_key(k, v)
                for k, v in list(value.items())[:10]
                if v not in (None, "", [], {})
            }
    return compact


def _truncate_text(value: Any, limit: int) -> str:
    text = str(value or "")
    return text if len(text) <= limit else text[: max(0, limit - 3)] + "..."


def _safe_len(value: Any) -> int:
    return len(value) if isinstance(value, (list, tuple)) else 0


THEORY_DEVELOPER_SYSTEM_PROMPT = """\
You are the LLM TheoryDeveloper inside an AI Statistician Architect.

Your job is research-level statistical theory development, not template
classification. Given an open research question, derive the mathematical setup,
estimand, procedure, theorem candidates, lemma DAG, proof plan, simulation
predictions, and formalization obligations. Use equation-level reasoning and
self-critique. Preserve uncertainty and semantic risks. Do not claim formal proof
or Lean kernel verification.
"""


THEORY_DEVELOPER_OUTPUT_CONTRACT: dict[str, Any] = {
    "problem_card": {
        "observed_data": "string",
        "dgp": "string",
        "estimand": "string",
        "nuisance_quantities": ["string"],
        "assumptions": ["string"],
        "asymptotic_regime": "string",
        "desired_theorem_type": "string",
    },
    "theory_derivation_packet": {
        "derivation_summary": "string",
        "derivation_steps": [
            {
                "id": "short id",
                "claim": "string",
                "equation_or_argument": "string",
                "depends_on": ["ids"],
                "formal_goal": "theorem_card_id or lemma_card_id",
                "risk": "string",
            }
        ],
        "equation_chain": [
            {
                "step_id": "short id",
                "lhs": "string",
                "relation": "=|≈|<=|=>|converges_to|implies",
                "rhs": "string",
                "justification": "string",
                "depends_on": ["derivation_step ids"],
            }
        ],
        "assumption_ledger": [
            {
                "assumption": "string",
                "role": "identification|regularity|algorithmic|simulation|formalization",
                "used_in": ["derivation/equation/theorem ids"],
                "risk_if_dropped": "string",
            }
        ],
        "formalization_handoff": {
            "source_theorem_target": "theorem_card_id",
            "candidate_lean_targets": ["string"],
            "required_definitions": ["string"],
            "lemma_dependencies": ["lemma_card or derivation ids"],
            "semantic_alignment_constraints": ["string"],
        },
        "self_critique": ["string"],
        "rejected_alternatives": [{"name": "string", "reason": "string"}],
    },
    "estimator_specs": [
        {
            "id": "short id",
            "name": "string",
            "formula": "string",
            "algorithm_sketch": "string",
            "tuning": ["string"],
            "required_assumptions": ["string"],
        }
    ],
    "theorem_cards": [
        {
            "id": "short id",
            "informal_statement": "string",
            "assumptions_used": ["string"],
            "conclusion": "string",
            "rate_or_limit_law": "string",
            "proof_strategy": "string",
            "semantic_risks": ["string"],
        }
    ],
    "lemma_cards": [
        {
            "id": "short id",
            "statement": "string",
            "depends_on": ["ids"],
            "used_by": ["ids"],
            "formalization_difficulty": "low|medium|high",
        }
    ],
    "proof_plan": {
        "proof_dependency_dag": [{"from": "id", "to": "id"}],
        "required_primitives": ["string"],
        "acceptable_strengthening": ["string"],
        "unacceptable_changes": ["string"],
    },
    "formalization_requests": [
        {
            "id": "short id",
            "target_theorem_card": "id",
            "lean_statement_sketch": "string",
            "semantic_alignment_constraints": ["string"],
            "kernel_status": "OPEN",
        }
    ],
    "simulation_ademp_spec": {
        "aim": "string",
        "dgps": ["string"],
        "methods": ["string"],
        "performance_measures": ["string"],
        "stress_tests": ["string"],
        "expected_theoretical_behavior": ["string"],
    },
    "critic_findings": [
        {"critic": "string", "finding": "string", "reroute_if_confirmed": "string"}
    ],
    "next_actions": [
        {"owner_agent": "string", "action": "string", "acceptance_gate": "string"}
    ],
}


THEORY_DEVELOPER_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": True,
    "required": [
        "problem_card",
        "theory_derivation_packet",
        "estimator_specs",
        "theorem_cards",
        "lemma_cards",
        "proof_plan",
        "formalization_requests",
        "simulation_ademp_spec",
        "critic_findings",
        "next_actions",
    ],
    "properties": {
        "problem_card": {"type": "object"},
        "theory_derivation_packet": {"type": "object"},
        "estimator_specs": {"type": "array", "minItems": 1},
        "theorem_cards": {"type": "array", "minItems": 1},
        "lemma_cards": {"type": "array", "minItems": 1},
        "proof_plan": {"type": "object"},
        "formalization_requests": {"type": "array", "minItems": 1},
        "simulation_ademp_spec": {"type": "object"},
        "critic_findings": {"type": "array", "minItems": 1},
        "next_actions": {"type": "array", "minItems": 1},
    },
}


def validate_theory_packet(packet: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in (
        "problem_card",
        "theory_derivation_packet",
        "estimator_specs",
        "theorem_cards",
        "lemma_cards",
        "proof_plan",
        "formalization_requests",
        "simulation_ademp_spec",
        "critic_findings",
        "next_actions",
    ):
        if packet.get(field) in (None, "", [], {}):
            errors.append(f"missing or empty field: {field}")
    derivation = packet.get("theory_derivation_packet", {})
    if not isinstance(derivation, Mapping):
        errors.append("theory_derivation_packet must be an object")
    else:
        derivation_steps = derivation.get("derivation_steps", [])
        if not isinstance(derivation_steps, list) or len(derivation_steps) < THEORY_MIN_DERIVATION_STEPS:
            errors.append(
                "theory_derivation_packet.derivation_steps must contain at least "
                f"{THEORY_MIN_DERIVATION_STEPS} steps"
            )
        else:
            for idx, row in enumerate(derivation_steps, start=1):
                if not isinstance(row, Mapping):
                    errors.append("theory_derivation_packet.derivation_steps entries must be objects")
                    continue
                if not str(row.get("id", "")).strip():
                    errors.append(f"derivation step {idx} missing id")
                if not str(row.get("claim", "")).strip():
                    errors.append(f"derivation step {idx} missing claim")
                if not str(row.get("equation_or_argument", "")).strip():
                    errors.append(f"derivation step {idx} missing equation_or_argument")
        equation_chain = derivation.get("equation_chain", [])
        if not isinstance(equation_chain, list) or len(equation_chain) < THEORY_MIN_EQUATION_CHAIN_STEPS:
            errors.append(
                "theory_derivation_packet.equation_chain must contain at least "
                f"{THEORY_MIN_EQUATION_CHAIN_STEPS} equation rows"
            )
        else:
            for idx, row in enumerate(equation_chain, start=1):
                if not isinstance(row, Mapping):
                    errors.append("theory_derivation_packet.equation_chain entries must be objects")
                    continue
                if not str(row.get("lhs", "")).strip() or not str(row.get("rhs", "")).strip():
                    errors.append(f"equation_chain row {idx} must include lhs and rhs")
                if not str(row.get("justification", "")).strip():
                    errors.append(f"equation_chain row {idx} missing justification")
        assumption_ledger = derivation.get("assumption_ledger", [])
        if not isinstance(assumption_ledger, list) or not assumption_ledger:
            errors.append("theory_derivation_packet.assumption_ledger must be non-empty")
        else:
            for idx, row in enumerate(assumption_ledger, start=1):
                if not isinstance(row, Mapping):
                    errors.append("theory_derivation_packet.assumption_ledger entries must be objects")
                    continue
                if not str(row.get("assumption", "")).strip():
                    errors.append(f"assumption_ledger row {idx} missing assumption")
                if not row.get("used_in"):
                    errors.append(f"assumption_ledger row {idx} missing used_in")
        formalization_handoff = derivation.get("formalization_handoff", {})
        if not isinstance(formalization_handoff, Mapping) or not formalization_handoff:
            errors.append("theory_derivation_packet.formalization_handoff must be non-empty")
        elif not formalization_handoff.get("semantic_alignment_constraints"):
            errors.append(
                "theory_derivation_packet.formalization_handoff.semantic_alignment_constraints must be non-empty"
            )
    for list_field in ("estimator_specs", "theorem_cards", "lemma_cards", "formalization_requests"):
        if not isinstance(packet.get(list_field), list) or not packet.get(list_field):
            errors.append(f"{list_field} must be a non-empty list")
    for row in packet.get("theorem_cards", []) or []:
        if not isinstance(row, Mapping):
            errors.append("theorem_cards entries must be objects")
            continue
        if not str(row.get("informal_statement", "")).strip():
            errors.append("theorem card missing informal_statement")
        if not str(row.get("proof_strategy", "")).strip():
            errors.append("theorem card missing proof_strategy")
    if packet.get("proof_evidence_status") != THEORY_DERIVATION_NOT_PROOF_EVIDENCE:
        errors.append("proof_evidence_status must preserve LLM-not-proof boundary")
    if packet.get("kernel_verified") is not False:
        errors.append("LLM theory packet cannot set kernel_verified=true")
    errors.extend(_forbidden_proof_claims(packet))
    return sorted(set(errors))


def _normalize_theory_packet(
    payload: Mapping[str, Any],
    *,
    question: OpenResearchQuestion,
    model: str,
    model_tier: str,
    provider_name: str,
    raw_response: str,
) -> dict[str, Any]:
    body = dict(payload)
    derivation_packet = body.get("theory_derivation_packet")
    if isinstance(derivation_packet, Mapping):
        body["theory_derivation_packet"] = _canonicalize_theory_derivation_packet(
            derivation_packet,
            formalization_requests=body.get("formalization_requests", []),
        )
    body["proof_evidence_status"] = THEORY_DERIVATION_NOT_PROOF_EVIDENCE
    body["proof_evidence_boundary"] = KERNEL_PROOF_BOUNDARY
    body["kernel_verified"] = False
    body["verified_theorem_count"] = 0
    derivation = (
        body.get("theory_derivation_packet", {})
        if isinstance(body.get("theory_derivation_packet", {}), Mapping)
        else {}
    )
    body["theory_derivation_contract"] = {
        "min_derivation_steps": THEORY_MIN_DERIVATION_STEPS,
        "min_equation_chain_steps": THEORY_MIN_EQUATION_CHAIN_STEPS,
        "n_derivation_steps": _safe_len(derivation.get("derivation_steps", [])),
        "n_equation_chain_steps": _safe_len(derivation.get("equation_chain", [])),
        "n_assumption_ledger_rows": _safe_len(derivation.get("assumption_ledger", [])),
        "has_formalization_handoff": bool(
            isinstance(derivation.get("formalization_handoff", {}), Mapping)
            and derivation.get("formalization_handoff")
        ),
        "proof_evidence_status": THEORY_DERIVATION_NOT_PROOF_EVIDENCE,
        "boundary": (
            "Theory derivation traces are structured LLM reasoning proposals for "
            "simulation/formalization handoff, not proof evidence."
        ),
    }
    packet_id = stable_hash(
        {
            "question_id": question.id,
            "provider": provider_name,
            "model": model,
            "model_tier": model_tier,
            "body": body,
        }
    )[:24]
    return {
        "schema_version": ARCHITECT_SCHEMA_VERSION,
        "artifact_kind": "TheoryDerivationPacket",
        "packet_id": f"theory_derivation:{packet_id}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_agent": "LLMTheoryDeveloperAgent",
        "provider": provider_name,
        "model": model,
        "model_tier": model_tier,
        "question": {
            "id": question.id,
            "title": question.title,
            "description": question.description,
            "tags": list(question.tags),
        },
        "raw_response_fingerprint": stable_hash(raw_response),
        **body,
    }


def _canonicalize_theory_derivation_packet(
    derivation: Mapping[str, Any],
    *,
    formalization_requests: Any,
) -> dict[str, Any]:
    packet = dict(derivation)
    packet["derivation_steps"] = [
        _canonicalize_derivation_step(row, index)
        for index, row in enumerate(packet.get("derivation_steps", []) or [], start=1)
        if isinstance(row, Mapping)
    ]
    packet["equation_chain"] = [
        _canonicalize_equation_row(row, index)
        for index, row in enumerate(packet.get("equation_chain", []) or [], start=1)
        if isinstance(row, Mapping)
    ]
    derivation_step_ids = [
        str(row.get("id", "") or "").strip()
        for row in packet["derivation_steps"]
        if str(row.get("id", "") or "").strip()
    ]
    packet["assumption_ledger"] = [
        _canonicalize_assumption_row(row, derivation_step_ids)
        for row in packet.get("assumption_ledger", []) or []
        if isinstance(row, Mapping)
    ]
    handoff = packet.get("formalization_handoff", {})
    if not isinstance(handoff, Mapping) or not handoff:
        handoff = _formalization_handoff_from_requests(formalization_requests)
    packet["formalization_handoff"] = dict(handoff) if isinstance(handoff, Mapping) else {}
    return packet


def _canonicalize_derivation_step(row: Mapping[str, Any], index: int) -> dict[str, Any]:
    canonical = dict(row)
    canonical["id"] = _first_nonempty(row, "id", "step_id", "name") or f"D{index}"
    canonical["claim"] = _first_nonempty(
        row,
        "claim",
        "statement",
        "result",
        "goal",
        "description",
        "summary",
    )
    canonical["equation_or_argument"] = _first_nonempty(
        row,
        "equation_or_argument",
        "argument",
        "equation",
        "justification",
        "reasoning",
        "derivation",
        "proof_idea",
    )
    return canonical


def _canonicalize_equation_row(row: Mapping[str, Any], index: int) -> dict[str, Any]:
    canonical = dict(row)
    canonical["step_id"] = _first_nonempty(row, "step_id", "id", "name") or f"E{index}"
    canonical["lhs"] = _first_nonempty(row, "lhs", "left", "from", "start")
    canonical["rhs"] = _first_nonempty(row, "rhs", "right", "to", "end")
    canonical["justification"] = _first_nonempty(
        row,
        "justification",
        "reason",
        "argument",
        "because",
        "explanation",
    )
    return canonical


def _canonicalize_assumption_row(
    row: Mapping[str, Any],
    derivation_step_ids: list[str],
) -> dict[str, Any]:
    canonical = dict(row)
    canonical["assumption"] = _first_nonempty(
        row,
        "assumption",
        "name",
        "label",
        "condition",
        "statement",
        "description",
    )
    used_in = row.get("used_in")
    if not used_in:
        used_in = row.get("used_by") or row.get("supports") or row.get("depends_on")
    if not used_in and derivation_step_ids:
        used_in = derivation_step_ids[:2]
        canonical["used_in_inferred_by_runtime"] = True
    canonical["used_in"] = used_in
    return canonical


def _formalization_handoff_from_requests(requests: Any) -> dict[str, Any]:
    request_rows = [row for row in (requests or []) if isinstance(row, Mapping)]
    first = request_rows[0] if request_rows else {}
    target = _first_nonempty(first, "target_theorem_card", "id", "target", "name")
    lean_target = _first_nonempty(
        first,
        "lean_statement_sketch",
        "lean_statement",
        "statement",
        "target",
    )
    constraints = first.get("semantic_alignment_constraints", [])
    if isinstance(constraints, str):
        constraints = [constraints]
    if not constraints:
        constraints = [
            "preserve the informal theorem semantics; local Lean kernel evidence is required before proof claims"
        ]
    return {
        "source_theorem_target": target,
        "candidate_lean_targets": [lean_target] if lean_target else [],
        "required_definitions": [],
        "lemma_dependencies": [],
        "semantic_alignment_constraints": list(constraints),
        "runtime_inferred_from_formalization_requests": True,
    }


def _first_nonempty(row: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        value = row.get(key)
        if value not in (None, "", [], {}):
            return value
    return ""


def research_loop_theory_repair_context(
    item: Mapping[str, Any],
    report: ResearchReport,
) -> dict[str, Any]:
    return {
        "mode": "research_loop_theory_repair",
        "failed_agenda_item": dict(item),
        "problem": {
            "question_id": report.problem.question_id,
            "problem_class": report.problem.problem_class,
            "dgp": report.problem.dgp,
            "estimand": report.problem.estimand,
            "assumptions": list(report.problem.assumptions),
            "asymptotic_regime": report.problem.asymptotic_regime,
            "diagnostics": list(report.problem.diagnostics),
            "stress_tests": list(report.problem.stress_tests),
        },
        "current_procedures": [
            {
                "id": row.id,
                "name": row.name,
                "role": row.role,
                "formula": row.formula,
                "informal_derivation": row.informal_derivation,
                "algorithm": row.algorithm,
                "theorem_goals": list(row.theorem_goals),
                "limitations": list(row.limitations),
            }
            for row in report.procedures
        ],
        "current_theorem_goals": [
            {
                "id": row.id,
                "title": row.title,
                "informal_statement": row.informal_statement,
                "proof_strategy": row.proof_strategy,
                "status": row.status,
                "required_primitives": list(row.required_primitives),
                "proof_obligations": list(row.proof_obligations),
            }
            for row in report.theorem_goals
        ],
        "formal_subclaims": [
            {
                "id": row.id,
                "title": row.title,
                "status": row.status,
                "claim_type": row.claim_type,
                "kernel_verified": row.kernel_verified,
                "gap_reason": row.gap_reason,
                "errors": list(row.errors),
            }
            for row in report.formal_subclaims
        ],
        "simulation_feedback": [
            {
                "procedure_id": row.procedure_id,
                "design": row.design,
                "passed": row.passed,
                "feedback": row.feedback,
                "metrics": dict(row.metrics),
                "stress_tests": list(row.stress_tests),
                "diagnosis": (
                    {
                        "status": row.diagnosis.status,
                        "escalate_to": row.diagnosis.escalate_to,
                        "failed_diagnostics": list(row.diagnosis.failed_diagnostics),
                        "failed_stress_tests": list(row.diagnosis.failed_stress_tests),
                        "rationale": row.diagnosis.rationale,
                        "metric_evidence": dict(row.diagnosis.metric_evidence),
                    }
                    if row.diagnosis is not None
                    else None
                ),
            }
            for row in report.simulations
        ],
        "required_output": (
            "Return a derivation that can be converted into a theory_revision_from_simulation_failure "
            "repair artifact with revised_procedure, revised_theorem_goals, assumption_delta, "
            "expected_simulation_delta, and next formalization obligations."
        ),
    }


def theory_revision_artifact_from_packet(
    packet: Mapping[str, Any],
    *,
    item: Mapping[str, Any],
    report: ResearchReport,
) -> dict[str, Any]:
    estimator_specs = [
        row for row in packet.get("estimator_specs", []) or [] if isinstance(row, Mapping)
    ]
    theorem_cards = [
        row for row in packet.get("theorem_cards", []) or [] if isinstance(row, Mapping)
    ]
    formalization_requests = [
        row
        for row in packet.get("formalization_requests", []) or []
        if isinstance(row, Mapping)
    ]
    problem_card = packet.get("problem_card", {}) if isinstance(packet.get("problem_card"), Mapping) else {}
    simulation_spec = (
        packet.get("simulation_ademp_spec", {})
        if isinstance(packet.get("simulation_ademp_spec"), Mapping)
        else {}
    )
    target_procedure = str(item.get("target_procedure", "")) or _first_procedure_id(report)
    first_estimator = estimator_specs[0] if estimator_specs else {}
    revised_procedure = _safe_identifier(
        str(first_estimator.get("id") or first_estimator.get("name") or target_procedure or "llm_theory_revision")
    )
    if not revised_procedure.endswith("_llm_theory_revision"):
        revised_procedure = f"{revised_procedure}_llm_theory_revision"
    revised_theorem_goals = [
        _safe_identifier(str(row.get("id") or row.get("conclusion") or "llm_theory_goal"))
        for row in theorem_cards
    ]
    assumption_delta = [
        str(row)
        for row in problem_card.get("assumptions", []) or []
        if str(row).strip()
    ]
    next_formal_obligations = [
        _safe_identifier(str(row.get("id") or row.get("target_theorem_card") or "llm_formalization_request"))
        for row in formalization_requests
    ]
    expected_simulation_delta = "; ".join(
        str(row)
        for row in simulation_spec.get("expected_theoretical_behavior", []) or []
        if str(row).strip()
    )
    if not expected_simulation_delta:
        expected_simulation_delta = str(
            packet.get("theory_derivation_packet", {}).get("derivation_summary", "")
            if isinstance(packet.get("theory_derivation_packet"), Mapping)
            else ""
        )
    return {
        "revision_kind": "llm_theory_developer_derivation",
        "target_procedure": target_procedure,
        "revised_procedure": revised_procedure,
        "revised_theorem_goals": [row for row in revised_theorem_goals if row],
        "assumption_delta": assumption_delta,
        "expected_simulation_delta": expected_simulation_delta
        or "LLM TheoryDeveloper expects revised theorem/procedure diagnostics to improve on rerun.",
        "next_formal_obligations": [row for row in next_formal_obligations if row],
        "failed_diagnostics": list(item.get("failed_diagnostics", []) or []),
        "failed_stress_tests": list(item.get("failed_stress_tests", []) or []),
        "failure_class": "llm_theory_revision_from_simulation_failure",
        "algorithm_unchanged": True,
        "full_theorem_proved": False,
        "kernel_verified": False,
        "proof_evidence_status": THEORY_DERIVATION_NOT_PROOF_EVIDENCE,
        "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
        "llm_theory_derivation_packet_id": str(packet.get("packet_id", "")),
        "llm_theory_derivation_packet": dict(packet),
    }


def write_theory_repair_artifacts(
    packet: Mapping[str, Any],
    repair_artifact: Mapping[str, Any],
    *,
    out_dir: Path,
    question: OpenResearchQuestion,
) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    packet_path = out_dir / "theory_derivation_packet.json"
    artifact_path = out_dir / "theory_repair_artifact.json"
    ledger_path = out_dir / "evidence_ledger.jsonl"
    manifest_path = out_dir / "llm_theory_repair_manifest.json"
    packet_path.write_text(json.dumps(packet, indent=2, default=str), encoding="utf-8")
    artifact_path.write_text(json.dumps(repair_artifact, indent=2, default=str), encoding="utf-8")
    ledger = asdict(_ledger_row_for_packet(packet, question))
    _write_jsonl(ledger_path, [ledger])
    manifest = {
        "schema_version": ARCHITECT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "question_id": question.id,
        "packet_id": packet.get("packet_id", ""),
        "repair_artifact_kind": "theory_revision_from_simulation_failure",
        "repair_contract_fields": [
            "revised_procedure",
            "revised_theorem_goals",
            "assumption_delta",
            "expected_simulation_delta",
        ],
        "proof_evidence_status": THEORY_DERIVATION_NOT_PROOF_EVIDENCE,
        "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
        "artifacts": {
            "packet": str(packet_path),
            "repair_artifact": str(artifact_path),
            "evidence_ledger": str(ledger_path),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    return {
        "manifest": str(manifest_path),
        "packet": str(packet_path),
        "repair_artifact": str(artifact_path),
        "evidence_ledger": str(ledger_path),
    }


def _ledger_row_for_packet(packet: Mapping[str, Any], question: OpenResearchQuestion) -> EvidenceLedgerRow:
    artifact_id = str(packet.get("packet_id", ""))
    return EvidenceLedgerRow(
        evidence_id="evidence:" + stable_hash([question.id, artifact_id])[:20],
        question_id=question.id,
        artifact_id=artifact_id,
        artifact_kind="TheoryDerivationPacket",
        source_agent="LLMTheoryDeveloperAgent",
        evidence_status="PROPOSAL_RECORDED_REQUIRES_GATES",
        proof_evidence_status=THEORY_DERIVATION_NOT_PROOF_EVIDENCE,
        boundary=KERNEL_PROOF_BOUNDARY,
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def _first_procedure_id(report: ResearchReport) -> str:
    return report.procedures[0].id if report.procedures else ""


def _safe_identifier(raw: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_]+", "_", raw.strip())
    value = re.sub(r"_+", "_", value).strip("_")
    if not value:
        return ""
    if value[0].isdigit():
        value = f"g_{value}"
    return value


def _project_state(
    questions: list[OpenResearchQuestion],
    packets: list[dict[str, Any]],
    ledger_rows: list[EvidenceLedgerRow],
) -> dict[str, Any]:
    return {
        "schema_version": ARCHITECT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "state_kind": "ResearchArchitectProjectState",
        "status": "LLM_THEORY_DEVELOPMENT_RECORDED_REQUIRES_VERIFIER_SIMULATION_GATES",
        "questions": [
            {"id": row.id, "title": row.title, "description": row.description, "tags": list(row.tags)}
            for row in questions
        ],
        "active_artifacts": [packet.get("packet_id", "") for packet in packets],
        "evidence_rows": [row.evidence_id for row in ledger_rows],
        "next_required_gates": [
            "source_grounding_review",
            "simulation_ademp_execution",
            "formalization_request_semantic_alignment",
            "AXLE_or_local_Lean_kernel_verification_for_formal_claims",
        ],
        "proof_evidence_status": THEORY_DERIVATION_NOT_PROOF_EVIDENCE,
        "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
    }


def _extract_json_object(text: str) -> dict[str, Any]:
    return extract_json_object(text, label="LLM TheoryDeveloper")


def _forbidden_proof_claims(value: Any, *, path: str = "") -> list[str]:
    errors: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            key_text = str(key).lower()
            if key_text in {"kernel_verified", "lean_verified", "theorem_verified"} and child is True:
                errors.append(f"forbidden proof claim at {child_path}")
            if key_text in {"proof_evidence_status", "kernel_status", "verification_strength"}:
                text = str(child).upper()
                if text in {"PROVED", "VERIFIED", "KERNEL_VERIFIED", "CLOSED"}:
                    errors.append(f"forbidden proof status at {child_path}: {child}")
            errors.extend(_forbidden_proof_claims(child, path=child_path))
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            errors.extend(_forbidden_proof_claims(child, path=f"{path}[{idx}]"))
    return errors


def _write_jsonl(path: Path, rows: list[Mapping[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, default=str, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _markdown_report(manifest: Mapping[str, Any], packets: list[Mapping[str, Any]]) -> str:
    lines = [
        "# Research Architect Theory Development",
        "",
        f"- Questions: {manifest.get('n_questions')}",
        f"- Theory packets: {manifest.get('n_theory_derivation_packets')}",
        f"- Proof evidence: `{THEORY_DERIVATION_NOT_PROOF_EVIDENCE}`",
        "",
        "## Packets",
        "",
    ]
    for packet in packets:
        question = packet.get("question", {}) if isinstance(packet.get("question"), Mapping) else {}
        lines.append(f"- `{packet.get('packet_id', '')}` for `{question.get('id', '')}`")
        for theorem in packet.get("theorem_cards", []) or []:
            if isinstance(theorem, Mapping):
                lines.append(f"  - theorem `{theorem.get('id', '')}`: {theorem.get('conclusion', '')}")
    lines.extend(["", "## Boundary", "", KERNEL_PROOF_BOUNDARY, ""])
    return "\n".join(lines)
