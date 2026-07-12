from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

from ai_statistician.formal_source_index import FormalDeclaration
from ai_statistician.lean_agent_providers import (
    LEAN_PROVIDER_BOUNDARY,
    CompositeFormalSourceRetriever,
    EmpericalProcessLeanRetrievalProvider,
    ExternalFormalSourceHit,
    GeneratorBackendCandidatePolicy,
    OpenProverHLMConfig,
    OpenProverHLMProofSearchProvider,
)
from ai_statistician.model_backend import GeneratorResponse


def _declaration(name: str, *, source_id: str = "local") -> FormalDeclaration:
    return FormalDeclaration(
        source_id=source_id,
        source_type="lean_library",
        path="StatInference/Test.lean",
        line=12,
        kind="theorem",
        name=name,
        namespace="StatInference",
        signature=f"theorem {name} (p : Prop) (hp : p) : p",
    )


def test_composite_formal_source_retriever_fuses_and_records_provider_failure() -> None:
    shared = ExternalFormalSourceHit(
        declaration=_declaration("StatInference.shared"),
        score=9.0,
        matched_terms=("shared",),
        provenance={"commit": "abc123", "branch": "main"},
    )

    @dataclass
    class Provider:
        name: str
        hits: list[ExternalFormalSourceHit]

        def search(self, _query: str, *, k: int = 10):
            return self.hits[:k]

    class BrokenProvider:
        name = "broken"

        def search(self, _query: str, *, k: int = 10):
            del k
            raise RuntimeError("index unavailable")

    retriever = CompositeFormalSourceRetriever(
        (
            Provider("first", [shared]),
            Provider("second", [shared]),
            BrokenProvider(),
        )
    )

    hits = retriever.search("shared theorem", k=3)

    assert len(hits) == 1
    assert hits[0].declaration.name == "StatInference.shared"
    support = hits[0].provenance["provider_support"]
    assert [row["provider"] for row in support] == ["first", "second"]
    assert hits[0].provenance["retrieval_fusion"] == "reciprocal_rank_fusion"
    diagnostics = retriever.runtime_diagnostics()
    assert [row["status"] for row in diagnostics] == ["ok", "ok", "provider_error"]
    assert "index unavailable" in diagnostics[-1]["error"]


def test_emperical_process_lean_provider_calls_structured_graph_api(
    tmp_path: Path,
) -> None:
    root = tmp_path / "EmpericalProcessLEAN"
    root.mkdir()
    db = root / "build" / "lean_graph" / "stat_inference.sqlite"
    db.parent.mkdir(parents=True)
    db.write_text("fixture", encoding="utf-8")
    checkout = root / "checkout"
    (checkout / "StatInference").mkdir(parents=True)

    class FakeSharedRetrievalModule:
        @staticmethod
        def load_manifest(_db_dir: Path):
            return [
                {
                    "name": "main",
                    "role": "main",
                    "path": str(checkout),
                    "db": str(db),
                    "branch": "codex/lean-reuse-source-integration",
                    "commit": "e8d5513d",
                    "dirty": False,
                    "indexed": True,
                }
            ]

        @staticmethod
        def iter_searchable_entries(manifest, _source, _checkouts):
            return list(manifest)

        @staticmethod
        def search_db(_db: Path, query: str, limit: int, no_sorry: bool):
            assert query == "exchangeability coverage"
            assert no_sorry is True
            return [
                {
                    "id": 7,
                    "name": "StatInference.exchangeable_coverage",
                    "kind": "theorem",
                    "path": "StatInference/Test.lean",
                    "line_start": 42,
                    "module": "StatInference.Test",
                    "signature": "theorem exchangeable_coverage : True",
                    "match_score": 8,
                    "fan_in": 3,
                    "fan_out": 5,
                }
            ][:limit]

        @staticmethod
        def source_path(entry, path: str):
            return Path(entry["path"]) / path

        @staticmethod
        def query_tokens(query: str):
            return query.split()

        @staticmethod
        def graph_context(_db: Path, _decl_id: int, _limit: int):
            return (
                [{"name": "StatInference.exchangeable", "scope": "same_file"}],
                [{"name": "StatInference.main_theorem", "scope": "repository"}],
            )

        @staticmethod
        def index_signature_state(_entry, _root: Path):
            return "unchanged"

    provider = EmpericalProcessLeanRetrievalProvider(
        root=root,
        module_loader=lambda: FakeSharedRetrievalModule(),  # type: ignore[arg-type]
    )

    hits = provider.search("exchangeability coverage", k=3)

    assert len(hits) == 1
    hit = hits[0]
    assert hit.declaration.name == "StatInference.exchangeable_coverage"
    assert hit.provenance["branch"] == "codex/lean-reuse-source-integration"
    assert hit.provenance["commit"] == "e8d5513d"
    assert hit.provenance["index_signature_state"] == "unchanged"
    assert hit.provenance["graph_context"]["uses"][0]["name"] == (
        "StatInference.exchangeable"
    )
    assert hit.provenance["no_sorry_filter"] is True


def test_emperical_process_lean_provider_globally_ranks_and_rejects_stale_hits(
    tmp_path: Path,
) -> None:
    root = tmp_path / "EmpericalProcessLEAN"
    entries = []
    for name, state in (
        ("first", "unchanged"),
        ("stale", "changed"),
        ("best", "unchanged"),
    ):
        checkout = root / name
        checkout.mkdir(parents=True)
        db = root / "build" / "lean_graph" / f"{name}.sqlite"
        db.parent.mkdir(parents=True, exist_ok=True)
        db.write_text("fixture", encoding="utf-8")
        entries.append(
            {
                "name": name,
                "role": "fixture",
                "path": str(checkout),
                "db": str(db),
                "branch": name,
                "commit": f"commit-{name}",
                "dirty": False,
                "indexed": True,
                "fixture_signature_state": state,
            }
        )

    class FakeSharedRetrievalModule:
        @staticmethod
        def load_manifest(_db_dir: Path):
            return entries

        @staticmethod
        def iter_searchable_entries(manifest, _source, _checkouts):
            return list(manifest)

        @staticmethod
        def search_db(db: Path, _query: str, _limit: int, _no_sorry: bool):
            name = db.stem
            score = {"first": 1, "stale": 100, "best": 9}[name]
            return [
                {
                    "id": score,
                    "name": f"Fixture.{name}",
                    "kind": "theorem",
                    "path": f"Fixture/{name}.lean",
                    "line_start": score,
                    "module": "Fixture",
                    "signature": f"theorem {name} : True",
                    "match_score": score,
                }
            ]

        @staticmethod
        def source_path(entry, path: str):
            return Path(entry["path"]) / path

        @staticmethod
        def query_tokens(query: str):
            return query.split()

        @staticmethod
        def graph_context(_db: Path, _decl_id: int, _limit: int):
            return ([], [])

        @staticmethod
        def index_signature_state(entry, _root: Path):
            return entry["fixture_signature_state"]

    provider = EmpericalProcessLeanRetrievalProvider(
        root=root,
        module_loader=lambda: FakeSharedRetrievalModule(),  # type: ignore[arg-type]
    )

    hits = provider.search("target", k=1)

    assert [hit.declaration.name for hit in hits] == ["Fixture.best"]
    diagnostics = provider.runtime_diagnostics()
    assert any(row["status"] == "stale_index_rejected" for row in diagnostics)
    assert diagnostics[-1]["ranking"] == "global_score_across_checkouts"


def test_emperical_process_lean_provider_rejects_unsigned_and_dirty_indexes(
    tmp_path: Path,
) -> None:
    root = tmp_path / "EmpericalProcessLEAN"
    entries = []
    for name, state, dirty in (
        ("unsigned", "unknown", False),
        ("dirty", "unchanged", True),
    ):
        checkout = root / name
        checkout.mkdir(parents=True)
        db = root / "build" / "lean_graph" / f"{name}.sqlite"
        db.parent.mkdir(parents=True, exist_ok=True)
        db.write_text("fixture", encoding="utf-8")
        entries.append(
            {
                "name": name,
                "path": str(checkout),
                "db": str(db),
                "dirty": dirty,
                "fixture_signature_state": state,
            }
        )

    class FakeSharedRetrievalModule:
        @staticmethod
        def load_manifest(_db_dir: Path):
            return entries

        @staticmethod
        def iter_searchable_entries(manifest, _source, _checkouts):
            return list(manifest)

        @staticmethod
        def index_signature_state(entry, _root: Path):
            return entry["fixture_signature_state"]

        @staticmethod
        def git_dirty(checkout: Path):
            return checkout.name == "dirty"

        @staticmethod
        def search_db(*_args, **_kwargs):
            raise AssertionError("rejected indexes must not be searched")

    provider = EmpericalProcessLeanRetrievalProvider(
        root=root,
        module_loader=lambda: FakeSharedRetrievalModule(),  # type: ignore[arg-type]
    )

    assert provider.search("target", k=2) == []
    diagnostics = provider.runtime_diagnostics()
    assert any(row["status"] == "unsigned_index_rejected" for row in diagnostics)
    assert any(row["status"] == "dirty_checkout_rejected" for row in diagnostics)
    descriptor = provider.descriptor()
    assert descriptor["reject_unknown_index_signature"] is True
    assert descriptor["reject_dirty_checkout"] is True


def test_emperical_process_lean_dynamic_loader_registers_dataclass_module(
    tmp_path: Path,
) -> None:
    root = tmp_path / "EmpericalProcessLEAN"
    script = root / "lean_rag" / "scripts" / "shared_proof_retrieval.py"
    script.parent.mkdir(parents=True)
    script.write_text(
        "from dataclasses import dataclass\n\n"
        "@dataclass(frozen=True)\n"
        "class FixtureRow:\n"
        "    value: int\n",
        encoding="utf-8",
    )
    provider = EmpericalProcessLeanRetrievalProvider(root=root)

    module = provider._load_module()

    assert module.FixtureRow(7).value == 7


def test_generator_backend_candidate_policy_reuses_negotiated_backend() -> None:
    class Backend:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests = []

        def generate(self, request):
            self.requests.append(request)
            return GeneratorResponse(
                text='{"candidates":["exact hp"]}',
                provider="anthropic",
                model=request.model,
                metadata={"capability_fallback_count": 1},
            )

    backend = Backend()
    policy = GeneratorBackendCandidatePolicy(
        provider=backend,  # type: ignore[arg-type]
        model="claude-opus-4-8",
        max_tokens=800,
        temperature=0.1,
        proof_generation_prompt=lambda _task, n: f"return {n}",
    )

    candidates = policy.propose(SimpleNamespace(), 1)

    assert candidates == ["exact hp"]
    assert backend.requests[0].metadata["subsystem"] == "OpenProverHLM"
    assert policy.last_diagnostics["response_metadata"][
        "capability_fallback_count"
    ] == 1


def test_generator_backend_candidate_policy_keeps_valid_siblings() -> None:
    class Backend:
        provider_name = "anthropic"

        def generate(self, request):
            return GeneratorResponse(
                text='{"candidates":["exact hp","sorry"]}',
                provider="anthropic",
                model=request.model,
            )

    policy = GeneratorBackendCandidatePolicy(
        provider=Backend(),  # type: ignore[arg-type]
        model="claude-opus-4-8",
        max_tokens=800,
        temperature=0.1,
        proof_generation_prompt=lambda _task, n: f"return {n}",
    )

    candidates = policy.propose(SimpleNamespace(), 2)

    assert candidates == ["exact hp"]
    assert policy.last_diagnostics["status"] == "partial_contract_rejection"
    assert policy.last_diagnostics["accepted_candidates"] == 1
    assert policy.last_diagnostics["rejected_candidates"] == 1
    violations = policy.last_diagnostics["candidate_contract_violations"]
    assert len(violations) == 1
    assert violations[0]["violations"] == ["forbidden proof-evidence token"]


def test_openprover_hlm_provider_returns_candidates_as_nonproof_feedback(
    tmp_path: Path,
) -> None:
    root = tmp_path / "OpenProver"
    controller = root / "src" / "openprover" / "controller.py"
    controller.parent.mkdir(parents=True)
    controller.write_text("# fixture\n", encoding="utf-8")
    lean_project = tmp_path / "lean-project"
    lean_project.mkdir()

    class Backend:
        provider_name = "anthropic"

        def generate(self, request):
            if request.metadata.get("agent") == "StructuredLeanTaskNormalizer":
                text = (
                    '{"context":['
                    '{"name":"p","typ":"Prop","kind":"explicit"},'
                    '{"name":"hp","typ":"p","kind":"explicit"}'
                    '],"target":"p"}'
                )
            else:
                text = '{"candidates":["exact hp"]}'
            return GeneratorResponse(
                text=text,
                provider="anthropic",
                model=request.model,
            )

    class FailureFeedback:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class LakeLeanBackend:
        name = "lake"

        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class LocalLeanBackend:
        name = "local"

        def __init__(self, **kwargs):
            self.kwargs = kwargs

    @dataclass(frozen=True)
    class Binding:
        name: str
        typ: str
        kind: str = "explicit"

    def run_policy_hlm_controller(**kwargs):
        assert kwargs["policy"].propose(SimpleNamespace(), 1) == ["exact hp"]
        feedback = kwargs["initial_failure_feedback"]
        assert len(feedback) == 2
        assert feedback[0].kwargs["error_kind"] == (
            "ai_statistician_lean_compiler_feedback"
        )
        assert "unknown identifier missing" in feedback[0].kwargs["error_tail"]
        assert "type mismatch from exact rerun" in feedback[1].kwargs["error_tail"]
        assert feedback[1].kwargs["proof_excerpt"] == "exact stale_candidate"
        assert kwargs["context"] == [
            Binding("p", "Prop", "explicit"),
            Binding("hp", "p", "explicit"),
        ]
        assert kwargs["target"] == "p"
        assert kwargs["final_feedback_retry"] is True
        assert kwargs["final_feedback_retry_budget"] == 4
        assert kwargs["final_feedback_retry_strategy"] == "retrieval_feedback"
        assert kwargs["skip_initial_search"] is True
        kwargs["out_path"].parent.mkdir(parents=True, exist_ok=True)
        kwargs["out_path"].write_text("{}\n", encoding="utf-8")
        return {
            "summary": {
                "backend": "lake",
                "rounds_run": 1,
                "direct_target_solved": 1,
                "final_solved": 1,
                "total_verified_assets": 1,
            },
            "direct_solution": {"proof": "exact hp"},
            "direct_successes": [],
            "final_search": {"proof": "assumption"},
            "assets": [
                {
                    "name": "checked_support",
                    "statement": "p",
                    "proof": "exact hp",
                    "theorem_src": "theorem checked_support (p : Prop) (hp : p) : p := by exact hp",
                }
            ],
            "failure_feedback": [{"branch": "old", "error_tail": "failed"}],
        }

    runtime = {
        "run_policy_hlm_controller": run_policy_hlm_controller,
        "FailureFeedback": FailureFeedback,
        "Binding": Binding,
        "proof_generation_prompt": lambda _task, n: f"return {n}",
        "LakeLeanBackend": LakeLeanBackend,
        "LocalLeanBackend": LocalLeanBackend,
    }
    provider = OpenProverHLMProofSearchProvider(
        generator_backend=Backend(),  # type: ignore[arg-type]
        config=OpenProverHLMConfig(
            root=root,
            out_dir=tmp_path / "runs",
            lean_project=lean_project,
            model="claude-opus-4-8",
            max_rounds=1,
            branches_per_round=1,
        ),
        runtime_loader=lambda: runtime,
    )

    result = provider.run(
        {
            "request_fingerprint": "request-123",
            "target_lean_declaration": "exact_source",
            "target_theorem_statement": (
                "theorem exact_source (p : Prop) (hp : p) : p"
            ),
            "current_proof_body_excerpt": "exact missing",
            "residual_goal_excerpt": ["p : Prop", "hp : p", "|- p"],
            "failed_proof_body_attempts": ["unknown identifier missing"],
            "compiler_feedback": {
                "checked": True,
                "returncode": 1,
                "diagnostics": ["unsolved goals from local Lean"],
            },
            "prior_exact_candidate_feedback": [
                {
                    "candidate_proof_body": "exact stale_candidate",
                    "returncode": 1,
                    "diagnostics": ["type mismatch from exact rerun"],
                    "status": "LOCAL_LEAN_FAILED",
                }
            ],
            "lean_header": "set_option autoImplicit false",
        }
    )

    assert result["status"] == "DIRECT_CANDIDATE_AVAILABLE"
    assert result["request_fingerprint"] == "request-123"
    assert result["source_theorem_candidate_proof_bodies"] == ["exact hp"]
    assert result["verified_support_assets"][0]["name"] == "checked_support"
    assert result["proof_evidence_status"] == (
        "OPENPROVER_HLM_RESULT_REQUIRES_EXACT_AI_STATISTICIAN_KERNEL_RERUN"
    )
    assert result["proof_evidence_boundary"] == LEAN_PROVIDER_BOUNDARY
    assert result["generation_mode"] == (
        "llm_zero_shot_with_lean_compile_feedback"
    )
    assert result["static_tactic_fallback"] is False
    assert result["compiler_feedback_consumed"] is True
    assert result["prior_exact_candidate_feedback_items"] == 1
    assert result["initial_failure_feedback_items"] == 2
    assert result["task_normalization"]["source"] == "llm_structured_json"
    assert result["task_normalization"]["context_binding_count"] == 2
    assert Path(result["report_path"]).exists()
