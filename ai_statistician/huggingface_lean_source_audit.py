from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


HUGGINGFACE_LEAN_SOURCE_AUDIT_SCHEMA_VERSION = 1
HF_API_BASE = "https://huggingface.co/api"

DEFAULT_HF_LEAN_SEARCH_TERMS: tuple[str, ...] = (
    "Lean4",
    "Lean theorem proving",
    "Lean proof",
    "compiler verified Lean",
    "formal mathematics Lean",
    "formal theorem proving Lean4",
    "OProver",
    "OProofs",
    "LeanDojo",
    "NuminaMath LEAN",
    "Lean-GitHub",
    "Lean Workbook",
    "LeanPolish",
    "proof repair Lean",
    "proof compression Lean",
    "ProofNet Lean",
    "miniF2F Lean",
    "PutnamBench Lean",
    "mathlib Lean dataset",
    "analysis Lean4",
    "calculus Lean4",
    "statistics Lean4",
)

PINNED_HF_LEAN_DATASETS: tuple[str, ...] = (
    "m-a-p/OProofs",
    "OProver/OProofs",
    "AI-MO/NuminaMath-LEAN",
    "internlm/Lean-Github",
    "pkuAI4M/lean_github",
    "pkuAI4M/Lean_github_formal_only_1119",
    "pkuAI4M/RAG_lean_github",
    "charliemeyer2000/leandojo_benchmark_lean4_17_0",
    "cat-searcher/leandojo-benchmark-4-random-sft",
    "JohnYang88/lean-dojo-mathlib4",
    "leanpolish-anon/lean-proof-compression",
    "Goedel-LM/Lean-workbook-proofs",
    "banach1729/goedel-workbook-lean427",
    "iiis-lean/NuminaMath-LEAN-Proof-Artifacts",
    "ricdomolm/numinamath-LEAN-trajs-850k",
    "phanerozoic/Lean4-Mathlib",
    "phanerozoic/Lean4-SciLean",
    "phanerozoic/Lean4-CvxLean",
    "phanerozoic/Lean4-PhysLean",
    "liminho123/lean4-stat-learning-theory-corpus",
)

DEFAULT_HF_COLLECTIONS: tuple[str, ...] = ("m-a-p/oprover",)

CURRENT_LOCAL_RAG_SOURCE_MARKERS: tuple[str, ...] = (
    "mathlib",
    "leandojo",
    "openprover",
    "autoform",
    "statinference",
    "empiricalprocesslean",
    "empericalprocesslean",
    "lean-stat-learning-theory",
    "atlas",
)

PROOF_EVIDENCE_BOUNDARY = (
    "Hugging Face Lean datasets are retrieval, training, or benchmark candidates. "
    "A dataset row is not AI-Statistician proof evidence until the concrete Lean "
    "statement/proof is imported or reconstructed and verified locally under the "
    "target Lean toolchain."
)


@dataclass(frozen=True)
class HuggingFaceLeanSourceRow:
    dataset_id: str
    url: str
    sha: str
    last_modified: str
    downloads: int
    likes: int
    private: bool
    gated: bool
    disabled: bool
    license: str
    tags: tuple[str, ...]
    size_categories: tuple[str, ...]
    formats: tuple[str, ...]
    num_rows: int
    used_storage_bytes: int
    parquet_shards: int
    schema_fields: tuple[str, ...]
    source_datasets: tuple[str, ...]
    discovered_by: tuple[str, ...]
    relevance_class: str
    retrieval_role: str
    priority: str
    integration_status: str
    trust_policy: str
    usage_policy: str
    rationale: str


def audit_huggingface_lean_sources(
    out_dir: Path,
    *,
    search_terms: tuple[str, ...] = DEFAULT_HF_LEAN_SEARCH_TERMS,
    pinned_dataset_ids: tuple[str, ...] = PINNED_HF_LEAN_DATASETS,
    collection_slugs: tuple[str, ...] = DEFAULT_HF_COLLECTIONS,
    max_results_per_query: int = 100,
    max_detail_fetches: int = 140,
    timeout_s: int = 20,
    use_network: bool = True,
    offline_payloads: dict[str, Any] | None = None,
) -> dict[str, object]:
    """Discover high-value Hugging Face Lean corpora for local RAG reuse.

    The audit writes a ranked manifest and report. It never downloads shard
    data, and it marks all proof-bearing corpora as candidates until local Lean
    revalidation succeeds.
    """

    out_dir.mkdir(parents=True, exist_ok=True)
    offline_payloads = offline_payloads or {}
    search_terms = _dedupe_tuple(search_terms)
    pinned_dataset_ids = _dedupe_tuple(pinned_dataset_ids)
    collection_slugs = _dedupe_tuple(collection_slugs)
    errors: list[dict[str, object]] = []
    warnings: list[str] = []
    collection_rows: list[dict[str, object]] = []
    model_rows: list[dict[str, object]] = []
    paper_rows: list[dict[str, object]] = []
    candidates: dict[str, dict[str, object]] = {}

    def payload_for(key: str, url: str) -> Any:
        if key in offline_payloads:
            return offline_payloads[key]
        if not use_network:
            return None
        try:
            return _fetch_json(url, timeout_s=timeout_s)
        except Exception as exc:  # pragma: no cover - network failures are environment-specific
            errors.append({"key": key, "url": url, "error": str(exc)})
            return None

    for slug in collection_slugs:
        key = f"collection:{slug}"
        collection_payload = payload_for(key, f"{HF_API_BASE}/collections/{urllib.parse.quote(slug, safe='/')}")
        if isinstance(collection_payload, dict):
            collection_rows.append(_collection_summary(slug, collection_payload))
            for item in _list(collection_payload.get("items")):
                item_id = str(item.get("id", ""))
                item_type = str(item.get("repoType") or item.get("type") or "")
                if not item_id:
                    continue
                if item_type == "dataset":
                    _merge_candidate(
                        candidates,
                        item_id,
                        item,
                        discovered_by=f"collection:{slug}",
                    )
                elif item_type == "model":
                    model_rows.append(_model_summary(item, discovered_by=f"collection:{slug}"))
                elif item_type == "paper":
                    paper_rows.append(_paper_summary(item, discovered_by=f"collection:{slug}"))

    for term in search_terms:
        query = urllib.parse.urlencode(
            {"search": term, "limit": max(1, max_results_per_query), "full": "true"}
        )
        payload = payload_for(f"search:{term}", f"{HF_API_BASE}/datasets?{query}")
        for item in payload if isinstance(payload, list) else []:
            item_id = str(item.get("id", ""))
            if item_id:
                _merge_candidate(candidates, item_id, item, discovered_by=f"search:{term}")

    for dataset_id in pinned_dataset_ids:
        _merge_candidate(
            candidates,
            dataset_id,
            {"id": dataset_id},
            discovered_by="pinned:high_value_lean_dataset",
        )

    detail_fetch_order = _detail_fetch_order(candidates, pinned_dataset_ids)
    for dataset_id in detail_fetch_order[: max(0, max_detail_fetches)]:
        key = f"dataset:{dataset_id}"
        url = f"{HF_API_BASE}/datasets/{urllib.parse.quote(dataset_id, safe='/')}"
        detail = payload_for(key, url)
        if isinstance(detail, dict):
            _merge_candidate(candidates, dataset_id, detail, discovered_by="dataset_detail")
        elif dataset_id in pinned_dataset_ids:
            warnings.append(f"missing detail metadata for pinned dataset {dataset_id}")

    rows = [
        _row_from_metadata(str(metadata.get("id", dataset_id)), metadata)
        for dataset_id, metadata in candidates.items()
    ]
    rows.sort(key=_row_sort_key)
    row_dicts = [_row_as_dict(row) for row in rows]

    critical_rows = [row for row in rows if row.priority == "critical"]
    high_rows = [row for row in rows if row.priority == "high"]
    oproofs_rows = [row for row in rows if row.dataset_id.lower() in {"m-a-p/oproofs", "oprover/oproofs"}]
    total_reported_dataset_rows = sum(row.num_rows for row in rows if row.num_rows > 0)
    payload: dict[str, object] = {
        "schema_version": HUGGINGFACE_LEAN_SOURCE_AUDIT_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources": {
            "collections": collection_slugs,
            "search_terms": search_terms,
            "pinned_dataset_ids": pinned_dataset_ids,
            "max_results_per_query": max_results_per_query,
            "max_detail_fetches": max_detail_fetches,
            "use_network": use_network,
        },
        "summary": {
            "n_candidates": len(rows),
            "n_critical": len(critical_rows),
            "n_high": len(high_rows),
            "n_public_ungated": sum(
                1 for row in rows if not row.private and not row.gated and not row.disabled
            ),
            "n_with_license": sum(1 for row in rows if row.license),
            "n_formal_proof_pair_sources": sum(
                1 for row in rows if row.relevance_class == "formal_proof_pairs"
            ),
            "n_tactic_state_sources": sum(
                1 for row in rows if row.relevance_class == "tactic_state_training"
            ),
            "n_repair_or_process_sources": sum(
                1 for row in rows if row.relevance_class == "proof_repair_or_process_training"
            ),
            "n_formal_code_corpora": sum(
                1 for row in rows if row.relevance_class == "formal_code_corpus"
            ),
            "n_benchmark_sources": sum(
                1 for row in rows if row.relevance_class == "benchmark_eval"
            ),
            "total_reported_dataset_rows": total_reported_dataset_rows,
            "proof_evidence_ready": 0,
            "oproofs_detected": bool(oproofs_rows),
            "oproofs_reported_rows": max((row.num_rows for row in oproofs_rows), default=0),
            "oproofs_parquet_shards": max((row.parquet_shards for row in oproofs_rows), default=0),
            "oproofs_used_storage_bytes": max(
                (row.used_storage_bytes for row in oproofs_rows), default=0
            ),
        },
        "collection_rows": collection_rows,
        "collection_models": model_rows,
        "collection_papers": paper_rows,
        "rows": row_dicts,
        "rag_integration_plan": _rag_integration_plan(rows),
        "top_recommendations": _top_recommendations(rows),
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "errors": errors,
        "warnings": warnings,
    }
    payload["manifest_fingerprint"] = stable_hash(
        {
            "schema_version": HUGGINGFACE_LEAN_SOURCE_AUDIT_SCHEMA_VERSION,
            "rows": row_dicts,
            "collection_models": model_rows,
            "collection_papers": paper_rows,
            "summary": payload["summary"],
        }
    )

    (out_dir / "huggingface_lean_source_audit_manifest.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    (out_dir / "huggingface_lean_rag_integration_plan.json").write_text(
        json.dumps(payload["rag_integration_plan"], indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    (out_dir / "huggingface_lean_source_audit.md").write_text(
        _markdown_report(payload),
        encoding="utf-8",
    )
    return payload


def _fetch_json(url: str, *, timeout_s: int) -> Any:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "AI-Statistician-HF-Lean-Source-Audit/1",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout_s) as response:  # nosec B310
        return json.loads(response.read().decode("utf-8"))


def _merge_candidate(
    candidates: dict[str, dict[str, object]],
    dataset_id: str,
    metadata: dict[str, object],
    *,
    discovered_by: str,
) -> None:
    key = dataset_id.lower()
    previous = candidates.get(key, {})
    discovered = set(_tuple(previous.get("discovered_by")))
    discovered.add(discovered_by)
    merged = _deep_merge(previous, metadata)
    merged["id"] = str(merged.get("id") or dataset_id)
    merged["discovered_by"] = tuple(sorted(discovered))
    candidates[key] = merged


def _deep_merge(left: dict[str, object], right: dict[str, object]) -> dict[str, object]:
    merged = dict(left)
    for key, value in right.items():
        if key == "discovered_by":
            continue
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(dict(merged[key]), value)
        elif isinstance(value, list) and isinstance(merged.get(key), list):
            merged[key] = _dedupe_list([*list(merged[key]), *value])
        elif value not in (None, "", [], {}):
            merged[key] = value
        elif key not in merged:
            merged[key] = value
    return merged


def _detail_fetch_order(
    candidates: dict[str, dict[str, object]],
    pinned_dataset_ids: tuple[str, ...],
) -> list[str]:
    pinned = [dataset_id for dataset_id in pinned_dataset_ids if dataset_id.lower() in candidates]
    rest = [
        str(metadata.get("id", dataset_id))
        for dataset_id, metadata in candidates.items()
        if str(metadata.get("id", dataset_id)) not in pinned
    ]
    rest.sort(key=lambda dataset_id: _candidate_priority_score(candidates[dataset_id.lower()]), reverse=True)
    return _dedupe_list([*pinned, *rest])


def _candidate_priority_score(metadata: dict[str, object]) -> int:
    text = _metadata_text(metadata)
    score = 0
    for marker, points in (
        ("oproofs", 100),
        ("formal_proof", 40),
        ("formal proof", 35),
        ("compiler", 30),
        ("leandojo", 30),
        ("tactic", 25),
        ("numinamath", 25),
        ("lean-github", 25),
        ("lean_github", 25),
        ("workbook", 20),
        ("proof compression", 20),
        ("proof-artifacts", 20),
        ("mathlib", 20),
        ("scilean", 15),
        ("cvxlean", 15),
        ("analysis", 10),
        ("calculus", 10),
        ("statistics", 10),
    ):
        if marker in text:
            score += points
    score += min(_int(metadata.get("downloads")), 500) // 50
    score += min(_int(metadata.get("likes")), 100)
    return score


def _row_from_metadata(dataset_id: str, metadata: dict[str, object]) -> HuggingFaceLeanSourceRow:
    dataset_id = str(dataset_id)
    tags = _tags(metadata)
    license_name = _license(metadata, tags)
    fields = _schema_fields(dataset_id, metadata)
    source_datasets = _source_datasets(metadata)
    num_rows = _num_rows(metadata)
    formats = _formats(metadata, tags)
    size_categories = _size_categories(metadata, tags)
    private = bool(metadata.get("private", False))
    gated = bool(metadata.get("gated", False))
    disabled = bool(metadata.get("disabled", False))
    classification = _classify_source(
        dataset_id,
        metadata,
        fields=fields,
        source_datasets=source_datasets,
        private=private,
        gated=gated,
        disabled=disabled,
        license_name=license_name,
    )
    return HuggingFaceLeanSourceRow(
        dataset_id=dataset_id,
        url=f"https://huggingface.co/datasets/{dataset_id}",
        sha=str(metadata.get("sha", "")),
        last_modified=str(metadata.get("lastModified", "")),
        downloads=_int(metadata.get("downloads")),
        likes=_int(metadata.get("likes")),
        private=private,
        gated=gated,
        disabled=disabled,
        license=license_name,
        tags=tags,
        size_categories=size_categories,
        formats=formats,
        num_rows=num_rows,
        used_storage_bytes=_int(metadata.get("usedStorage")),
        parquet_shards=_parquet_shards(metadata),
        schema_fields=fields,
        source_datasets=source_datasets,
        discovered_by=_tuple(metadata.get("discovered_by")),
        relevance_class=str(classification["relevance_class"]),
        retrieval_role=str(classification["retrieval_role"]),
        priority=str(classification["priority"]),
        integration_status=str(classification["integration_status"]),
        trust_policy=str(classification["trust_policy"]),
        usage_policy=str(classification["usage_policy"]),
        rationale=str(classification["rationale"]),
    )


def _classify_source(
    dataset_id: str,
    metadata: dict[str, object],
    *,
    fields: tuple[str, ...],
    source_datasets: tuple[str, ...],
    private: bool,
    gated: bool,
    disabled: bool,
    license_name: str,
) -> dict[str, str]:
    text = _metadata_text(metadata)
    dataset_lower = dataset_id.lower()
    field_set = {field.lower() for field in fields}
    relevance_class = "unclear"
    retrieval_role = "manual_review"
    priority = "low"
    rationale = "Lean-related dataset discovered by Hugging Face search; manual schema review is needed."

    if dataset_lower in {"m-a-p/oproofs", "oprover/oproofs"}:
        relevance_class = "formal_proof_pairs"
        retrieval_role = "retrieval_memory_and_proof_repair_sft_candidate"
        priority = "critical"
        rationale = (
            "OProofs is the OProver corpus with Lean statements, compiler-verified proofs, "
            "and proof-repair trajectory fields according to upstream metadata/paper."
        )
    elif {"formal_statement", "formal_proof"}.issubset(field_set):
        relevance_class = "formal_proof_pairs"
        retrieval_role = "retrieval_memory_and_sft_candidate"
        priority = "high" if _num_rows(metadata) >= 10000 else "medium"
        rationale = "Schema exposes formal_statement/formal_proof pairs suitable for sampled retrieval and SFT review."
    elif any(marker in text for marker in ("lean-github", "lean_github", "github lean", "phanerozoic/lean4", "mathlib", "scilean", "cvxlean", "physlean", "batteries", "stdlib")):
        relevance_class = "formal_code_corpus"
        retrieval_role = "declaration_and_code_context_retrieval_candidate"
        priority = "high" if any(marker in text for marker in ("mathlib", "lean-github", "lean_github", "scilean", "cvxlean", "statistics")) else "medium"
        rationale = "Structured Lean code corpus can improve declaration/code-context retrieval after license and source review."
    elif "leandojo" in text or {"state", "tactic", "result"}.intersection(field_set):
        relevance_class = "tactic_state_training"
        retrieval_role = "proof_state_premise_selection_and_tactic_policy_candidate"
        priority = "high"
        rationale = "LeanDojo-style tactic-state data is useful for proof-state-aware retrieval and tactic selection."
    elif any(marker in text for marker in ("proof-artifacts", "proof artifacts", "trajs", "trajectory", "repair", "proof compression", "leanpolish")):
        relevance_class = "proof_repair_or_process_training"
        retrieval_role = "proof_repair_policy_and_process_supervision_candidate"
        priority = "high"
        rationale = "Dataset appears to contain proof process, trajectory, repair, or compression supervision."
    elif any(marker in text for marker in ("minif2f", "proofnet", "putnambench", "benchmark")):
        relevance_class = "benchmark_eval"
        retrieval_role = "evaluation_holdout_or_calibration_only"
        priority = "medium"
        rationale = "Benchmark-style Lean dataset should be held out from training by default and used for calibration/evaluation."

    if dataset_lower.startswith("phanerozoic/lean4-") and relevance_class == "unclear":
        relevance_class = "formal_code_corpus"
        retrieval_role = "declaration_and_code_context_retrieval_candidate"
        priority = "medium"
        rationale = "Phanerozoic Lean4 shards are structured Lean source corpora and need per-repo source review."

    integration_status = "new_hf_candidate"
    if any(marker in dataset_lower for marker in CURRENT_LOCAL_RAG_SOURCE_MARKERS):
        integration_status = "concept_known_but_hf_dataset_audit_needed"
    if dataset_lower in {"m-a-p/oproofs", "oprover/oproofs"}:
        integration_status = "new_critical_hf_corpus_for_rag_and_repair_training"

    if private or gated or disabled:
        trust_policy = "blocked_until_access_and_license_review"
        priority = "blocked"
    elif not license_name:
        trust_policy = "metadata_only_until_license_review"
        if priority == "critical":
            priority = "high"
    elif dataset_lower in {"m-a-p/oproofs", "oprover/oproofs"}:
        trust_policy = "upstream_claims_compiler_verified; local_lean_revalidation_required_before_proof_evidence"
    else:
        trust_policy = "candidate_source; local_lean_revalidation_required_before_proof_evidence"

    if relevance_class == "benchmark_eval":
        usage_policy = "holdout_or_evaluation_only_by_default; do_not_add_to_training_exports_without_split_review"
    elif relevance_class == "formal_code_corpus":
        usage_policy = "index_metadata_or_source_context_for_retrieval; do_not_vendor_generated_indexes"
    elif relevance_class in {"formal_proof_pairs", "proof_repair_or_process_training", "tactic_state_training"}:
        usage_policy = "stream_or_sample; dedupe_by_statement_and_proof_hash; locally_revalidate_before_promotion"
    else:
        usage_policy = "manual_review_before_indexing_or_training"

    if source_datasets and dataset_lower in {"m-a-p/oproofs", "oprover/oproofs"}:
        rationale += " Source mentions: " + ", ".join(source_datasets[:6]) + "."

    return {
        "relevance_class": relevance_class,
        "retrieval_role": retrieval_role,
        "priority": priority,
        "integration_status": integration_status,
        "trust_policy": trust_policy,
        "usage_policy": usage_policy,
        "rationale": rationale,
    }


def _tags(metadata: dict[str, object]) -> tuple[str, ...]:
    tags = [str(tag) for tag in _list(metadata.get("tags"))]
    card = _dict(metadata.get("cardData"))
    tags.extend(str(tag) for tag in _list(card.get("tags")))
    return tuple(sorted(set(tag for tag in tags if tag)))


def _license(metadata: dict[str, object], tags: tuple[str, ...]) -> str:
    card = _dict(metadata.get("cardData"))
    license_name = str(card.get("license", "") or "")
    if license_name:
        return license_name
    for tag in tags:
        if tag.startswith("license:"):
            return tag.split(":", 1)[1]
    return ""


def _formats(metadata: dict[str, object], tags: tuple[str, ...]) -> tuple[str, ...]:
    formats: list[str] = []
    server = _dict(metadata.get("datasetsServerInfo"))
    formats.extend(str(item) for item in _list(server.get("formats")))
    formats.extend(tag.split(":", 1)[1] for tag in tags if tag.startswith("format:"))
    if _parquet_shards(metadata):
        formats.append("parquet")
    return tuple(sorted(set(item for item in formats if item)))


def _size_categories(metadata: dict[str, object], tags: tuple[str, ...]) -> tuple[str, ...]:
    card = _dict(metadata.get("cardData"))
    categories = [str(item) for item in _list(card.get("size_categories"))]
    categories.extend(tag.split(":", 1)[1] for tag in tags if tag.startswith("size_categories:"))
    return tuple(sorted(set(item for item in categories if item)))


def _schema_fields(dataset_id: str, metadata: dict[str, object]) -> tuple[str, ...]:
    card = _dict(metadata.get("cardData"))
    dataset_info = _dict(card.get("dataset_info"))
    fields: list[str] = []
    for feature in _list(dataset_info.get("features")):
        if isinstance(feature, dict):
            name = str(feature.get("name", ""))
            if name:
                fields.append(name)
    if dataset_id.lower() in {"m-a-p/oproofs", "oprover/oproofs"}:
        fields.extend(["formal_statement", "formal_proof", "cot_proof", "prompt"])
    description = str(metadata.get("description", "") or "")
    for candidate in ("formal_statement", "formal_proof", "cot_proof", "prompt", "STATE", "TACTIC", "RESULT"):
        if candidate in description:
            fields.append(candidate)
    return tuple(sorted(set(fields)))


def _source_datasets(metadata: dict[str, object]) -> tuple[str, ...]:
    text = str(metadata.get("description", "") or "")
    known = (
        "NuminaMath-LEAN",
        "Lean-Workbook",
        "Leanabell-FormalStmt",
        "Leanabell-SFT",
        "Goedel-Pset",
        "FineLeanCorpus",
        "miniF2F",
        "ProofNet",
        "PutnamBench",
        "Mathlib",
        "LeanDojo",
    )
    return tuple(item for item in known if item.lower() in text.lower())


def _num_rows(metadata: dict[str, object]) -> int:
    server = _dict(metadata.get("datasetsServerInfo"))
    if server.get("numRows") is not None:
        return _int(server.get("numRows"))
    card = _dict(metadata.get("cardData"))
    dataset_info = _dict(card.get("dataset_info"))
    split_rows = 0
    for split in _list(dataset_info.get("splits")):
        if isinstance(split, dict):
            split_rows += _int(split.get("num_examples"))
    if split_rows:
        return split_rows
    description = str(metadata.get("description", "") or "")
    match = re.search(r"Records:\s*([0-9,]+)", description)
    if match:
        return _int(match.group(1).replace(",", ""))
    return 0


def _parquet_shards(metadata: dict[str, object]) -> int:
    siblings = _list(metadata.get("siblings"))
    count = sum(
        1
        for item in siblings
        if isinstance(item, dict) and str(item.get("rfilename", "")).endswith(".parquet")
    )
    if count:
        return count
    description = str(metadata.get("description", "") or "")
    match = re.search(r"Files:\s*([0-9,]+)\s+parquet", description, re.IGNORECASE)
    if match:
        return _int(match.group(1).replace(",", ""))
    return 0


def _collection_summary(slug: str, payload: dict[str, object]) -> dict[str, object]:
    items = _list(payload.get("items"))
    return {
        "slug": slug,
        "title": str(payload.get("title", "")),
        "last_updated": str(payload.get("lastUpdated", "")),
        "url": str(payload.get("shareUrl", "")) or f"https://huggingface.co/collections/{slug}",
        "n_items": len(items),
        "n_datasets": sum(
            1 for item in items if str(item.get("repoType") or item.get("type") or "") == "dataset"
        ),
        "n_models": sum(
            1 for item in items if str(item.get("repoType") or item.get("type") or "") == "model"
        ),
        "n_papers": sum(1 for item in items if str(item.get("type") or "") == "paper"),
    }


def _model_summary(item: dict[str, object], *, discovered_by: str) -> dict[str, object]:
    return {
        "model_id": str(item.get("id", "")),
        "url": f"https://huggingface.co/{item.get('id', '')}",
        "last_modified": str(item.get("lastModified", "")),
        "downloads": _int(item.get("downloads")),
        "likes": _int(item.get("likes")),
        "num_parameters": _int(item.get("numParameters")),
        "private": bool(item.get("private", False)),
        "gated": bool(item.get("gated", False)),
        "discovered_by": discovered_by,
    }


def _paper_summary(item: dict[str, object], *, discovered_by: str) -> dict[str, object]:
    paper_id = str(item.get("id", ""))
    return {
        "paper_id": paper_id,
        "title": str(item.get("title", "")),
        "url": f"https://arxiv.org/abs/{paper_id}" if paper_id else "",
        "published_at": str(item.get("publishedAt", "")),
        "upvotes": _int(item.get("upvotes")),
        "discovered_by": discovered_by,
    }


def _top_recommendations(rows: list[HuggingFaceLeanSourceRow]) -> list[str]:
    recommendations = [
        "Add OProofs as a high-priority streamed HF source for retrieval memory, proof-pair SFT, and repair-supervision experiments; do not vendor the full parquet shards.",
        "Build a shard sampler/ingester that hashes formal_statement/formal_proof pairs, deduplicates near duplicates, records license/provenance, and verifies sampled rows under local Lean before proof-bank promotion.",
        "Keep benchmark corpora such as miniF2F, ProofNet, and PutnamBench as evaluation/holdout sets unless a split-specific training policy is explicitly recorded.",
        "Separate source roles in the RAG stack: formal code corpora for declaration search, tactic-state corpora for proof-state retrieval, proof-pair corpora for premise memory/SFT, and repair trajectories for feedback-conditioned proof repair.",
    ]
    if not any(row.dataset_id.lower() in {"m-a-p/oproofs", "oprover/oproofs"} for row in rows):
        recommendations.insert(
            0,
            "Re-run the audit with network access; OProofs was not discovered, so the critical OProver source is missing.",
        )
    return recommendations


def _rag_integration_plan(rows: list[HuggingFaceLeanSourceRow]) -> list[dict[str, object]]:
    plan: list[dict[str, object]] = []
    for row in rows:
        if row.priority not in {"critical", "high"}:
            continue
        plan.append(
            {
                "source_id": "hf::" + row.dataset_id.replace("/", "::"),
                "dataset_id": row.dataset_id,
                "url": row.url,
                "priority": row.priority,
                "relevance_class": row.relevance_class,
                "retrieval_role": row.retrieval_role,
                "ingestion_mode": _ingestion_mode(row),
                "license": row.license,
                "num_rows": row.num_rows,
                "formats": list(row.formats),
                "schema_fields": list(row.schema_fields),
                "trust_policy": row.trust_policy,
                "usage_policy": row.usage_policy,
                "local_validation_gate": (
                    "sample rows, reconstruct complete Lean imports/header when available, "
                    "run local Lean under the target toolchain, and only then promote a row "
                    "to proof-bank or proof-search evidence"
                ),
                "dedupe_keys": ("formal_statement_hash", "formal_proof_hash", "dataset_id", "sha"),
                "do_not_vendor": True,
            }
        )
    return plan


def _ingestion_mode(row: HuggingFaceLeanSourceRow) -> str:
    if row.relevance_class == "benchmark_eval":
        return "metadata_index_and_holdout_split_only"
    if row.relevance_class == "formal_code_corpus":
        return "stream_or_sample_code_context_for_declaration_retrieval"
    if row.relevance_class == "tactic_state_training":
        return "stream_or_sample_tactic_state_rows_for_proof_state_retrieval_training"
    if row.relevance_class == "proof_repair_or_process_training":
        return "stream_or_sample_process_rows_for_feedback_conditioned_repair_training"
    if row.relevance_class == "formal_proof_pairs":
        return "stream_or_sample_proof_pairs_for_retrieval_memory_and_sft"
    return "manual_review_before_ingestion"


def _markdown_report(payload: dict[str, object]) -> str:
    summary = dict(payload.get("summary", {}) or {})
    rows = [dict(row) for row in _list(payload.get("rows"))]
    lines = [
        "# Hugging Face Lean Source Audit",
        "",
        f"- Generated at: `{payload.get('generated_at')}`",
        f"- Candidates: `{summary.get('n_candidates')}`",
        f"- Critical/high: `{summary.get('n_critical')}/{summary.get('n_high')}`",
        f"- Public ungated: `{summary.get('n_public_ungated')}`",
        f"- OProofs rows: `{summary.get('oproofs_reported_rows')}`",
        f"- OProofs parquet shards: `{summary.get('oproofs_parquet_shards')}`",
        f"- Proof evidence ready: `{summary.get('proof_evidence_ready')}`",
        "",
        "## Boundary",
        "",
        str(payload.get("proof_evidence_boundary", PROOF_EVIDENCE_BOUNDARY)),
        "",
        "## Top Sources",
        "",
        "| priority | dataset | class | rows | license | role | policy |",
        "| --- | --- | --- | ---: | --- | --- | --- |",
    ]
    for row in rows[:40]:
        lines.append(
            "| {priority} | [{dataset}]({url}) | {klass} | {num_rows} | {license} | {role} | {policy} |".format(
                priority=row.get("priority", ""),
                dataset=row.get("dataset_id", ""),
                url=row.get("url", ""),
                klass=row.get("relevance_class", ""),
                num_rows=row.get("num_rows", 0),
                license=row.get("license", "") or "unknown",
                role=row.get("retrieval_role", ""),
                policy=str(row.get("usage_policy", "")).replace("|", "/"),
            )
        )
    lines.extend(["", "## OProver Collection", ""])
    for row in _list(payload.get("collection_rows")):
        row_dict = dict(row)
        lines.append(
            f"- `{row_dict.get('slug')}`: items=`{row_dict.get('n_items')}` "
            f"models=`{row_dict.get('n_models')}` datasets=`{row_dict.get('n_datasets')}` "
            f"papers=`{row_dict.get('n_papers')}`"
        )
    models = _list(payload.get("collection_models"))
    if models:
        lines.append("- Models: " + ", ".join(f"`{dict(model).get('model_id')}`" for model in models))
    papers = _list(payload.get("collection_papers"))
    if papers:
        lines.append("- Papers: " + ", ".join(f"[{dict(paper).get('paper_id')}]({dict(paper).get('url')})" for paper in papers))
    lines.extend(["", "## Recommended Actions", ""])
    for action in _list(payload.get("top_recommendations")):
        lines.append(f"- {action}")
    plan = _list(payload.get("rag_integration_plan"))
    if plan:
        lines.extend(["", "## Integration Plan", ""])
        lines.append(
            f"`huggingface_lean_rag_integration_plan.json` contains `{len(plan)}` critical/high source plans."
        )
    errors = _list(payload.get("errors"))
    warnings = _list(payload.get("warnings"))
    if errors or warnings:
        lines.extend(["", "## Diagnostics", ""])
        for warning in warnings:
            lines.append(f"- warning: {warning}")
        for error in errors[:20]:
            err = dict(error)
            lines.append(f"- error `{err.get('key')}`: {err.get('error')}")
    lines.append("")
    return "\n".join(lines)


def _metadata_text(metadata: dict[str, object]) -> str:
    parts = [
        str(metadata.get("id", "")),
        str(metadata.get("description", "")),
        " ".join(_tags(metadata)),
        " ".join(_schema_fields(str(metadata.get("id", "")), metadata)),
    ]
    return " ".join(parts).lower()


def _row_as_dict(row: HuggingFaceLeanSourceRow) -> dict[str, object]:
    payload = asdict(row)
    for key, value in tuple(payload.items()):
        if isinstance(value, tuple):
            payload[key] = list(value)
    return payload


def _row_sort_key(row: HuggingFaceLeanSourceRow) -> tuple[int, int, int, str]:
    priority_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3, "blocked": 4}.get(
        row.priority,
        5,
    )
    return (priority_rank, -row.num_rows, -row.downloads, row.dataset_id.lower())


def _dedupe_tuple(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(_dedupe_list([str(value) for value in values if str(value)]))


def _dedupe_list(values: list[Any]) -> list[Any]:
    seen: set[str] = set()
    out: list[Any] = []
    for value in values:
        key = json.dumps(value, sort_keys=True, default=str)
        if key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out


def _tuple(value: object) -> tuple[str, ...]:
    if isinstance(value, tuple):
        return tuple(str(item) for item in value if str(item))
    if isinstance(value, list):
        return tuple(str(item) for item in value if str(item))
    if isinstance(value, str) and value:
        return (value,)
    return ()


def _list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def _dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _int(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value.replace(",", ""))
        except ValueError:
            return 0
    return 0
