from __future__ import annotations

import re
from typing import Any


NUMBER = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"


def infer_dgp_family(dgp: str, target: str = "", tags: tuple[str, ...] = ()) -> str:
    text = _norm(" ".join([dgp, target, " ".join(tags)]))
    if any(term in text for term in ("bernoulli", "binary", "binomial(1", "0/1", "0-1")):
        return "bernoulli"
    if any(term in text for term in ("normal", "gaussian", "n(")):
        return "normal"
    if any(term in text for term in ("constant", "almost surely", "a.s.", "degenerate")):
        return "constant"
    if re.search(r"\bx\s*(?:_?i)?\s*=\s*(?:c|" + NUMBER + r")", text):
        return "constant"
    raise ValueError(
        "could not infer dgp_family. Provide one of: normal, bernoulli, constant"
    )


def infer_estimator_family(
    dgp_family: str,
    target: str,
    tags: tuple[str, ...] = (),
) -> str:
    text = _norm(" ".join([target, " ".join(tags)]))
    if dgp_family == "normal" and any(
        term in text for term in ("variance", "var(", "var[x]", "sigma^2", "sigma2", "σ²")
    ):
        return "sample_variance"
    if dgp_family == "normal" and any(term in text for term in ("mean", "mu", "e[x]", "expectation")):
        return "sample_mean"
    if dgp_family == "bernoulli" and any(
        term in text for term in ("probability", "proportion", "p(", "p =", "event", "mean", "p")
    ):
        return "sample_proportion"
    if dgp_family == "constant":
        return "constant_estimator"
    raise ValueError(
        "could not infer estimator_family from dgp_family/target. "
        "Provide one of: sample_mean, sample_variance, sample_proportion, constant_estimator"
    )


def infer_true_params(dgp_family: str, dgp: str, provided: dict[str, Any] | None = None) -> dict[str, float]:
    params = {str(k): float(v) for k, v in (provided or {}).items()}
    text = dgp
    if dgp_family == "normal":
        params.setdefault("mu", _find_number(text, ("mu", "μ", "mean")))
        params.setdefault("sigma", _find_number(text, ("sigma", "σ", "sd", "std")))
        if "sigma" not in params and "sigma2" in params:
            params["sigma"] = params["sigma2"] ** 0.5
        _require_params(params, ("mu", "sigma"), dgp_family)
    elif dgp_family == "bernoulli":
        params.setdefault("p", _find_number(text, ("p", "prob")))
        _require_params(params, ("p",), dgp_family)
        if not 0.0 <= params["p"] <= 1.0:
            raise ValueError("bernoulli parameter p must be in [0, 1]")
    elif dgp_family == "constant":
        value = _find_number(text, ("c", "constant", "x_i", "x"))
        if value is not None:
            params.setdefault("c", value)
        _require_params(params, ("c",), dgp_family)
    else:
        raise ValueError(f"unsupported dgp_family {dgp_family!r}")
    return params


def infer_tags(
    *,
    dgp_family: str,
    estimator_family: str,
    target: str,
    provided: tuple[str, ...] = (),
) -> tuple[str, ...]:
    tags = list(provided)
    tags.extend([dgp_family, estimator_family])
    target_text = _norm(target)
    if any(term in target_text for term in ("mean", "mu", "expectation", "e[x]")):
        tags.append("mean")
        tags.append("expectation")
    if any(term in target_text for term in ("variance", "var(", "sigma^2", "sigma2")):
        tags.append("variance")
    if any(term in target_text for term in ("probability", "event", "proportion")):
        tags.append("probability")
    return tuple(dict.fromkeys(tag for tag in tags if tag))


def _norm(text: str) -> str:
    return text.lower().replace("μ", "mu").replace("σ", "sigma")


def _find_number(text: str, keys: tuple[str, ...]) -> float | None:
    normalized = _norm(text)
    for key in keys:
        key_re = re.escape(_norm(key))
        patterns = [
            rf"{key_re}\s*(?:=|:)\s*({NUMBER})",
            rf"{key_re}\s*(?:is|equals)\s*({NUMBER})",
            rf"{key_re}\s+({NUMBER})",
        ]
        for pattern in patterns:
            match = re.search(pattern, normalized)
            if match:
                return float(match.group(1))
    return None


def _require_params(params: dict[str, float], required: tuple[str, ...], family: str) -> None:
    missing = [name for name in required if name not in params or params[name] is None]
    if missing:
        raise ValueError(
            f"could not infer true_params for {family}; missing: {', '.join(missing)}"
        )
