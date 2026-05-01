from pathlib import Path

from statlean_agent.retrieval import build_premise_index, search_premises


def test_build_premise_index_finds_local_theorems() -> None:
    records = build_premise_index(Path("."))
    names = {record.name for record in records}
    assert "oracle_ineq_of_uniform_deviation" in names
    assert "asymptotic_normality_of_bridge" in names


def test_search_premises_returns_deterministic_matches() -> None:
    records = build_premise_index(Path("."))
    matches = search_premises(records, "oracle excess risk", top_k=3)
    assert matches
    assert any("oracle" in record.name for record in matches)

