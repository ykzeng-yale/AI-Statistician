from __future__ import annotations

import json
import os
import subprocess
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from .fingerprint import stable_hash

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEGACY_AI_STATISTICIAN_ROOT = PROJECT_ROOT / "legacy_sources" / "ai_statistician"
VENDORED_EMPIRICAL_PROCESS_ROOT = PROJECT_ROOT / "legacy_sources" / "emperical_process_lean"
USER_ATLAS_LEAN_ROOT = Path("/Users/yukang/.codex/external/ykzeng-atlas-lean")
UPSTREAM_ATLAS_LEAN_ROOT = Path("/Users/yukang/.codex/external/atlas-lean")
USER_AUTOFORM_BOT_ROOT = Path("/Users/yukang/.codex/external/ykzeng-autoform-bot")
UPSTREAM_AUTOFORM_BOT_ROOT = Path("/Users/yukang/.codex/external/autoform-bot")
ATLAS_LEAN_ROOT = USER_ATLAS_LEAN_ROOT if USER_ATLAS_LEAN_ROOT.exists() else UPSTREAM_ATLAS_LEAN_ROOT
AUTOFORM_BOT_ROOT = USER_AUTOFORM_BOT_ROOT if USER_AUTOFORM_BOT_ROOT.exists() else UPSTREAM_AUTOFORM_BOT_ROOT
FORMAL_SLT_ROOT = Path("/Users/yukang/.codex/external/FormalSLT")
LEAN_RADEMACHER_ROOT = Path("/Users/yukang/.codex/external/lean-rademacher")
LEAN_MACHINE_LEARNING_ROOT = Path("/Users/yukang/.codex/external/LeanMachineLearning-LML")
BROWNIAN_MOTION_ROOT = Path("/Users/yukang/.codex/external/brownian-motion")
KOLMOGOROV_EXTENSION_ROOT = Path("/Users/yukang/.codex/external/kolmogorov_extension4")
SCILEAN_ROOT = Path("/Users/yukang/.codex/external/SciLean")
LEAN_BLUEPRINT_ROOT = Path("/Users/yukang/.codex/external/leanblueprint")


@dataclass(frozen=True)
class SourceInventoryTarget:
    id: str
    source_type: str
    location: str
    required_extensions: tuple[str, ...]
    keywords: tuple[str, ...]
    license_policy: str = "unspecified"
    usage_policy: str = "retrieval_and_training_allowed"


@dataclass(frozen=True)
class SourceInventoryRow:
    source_id: str
    source_type: str
    location: str
    license_policy: str
    usage_policy: str
    git_commit: str
    remote_url: str
    exists: bool
    n_files: int
    extension_counts: dict[str, int]
    keyword_hits: dict[str, int]
    sample_files: tuple[str, ...]
    ok: bool
    errors: tuple[str, ...] = ()


SOURCE_INVENTORY_TARGETS: tuple[SourceInventoryTarget, ...] = (
    SourceInventoryTarget(
        id="ai_for_math_resources",
        source_type="paper_collection",
        location=str(PROJECT_ROOT / "AI for Math Resources"),
        required_extensions=(".md", ".html", ".json", ".txt"),
        keywords=("formal", "verification", "lean", "reprover", "alpha", "math"),
    ),
    SourceInventoryTarget(
        id="mathlib_probability",
        source_type="lean_library",
        location="/Users/yukang/LeanProjects/LeanPractice/.lake/packages/mathlib/Mathlib/Probability",
        required_extensions=(".lean",),
        keywords=("CentralLimit", "Variance", "Independence", "BorelCantelli", "Martingale", "Kernel"),
    ),
    SourceInventoryTarget(
        id="mathlib_measure_theory",
        source_type="lean_library",
        location="/Users/yukang/LeanProjects/LeanPractice/.lake/packages/mathlib/Mathlib/MeasureTheory",
        required_extensions=(".lean",),
        keywords=("Integral", "Function", "Conditional", "Measure", "Lp", "Decomposition"),
    ),
    SourceInventoryTarget(
        id="empirical_process_lean",
        source_type="lean_library",
        location=str(VENDORED_EMPIRICAL_PROCESS_ROOT),
        required_extensions=(".lean",),
        keywords=(
            "StatInference",
            "AsymptoticStatistics",
            "EmpiricalProcess",
            "ProbabilityMeasure",
            "ProbabilityTheory",
            "Rademacher",
            "BackwardMartingale",
        ),
    ),
    SourceInventoryTarget(
        id="local_statinference_repo",
        source_type="lean_library",
        location="/Users/yukang/.codex/wdsm-lean-gate/StatInference",
        required_extensions=(".lean",),
        keywords=("Bias", "Variance", "Godambe", "Bootstrap", "Studentized", "Martingale"),
    ),
    SourceInventoryTarget(
        id="lean_stat_learning_theory",
        source_type="lean_library",
        location="/Users/yukang/.codex/external/lean-stat-learning-theory",
        required_extensions=(".lean",),
        keywords=("Covering", "SubGaussian", "LeastSquares", "Gaussian", "Concentration", "Poincare"),
    ),
    SourceInventoryTarget(
        id="formal_slt",
        source_type="lean_library",
        location=str(FORMAL_SLT_ROOT / "FormalSLT"),
        required_extensions=(".lean",),
        keywords=(
            "Rademacher",
            "ERM",
            "PAC",
            "VC",
            "Azuma",
            "SubGamma",
            "AlgorithmicStability",
            "Dudley",
        ),
        license_policy="MIT",
    ),
    SourceInventoryTarget(
        id="lean_rademacher",
        source_type="lean_library",
        location=str(LEAN_RADEMACHER_ROOT / "FoML"),
        required_extensions=(".lean",),
        keywords=("Rademacher", "McDiarmid", "Dudley", "Massart", "Hoeffding", "LinearPredictor"),
        license_policy="MIT",
    ),
    SourceInventoryTarget(
        id="lean_machine_learning_lml",
        source_type="lean_library",
        location=str(LEAN_MACHINE_LEARNING_ROOT / "LeanMachineLearning"),
        required_extensions=(".lean",),
        keywords=("Bandit", "Regret", "UCB", "ExploreThenCommit", "Stochastic", "Algorithm"),
        license_policy="Apache-2.0",
    ),
    SourceInventoryTarget(
        id="brownian_motion_lean",
        source_type="lean_library",
        location=str(BROWNIAN_MOTION_ROOT / "BrownianMotion"),
        required_extensions=(".lean",),
        keywords=("Brownian", "Gaussian", "Kolmogorov", "Chentsov", "StochasticIntegral", "Ito"),
        license_policy="Apache-2.0",
        usage_policy="retrieval_only_no_training_export",
    ),
    SourceInventoryTarget(
        id="kolmogorov_extension_lean",
        source_type="lean_library",
        location=str(KOLMOGOROV_EXTENSION_ROOT / "KolmogorovExtension4"),
        required_extensions=(".lean",),
        keywords=("Kolmogorov", "Projective", "Measure", "CompactSystem", "Extension", "RegularContent"),
        license_policy="Apache-2.0",
    ),
    SourceInventoryTarget(
        id="scilean_calculus",
        source_type="lean_library",
        location=str(SCILEAN_ROOT / "SciLean"),
        required_extensions=(".lean",),
        keywords=("derivative", "gradient", "jacobian", "Optimization", "Gaussian", "RnDeriv"),
        license_policy="Apache-2.0",
        usage_policy="retrieval_only_no_training_export",
    ),
    SourceInventoryTarget(
        id="legacy_ai_statistician_statinference",
        source_type="lean_library",
        location=str(LEGACY_AI_STATISTICIAN_ROOT / "StatInference"),
        required_extensions=(".lean",),
        keywords=("Asymptotic", "Estimator", "EmpiricalProcess", "Causal", "Semiparametric", "WDSM"),
    ),
    SourceInventoryTarget(
        id="legacy_ai_statistician_benchmarks",
        source_type="benchmark_corpus",
        location=str(LEGACY_AI_STATISTICIAN_ROOT / "benchmarks"),
        required_extensions=(".jsonl", ".md"),
        keywords=("benchmarks", "seeds", "README"),
    ),
    SourceInventoryTarget(
        id="legacy_ai_statistician_schemas",
        source_type="schema_corpus",
        location=str(LEGACY_AI_STATISTICIAN_ROOT / "schemas"),
        required_extensions=(".json",),
        keywords=("lean_task", "proof_attempt", "benchmark_task", "verification_report"),
    ),
    SourceInventoryTarget(
        id="legacy_ai_statistician_training_artifacts",
        source_type="training_artifacts",
        location=str(LEGACY_AI_STATISTICIAN_ROOT / "artifacts" / "training"),
        required_extensions=(".json", ".jsonl"),
        keywords=("dpo", "grpo", "premise", "reward", "attempt"),
    ),
    SourceInventoryTarget(
        id="leansearch_client",
        source_type="lean_library",
        location="/Users/yukang/Axiom Interview/.lake/packages/LeanSearchClient",
        required_extensions=(".lean",),
        keywords=("LeanSearchClient", "Loogle", "leansearch", "statesearch", "TryThis"),
    ),
    SourceInventoryTarget(
        id="leandojo_v2_local",
        source_type="prover_pipeline",
        location="/Users/yukang/Desktop/AI for Math/Axiom Code Practice/external/LeanDojo-v2",
        required_extensions=(".py", ".md"),
        keywords=("lean_dojo_v2", "retrieval", "prover", "trainer", "GRPO", "LeanProgress"),
    ),
    SourceInventoryTarget(
        id="openprover_pipeline",
        source_type="prover_pipeline",
        location="/Users/yukang/Documents/OpenProver",
        required_extensions=(".py",),
        keywords=("retrieval", "search", "trace", "verifier", "ablation", "policy"),
    ),
    SourceInventoryTarget(
        id="atlas_lean_repository",
        source_type="formal_source_collection",
        location=str(ATLAS_LEAN_ROOT),
        required_extensions=(".lean", ".json", ".yaml", ".md"),
        keywords=("HighDimensionalStatistics", "TheoryOfProbability", "targets", "report", "Atlas"),
        license_policy="CC-BY-NC-4.0-no-training-rider",
        usage_policy="retrieval_only_no_training_export",
    ),
    SourceInventoryTarget(
        id="atlas_lean_high_dimensional_statistics",
        source_type="lean_library",
        location=str(ATLAS_LEAN_ROOT / "Atlas" / "HighDimensionalStatistics"),
        required_extensions=(".lean",),
        keywords=("HighDimensionalStatistics", "Chapter1", "Chapter2", "SubGaussian", "Bernstein", "Fano"),
        license_policy="CC-BY-NC-4.0-no-training-rider",
        usage_policy="retrieval_only_no_training_export",
    ),
    SourceInventoryTarget(
        id="atlas_lean_theory_of_probability",
        source_type="lean_library",
        location=str(ATLAS_LEAN_ROOT / "Atlas" / "TheoryOfProbability"),
        required_extensions=(".lean",),
        keywords=("TheoryOfProbability", "BorelCantelli", "CLT", "Martingale", "Conditional", "WeakConvergence"),
        license_policy="CC-BY-NC-4.0-no-training-rider",
        usage_policy="retrieval_only_no_training_export",
    ),
    SourceInventoryTarget(
        id="atlas_lean_probabilistic_methods",
        source_type="lean_library",
        location=str(ATLAS_LEAN_ROOT / "Atlas" / "ProbabilisticMethodsInCombinatorics"),
        required_extensions=(".lean",),
        keywords=("ProbabilisticMethodsInCombinatorics", "concentration", "random", "probability", "expectation"),
        license_policy="CC-BY-NC-4.0-no-training-rider",
        usage_policy="retrieval_only_no_training_export",
    ),
    SourceInventoryTarget(
        id="atlas_lean_analysis_foundations",
        source_type="lean_library",
        location=str(ATLAS_LEAN_ROOT / "Atlas" / "RealAnalysis"),
        required_extensions=(".lean",),
        keywords=("RealAnalysis", "sequence", "limit", "continuity", "compact"),
        license_policy="CC-BY-NC-4.0-no-training-rider",
        usage_policy="retrieval_only_no_training_export",
    ),
    SourceInventoryTarget(
        id="atlas_lean_fourier_analysis",
        source_type="lean_library",
        location=str(ATLAS_LEAN_ROOT / "Atlas" / "FourierAnalysis"),
        required_extensions=(".lean",),
        keywords=("FourierAnalysis", "CharacteristicFunction", "CentralLimitTheorem", "WeakConvergence", "BrownianMotion"),
        license_policy="CC-BY-NC-4.0-no-training-rider",
        usage_policy="retrieval_only_no_training_export",
    ),
    SourceInventoryTarget(
        id="atlas_lean_functional_analysis",
        source_type="lean_library",
        location=str(ATLAS_LEAN_ROOT / "Atlas" / "IntroductionToFunctionalAnalysis"),
        required_extensions=(".lean",),
        keywords=("BanachSpace", "HilbertSpace", "CauchySchwarz", "Riesz", "Projection"),
        license_policy="CC-BY-NC-4.0-no-training-rider",
        usage_policy="retrieval_only_no_training_export",
    ),
    SourceInventoryTarget(
        id="atlas_lean_differential_analysis",
        source_type="lean_library",
        location=str(ATLAS_LEAN_ROOT / "Atlas" / "DifferentialAnalysis"),
        required_extensions=(".lean",),
        keywords=("DifferentialAnalysis", "Frechet", "Taylor", "Sobolev", "Fourier"),
        license_policy="CC-BY-NC-4.0-no-training-rider",
        usage_policy="retrieval_only_no_training_export",
    ),
    SourceInventoryTarget(
        id="atlas_lean_projection_theory",
        source_type="lean_library",
        location=str(ATLAS_LEAN_ROOT / "Atlas" / "ProjectionTheory"),
        required_extensions=(".lean",),
        keywords=("ProjectionTheory", "orthogonalProjection", "large_sieve", "grid_projection", "Furstenberg"),
        license_policy="CC-BY-NC-4.0-no-training-rider",
        usage_policy="retrieval_only_no_training_export",
    ),
    SourceInventoryTarget(
        id="autoform_bot_harness",
        source_type="autoformalization_harness",
        location=str(AUTOFORM_BOT_ROOT),
        required_extensions=(".py", ".md", ".toml"),
        keywords=(
            "statement_extraction",
            "lean_checks",
            "proof_checker",
            "dependency_graph",
            "repl",
            "bot",
            "eval",
            "visualizer",
        ),
        license_policy="CC-BY-NC-4.0",
        usage_policy="integration_reference_no_training_export",
    ),
    SourceInventoryTarget(
        id="lean_blueprint",
        source_type="formalization_blueprint_tool",
        location=str(LEAN_BLUEPRINT_ROOT),
        required_extensions=(".py", ".md", ".tex", ".sty", ".yml"),
        keywords=(
            "leanblueprint",
            "blueprint",
            "dependency",
            "leanok",
            "notready",
            "mathlibok",
            "graphcolor",
        ),
        license_policy="Apache-2.0",
        usage_policy="integration_reference_no_training_export",
    ),
)


NO_TRAINING_EXPORT_SOURCE_IDS: frozenset[str] = frozenset(
    target.id
    for target in SOURCE_INVENTORY_TARGETS
    if "no_training_export" in target.usage_policy
)


def source_allows_training_export(source_id: str) -> bool:
    """Return whether artifacts from a source may enter training-data exports.

    Some external formal corpora are valuable retrieval inputs but carry license
    restrictions that prohibit model training/fine-tuning/evaluation. The
    production retriever may use them for local proof planning, but SFT/GRPO
    exporters strip their declaration payloads by default. A project owner can
    explicitly opt in to exporting every registered source by setting
    `AI_STATISTICIAN_INCLUDE_EXTERNAL_TRAINING_SOURCES=1`; this keeps the
    default release artifact conservative while avoiding a hardcoded engineering
    block when an authorized local mirror should be used more broadly.
    """

    if os.environ.get("AI_STATISTICIAN_INCLUDE_EXTERNAL_TRAINING_SOURCES") == "1":
        return True
    return source_id not in NO_TRAINING_EXPORT_SOURCE_IDS


def build_research_source_inventory(
    out_dir: Path | None = None,
    *,
    targets: tuple[SourceInventoryTarget, ...] = SOURCE_INVENTORY_TARGETS,
) -> dict[str, object]:
    rows = [_inventory_target(target) for target in targets]
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "inventory_fingerprint": research_source_inventory_fingerprint(rows),
        "n_sources": len(rows),
        "n_ok": sum(1 for row in rows if row.ok),
        "all_ok": all(row.ok for row in rows),
        "rows": [asdict(row) for row in rows],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "research_source_inventory_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "research_source_inventory.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def research_source_inventory_fingerprint(rows: list[SourceInventoryRow] | None = None) -> str:
    actual_rows = rows if rows is not None else list(_cached_inventory_rows())
    stable_rows = [
        {
            "source_id": row.source_id,
            "source_type": row.source_type,
            "location": row.location,
            "license_policy": row.license_policy,
            "usage_policy": row.usage_policy,
            "git_commit": row.git_commit,
            "remote_url": row.remote_url,
            "exists": row.exists,
            "n_files": row.n_files,
            "extension_counts": row.extension_counts,
            "keyword_hits": row.keyword_hits,
            "ok": row.ok,
        }
        for row in actual_rows
    ]
    return stable_hash(stable_rows)


@lru_cache(maxsize=1)
def _cached_inventory_rows() -> tuple[SourceInventoryRow, ...]:
    return tuple(_inventory_target(target) for target in SOURCE_INVENTORY_TARGETS)


def _inventory_target(target: SourceInventoryTarget) -> SourceInventoryRow:
    root = Path(target.location).expanduser()
    errors: list[str] = []
    if not root.exists():
        return SourceInventoryRow(
            source_id=target.id,
            source_type=target.source_type,
            location=target.location,
            license_policy=target.license_policy,
            usage_policy=target.usage_policy,
            git_commit="",
            remote_url="",
            exists=False,
            n_files=0,
            extension_counts={},
            keyword_hits={},
            sample_files=(),
            ok=False,
            errors=(f"missing path: {root}",),
        )

    files = [path for path in root.rglob("*") if path.is_file()]
    extension_counts = Counter(path.suffix.lower() or "<none>" for path in files)
    required_total = sum(extension_counts.get(ext, 0) for ext in target.required_extensions)
    if required_total == 0:
        errors.append(f"no files with required extensions: {', '.join(target.required_extensions)}")

    keyword_hits: dict[str, int] = {}
    lowered_paths = [str(path.relative_to(root)).lower() for path in files]
    for keyword in target.keywords:
        keyword_hits[keyword] = sum(1 for rel in lowered_paths if keyword.lower() in rel)
    if target.keywords and not any(keyword_hits.values()):
        errors.append("no keyword evidence in file paths")

    sample_files = tuple(
        str(path.relative_to(root))
        for path in sorted(files, key=lambda item: str(item.relative_to(root)))[:12]
    )
    git_commit, remote_url = _git_metadata(root)
    return SourceInventoryRow(
        source_id=target.id,
        source_type=target.source_type,
        location=target.location,
        license_policy=target.license_policy,
        usage_policy=target.usage_policy,
        git_commit=git_commit,
        remote_url=remote_url,
        exists=True,
        n_files=len(files),
        extension_counts=dict(sorted(extension_counts.items())),
        keyword_hits=dict(sorted(keyword_hits.items())),
        sample_files=sample_files,
        ok=not errors,
        errors=tuple(errors),
    )


def _git_metadata(root: Path) -> tuple[str, str]:
    git_root = _nearest_git_root(root)
    if git_root is None:
        return "", ""
    commit = _git_output(git_root, "rev-parse", "HEAD")
    remote = _git_output(git_root, "remote", "get-url", "origin")
    return commit, remote


def _nearest_git_root(root: Path) -> Path | None:
    for candidate in (root, *root.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def _git_output(git_root: Path, *args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(git_root), *args],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5,
        ).strip()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return ""


def _markdown_report(payload: dict[str, object]) -> str:
    rows = payload.get("rows", [])
    lines = [
        "# Research Source Inventory",
        "",
        f"- Sources: {payload.get('n_ok')}/{payload.get('n_sources')} inventory-clean",
        f"- Fingerprint: `{payload.get('inventory_fingerprint')}`",
        "",
        "| Source | Type | Usage | Commit | OK | Files | Extension counts | Keyword hits |",
        "|---|---|---|---|---:|---:|---|---|",
    ]
    for row in rows:
        if not isinstance(row, dict):
            continue
        ext_counts = ", ".join(f"{key}:{value}" for key, value in row.get("extension_counts", {}).items())
        hits = ", ".join(
            f"{key}:{value}"
            for key, value in row.get("keyword_hits", {}).items()
            if value
        ) or "none"
        lines.append(
            f"| `{row.get('source_id')}` | {row.get('source_type')} | "
            f"{row.get('usage_policy', '')} | `{str(row.get('git_commit', ''))[:12]}` | {row.get('ok')} | "
            f"{row.get('n_files')} | {ext_counts or 'none'} | {hits} |"
        )
        errors = row.get("errors") or []
        for error in errors:
            lines.append(f"| | | | | | Error: {error} |")
    return "\n".join(lines) + "\n"
