from pathlib import Path

from statlean_agent.retrieval import build_premise_index, search_premises


def test_build_premise_index_finds_local_theorems() -> None:
    records = build_premise_index(Path("."))
    names = {record.name for record in records}
    full_names = {record.full_name for record in records}
    assert "oracle_ineq_of_uniform_deviation" in names
    assert "asymptotic_normality_of_bridge" in names
    assert "StatInference.oracle_ineq_of_uniform_deviation" in full_names
    assert "StatInference.asymptotic_normality_of_bridge" in full_names


def test_build_premise_index_tags_empirical_deviation_declarations() -> None:
    records = build_premise_index(Path("."))
    empirical = {
        record.name: record for record in records if record.module == "StatInference.EmpiricalProcess.Basic"
    }

    assert "EmpiricalDeviationBound" in empirical
    assert "EmpiricalDeviationBoundOn" in empirical
    assert "EmpiricalDeviationSequence" in empirical
    assert "EmpiricalDeviationSequenceOn" in empirical
    assert "EmpiricalDeviationBound.apply_at" in empirical
    assert "EmpiricalDeviationSequenceOn.apply_at" in empirical

    bound = empirical["EmpiricalDeviationBound"]
    assert bound.full_name == "StatInference.EmpiricalDeviationBound"
    assert "empirical_process" in bound.module_tags
    assert "empirical_deviation_bound" in bound.name_tags
    assert "empirical_process" in bound.domain_tags
    assert "uniform_deviation" in bound.domain_tags


def test_estimator_uniform_deviation_bound_remains_distinct() -> None:
    records = build_premise_index(Path("."))
    matches = [record for record in records if record.name == "UniformDeviationBound"]

    assert len(matches) == 1
    uniform = matches[0]
    assert uniform.full_name == "StatInference.UniformDeviationBound"
    assert uniform.module == "StatInference.Estimator.Basic"
    assert "estimator_interface" in uniform.domain_tags
    assert "empirical_process" not in uniform.domain_tags

    empirical_names = {
        record.name for record in records if record.module == "StatInference.EmpiricalProcess.Basic"
    }
    assert "UniformDeviationBound" not in empirical_names

    search_match = search_premises(records, "UniformDeviationBound", top_k=1)
    assert search_match
    assert search_match[0].full_name == "StatInference.UniformDeviationBound"


def test_search_premises_returns_deterministic_matches() -> None:
    records = build_premise_index(Path("."))
    matches = search_premises(records, "oracle excess risk", top_k=3)
    assert matches
    assert any("oracle" in record.name for record in matches)


def test_search_premises_uses_stable_tags() -> None:
    records = build_premise_index(Path("."))
    matches = search_premises(records, "empirical process deviation bound", top_k=5)
    full_names = {record.full_name for record in matches}

    assert "StatInference.EmpiricalDeviationBound" in full_names


def test_estimator_family_tags_cover_m_and_z_estimators() -> None:
    records = build_premise_index(Path("."))
    by_full_name = {record.full_name: record for record in records}

    m_estimator = by_full_name["StatInference.MEstimator"]
    z_estimator = by_full_name["StatInference.ZEstimator"]

    assert "estimator_interface" in m_estimator.domain_tags
    assert "m_estimation" in m_estimator.domain_tags
    assert "estimator_interface" in z_estimator.domain_tags
    assert "z_estimation" in z_estimator.domain_tags

    m_matches = search_premises(records, "m estimation oracle excess", top_k=8)
    assert any("MEstimatorWithOracle" in record.full_name for record in m_matches)

    z_matches = search_premises(records, "z estimation residual oracle", top_k=8)
    assert any("ZEstimatorWithOracle" in record.full_name for record in z_matches)
