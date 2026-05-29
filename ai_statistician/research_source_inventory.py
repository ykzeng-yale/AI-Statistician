from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from .fingerprint import stable_hash

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEGACY_AI_STATISTICIAN_ROOT = PROJECT_ROOT / "legacy_sources" / "ai_statistician"
VENDORED_EMPIRICAL_PROCESS_ROOT = PROJECT_ROOT / "legacy_sources" / "emperical_process_lean"


@dataclass(frozen=True)
class SourceInventoryTarget:
    id: str
    source_type: str
    location: str
    required_extensions: tuple[str, ...]
    keywords: tuple[str, ...]


@dataclass(frozen=True)
class SourceInventoryRow:
    source_id: str
    source_type: str
    location: str
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
)


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
    return SourceInventoryRow(
        source_id=target.id,
        source_type=target.source_type,
        location=target.location,
        exists=True,
        n_files=len(files),
        extension_counts=dict(sorted(extension_counts.items())),
        keyword_hits=dict(sorted(keyword_hits.items())),
        sample_files=sample_files,
        ok=not errors,
        errors=tuple(errors),
    )


def _markdown_report(payload: dict[str, object]) -> str:
    rows = payload.get("rows", [])
    lines = [
        "# Research Source Inventory",
        "",
        f"- Sources: {payload.get('n_ok')}/{payload.get('n_sources')} inventory-clean",
        f"- Fingerprint: `{payload.get('inventory_fingerprint')}`",
        "",
        "| Source | Type | OK | Files | Extension counts | Keyword hits |",
        "|---|---|---:|---:|---|---|",
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
            f"| `{row.get('source_id')}` | {row.get('source_type')} | {row.get('ok')} | "
            f"{row.get('n_files')} | {ext_counts or 'none'} | {hits} |"
        )
        errors = row.get("errors") or []
        for error in errors:
            lines.append(f"| | | | | | Error: {error} |")
    return "\n".join(lines) + "\n"
