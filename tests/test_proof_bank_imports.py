from ai_statistician.proof_bank import get_obligation, obligations_by_tags


def _import_lines(obligation_id: str) -> list[str]:
    return [
        line.strip()
        for line in get_obligation(obligation_id).formal_statement.splitlines()
        if line.strip().startswith("import ")
    ]


def test_source_theorem_semantic_primitives_avoid_monolithic_mathlib_import() -> None:
    for obligation in obligations_by_tags(
        {"source_theorem_semantic_primitive"},
        require_all=True,
    ):
        assert "import Mathlib" not in _import_lines(obligation.id)


def test_runtime_kernel_smoke_obligations_avoid_monolithic_mathlib_import() -> None:
    for obligation_id in ("prob_measure_univ", "variance_nonneg"):
        assert "import Mathlib" not in _import_lines(obligation_id)
