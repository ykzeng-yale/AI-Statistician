from __future__ import annotations

import importlib
import importlib.util
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Mapping, Protocol, Sequence

from .fingerprint import stable_hash
from .formal_source_index import FormalDeclaration, FormalSourceHit
from .model_backend import GeneratorBackend, GeneratorRequest


LEAN_PROVIDER_BOUNDARY = (
    "External retrieval hits, generated proof bodies, verifier diagnostics, and "
    "OpenProver lemma assets are agent feedback. They do not prove the AI "
    "Statistician source theorem until its exact declaration passes the configured "
    "local Lean/AXLE gate."
)


class LeanProviderUnavailable(RuntimeError):
    """Raised when an explicitly configured external Lean provider cannot run."""


class FormalSourceSearchProvider(Protocol):
    name: str

    def search(self, query: str, *, k: int = 10) -> list[Any]:
        ...


class LeanProofSearchProvider(Protocol):
    name: str

    def run(self, request: Mapping[str, Any]) -> Mapping[str, Any]:
        ...


@dataclass(frozen=True)
class ExternalFormalSourceHit:
    declaration: FormalDeclaration
    score: float
    matched_terms: tuple[str, ...]
    provenance: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CompositeFormalSourceHit:
    declaration: FormalDeclaration
    score: float
    matched_terms: tuple[str, ...]
    provenance: Mapping[str, Any] = field(default_factory=dict)


class CompositeFormalSourceRetriever:
    """Fuse ranked provider results while retaining per-provider provenance."""

    name = "composite_formal_source_retriever"

    def __init__(self, providers: Sequence[FormalSourceSearchProvider]) -> None:
        self.providers = tuple(providers)
        if not self.providers:
            raise ValueError("CompositeFormalSourceRetriever requires at least one provider")
        self._runtime_diagnostics: list[dict[str, Any]] = []

    def reset_runtime_diagnostics(self) -> None:
        self._runtime_diagnostics.clear()

    def runtime_diagnostics(self) -> list[dict[str, Any]]:
        return [dict(row) for row in self._runtime_diagnostics]

    def descriptor(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "provider_count": len(self.providers),
            "providers": [provider_descriptor(provider) for provider in self.providers],
            "fusion": "reciprocal_rank_fusion",
            "boundary": LEAN_PROVIDER_BOUNDARY,
        }

    def search(self, query: str, *, k: int = 10) -> list[CompositeFormalSourceHit]:
        limit = max(int(k), 0)
        if limit == 0:
            return []
        fused: dict[tuple[str, str, int, str, str], dict[str, Any]] = {}
        query_fingerprint = stable_hash(query)
        provider_limit = max(limit * 2, limit)
        for provider_index, provider in enumerate(self.providers):
            provider_name = str(getattr(provider, "name", type(provider).__name__))
            diagnostic = {
                "provider": provider_name,
                "query_fingerprint": query_fingerprint,
                "query_chars": len(query),
                "requested_k": provider_limit,
                "status": "ok",
                "n_hits": 0,
            }
            try:
                hits = list(provider.search(query, k=provider_limit))
            except Exception as exc:
                diagnostic["status"] = "provider_error"
                diagnostic["error"] = f"{type(exc).__name__}: {str(exc)[:300]}"
                self._runtime_diagnostics.append(diagnostic)
                continue
            diagnostic["n_hits"] = len(hits)
            self._runtime_diagnostics.append(diagnostic)
            for rank, hit in enumerate(hits, start=1):
                declaration = getattr(hit, "declaration", None)
                if declaration is None:
                    continue
                raw_provenance = getattr(hit, "provenance", {})
                provenance = (
                    dict(raw_provenance) if isinstance(raw_provenance, Mapping) else {}
                )
                commit = str(provenance.get("commit", "") or "")
                key = (
                    str(getattr(declaration, "source_id", "") or ""),
                    str(getattr(declaration, "path", "") or ""),
                    int(getattr(declaration, "line", 0) or 0),
                    str(getattr(declaration, "name", "") or ""),
                    commit,
                )
                row = fused.setdefault(
                    key,
                    {
                        "declaration": declaration,
                        "score": 0.0,
                        "matched_terms": set(),
                        "provider_support": [],
                    },
                )
                row["score"] += 1.0 / (60.0 + rank)
                row["matched_terms"].update(
                    str(value)
                    for value in getattr(hit, "matched_terms", ())
                    if str(value)
                )
                row["provider_support"].append(
                    {
                        "provider": provider_name,
                        "provider_index": provider_index,
                        "rank": rank,
                        "raw_score": float(getattr(hit, "score", 0.0) or 0.0),
                        "provenance": provenance,
                    }
                )
        ordered = sorted(
            fused.values(),
            key=lambda row: (
                -float(row["score"]),
                str(row["declaration"].name),
                str(row["declaration"].path),
                int(row["declaration"].line),
            ),
        )[:limit]
        return [
            CompositeFormalSourceHit(
                declaration=row["declaration"],
                score=float(row["score"]),
                matched_terms=tuple(sorted(row["matched_terms"]))[:16],
                provenance={
                    "retrieval_fusion": "reciprocal_rank_fusion",
                    "provider_support": row["provider_support"],
                    "query_fingerprint": query_fingerprint,
                    "proof_evidence_status": (
                        "FORMAL_SOURCE_RETRIEVAL_NOT_PROOF_EVIDENCE"
                    ),
                    "proof_evidence_boundary": LEAN_PROVIDER_BOUNDARY,
                },
            )
            for row in ordered
        ]


class EmpericalProcessLeanRetrievalProvider:
    """Call EmpericalProcessLEAN's declaration-graph search API directly."""

    name = "emperical_process_lean_shared_proof_retrieval"

    def __init__(
        self,
        *,
        root: Path,
        db_dir: Path | str = Path("build/lean_graph"),
        source: str = "all",
        checkouts: Sequence[str] = (),
        no_sorry: bool = True,
        with_graph_context: bool = True,
        module_loader: Callable[[], ModuleType] | None = None,
    ) -> None:
        self.root = Path(root).expanduser().resolve()
        raw_db_dir = Path(db_dir).expanduser()
        self.db_dir = (
            raw_db_dir.resolve()
            if raw_db_dir.is_absolute()
            else (self.root / raw_db_dir).resolve()
        )
        self.source = source
        self.checkouts = tuple(str(value) for value in checkouts if str(value))
        self.no_sorry = bool(no_sorry)
        self.with_graph_context = bool(with_graph_context)
        self._module_loader = module_loader
        self._module: ModuleType | None = None

    @property
    def script_path(self) -> Path:
        return self.root / "lean_rag" / "scripts" / "shared_proof_retrieval.py"

    def descriptor(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "repository": "ykzeng-yale/EmpericalProcessLEAN",
            "root": str(self.root),
            "script_path": str(self.script_path),
            "db_dir": str(self.db_dir),
            "source": self.source,
            "checkouts": list(self.checkouts),
            "available": self.script_path.is_file(),
            "repository_provenance": _git_provenance(self.root),
            "boundary": LEAN_PROVIDER_BOUNDARY,
        }

    def search(self, query: str, *, k: int = 10) -> list[ExternalFormalSourceHit]:
        limit = max(int(k), 0)
        if limit == 0:
            return []
        module = self._load_module()
        try:
            manifest = list(module.load_manifest(self.db_dir))
        except SystemExit as exc:
            raise LeanProviderUnavailable(str(exc)) from exc
        except (OSError, ValueError) as exc:
            raise LeanProviderUnavailable(
                f"cannot load EmpericalProcessLEAN retrieval manifest: {exc}"
            ) from exc
        entries = list(
            module.iter_searchable_entries(
                manifest,
                self.source,
                self.checkouts or None,
            )
        )
        per_checkout = max(limit, 4)
        hits: list[ExternalFormalSourceHit] = []
        for entry in entries:
            db = Path(str(entry.get("db", "") or ""))
            if not db.exists():
                continue
            rows = module.search_db(db, query, per_checkout, self.no_sorry)
            for rank, row in enumerate(rows, start=1):
                if len(hits) >= limit:
                    break
                provenance = self._hit_provenance(
                    module,
                    entry=entry,
                    db=db,
                    row=row,
                    rank=rank,
                )
                row_path = str(_row_value(row, "path", "") or "")
                source_path = module.source_path(entry, row_path)
                declaration = FormalDeclaration(
                    source_id=(
                        "emperical_process_lean:"
                        + str(entry.get("name", "checkout") or "checkout")
                    ),
                    source_type="lean_shared_declaration_graph",
                    path=str(source_path),
                    line=int(_row_value(row, "line_start", 0) or 0),
                    kind=str(_row_value(row, "kind", "declaration") or "declaration"),
                    name=str(_row_value(row, "name", "") or ""),
                    namespace=str(_row_value(row, "module", "") or ""),
                    signature=str(_row_value(row, "signature", "") or ""),
                )
                raw_score = _row_value(row, "match_score", None)
                score = float(raw_score) if raw_score is not None else 1.0 / rank
                hits.append(
                    ExternalFormalSourceHit(
                        declaration=declaration,
                        score=score,
                        matched_terms=tuple(
                            str(value)
                            for value in module.query_tokens(query)[:16]
                            if str(value)
                        ),
                        provenance=provenance,
                    )
                )
            if len(hits) >= limit:
                break
        return hits[:limit]

    def _load_module(self) -> ModuleType:
        if self._module is not None:
            return self._module
        if self._module_loader is not None:
            self._module = self._module_loader()
            return self._module
        if not self.script_path.is_file():
            raise LeanProviderUnavailable(
                "EmpericalProcessLEAN shared retrieval script is missing at "
                f"{self.script_path}"
            )
        module_name = "ai_statistician_external_shared_proof_retrieval_" + stable_hash(
            str(self.script_path)
        )[:12]
        spec = importlib.util.spec_from_file_location(module_name, self.script_path)
        if spec is None or spec.loader is None:
            raise LeanProviderUnavailable(
                f"cannot import EmpericalProcessLEAN provider from {self.script_path}"
            )
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except Exception:
            sys.modules.pop(module_name, None)
            raise
        self._module = module
        return module

    def _hit_provenance(
        self,
        module: ModuleType,
        *,
        entry: Mapping[str, Any],
        db: Path,
        row: Any,
        rank: int,
    ) -> dict[str, Any]:
        checkout_path = Path(str(entry.get("path", "") or self.root))
        branch = str(entry.get("branch", "") or "")
        commit = str(entry.get("commit", "") or "")
        dirty = bool(entry.get("dirty", False))
        index_signature_state = "unknown"
        if hasattr(module, "index_signature_state"):
            try:
                index_signature_state = str(
                    module.index_signature_state(dict(entry), checkout_path)
                )
            except Exception:
                index_signature_state = "unknown"
        graph: dict[str, Any] = {}
        decl_id = _row_value(row, "id", None)
        if self.with_graph_context and decl_id is not None:
            try:
                uses, used_by = module.graph_context(db, int(decl_id), 4)
            except Exception:
                pass
            else:
                graph = {
                    "uses": [_graph_row_json(value) for value in uses],
                    "used_by": [_graph_row_json(value) for value in used_by],
                }
        return {
            "provider": self.name,
            "repository": "ykzeng-yale/EmpericalProcessLEAN",
            "repository_root": str(self.root),
            "checkout_name": str(entry.get("name", "") or ""),
            "checkout_role": str(entry.get("role", "") or ""),
            "checkout_path": str(checkout_path),
            "branch": branch,
            "commit": commit,
            "dirty": dirty,
            "db": str(db),
            "manifest": str(self.db_dir / "shared_manifest.json"),
            "index_signature_state": index_signature_state,
            "rank": rank,
            "fan_in": float(_row_value(row, "fan_in", 0.0) or 0.0),
            "fan_out": float(_row_value(row, "fan_out", 0.0) or 0.0),
            "graph_context": graph,
            "no_sorry_filter": self.no_sorry,
            "proof_evidence_status": "RETRIEVED_DECLARATION_NOT_PROOF_EVIDENCE",
            "proof_evidence_boundary": LEAN_PROVIDER_BOUNDARY,
        }


@dataclass(frozen=True)
class OpenProverHLMConfig:
    root: Path
    out_dir: Path
    lean_project: Path | None = None
    model: str = ""
    max_tokens: int = 1600
    temperature: float = 0.1
    max_rounds: int = 2
    branches_per_round: int = 4
    feedback_top_k: int = 4
    max_attempts: int = 120
    route_strategy: str = "hybrid"
    verifier_timeout_s: int = 120
    require_lake_project: bool = True


class GeneratorBackendCandidatePolicy:
    """Expose AI-Statistician's negotiated LLM backend as an OpenProver policy."""

    def __init__(
        self,
        *,
        provider: GeneratorBackend,
        model: str,
        max_tokens: int,
        temperature: float,
        proof_generation_prompt: Callable[[Any, int], str],
        extract_proof_candidates: Callable[[str], Sequence[str]],
        candidate_contract_violations: Callable[[Sequence[str]], Sequence[Any]],
    ) -> None:
        self.provider = provider
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._proof_generation_prompt = proof_generation_prompt
        self._extract_proof_candidates = extract_proof_candidates
        self._candidate_contract_violations = candidate_contract_violations
        provider_name = str(getattr(provider, "provider_name", type(provider).__name__))
        self.name = f"ai-statistician-generator:{provider_name}"
        self.last_diagnostics: dict[str, Any] = {}

    def propose(self, task: Any, n: int) -> list[str]:
        prompt = self._proof_generation_prompt(task, n)
        request = GeneratorRequest(
            system_prompt=(
                "You generate only Lean proof bodies for OpenProver. Return the "
                "requested fenced Lean candidates; OpenProver owns route allocation, "
                "verification, failed-branch mining, and search."
            ),
            user_prompt=prompt,
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            schema=None,
            metadata={
                "subsystem": "OpenProverHLM",
                "agent": "GeneratorBackendCandidatePolicy",
                "requested_candidates": n,
            },
        )
        try:
            response = self.provider.generate(request)
        except Exception as exc:
            self.last_diagnostics = {
                "status": "provider_error",
                "error": f"{type(exc).__name__}: {str(exc)[:300]}",
                "requested_candidates": n,
                "extracted_candidates": 0,
            }
            return []
        candidates = [
            str(value).strip()
            for value in self._extract_proof_candidates(response.text)
            if str(value).strip()
        ][:n]
        accepted_candidates: list[str] = []
        violations: list[dict[str, Any]] = []
        for candidate_index, candidate in enumerate(candidates):
            candidate_violations = list(
                self._candidate_contract_violations([candidate])
            )
            if not candidate_violations:
                accepted_candidates.append(candidate)
                continue
            for violation in candidate_violations:
                if isinstance(violation, Mapping):
                    row = dict(violation)
                    row["candidate_index"] = candidate_index
                else:
                    row = {
                        "candidate_index": candidate_index,
                        "violations": [str(violation)],
                    }
                violations.append(row)
        self.last_diagnostics = {
            "status": (
                "ok"
                if not violations
                else "partial_contract_rejection"
                if accepted_candidates
                else "contract_rejected"
            ),
            "provider": response.provider,
            "model": response.model,
            "requested_candidates": n,
            "extracted_candidates": len(candidates),
            "accepted_candidates": len(accepted_candidates),
            "rejected_candidates": len(candidates) - len(accepted_candidates),
            "candidate_contract_violations": violations[:12],
            "response_metadata": (
                dict(response.metadata) if isinstance(response.metadata, Mapping) else {}
            ),
        }
        return accepted_candidates


class OpenProverHLMProofSearchProvider:
    """Drive OpenProver's verifier-backed HLM controller for a repair task."""

    name = "openprover_hlm_controller"

    def __init__(
        self,
        *,
        generator_backend: GeneratorBackend,
        config: OpenProverHLMConfig,
        runtime_loader: Callable[[], Mapping[str, Any]] | None = None,
    ) -> None:
        self.generator_backend = generator_backend
        self.config = config
        self._runtime_loader = runtime_loader
        self._runtime: Mapping[str, Any] | None = None

    def descriptor(self) -> dict[str, Any]:
        root = self.config.root.expanduser().resolve()
        return {
            "name": self.name,
            "repository": "ykzeng-yale/OpenProver",
            "root": str(root),
            "available": (root / "src" / "openprover" / "controller.py").is_file(),
            "repository_provenance": _git_provenance(root),
            "model": self.config.model,
            "max_rounds": self.config.max_rounds,
            "branches_per_round": self.config.branches_per_round,
            "feedback_top_k": self.config.feedback_top_k,
            "max_attempts": self.config.max_attempts,
            "route_strategy": self.config.route_strategy,
            "lean_project": str(self.config.lean_project or ""),
            "boundary": LEAN_PROVIDER_BOUNDARY,
        }

    def run(self, request: Mapping[str, Any]) -> Mapping[str, Any]:
        request_payload = dict(request)
        request_fingerprint = str(
            request_payload.get("request_fingerprint", "")
            or stable_hash(request_payload)
        )
        target_statement = str(
            request_payload.get("target_theorem_statement", "") or ""
        ).strip()
        target_declaration = str(
            request_payload.get("target_lean_declaration", "") or ""
        ).strip()
        if not target_statement or not target_declaration:
            raise ValueError(
                "OpenProver HLM requires target_theorem_statement and "
                "target_lean_declaration"
            )
        lean_project = self.config.lean_project
        if self.config.require_lake_project and (
            lean_project is None or not lean_project.expanduser().exists()
        ):
            return self._blocked_result(
                request_fingerprint,
                target_declaration=target_declaration,
                reason="configured OpenProver Lake project is missing",
            )
        runtime = self._load_runtime()
        parser_statement = target_statement
        if ":=" not in parser_statement:
            parser_statement += " := by"
        theorem_name, context, target = runtime["parse_theorem_signature"](
            parser_statement
        )
        header = str(request_payload.get("lean_header", "") or "").strip()
        if not header:
            header = "\n".join(
                str(value)
                for value in request_payload.get("candidate_imports", []) or []
                if str(value).strip()
            )
        policy = GeneratorBackendCandidatePolicy(
            provider=self.generator_backend,
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            proof_generation_prompt=runtime["proof_generation_prompt"],
            extract_proof_candidates=runtime["extract_proof_candidates"],
            candidate_contract_violations=runtime[
                "candidate_contract_violations"
            ],
        )
        backend = (
            runtime["LakeLeanBackend"](
                lake_cwd=lean_project,
                timeout_s=self.config.verifier_timeout_s,
            )
            if lean_project is not None
            else runtime["LocalLeanBackend"](
                timeout_s=self.config.verifier_timeout_s
            )
        )
        feedback_text = "\n".join(
            str(value)
            for value in (
                request_payload.get("failed_proof_body_attempts", []) or []
            )
            if str(value)
        )
        residual_goals = tuple(
            str(value)
            for value in request_payload.get("residual_goal_excerpt", []) or []
            if str(value)
        )
        initial_failure_feedback = [
            runtime["FailureFeedback"](
                branch="ai_statistician_current_candidate",
                route="whole_proof",
                round=0,
                proof_excerpt=str(
                    request_payload.get("current_proof_body_excerpt", "") or ""
                )[:1200],
                error_tail=feedback_text[:1800],
                error_kind="ai_statistician_exact_whole_proof_failure",
                goal_snapshots=residual_goals[:4],
            )
        ]
        run_dir = self.config.out_dir / request_fingerprint[:20]
        report_path = run_dir / "openprover_hlm_report.json"
        checkpoint_path = run_dir / "openprover_hlm_checkpoint.json"
        report = runtime["run_policy_hlm_controller"](
            name=theorem_name,
            target=target,
            context=list(context),
            header=header,
            policy=policy,
            backend=backend,
            out_path=report_path,
            rounds=self.config.max_rounds,
            branches_per_round=self.config.branches_per_round,
            feedback_top_k=self.config.feedback_top_k,
            max_attempts=self.config.max_attempts,
            stop_on_success=True,
            adaptive_route_allocation=True,
            route_strategy=self.config.route_strategy,
            initial_failure_feedback=initial_failure_feedback,
            checkpoint_path=checkpoint_path,
        )
        return self._compact_result(
            report,
            request_fingerprint=request_fingerprint,
            target_declaration=target_declaration,
            report_path=report_path,
            checkpoint_path=checkpoint_path,
            policy=policy,
        )

    def _load_runtime(self) -> Mapping[str, Any]:
        if self._runtime is not None:
            return self._runtime
        if self._runtime_loader is not None:
            self._runtime = dict(self._runtime_loader())
            return self._runtime
        root = self.config.root.expanduser().resolve()
        src = root / "src"
        controller_path = src / "openprover" / "controller.py"
        if not controller_path.is_file():
            raise LeanProviderUnavailable(
                f"OpenProver controller is missing at {controller_path}"
            )
        src_text = str(src)
        if src_text not in sys.path:
            sys.path.insert(0, src_text)
        controller = importlib.import_module("openprover.controller")
        policies = importlib.import_module("openprover.policies")
        public_hlm = importlib.import_module("openprover.benchmarks.public_hlm")
        verifier = importlib.import_module("openprover.verifier")
        loaded_controller = Path(str(controller.__file__ or "")).resolve()
        if src not in loaded_controller.parents:
            raise LeanProviderUnavailable(
                "an OpenProver package from a different checkout is already loaded: "
                f"{loaded_controller}"
            )
        self._runtime = {
            "run_policy_hlm_controller": controller.run_policy_hlm_controller,
            "FailureFeedback": controller.FailureFeedback,
            "parse_theorem_signature": public_hlm.parse_theorem_signature,
            "proof_generation_prompt": policies.proof_generation_prompt,
            "extract_proof_candidates": policies.extract_proof_candidates,
            "candidate_contract_violations": (
                policies.candidate_contract_violations
            ),
            "LakeLeanBackend": verifier.LakeLeanBackend,
            "LocalLeanBackend": verifier.LocalLeanBackend,
        }
        return self._runtime

    def _compact_result(
        self,
        report: Mapping[str, Any],
        *,
        request_fingerprint: str,
        target_declaration: str,
        report_path: Path,
        checkpoint_path: Path,
        policy: GeneratorBackendCandidatePolicy,
    ) -> dict[str, Any]:
        summary = (
            dict(report.get("summary", {}))
            if isinstance(report.get("summary", {}), Mapping)
            else {}
        )
        proof_bodies = _openprover_direct_proof_bodies(report)
        assets = [
            _compact_openprover_asset(row)
            for row in report.get("assets", []) or []
            if isinstance(row, Mapping)
        ][:8]
        failure_feedback = [
            _compact_openprover_failure_feedback(row)
            for row in report.get("failure_feedback", []) or []
            if isinstance(row, Mapping)
        ][:8]
        result_id = "openprover_hlm_result:" + stable_hash(
            [request_fingerprint, summary, proof_bodies, assets]
        )[:20]
        return {
            "schema_version": 1,
            "artifact_kind": "RuntimeOpenProverHLMProofSearchResult",
            "result_id": result_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "provider": self.name,
            "provider_descriptor": self.descriptor(),
            "request_fingerprint": request_fingerprint,
            "target_lean_declaration": target_declaration,
            "status": (
                "DIRECT_CANDIDATE_AVAILABLE"
                if proof_bodies
                else "VERIFIED_SUPPORT_ASSETS_AVAILABLE"
                if assets
                else "NO_CANDIDATE_FOUND"
            ),
            "openprover_summary": {
                key: summary.get(key)
                for key in (
                    "backend",
                    "rounds_run",
                    "final_solved",
                    "direct_target_solved",
                    "final_cumulative_solved",
                    "total_branches",
                    "total_verified_assets",
                    "total_checked_local_facts",
                    "total_valid_prefix_steps",
                    "total_failure_feedback_items",
                    "route_strategy",
                )
                if key in summary
            },
            "source_theorem_candidate_proof_bodies": proof_bodies,
            "verified_support_assets": assets,
            "failure_feedback": failure_feedback,
            "policy_diagnostics": dict(policy.last_diagnostics),
            "report_path": str(report_path),
            "checkpoint_path": str(checkpoint_path),
            "proof_evidence_status": (
                "OPENPROVER_HLM_RESULT_REQUIRES_EXACT_AI_STATISTICIAN_KERNEL_RERUN"
            ),
            "proof_evidence_boundary": LEAN_PROVIDER_BOUNDARY,
        }

    def _blocked_result(
        self,
        request_fingerprint: str,
        *,
        target_declaration: str,
        reason: str,
    ) -> dict[str, Any]:
        result_id = "openprover_hlm_result:" + stable_hash(
            [request_fingerprint, target_declaration, reason]
        )[:20]
        return {
            "schema_version": 1,
            "artifact_kind": "RuntimeOpenProverHLMProofSearchResult",
            "result_id": result_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "provider": self.name,
            "provider_descriptor": self.descriptor(),
            "request_fingerprint": request_fingerprint,
            "target_lean_declaration": target_declaration,
            "status": "BLOCKED_PROVIDER_ENVIRONMENT",
            "blocker": reason,
            "source_theorem_candidate_proof_bodies": [],
            "verified_support_assets": [],
            "failure_feedback": [],
            "proof_evidence_status": "OPENPROVER_HLM_BLOCKED_NOT_PROOF_EVIDENCE",
            "proof_evidence_boundary": LEAN_PROVIDER_BOUNDARY,
        }


def provider_descriptor(provider: Any) -> dict[str, Any]:
    descriptor = getattr(provider, "descriptor", None)
    if callable(descriptor):
        try:
            value = descriptor()
        except Exception as exc:
            return {
                "name": str(getattr(provider, "name", type(provider).__name__)),
                "descriptor_error": f"{type(exc).__name__}: {str(exc)[:240]}",
                "boundary": LEAN_PROVIDER_BOUNDARY,
            }
        if isinstance(value, Mapping):
            return dict(value)
    return {
        "name": str(getattr(provider, "name", type(provider).__name__)),
        "type": f"{type(provider).__module__}.{type(provider).__name__}",
        "boundary": LEAN_PROVIDER_BOUNDARY,
    }


def reset_provider_runtime_diagnostics(provider: Any) -> None:
    reset = getattr(provider, "reset_runtime_diagnostics", None)
    if callable(reset):
        reset()


def provider_runtime_diagnostics(provider: Any) -> list[dict[str, Any]]:
    diagnostics = getattr(provider, "runtime_diagnostics", None)
    if not callable(diagnostics):
        return []
    try:
        rows = diagnostics()
    except Exception as exc:
        return [
            {
                "status": "diagnostics_error",
                "error": f"{type(exc).__name__}: {str(exc)[:240]}",
            }
        ]
    return [dict(row) for row in rows if isinstance(row, Mapping)]


def _row_value(row: Any, key: str, default: Any) -> Any:
    try:
        keys = row.keys()
    except AttributeError:
        return row.get(key, default) if isinstance(row, Mapping) else default
    return row[key] if key in keys else default


def _graph_row_json(row: Any) -> dict[str, Any]:
    try:
        keys = row.keys()
    except AttributeError:
        return dict(row) if isinstance(row, Mapping) else {"value": str(row)}
    return {str(key): row[key] for key in keys}


def _git_provenance(root: Path) -> dict[str, Any]:
    def git(*args: str) -> str:
        try:
            proc = subprocess.run(
                ["git", "-C", str(root), *args],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return ""
        return proc.stdout.strip() if proc.returncode == 0 else ""

    return {
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "commit": git("rev-parse", "HEAD"),
        "dirty": bool(git("status", "--short")),
    }


def _openprover_direct_proof_bodies(report: Mapping[str, Any]) -> list[str]:
    candidates: list[str] = []
    sources: list[Any] = [
        report.get("direct_solution"),
        report.get("final_search"),
        *(report.get("direct_successes", []) or []),
    ]
    for source in sources:
        if not isinstance(source, Mapping):
            continue
        for key in ("proof", "script", "proof_body", "candidate"):
            value = str(source.get(key, "") or "").strip()
            if not value or _forbidden_proof_body(value):
                continue
            if value not in candidates:
                candidates.append(value)
            if len(candidates) >= 8:
                return candidates
    return candidates


def _forbidden_proof_body(source: str) -> bool:
    return bool(re.search(r"\b(sorry|admit|axiom|unsafe)\b", source, flags=re.I))


def _compact_openprover_asset(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: row.get(key)
        for key in (
            "name",
            "task",
            "branch",
            "statement",
            "proof",
            "theorem_src",
            "call_expr",
            "minimized_context",
            "removed_binders",
            "axioms_report",
            "utility_score",
            "proof_source",
        )
        if row.get(key) not in (None, "", [], {})
    }


def _compact_openprover_failure_feedback(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: row.get(key)
        for key in (
            "branch",
            "route",
            "round",
            "proof_excerpt",
            "error_tail",
            "error_kind",
            "unknown_identifiers",
            "repair_hints",
            "goal_snapshots",
        )
        if row.get(key) not in (None, "", [], {})
    }
