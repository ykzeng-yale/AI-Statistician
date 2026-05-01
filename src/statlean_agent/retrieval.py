"""Lightweight premise indexing for local Lean files."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


DECL_RE = re.compile(r"^\s*(?:theorem|lemma|def|abbrev|structure|class|inductive)\s+([A-Za-z_][A-Za-z0-9_'.]*)")
IMPORT_RE = re.compile(r"^\s*import\s+([A-Za-z0-9_'.]+)")
TOKEN_RE = re.compile(r"[A-Za-z0-9_']+")


@dataclass(frozen=True)
class PremiseRecord:
    """A retrievable Lean declaration."""

    name: str
    kind: str
    module: str
    file: str
    line: int
    imports: tuple[str, ...] = ()


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
        for line_number, line in enumerate(text.splitlines(), start=1):
            match = DECL_RE.match(line)
            if not match:
                continue
            kind = line.strip().split(maxsplit=1)[0]
            records.append(
                PremiseRecord(
                    name=match.group(1),
                    kind=kind,
                    module=module,
                    file=str(path.relative_to(root)),
                    line=line_number,
                    imports=imports,
                )
            )
    return tuple(records)


def search_premises(records: tuple[PremiseRecord, ...], query: str, top_k: int = 8) -> tuple[PremiseRecord, ...]:
    """Return deterministic token-overlap premise matches."""

    query_tokens = set(_tokens(query))
    scored: list[tuple[int, str, PremiseRecord]] = []
    for record in records:
        haystack = set(_tokens(f"{record.name} {record.kind} {record.module} {' '.join(record.imports)}"))
        overlap = len(query_tokens & haystack)
        substring_bonus = 2 if query.lower() and query.lower() in record.name.lower() else 0
        score = overlap + substring_bonus
        if score > 0:
            scored.append((-score, record.name, record))
    scored.sort()
    return tuple(record for _, _, record in scored[:top_k])


def _tokens(value: str) -> tuple[str, ...]:
    tokens: list[str] = []
    for token in TOKEN_RE.findall(value):
        tokens.extend(part.lower() for part in token.split("_") if part)
    return tuple(tokens)


def _module_name(path: Path, root: Path) -> str:
    relative = path.relative_to(root).with_suffix("")
    return ".".join(relative.parts)
