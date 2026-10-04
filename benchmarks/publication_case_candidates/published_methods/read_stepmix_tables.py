"""Assessment-only decoding of declared StepMix 2.2.3 stdout channels.

This reads submitted text, not author code or cached reference results. It does
not check a task grid, compare values, supply a tolerance or issue a verdict.
"""

import argparse
from decimal import Decimal, InvalidOperation
import json
import math
from pathlib import Path


METHODS = ("1-step", "2-step", "3-step (Naive)", "3-step (BCH)", "3-step (ML)")


def printed_number(token):
    if token.lower() in {"nan", "inf", "+inf", "-inf"}:
        state = {"nan": "NaN", "inf": "Inf", "+inf": "Inf", "-inf": "-Inf"}[token.lower()]
        return {"printed": token, "state": state, "value": None}
    try:
        number = Decimal(token)
    except InvalidOperation as exc:
        raise ValueError(f"not a printed numeric cell: {token!r}") from exc
    value = float(number)
    if not number.is_finite() or not math.isfinite(value):
        raise ValueError(f"unsupported printed numeric cell: {token!r}")
    return {"printed": token, "state": "finite", "value": value}


def _rows(lines, header_row, index_names, columns, line_offset=0):
    header = lines[header_row]
    starts, cursor = [], 0
    for name in index_names:
        start = header.find(name, cursor)
        if start < 0 or header[cursor:start].strip():
            raise ValueError("index header does not match the declared channel")
        starts.append(start)
        cursor = start + len(name)
    if header[cursor:].strip():
        raise ValueError("unexpected index header suffix")
    rows, previous, seen = [], {}, set()
    for position in range(header_row + 1, len(lines)):
        line = lines[position]
        if not line.strip():
            break
        fields = line.rsplit(None, len(columns))
        if len(fields) != len(columns) + 1 or "..." in line:
            raise ValueError("incomplete, wrapped or truncated table row")
        prefix = fields[0]
        if prefix[:starts[0]].strip():
            raise ValueError("unexpected row prefix")
        index = {}
        for level, name in enumerate(index_names):
            stop = starts[level + 1] if level + 1 < len(starts) else len(prefix)
            label = prefix[starts[level]:stop].strip()
            if not label:
                parent_changed = any(index[earlier] != previous.get(earlier) for earlier in index)
                if level == len(starts) - 1 or name not in previous or parent_changed:
                    raise ValueError("unbound sparse index label")
                label = previous[name]
            index[name] = label
        key = tuple(index.values())
        if key in seen:
            raise ValueError("duplicate table coordinate")
        seen.add(key)
        previous = index
        rows.append({"source_line": line_offset + position + 1,
                     "raw_line": line, "index": index,
                     "cells": [{"column": column, **printed_number(token)}
                               for column, token in zip(columns, fields[1:])]})
    if not rows:
        raise ValueError("table has no printed rows")
    return rows


def read_simulation(text, *, variant):
    if variant not in {"response", "covariate", "complete"}:
        raise ValueError("simulation variant must be bound explicitly")
    lines = text.splitlines()
    if len(lines) < 4 or lines[0].split() != ["variable", "Bias", "RMSE"]:
        raise ValueError("expected the declared Bias/RMSE table header")
    if " ".join(lines[1].split()) != "Model " + " ".join(METHODS * 2):
        raise ValueError("method header/order does not match the declared channel")
    scenario = "NaN Ratio" if variant == "complete" else "Class Separation"
    columns = [{"metric": metric, "method": method}
               for metric in ("Bias", "RMSE") for method in METHODS]
    rows = _rows(lines, 2, (scenario, "Sample Size"), columns)
    if any(line.strip() for line in lines[rows[-1]["source_line"]:]):
        raise ValueError("unexpected content after the declared simulation table")
    return {"channel": f"stepmix_{variant}_simulation",
            "rounding": "source rounds aggregate values to two decimals before printing",
            "rows": rows}


def read_gss(text):
    classes = ("Low", "Middle", "High")
    specs = {
        "Table 8 : Estimated MM parameters": (("model_name", "param", "variable"), classes),
        "Table 8 : Class weights": (("param",), classes),
        "Table 9 : Estimated SM parameters (means)": (("variable", "method"), classes),
        "Table 9 : Estimated SM parameters (errors)": (("variable", "method"), classes),
        "Table 10 : Family\u2019s income differences between classes for each method.":
            (("variable", "method", "class_no"), ("mean", "std", "Z", "P(>|z|)")),
    }
    for method in ("1-step", "2-step", "3-step", "3-step (BCH)", "3-step (ML)"):
        specs[f"Class prevalence for {method}:"] = (("param",), ("0", "1", "2"))
    lines, tables = text.splitlines(), {}
    for position, line in enumerate(lines):
        if line.strip() not in specs:
            continue
        label = line.strip()
        if label in tables:
            raise ValueError("duplicate declared table section")
        index_names, columns = specs[label]
        if position + 2 >= len(lines):
            raise ValueError("incomplete declared table section")
        numeric_header = lines[position + 1].split()
        if numeric_header not in [list(columns), ["class_no", *columns]]:
            raise ValueError("numeric header/order does not match the declared section")
        tables[label] = _rows(lines[position + 1:], 1, index_names, list(columns), position + 1)
    return {"channel": "stepmix_gss", "tables": tables,
            "missing_sections": [label for label in specs if label not in tables]}


def read_package_comparison(text):
    labels = {"Table 11: Fit Times (sec.)": "fit_time_seconds",
              "Table 11: StepMix Log-Likelihoods": "log_likelihood"}
    sections, active = {}, None
    for position, line in enumerate(text.splitlines()):
        if line.strip() in labels:
            active = labels[line.strip()]
            if active in sections:
                raise ValueError("duplicate declared table section")
            sections[active] = {}
        elif active is not None:
            if not line.strip():
                active = None
                continue
            name, separator, token = line.partition(":")
            name = name.strip()
            if not separator or not name or name in sections[active]:
                raise ValueError("invalid or duplicate dataset coordinate")
            sections[active][name] = {"source_line": position + 1, "raw_line": line,
                                      **printed_number(token.strip())}
    return {"channel": "stepmix_package_comparison", "sections": sections,
            "missing_sections": [name for name in labels.values() if name not in sections]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("channel", choices=("response_simulation", "covariate_simulation", "complete_simulation", "gss", "package_comparison"))
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    text = args.path.read_text(encoding="utf-8")
    if args.channel.endswith("_simulation"):
        result = read_simulation(text, variant=args.channel.removesuffix("_simulation"))
    else:
        result = (read_gss if args.channel == "gss" else read_package_comparison)(text)
    print(json.dumps(result, allow_nan=False))
