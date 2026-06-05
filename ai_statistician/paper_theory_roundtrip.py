from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .retrieval import tokens


PAPER_THEORY_ROUNDTRIP_SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = "PAPER_THEORY_ROUNDTRIP_NOT_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "Paper-theory extraction, Lean-candidate queues, and Lean-to-LaTeX "
    "round-trip review packets are source-grounding and semantic-review "
    "artifacts. They are not theorem proof evidence until exact Lean "
    "declarations pass a local kernel/AXLE verifier and promotion review."
)

STATEMENT_KINDS = (
    "definition",
    "assumption",
    "theorem",
    "lemma",
    "proposition",
    "corollary",
    "remark",
)
FORMALIZATION_KINDS = {"definition", "assumption", "theorem", "lemma", "proposition", "corollary"}
WORKER_OUTPUT_JSONL = "paper_theory_roundtrip_worker_outputs.jsonl"


@dataclass(frozen=True)
class PaperTheoryStatement:
    schema_version: int
    paper_id: str
    statement_id: str
    kind: str
    title: str
    label: str
    source_path: str
    source_start_line: int
    source_end_line: int
    latex: str
    normalized_text: str
    formulas: tuple[str, ...]
    dependency_labels: tuple[str, ...]
    proof_latex: str
    proof_start_line: int
    proof_end_line: int
    source_span: dict[str, object]
    proof_evidence_ready: int
    proof_evidence_status: str
    proof_evidence_boundary: str


@dataclass(frozen=True)
class StatTheoryIRRow:
    schema_version: int
    paper_id: str
    statement_id: str
    statement_kind: str
    statistical_objects: tuple[str, ...]
    dgp_terms: tuple[str, ...]
    estimand_terms: tuple[str, ...]
    estimator_terms: tuple[str, ...]
    assumption_terms: tuple[str, ...]
    asymptotic_terms: tuple[str, ...]
    conclusion_text: str
    proof_obligations: tuple[str, ...]
    semantic_risk_flags: tuple[str, ...]
    proof_evidence_status: str


@dataclass(frozen=True)
class LeanCandidateQueueRow:
    schema_version: int
    queue_id: str
    paper_id: str
    statement_id: str
    statement_kind: str
    label: str
    candidate_namespace: str
    suggested_declaration_name: str
    source_latex: str
    stat_theory_ir: dict[str, object]
    dependency_labels: tuple[str, ...]
    expected_output_contract: dict[str, object]
    acceptance_gate: str
    forbidden_shortcuts: tuple[str, ...]
    proof_evidence_ready: int
    proof_evidence_status: str
    proof_evidence_boundary: str


@dataclass(frozen=True)
class LeanToLatexRoundtripRow:
    schema_version: int
    review_id: str
    paper_id: str
    statement_id: str
    source_statement_label: str
    required_inputs: tuple[str, ...]
    expected_outputs: tuple[str, ...]
    semantic_review_gate: str
    original_paper_hidden_from_informalizer: bool
    proof_evidence_status: str
    proof_evidence_boundary: str


def export_paper_theory_roundtrip(
    paper_root: Path,
    out_dir: Path,
    *,
    paper_id: str | None = None,
    max_statements: int = 200,
) -> dict[str, object]:
    """Extract paper-theory statements and queue formalization/round-trip work.

    This is the MerLean-inspired front-end for statistics papers: prefer TeX
    source, keep source spans, build a statement dependency graph, map each
    statement into a statistics-theory IR, then emit worker queues for
    Lean-candidate realization and Lean-origin LaTeX review. It deliberately
    stops before claiming any proof evidence.
    """

    if max_statements <= 0:
        raise ValueError("max_statements must be positive")
    tex_files = _tex_files(paper_root)
    statements: list[PaperTheoryStatement] = []
    for tex_path in tex_files:
        statements.extend(_extract_statements(tex_path, paper_id=paper_id or _paper_id(paper_root)))
        if len(statements) >= max_statements:
            statements = statements[:max_statements]
            break
    ir_rows = [_stat_theory_ir(row) for row in statements]
    ir_by_statement = {row.statement_id: asdict(row) for row in ir_rows}
    candidate_rows = [
        _lean_candidate_row(row, ir_by_statement[row.statement_id])
        for row in statements
        if row.kind in FORMALIZATION_KINDS
    ]
    roundtrip_rows = [_roundtrip_row(row) for row in statements if row.kind in FORMALIZATION_KINDS]
    graph = _dependency_graph(statements)

    out_dir.mkdir(parents=True, exist_ok=True)
    statement_jsonl = out_dir / "paper_statement_catalog.jsonl"
    ir_jsonl = out_dir / "stat_theory_ir.jsonl"
    candidate_jsonl = out_dir / "statement_to_lean_candidate_queue.jsonl"
    roundtrip_jsonl = out_dir / "lean_to_latex_roundtrip_review_queue.jsonl"
    graph_path = out_dir / "paper_theory_dependency_graph.json"
    report_path = out_dir / "paper_theory_roundtrip.md"
    manifest_path = out_dir / "paper_theory_roundtrip_manifest.json"

    statement_dicts = [asdict(row) for row in statements]
    ir_dicts = [asdict(row) for row in ir_rows]
    candidate_dicts = [asdict(row) for row in candidate_rows]
    roundtrip_dicts = [asdict(row) for row in roundtrip_rows]
    _write_jsonl(statement_jsonl, statement_dicts)
    _write_jsonl(ir_jsonl, ir_dicts)
    _write_jsonl(candidate_jsonl, candidate_dicts)
    _write_jsonl(roundtrip_jsonl, roundtrip_dicts)
    graph_path.write_text(json.dumps(graph, indent=2), encoding="utf-8")

    payload: dict[str, object] = {
        "schema_version": PAPER_THEORY_ROUNDTRIP_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "paper_id": paper_id or _paper_id(paper_root),
        "paper_root": str(paper_root),
        "n_tex_files": len(tex_files),
        "n_statements": len(statements),
        "n_with_proofs": sum(1 for row in statements if row.proof_latex.strip()),
        "n_dependency_edges": len(graph["edges"]),
        "n_stat_theory_ir_rows": len(ir_rows),
        "n_lean_candidate_queue_rows": len(candidate_rows),
        "n_roundtrip_review_rows": len(roundtrip_rows),
        "n_proof_evidence_ready": 0,
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "worker_output_jsonl": WORKER_OUTPUT_JSONL,
        "statement_catalog_jsonl": str(statement_jsonl),
        "stat_theory_ir_jsonl": str(ir_jsonl),
        "statement_to_lean_candidate_queue_jsonl": str(candidate_jsonl),
        "lean_to_latex_roundtrip_review_queue_jsonl": str(roundtrip_jsonl),
        "dependency_graph": str(graph_path),
        "report_path": str(report_path),
        "dataset_fingerprint": stable_hash(
            [statement_dicts, ir_dicts, candidate_dicts, roundtrip_dicts, graph]
        ),
        "all_ok": bool(tex_files)
        and bool(statements)
        and bool(ir_rows)
        and len(candidate_rows) == len(roundtrip_rows)
        and all(row.expected_output_contract for row in candidate_rows),
        "limitations": [
            "regex TeX extraction is a deterministic P0 source-span catalog, not a full semantic paper parser",
            "PDF/OCR theorem extraction is intentionally not attempted here; use multimodal extraction as a fallback when TeX source is unavailable",
            "Lean candidate and round-trip review rows are work contracts, not proof evidence",
            "autoinformalized LaTeX should be generated only from Lean artifacts, with the original paper hidden from the informalizer",
        ],
        "statements_preview": statement_dicts[:10],
    }
    manifest_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    report_path.write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _tex_files(path: Path) -> list[Path]:
    if path.is_file() and path.suffix == ".tex":
        return [path]
    if path.is_dir():
        return sorted(row for row in path.rglob("*.tex") if row.is_file())
    return []


def _paper_id(path: Path) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", path.stem or path.name).strip("_") or "paper"


def _extract_statements(path: Path, *, paper_id: str) -> list[PaperTheoryStatement]:
    text = path.read_text(encoding="utf-8")
    line_starts = _line_starts(text)
    env_pattern = re.compile(
        r"\\begin\{(?P<kind>" + "|".join(STATEMENT_KINDS + ("proof",)) + r")\}"
        r"(?P<option>\[[^\]]*\])?"
        r"(?P<body>.*?)"
        r"\\end\{(?P=kind)\}",
        re.DOTALL | re.IGNORECASE,
    )
    events: list[dict[str, Any]] = []
    for match in env_pattern.finditer(text):
        kind = match.group("kind").lower()
        option = (match.group("option") or "").strip("[]")
        body = match.group("body").strip()
        start_line = _line_for_offset(line_starts, match.start()) + 1
        end_line = _line_for_offset(line_starts, match.end()) + 1
        events.append(
            {
                "kind": kind,
                "title": option,
                "body": body,
                "start_line": start_line,
                "end_line": end_line,
                "start_offset": match.start(),
                "end_offset": match.end(),
            }
        )

    rows: list[PaperTheoryStatement] = []
    statement_index = 0
    for idx, event in enumerate(events):
        if event["kind"] == "proof":
            continue
        statement_index += 1
        proof = _following_proof(events, idx)
        label = _label(event["body"])
        statement_id = label or f"{paper_id}:{event['kind']}:{statement_index:04d}"
        rows.append(
            PaperTheoryStatement(
                schema_version=PAPER_THEORY_ROUNDTRIP_SCHEMA_VERSION,
                paper_id=paper_id,
                statement_id=statement_id,
                kind=event["kind"],
                title=str(event["title"]),
                label=label,
                source_path=str(path),
                source_start_line=int(event["start_line"]),
                source_end_line=int(event["end_line"]),
                latex=str(event["body"]),
                normalized_text=_strip_tex(event["body"]),
                formulas=tuple(_formulas(event["body"])),
                dependency_labels=tuple(_dependency_labels(event["body"] + "\n" + str(proof.get("body", "")))),
                proof_latex=str(proof.get("body", "")),
                proof_start_line=int(proof.get("start_line", 0) or 0),
                proof_end_line=int(proof.get("end_line", 0) or 0),
                source_span={
                    "path": str(path),
                    "start_line": int(event["start_line"]),
                    "end_line": int(event["end_line"]),
                    "proof_start_line": int(proof.get("start_line", 0) or 0),
                    "proof_end_line": int(proof.get("end_line", 0) or 0),
                },
                proof_evidence_ready=0,
                proof_evidence_status=PROOF_EVIDENCE_STATUS,
                proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
            )
        )
    return rows


def _following_proof(events: list[dict[str, Any]], statement_idx: int) -> dict[str, Any]:
    for event in events[statement_idx + 1 :]:
        if event["kind"] == "proof":
            return event
        return {}
    return {}


def _line_starts(text: str) -> list[int]:
    starts = [0]
    for match in re.finditer("\n", text):
        starts.append(match.end())
    return starts


def _line_for_offset(line_starts: list[int], offset: int) -> int:
    lo, hi = 0, len(line_starts)
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        if line_starts[mid] <= offset:
            lo = mid
        else:
            hi = mid
    return lo


def _label(text: str) -> str:
    match = re.search(r"\\label\{([^}]+)\}", text)
    return match.group(1).strip() if match else ""


def _dependency_labels(text: str) -> list[str]:
    labels: list[str] = []
    for pattern in (
        r"\\(?:ref|eqref|autoref)\{([^}]+)\}",
        r"\\(?:cref|Cref)\{([^}]+)\}",
    ):
        for match in re.finditer(pattern, text):
            labels.extend(label.strip() for label in match.group(1).split(",") if label.strip())
    own_label = _label(text)
    return sorted(label for label in set(labels) if label != own_label)


def _formulas(text: str) -> list[str]:
    formulas: list[str] = []
    formulas.extend(match.group(1).strip() for match in re.finditer(r"\$\$(.*?)\$\$", text, re.DOTALL))
    formulas.extend(match.group(1).strip() for match in re.finditer(r"\\\[(.*?)\\\]", text, re.DOTALL))
    formulas.extend(match.group(1).strip() for match in re.finditer(r"\$(.+?)\$", text, re.DOTALL))
    return [formula for formula in formulas if formula]


def _strip_tex(text: str) -> str:
    no_labels = re.sub(r"\\label\{[^}]+\}", "", text)
    no_commands = re.sub(r"\\[A-Za-z]+\*?(?:\[[^\]]*\])?(?:\{([^{}]*)\})?", r"\1", no_labels)
    no_math = no_commands.replace("$", " ")
    return " ".join(no_math.split())


def _stat_theory_ir(statement: PaperTheoryStatement) -> StatTheoryIRRow:
    all_text = " ".join([statement.normalized_text, _strip_tex(statement.proof_latex)])
    text_tokens = tokens(all_text)
    dgp_terms = _matched_terms(
        text_tokens,
        {
            "sample",
            "sampling",
            "distribution",
            "model",
            "potential",
            "outcome",
            "filtration",
            "process",
            "covariate",
            "randomized",
            "independent",
        },
    )
    estimand_terms = _matched_terms(
        text_tokens,
        {"estimand", "parameter", "effect", "risk", "mean", "quantile", "variance", "target"},
    )
    estimator_terms = _matched_terms(
        text_tokens,
        {"estimator", "estimate", "procedure", "test", "statistic", "algorithm", "confidence"},
    )
    assumption_terms = _matched_terms(
        text_tokens,
        {"assume", "assumption", "regularity", "positivity", "exchangeability", "measurable", "integrable"},
    )
    asymptotic_terms = _matched_terms(
        text_tokens,
        {"asymptotic", "limit", "converges", "normal", "rate", "consistency", "uniform", "finite"},
    )
    proof_obligations = _proof_obligations(statement, text_tokens)
    risk_flags = _semantic_risk_flags(statement, text_tokens)
    return StatTheoryIRRow(
        schema_version=PAPER_THEORY_ROUNDTRIP_SCHEMA_VERSION,
        paper_id=statement.paper_id,
        statement_id=statement.statement_id,
        statement_kind=statement.kind,
        statistical_objects=tuple(
            sorted(set(dgp_terms + estimand_terms + estimator_terms + asymptotic_terms))
        ),
        dgp_terms=tuple(dgp_terms),
        estimand_terms=tuple(estimand_terms),
        estimator_terms=tuple(estimator_terms),
        assumption_terms=tuple(assumption_terms),
        asymptotic_terms=tuple(asymptotic_terms),
        conclusion_text=statement.normalized_text,
        proof_obligations=tuple(proof_obligations),
        semantic_risk_flags=tuple(risk_flags),
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
    )


def _matched_terms(text_tokens: set[str], vocabulary: set[str]) -> list[str]:
    return sorted(text_tokens & vocabulary)


def _proof_obligations(statement: PaperTheoryStatement, text_tokens: set[str]) -> list[str]:
    obligations: list[str] = []
    if statement.kind in {"theorem", "lemma", "proposition", "corollary"}:
        obligations.append("formalize theorem statement with explicit assumptions and conclusion")
    if statement.kind in {"definition", "assumption"}:
        obligations.append("formalize reusable definition or assumption interface")
    if "measurable" in text_tokens or "integrable" in text_tokens:
        obligations.append("discharge measurability/integrability side conditions")
    if "asymptotic" in text_tokens or "converges" in text_tokens or "limit" in text_tokens:
        obligations.append("identify topology/mode of convergence and asymptotic index")
    if statement.proof_latex.strip():
        obligations.append("split proof sketch into Lean-checkable intermediate lemmas")
    else:
        obligations.append("recover or request proof sketch before proof-worker promotion")
    return obligations


def _semantic_risk_flags(statement: PaperTheoryStatement, text_tokens: set[str]) -> list[str]:
    flags: list[str] = []
    if not statement.label:
        flags.append("missing_latex_label")
    if not statement.proof_latex.strip() and statement.kind in {"theorem", "lemma", "proposition", "corollary"}:
        flags.append("missing_proof_environment")
    if "standard" in text_tokens or "routine" in text_tokens or "obvious" in text_tokens:
        flags.append("proof_sketch_omits_standard_argument")
    if not (set(text_tokens) & {"assume", "assumption", "regularity", "independent", "randomized"}):
        flags.append("assumptions_may_be_implicit")
    return flags


def _lean_candidate_row(
    statement: PaperTheoryStatement,
    stat_theory_ir: dict[str, object],
) -> LeanCandidateQueueRow:
    declaration_name = _lean_name(statement)
    return LeanCandidateQueueRow(
        schema_version=PAPER_THEORY_ROUNDTRIP_SCHEMA_VERSION,
        queue_id=f"paper_theory_lean_candidate:{statement.statement_id}",
        paper_id=statement.paper_id,
        statement_id=statement.statement_id,
        statement_kind=statement.kind,
        label=statement.label,
        candidate_namespace=_lean_namespace(statement.paper_id),
        suggested_declaration_name=declaration_name,
        source_latex=statement.latex,
        stat_theory_ir=stat_theory_ir,
        dependency_labels=statement.dependency_labels,
        expected_output_contract={
            "write_jsonl": WORKER_OUTPUT_JSONL,
            "required_fields": [
                "queue_id",
                "statement_id",
                "lean_declarations",
                "kernel_verified",
                "axioms",
                "sorry_count",
                "semantic_review_status",
                "lean_to_latex_review_input",
                "evidence_paths",
            ],
            "zero_evidence_response": {
                "kernel_verified": False,
                "proof_evidence_ready": 0,
                "evidence_paths": [],
            },
            "local_kernel_evidence_rule": (
                "Only set proof_evidence_ready > 0 when exact Lean declarations "
                "compile without sorry/admit under local Lean/AXLE and verifier "
                "artifacts are attached."
            ),
        },
        acceptance_gate="local Lean/AXLE kernel verification plus semantic review against source span",
        forbidden_shortcuts=(
            "do not introduce an axiom that restates the target theorem",
            "do not weaken or omit statistical assumptions silently",
            "do not mark autoinformalized LaTeX as proof evidence",
        ),
        proof_evidence_ready=0,
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
    )


def _roundtrip_row(statement: PaperTheoryStatement) -> LeanToLatexRoundtripRow:
    return LeanToLatexRoundtripRow(
        schema_version=PAPER_THEORY_ROUNDTRIP_SCHEMA_VERSION,
        review_id=f"lean_to_latex_roundtrip_review:{statement.statement_id}",
        paper_id=statement.paper_id,
        statement_id=statement.statement_id,
        source_statement_label=statement.label,
        required_inputs=(
            "kernel-checked Lean declaration metadata",
            "Lean dependency cone",
            "autoinformalized LaTeX generated from Lean only",
            "original source span revealed only to semantic reviewer",
        ),
        expected_outputs=(
            "human-readable theorem/proof derivation",
            "dependency graph with proof status",
            "semantic drift notes",
            "axiom/open-gap highlights",
        ),
        semantic_review_gate=(
            "compare Lean-origin LaTeX against the source span for assumptions, "
            "estimand, conclusion, rates/constants, and proof dependencies"
        ),
        original_paper_hidden_from_informalizer=True,
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
    )


def _lean_name(statement: PaperTheoryStatement) -> str:
    raw = statement.label or statement.statement_id
    suffix = re.sub(r"[^A-Za-z0-9_]+", "_", raw).strip("_")
    if not suffix:
        suffix = statement.kind
    if suffix[0].isdigit():
        suffix = f"s_{suffix}"
    return suffix


def _lean_namespace(paper_id: str) -> str:
    raw = re.sub(r"[^A-Za-z0-9_]+", "_", paper_id).strip("_") or "PaperTheory"
    if raw[0].isdigit():
        raw = f"Paper_{raw}"
    return raw


def _dependency_graph(statements: list[PaperTheoryStatement]) -> dict[str, object]:
    by_label = {row.label: row.statement_id for row in statements if row.label}
    nodes = [
        {
            "id": row.statement_id,
            "kind": row.kind,
            "label": row.label,
            "source_path": row.source_path,
            "source_start_line": row.source_start_line,
            "source_end_line": row.source_end_line,
            "has_proof": bool(row.proof_latex.strip()),
        }
        for row in statements
    ]
    edges: list[dict[str, object]] = []
    for row in statements:
        for label in row.dependency_labels:
            edges.append(
                {
                    "src": row.statement_id,
                    "dst": by_label.get(label, label),
                    "label": label,
                    "edge_kind": "latex_reference",
                    "resolved": label in by_label,
                }
            )
    return {
        "nodes": nodes,
        "edges": edges,
        "n_nodes": len(nodes),
        "n_edges": len(edges),
        "n_unresolved_edges": sum(1 for edge in edges if not edge["resolved"]),
    }


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, default=str) + "\n" for row in rows),
        encoding="utf-8",
    )


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Paper Theory Round-Trip Export",
        "",
        "This MerLean-style export extracts TeX theorem-like statements, queues Lean realization work, and prepares Lean-origin LaTeX review packets.",
        "",
        f"- Paper: `{payload.get('paper_id')}`",
        f"- TeX files: {payload.get('n_tex_files')}",
        f"- Statements: {payload.get('n_statements')}",
        f"- Statements with proofs: {payload.get('n_with_proofs')}",
        f"- Dependency edges: {payload.get('n_dependency_edges')}",
        f"- StatTheory IR rows: {payload.get('n_stat_theory_ir_rows')}",
        f"- Lean candidate rows: {payload.get('n_lean_candidate_queue_rows')}",
        f"- Round-trip review rows: {payload.get('n_roundtrip_review_rows')}",
        f"- Proof evidence ready: {payload.get('n_proof_evidence_ready')}",
        f"- Proof status: `{payload.get('proof_evidence_status')}`",
        f"- Fingerprint: `{payload.get('dataset_fingerprint')}`",
        "",
        "## Preview",
        "",
        "| Statement | Kind | Source span | Proof |",
        "|---|---|---|---:|",
    ]
    for row in payload.get("statements_preview", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"| `{row.get('statement_id')}` | `{row.get('kind')}` | "
            f"{row.get('source_path')}:{row.get('source_start_line')}-{row.get('source_end_line')} | "
            f"{bool(row.get('proof_latex'))} |"
        )
    return "\n".join(lines) + "\n"
