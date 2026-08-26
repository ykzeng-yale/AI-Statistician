from __future__ import annotations

import argparse
from pathlib import Path

import ai_statistician
from ai_statistician.cli import build_parser
from ai_statistician.model_backend import (
    ALLOWED_LIVE_ANTHROPIC_MODEL_TIERS,
    LIVE_EVALUATION_CLAUDE_MODEL,
    LIVE_EVALUATION_CLAUDE_MODEL_TIER,
    PROHIBITED_LIVE_ANTHROPIC_MODEL_TIERS,
)


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "ai_statistician"

RETIRED_MODULE_PREFIXES = (
    "exact_semantic_definition_",
    "exact_source_theorem_proof_body_",
    "formalization_gap_planner_",
    "pseudo_formal",
    "source_semantic_proofengineer_",
    "source_theorem_exact_semantic_definition_",
    "source_theorem_promotion_",
    "source_theorem_proof_body_adapter_",
    "source_theorem_semantic_primitive_",
    "theorem_reduction_closure_",
    "research_next_iteration_audit",
)

RETIRED_CLI_COMMANDS = {
    "research-system-audit",
    "formalization-gap-planner",
    "formalization-gap-planner-evaluation",
    "formalization-gap-planner-interactive-session",
    "next-iteration-audit",
}


def _subcommands(parser: argparse.ArgumentParser) -> set[str]:
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return set(action.choices)
    raise AssertionError("CLI parser has no subcommands")


def test_package_imports_from_this_checkout() -> None:
    package_path = Path(ai_statistician.__file__).resolve()

    assert package_path.is_relative_to(PACKAGE)


def test_retired_parallel_formalization_planes_are_absent() -> None:
    module_names = {path.stem for path in PACKAGE.glob("*.py")}

    leftovers = {
        name
        for name in module_names
        if any(name.startswith(prefix) for prefix in RETIRED_MODULE_PREFIXES)
    }
    assert leftovers == set()


def test_cli_exposes_canonical_runtime_without_retired_control_planes() -> None:
    commands = _subcommands(build_parser())

    assert {"research-agent-runtime", "research-agent-runtime-audit"} <= commands
    assert commands.isdisjoint(RETIRED_CLI_COMMANDS)


def test_canonical_control_plane_has_a_regression_budget() -> None:
    runtime_lines = (PACKAGE / "research_agent_runtime.py").read_text(
        encoding="utf-8"
    ).count("\n")
    cli_lines = (PACKAGE / "cli.py").read_text(encoding="utf-8").count("\n")
    package_sources = tuple(PACKAGE.glob("*.py"))
    package_lines = sum(
        path.read_text(encoding="utf-8").count("\n") for path in package_sources
    )
    production_design_lines = (
        ROOT / "docs" / "production_design.md"
    ).read_text(encoding="utf-8").count("\n")

    assert runtime_lines < 25_000
    assert cli_lines < 8_000
    assert len(package_sources) < 150
    assert package_lines < 150_000
    assert production_design_lines < 400


def test_canonical_runtime_does_not_restore_retired_routing_surfaces() -> None:
    runtime_source = (PACKAGE / "research_agent_runtime.py").read_text(
        encoding="utf-8"
    )
    forbidden = {
        "_architect_post_result_metric_protocol_revision_result",
        "metric_protocol_max_fresh_candidate_revisions",
        "RuntimeProofStateFeedbackManifest",
        "RuntimeFormalizerLeanCandidateProofStateFeedbackManifest",
    }

    assert not {needle for needle in forbidden if needle in runtime_source}


def test_live_model_policy_forbids_opus_and_pins_evaluation_to_haiku() -> None:
    assert ALLOWED_LIVE_ANTHROPIC_MODEL_TIERS == {"haiku", "sonnet"}
    assert PROHIBITED_LIVE_ANTHROPIC_MODEL_TIERS == {"opus"}
    assert LIVE_EVALUATION_CLAUDE_MODEL_TIER == "haiku"
    assert LIVE_EVALUATION_CLAUDE_MODEL == "claude-haiku-4-5-20251001"


def test_source_authoring_path_contains_no_benchmark_family_policy() -> None:
    source_paths = (
        PACKAGE / "research_agent_runtime.py",
        PACKAGE / "formalizer_llm.py",
        PACKAGE / "lean_candidate_revision_tool_loop.py",
        PACKAGE / "formal_source_prompt_context.py",
        PACKAGE / "lean_kernel_promotion.py",
    )
    forbidden = (
        "split_conformal",
        "benjamini_hochberg",
        "kaplan_meier",
        "spiked_pca",
        "hill_estimator",
    )

    sources = "\n".join(path.read_text(encoding="utf-8").lower() for path in source_paths)
    assert not {needle for needle in forbidden if needle in sources}
