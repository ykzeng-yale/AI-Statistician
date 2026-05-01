"""Lightweight premise indexing for local Lean files."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path


DECL_RE = re.compile(
    r"^\s*(?P<kind>theorem|lemma|def|abbrev|structure|class|inductive)\s+"
    r"(?P<name>[A-Za-z_][A-Za-z0-9_'.]*)"
)
NAMESPACE_RE = re.compile(r"^\s*namespace\s+([A-Za-z_][A-Za-z0-9_'.]*)\s*$")
END_RE = re.compile(r"^\s*end(?:\s+([A-Za-z_][A-Za-z0-9_'.]*))?\s*$")
IMPORT_RE = re.compile(r"^\s*import\s+([A-Za-z0-9_'.]+)")
TOKEN_RE = re.compile(r"[A-Za-z0-9']+")
CAMEL_TOKEN_RE = re.compile(r"[A-Z]+(?=[A-Z][a-z]|[0-9]|$)|[A-Z]?[a-z]+|[0-9]+")


@dataclass(frozen=True)
class PremiseRecord:
    """A retrievable Lean declaration."""

    name: str
    kind: str
    module: str
    file: str
    line: int
    full_name: str = ""
    imports: tuple[str, ...] = ()
    module_tags: tuple[str, ...] = ()
    name_tags: tuple[str, ...] = ()
    domain_tags: tuple[str, ...] = ()


def build_premise_index(root: Path, source_dir: str = "StatInference") -> tuple[PremiseRecord, ...]:
    """Extract declarations from Lean source files under `source_dir`."""

    base = root / source_dir
    if not base.exists():
        return ()

    records: list[PremiseRecord] = []
    for path in sorted(base.rglob("*.lean")):
        text = path.read_text(encoding="utf-8")
        imports = tuple(match.group(1) for match in IMPORT_RE.finditer(text))
        module = _module_name(path, root)
        namespace_stack: list[str] = []
        for line_number, line in enumerate(text.splitlines(), start=1):
            namespace_match = NAMESPACE_RE.match(line)
            if namespace_match:
                namespace_stack.extend(_name_parts(namespace_match.group(1)))
                continue

            end_match = END_RE.match(line)
            if end_match:
                _pop_namespace(namespace_stack, end_match.group(1))
                continue

            match = DECL_RE.match(line)
            if not match:
                continue
            raw_name = match.group("name")
            kind = match.group("kind")
            full_name = _qualified_name(namespace_stack, raw_name)
            name = _relative_name(full_name, source_dir)
            records.append(
                PremiseRecord(
                    name=name,
                    kind=kind,
                    module=module,
                    file=str(path.relative_to(root)),
                    line=line_number,
                    full_name=full_name,
                    imports=imports,
                    module_tags=_module_tags(module),
                    name_tags=_name_tags(name),
                    domain_tags=_domain_tags(module, name, full_name),
                )
            )
    return tuple(records)


def search_premises(records: tuple[PremiseRecord, ...], query: str, top_k: int = 8) -> tuple[PremiseRecord, ...]:
    """Return deterministic token-overlap premise matches."""

    query_tokens = set(_tokens(query))
    scored: list[tuple[int, str, PremiseRecord]] = []
    for record in records:
        haystack = set(_tokens(_search_text(record)))
        overlap = len(query_tokens & haystack)
        stable_name = record.full_name or record.name
        substring_bonus = 2 if query.lower() and query.lower() in stable_name.lower() else 0
        score = overlap + substring_bonus
        if score > 0:
            scored.append((-score, stable_name, record))
    scored.sort()
    return tuple(record for _, _, record in scored[:top_k])


def _tokens(value: str) -> tuple[str, ...]:
    tokens: list[str] = []
    for raw_token in TOKEN_RE.findall(value.replace("_", " ").replace(".", " ")):
        token = raw_token.replace("'", "")
        parts = CAMEL_TOKEN_RE.findall(token) or [token]
        tokens.extend(part.lower() for part in parts if part)
    return tuple(tokens)


def _module_name(path: Path, root: Path) -> str:
    relative = path.relative_to(root).with_suffix("")
    return ".".join(relative.parts)


def _name_parts(name: str) -> tuple[str, ...]:
    return tuple(part for part in name.split(".") if part)


def _qualified_name(namespace_stack: list[str], raw_name: str) -> str:
    return ".".join((*namespace_stack, *_name_parts(raw_name)))


def _relative_name(full_name: str, source_dir: str) -> str:
    source_root = ".".join(Path(source_dir).parts)
    prefix = f"{source_root}."
    if full_name.startswith(prefix):
        return full_name[len(prefix) :]
    return full_name


def _pop_namespace(namespace_stack: list[str], name: str | None) -> None:
    if not namespace_stack:
        return
    if not name:
        namespace_stack.pop()
        return

    parts = _name_parts(name)
    if parts and tuple(namespace_stack[-len(parts) :]) == parts:
        del namespace_stack[-len(parts) :]
    else:
        namespace_stack.pop()


def _module_tags(module: str) -> tuple[str, ...]:
    return _tags_from_parts(module.split("."))


def _name_tags(name: str) -> tuple[str, ...]:
    return _dedupe((_tag_from_text(name), *_tags_from_parts(name.split("."))))


def _domain_tags(module: str, name: str, full_name: str) -> tuple[str, ...]:
    module_parts = set(module.split("."))
    tokens = set(_tokens(f"{module} {name} {full_name}"))
    identifier_text = f"{module} {name} {full_name}".lower()
    tags: list[str] = []

    if "Benchmarks" in module_parts:
        tags.append("benchmark")
    if "Asymptotics" in module_parts:
        tags.append("asymptotic_calculus")
    if "Estimator" in module_parts:
        tags.append("estimator_interface")
    if "EmpiricalProcess" in module_parts:
        tags.append("empirical_process")
    if "Causal" in module_parts:
        tags.append("causal_identification")
    if "Semiparametric" in module_parts:
        tags.append("semiparametric")

    if {"asymptotic", "normality"} <= tokens:
        tags.append("asymptotic_normality")
    if "bridge" in tokens and "asymptotic" in tokens:
        tags.append("asymptotic_bridge")
    if "convergence" in tokens or "tendsto" in tokens:
        tags.append("convergence")
    if "uniform" in tokens and "deviation" in tokens:
        tags.append("uniform_deviation")
    if "empirical" in tokens and "deviation" in tokens:
        tags.append("uniform_deviation")
    if "mestimator" in identifier_text or "m_estimator" in identifier_text:
        tags.append("m_estimation")
    if "zestimator" in identifier_text or "z_estimator" in identifier_text:
        tags.append("z_estimation")
    if "clt" in tokens or {"central", "limit", "theorem"} <= tokens:
        tags.append("clt")
    if {"delta", "method"} <= tokens:
        tags.append("delta_method")
    if "slutsky" in tokens:
        tags.append("slutsky")
    if {"glivenko", "cantelli"} <= tokens:
        tags.append("glivenko_cantelli")
    if "donsker" in tokens:
        tags.append("donsker")
    if {"oracle", "risk"} & tokens and ({"erm", "excess", "deviation"} & tokens):
        tags.append("erm_consistency")
    if {"potential", "outcomes"} <= tokens or "estimand" in tokens:
        tags.append("potential_outcomes")
    if {"influence", "function"} <= tokens:
        tags.append("influence_function")
    if {"neyman", "orthogonality"} <= tokens:
        tags.append("neyman_orthogonality")

    return _dedupe(tags)


def _tags_from_parts(parts: Iterable[str]) -> tuple[str, ...]:
    tags: list[str] = []
    for part in parts:
        tags.append(_tag_from_text(part))
        tags.extend(_tokens(part))
    return _dedupe(tag for tag in tags if tag)


def _tag_from_text(value: str) -> str:
    return "_".join(_tokens(value))


def _dedupe(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    tags: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            tags.append(value)
    return tuple(tags)


def _search_text(record: PremiseRecord) -> str:
    return " ".join(
        (
            record.name,
            record.full_name,
            record.kind,
            record.module,
            *record.imports,
            *record.module_tags,
            *record.name_tags,
            *record.domain_tags,
        )
    )
