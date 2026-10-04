"""Fresh printed-table fixtures, not published results or scientific grading."""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from benchmarks.publication_case_candidates.published_methods import read_stepmix_tables as reader


def simulation_table(scenario="Class Separation", rows=None):
    if rows is None:
        rows = [("0.7", "500", ["-0.00", "NaN", "inf", "-inf", *["0.03"] * 6]),
                ("", "1000", ["1.24"] * 10), ("0.8", "500", ["3.14"] * 10)]
    lines = ["variable Bias RMSE", "Model " + " ".join(reader.METHODS * 2),
             f"{scenario:<17}Sample Size"]
    lines.extend(f"{group:<17}{size:<12}" + " ".join(values) for group, size, values in rows)
    return "\n".join(lines) + "\n"


def pandas_table(index_names, widths, rows, columns, column_name="class_no"):
    lines = [column_name + " " + " ".join(columns),
             "".join(f"{name:<{width}}" for name, width in zip(index_names, widths))]
    lines.extend("".join(f"{label:<{width}}" for label, width in zip(labels, widths))
                 + " ".join(values) for labels, values in rows)
    return "\n".join(lines) + "\n"


@pytest.mark.parametrize("variant", ["response", "covariate", "complete"])
def test_simulation_coordinates_printed_precision_and_nonfinite_states(variant):
    scenario = "NaN Ratio" if variant == "complete" else "Class Separation"
    text = simulation_table(scenario)
    result = reader.read_simulation(text, variant=variant)
    assert result["channel"] == f"stepmix_{variant}_simulation"
    assert result["rows"][1]["index"] == {scenario: "0.7", "Sample Size": "1000"}
    row = result["rows"][0]
    assert row["source_line"] == 4 and row["raw_line"] == text.splitlines()[3]
    assert row["cells"][0] == {"column": {"metric": "Bias", "method": "1-step"},
                               "printed": "-0.00", "state": "finite", "value": -0.0}
    assert [cell["state"] for cell in row["cells"][1:4]] == ["NaN", "Inf", "-Inf"]
    assert all(cell["value"] is None for cell in row["cells"][1:4])
    assert len(result["rows"]) == 3  # Not filled out to a presumed complete grid.
    assert "missing_sections" not in result and "passed" not in result
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("change", [
    lambda text: text.replace("Model 1-step 2-step", "Model 2-step 1-step", 1),
    lambda text: text.replace("0.7              500", "                 500", 1),
    lambda text: text + text,
    lambda text: text + "\n" + text,
    lambda text: text.replace("NaN", "...", 1),
    lambda text: text.replace("1.24", "1e9999", 1),
    lambda text: text.replace("1.24", "unknown", 1),
    lambda text: text + text.splitlines()[-1] + "\n",
    lambda text: "\n".join(text.splitlines()[:3]),
])
def test_invalid_or_ambiguous_simulation_display_rejects(change):
    with pytest.raises(ValueError):
        reader.read_simulation(change(simulation_table()), variant="response")


def test_gss_keeps_measurement_weights_mean_error_and_contrast_distinct():
    sections = []
    def add(label, names, widths, rows, columns=("Low", "Middle", "High"), column_name="class_no"):
        sections.append(label + "\n" + pandas_table(names, widths, rows, columns, column_name))
    add("Table 8 : Estimated MM parameters", ("model_name", "param", "variable"), (18, 7, 30),
        [(("categorical_nan", "pis", "Father's job prestige_0"), (".1", ".2", ".3")),
         (("", "", "Mother's education_1"), (".4", ".5", ".6"))])
    add("Table 8 : Class weights", ("param",), (20,), [(("class_weights",), (".2", ".3", ".5"))])
    for method in ("1-step", "2-step", "3-step", "3-step (BCH)", "3-step (ML)"):
        add(f"Class prevalence for {method}:", ("param",), (20,),
            [(("class_weights",), (".2", ".3", ".5"))], ("0", "1", "2"))
    for label, values in [("means", ("11", "12", "13")), ("errors", (".1", ".2", ".3"))]:
        add(f"Table 9 : Estimated SM parameters ({label})", ("variable", "method"), (15, 16),
            [(("Income (1000)", "1-step"), values), (("", "3-step"), values)])
    contrast = "Table 10 : Family\u2019s income differences between classes for each method."
    add(contrast, ("variable", "method", "class_no"), (15, 16, 10),
        [(("Income (1000)", "1-step", "High"), ("2", ".1", "20", ".000")),
         (("", "", "Middle"), ("1", ".2", "5", ".001"))],
        ("mean", "std", "Z", "P(>|z|)"), "")
    text = "\n".join(sections)
    result = reader.read_gss(text)
    assert not result["missing_sections"] and len(result["tables"]) == 10
    cells = result["tables"][contrast][1]
    assert cells["index"] == {"variable": "Income (1000)", "method": "1-step", "class_no": "Middle"}
    assert cells["cells"][-1]["printed"] == ".001"
    assert result["tables"]["Table 9 : Estimated SM parameters (errors)"][1]["index"]["method"] == "3-step"
    assert cells["raw_line"] == text.splitlines()[cells["source_line"] - 1]
    assert "passed" not in result


def test_missing_gss_section_is_explicit_and_changed_header_does_not_autodetect():
    text = "Table 9 : Estimated SM parameters (means)\n" + pandas_table(
        ("variable", "method"), (15, 16), [(("Income (1000)", "1-step"), ("1", "2", "3"))],
        ("Low", "Middle", "High"))
    result = reader.read_gss(text)
    assert len(result["missing_sections"]) == 9
    with pytest.raises(ValueError, match="header"):
        reader.read_gss(text.replace("Low Middle High", "High Middle Low"))
    with pytest.raises(ValueError, match="duplicate"):
        reader.read_gss(text + "\n" + text)


def test_sparse_child_cannot_cross_a_changed_parent():
    text = "Table 9 : Estimated SM parameters (means)\n" + pandas_table(
        ("variable", "method"), (15, 16),
        [(("Income (1000)", "1-step"), ("1", "2", "3")),
         (("New variable", ""), ("4", "5", "6"))], ("Low", "Middle", "High"))
    with pytest.raises(ValueError, match="sparse"):
        reader.read_gss(text)


def test_package_comparison_preserves_datasets_units_printed_values_and_absence():
    text = "Table 11: Fit Times (sec.)\nopaqueA      : 0.003\nopaqueB      : 1.234\n\n\n" \
           "Table 11: StepMix Log-Likelihoods\nopaqueA      : -12.345\nopaqueB      : NaN\n"
    result = reader.read_package_comparison(text)
    assert result["missing_sections"] == []
    assert result["sections"]["fit_time_seconds"]["opaqueA"]["value"] == .003
    assert result["sections"]["log_likelihood"]["opaqueA"]["printed"] == "-12.345"
    assert result["sections"]["log_likelihood"]["opaqueB"]["state"] == "NaN"
    assert reader.read_package_comparison("")["missing_sections"] == ["fit_time_seconds", "log_likelihood"]
    with pytest.raises(ValueError, match="duplicate"):
        reader.read_package_comparison(text + "opaqueA: 3.21\n")
    with pytest.raises(ValueError, match="duplicate"):
        reader.read_package_comparison(text + "\n" + text)


def test_cli_reads_only_supplied_text_and_reports_corrupt_or_missing_selection(tmp_path):
    script = Path(reader.__file__)
    selected = tmp_path / "submission.txt"
    text = simulation_table()
    selected.write_text(text)
    command = [sys.executable, str(script), "response_simulation", str(selected)]
    success = subprocess.run(command, capture_output=True, text=True, check=False)
    assert success.returncode == 0 and json.loads(success.stdout)["rows"]
    assert selected.read_text() == text
    selected.write_text("not a table")
    invalid = subprocess.run(command, capture_output=True, text=True, check=False)
    assert invalid.returncode != 0 and "ValueError" in invalid.stderr
    selected.unlink()
    absent = subprocess.run(command, capture_output=True, text=True, check=False)
    assert absent.returncode != 0 and "FileNotFoundError" in absent.stderr


@pytest.mark.skipif(not os.environ.get("AI_STATISTICIAN_STEPMIX_FORMAT_PYTHON"),
                    reason="explicit pinned pandas format interpreter required")
def test_declared_pandas_153_print_format_not_handwritten_alignment(tmp_path):
    command = [os.environ["AI_STATISTICIAN_STEPMIX_FORMAT_PYTHON"], "-B", "-s", "-c", r'''
import json
import pandas as pd
assert pd.__version__ == "1.5.3"
methods = ["1-step", "2-step", "3-step (Naive)", "3-step (BCH)", "3-step (ML)"]
printed = {}
for variant, scenario in [("response", "Class Separation"), ("covariate", "Class Separation"), ("complete", "NaN Ratio")]:
    index = pd.MultiIndex.from_product([[.7, .8, .9], [500, 1000, 2000]], names=[scenario, "Sample Size"])
    cols = pd.MultiIndex.from_product([["Bias", "RMSE"], methods], names=["variable", "Model"])
    values = [[(i * 10 + j) / 100 for j in range(10)] for i in range(9)]
    values[0][:4] = [-0., float("nan"), float("inf"), float("-inf")]
    printed[variant] = pd.DataFrame(values, index=index, columns=cols).to_string()
sections = []
def add(label, index, columns, data):
    frame = pd.DataFrame(data, index=index, columns=columns)
    sections.append(label + "\n" + str(frame))
classes = pd.Index(["Low", "Middle", "High"], name="class_no")
measurement = pd.MultiIndex.from_tuples([("categorical_nan", "pis", "Father's job prestige_0"),
    ("categorical_nan", "pis", "Mother's education_1")], names=["model_name", "param", "variable"])
add("Table 8 : Estimated MM parameters", measurement, classes, [[.1,.2,.3],[.4,.5,.6]])
weights = pd.Index(["class_weights"], name="param")
add("Table 8 : Class weights", weights, classes, [[.2,.3,.5]])
gss_methods = ["1-step", "2-step", "3-step", "3-step (BCH)", "3-step (ML)"]
for method in gss_methods:
    add("Class prevalence for " + method + ":", weights, pd.Index([0,1,2], name="class_no"), [[.2,.3,.5]])
means = pd.MultiIndex.from_product([["Income (1000)"], gss_methods], names=["variable","method"])
for kind in ["means", "errors"]:
    add("Table 9 : Estimated SM parameters (" + kind + ")", means, classes, [[11.,12.,13.]] * 5)
contrasts = pd.MultiIndex.from_product([["Income (1000)"], gss_methods, ["High","Middle"]], names=["variable","method","class_no"])
add("Table 10 : Family\u2019s income differences between classes for each method.", contrasts,
    ["mean","std","Z","P(>|z|)"], [[1.,.2,5.,.001]] * 10)
printed["gss"] = "\n\n".join(sections)
print(json.dumps(printed))
''']
    emitted = subprocess.run(command, cwd=tmp_path, env={"HOME": str(tmp_path), "PATH": os.defpath},
                             capture_output=True, text=True, check=False, timeout=30)
    assert emitted.returncode == 0, emitted.stderr
    frames = json.loads(emitted.stdout)
    for variant in ("response", "covariate", "complete"):
        decoded = reader.read_simulation(frames[variant], variant=variant)
        assert len(decoded["rows"]) == 9 and all(len(row["cells"]) == 10 for row in decoded["rows"])
        assert decoded["rows"][1]["index"]["Sample Size"] == "1000"
    gss = reader.read_gss(frames["gss"])
    assert not gss["missing_sections"] and len(gss["tables"]) == 10
    assert len(gss["tables"]["Table 9 : Estimated SM parameters (means)"]) == 5
    assert len(gss["tables"]["Table 10 : Family\u2019s income differences between classes for each method."]) == 10
