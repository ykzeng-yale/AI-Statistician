from __future__ import annotations

from types import SimpleNamespace

from ai_statistician.formal_source_prompt_context import (
    _formal_source_dependency_context,
)
from ai_statistician.formal_source_index import (
    FormalDeclaration,
    FormalSourceHit,
)
from ai_statistician.formal_source_retrieval_benchmark import (
    FormalSourceRetrievalBenchmarkCase,
    run_formal_source_retrieval_benchmark,
)
from ai_statistician.formal_source_topology import (
    FORMAL_SOURCE_SCOPE_EXPANSION_POLICY,
    FORMAL_SOURCE_TOPOLOGY_EVIDENCE_STATUS,
    canonicalize_formal_source_scope_ids,
    expand_formal_source_scope_ids,
    identify_formal_source_topology,
    resolve_formal_source_topologies,
)


def _topology(
    *,
    remote: str,
    entry_module: str,
    source_root: str,
    lean_toolchain: str,
    mathlib_revision: str,
):
    topology = identify_formal_source_topology(
        {
            "source_git_remote": remote,
            "entry_module": entry_module,
            "source_root": source_root,
            "lean_toolchain": lean_toolchain,
            "mathlib_revision": mathlib_revision,
        }
    )
    assert topology is not None
    return topology


def test_topology_identity_uses_snapshot_metadata_not_database_name() -> None:
    topology = _topology(
        remote="https://github.com/stat-lib/statlib.git",
        entry_module="Statlib",
        source_root="/tmp/arbitrarily-renamed/source/Statlib",
        lean_toolchain="leanprover/lean4:v4.30.0",
        mathlib_revision="a" * 40,
    )

    assert topology.source_id == "statlib"
    assert topology.role == "canonical_statistics_foundation"
    assert topology.relation_to_active_project == "direct_lake_dependency"
    assert topology.identity_basis == (
        "source_git_remote",
        "entry_module",
    )


def test_topology_does_not_canonicalize_an_unrecognized_fork() -> None:
    topology = identify_formal_source_topology(
        {
            "source_git_remote": "https://github.com/example/statlib-fork.git",
            "entry_module": "Statlib",
            "source_root": "/tmp/Statlib",
        }
    )

    assert topology is None


def test_topology_resolves_foundation_and_companion_against_active_project() -> None:
    active = _topology(
        remote="https://github.com/ykzeng-yale/EmpericalProcessLEAN.git",
        entry_module="StatInference",
        source_root="/tmp/StatInference",
        lean_toolchain="leanprover/lean4:v4.30.0",
        mathlib_revision="a" * 40,
    )
    statlib = _topology(
        remote="https://github.com/stat-lib/statlib.git",
        entry_module="Statlib",
        source_root="/tmp/Statlib",
        lean_toolchain="leanprover/lean4:v4.30.0",
        mathlib_revision="a" * 40,
    )
    companion = _topology(
        remote="https://github.com/YuanheZ/lean-stat-learning-theory.git",
        entry_module="",
        source_root="/tmp/SLT",
        lean_toolchain="leanprover/lean4:v4.32.0",
        mathlib_revision="b" * 40,
    )

    resolved = {
        row.source_id: row
        for row in resolve_formal_source_topologies(
            (statlib, active, companion)
        )
    }

    assert resolved["empirical_process_lean"].compatibility_status == (
        "active_project"
    )
    assert resolved["statlib"].compatibility_status == (
        "same_lean_toolchain_and_mathlib_revision"
    )
    assert resolved["lean_stat_learning_theory"].compatibility_status == (
        "different_lean_toolchain_requires_port"
    )


def test_active_project_scope_includes_only_declared_foundation_dependencies() -> None:
    assert canonicalize_formal_source_scope_ids(
        ("local_statinference_repo", "unregistered_source")
    ) == ("empirical_process_lean", "unregistered_source")
    assert expand_formal_source_scope_ids(("empirical_process_lean",)) == (
        "empirical_process_lean",
        "statlib",
    )
    assert expand_formal_source_scope_ids(("local_statinference_repo",)) == (
        "empirical_process_lean",
        "statlib",
    )
    assert expand_formal_source_scope_ids(("statlib",)) == ("statlib",)
    assert expand_formal_source_scope_ids(("lean_stat_learning_theory",)) == (
        "lean_stat_learning_theory",
    )
    assert expand_formal_source_scope_ids(("unregistered_source",)) == (
        "unregistered_source",
    )

    active = _topology(
        remote="https://github.com/ykzeng-yale/EmpericalProcessLEAN.git",
        entry_module="StatInference",
        source_root="/tmp/StatInference",
        lean_toolchain="leanprover/lean4:v4.30.0",
        mathlib_revision="a" * 40,
    )
    assert active.dependency_source_ids == ("statlib",)
    assert active.as_prompt_payload()["source_scope_expansion_policy"] == (
        FORMAL_SOURCE_SCOPE_EXPANSION_POLICY
    )


def test_external_companion_prompt_requires_port_and_local_reelaboration() -> None:
    context = SimpleNamespace(
        source_id="lean_stat_learning_theory",
        module="SLT.LeastSquares.MasterErrorBound",
        fan_in=2,
        fan_out=1,
        uses=(),
        used_by=(),
        statement_uses=(),
        proof_uses=(),
        source_snapshot_status="BOUND_MATCH",
        source_snapshot_bound=True,
        source_snapshot_match=True,
        source_snapshot_metadata=(
            ("source_git_commit", "a" * 40),
            ("lean_toolchain", "leanprover/lean4:v4.32.0"),
            ("mathlib_revision", "b" * 40),
        ),
        source_topology_id="statlib_centered_statistics_sources_v1",
        source_role="verified_companion_library",
        source_relation_to_active_project="external_companion",
        source_compatibility_status="different_lean_toolchain_requires_port",
        source_reuse_policy=(
            "port_into_target_toolchain_and_import_closure_then_reelaborate_locally"
        ),
        source_topology_identity_basis=("source_git_remote", "source_root_name"),
        source_topology_evidence_status=(
            FORMAL_SOURCE_TOPOLOGY_EVIDENCE_STATUS
        ),
    )

    class Provider:
        source = "fixture_dependency_graph"

        @staticmethod
        def dependency_context(*args, **kwargs):
            return context

    payload = _formal_source_dependency_context(
        Provider(),
        "LeastSquares.master_error_bound",
        source_id="lean_stat_learning_theory",
        path="SLT/LeastSquares/MasterErrorBound.lean",
        limit=8,
    )

    assert payload["source_topology"]["evidence_status"] == (
        FORMAL_SOURCE_TOPOLOGY_EVIDENCE_STATUS
    )
    assert payload["candidate_use_policy"]["classification"] == (
        "external_companion_port_candidate"
    )
    assert "port into the active Lean and Mathlib toolchain" in payload[
        "candidate_use_policy"
    ]["activation_gate"]
    assert "exactly re-elaborate locally" in payload["candidate_use_policy"][
        "activation_gate"
    ]
    assert "kernel_verified" not in payload


def test_retrieval_benchmark_records_nonproof_source_topology() -> None:
    declaration = FormalDeclaration(
        source_id="statlib",
        source_type="lean_rag_dependency_graph",
        path="Statlib/QMD.lean",
        line=1,
        kind="theorem",
        name="QMD.integral_score_eq_zero_of_mem_nhds",
        namespace="QMD",
        signature="theorem integral_score_eq_zero_of_mem_nhds : True",
    )

    class Retriever:
        lean_rag_dependency_graph_enabled = True
        lean_rag_source_topology = (
            {
                "source_id": "statlib",
                "role": "canonical_statistics_foundation",
                "evidence_status": FORMAL_SOURCE_TOPOLOGY_EVIDENCE_STATUS,
            },
        )

        @staticmethod
        def search(_query: str, *, k: int = 10):
            return [FormalSourceHit(declaration, 1.0, ("qmd",))][:k]

        @staticmethod
        def search_with_source_scope(
            _query: str,
            *,
            source_scope_ids: tuple[str, ...],
            k: int = 10,
        ):
            assert source_scope_ids == ("statlib",)
            return [FormalSourceHit(declaration, 1.0, ("qmd",))][:k]

    payload = run_formal_source_retrieval_benchmark(
        retriever=Retriever(),
        cases=(
            FormalSourceRetrievalBenchmarkCase(
                query_id="statlib_topology_manifest",
                query="mean zero score",
                expected_name_fragments=("integral_score_eq_zero",),
                expected_source_ids=("statlib",),
            ),
        ),
        k=2,
    )

    assert payload["lean_rag_source_topology"] == (
        {
            "source_id": "statlib",
            "role": "canonical_statistics_foundation",
            "evidence_status": FORMAL_SOURCE_TOPOLOGY_EVIDENCE_STATUS,
        },
    )
    assert payload["all_ok"] is True
