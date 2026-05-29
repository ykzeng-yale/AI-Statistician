from __future__ import annotations

import json
import os
import re
import sys
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from .proof_bank import all_obligations, proof_bank_fingerprint
from .schema import FormalObligation, RetrievalHit


TOKEN_RE = re.compile(r"[\w'₀-₉.]+|[∀∃∧∨→↔=≤≥<>+*/^.-]+", re.UNICODE)
STOP_TOKENS = {
    "the",
    "a",
    "an",
    "of",
    "for",
    "and",
    "or",
    "is",
    "to",
    "by",
    "with",
    "exact",
    "fun",
    "have",
    "let",
    "match",
    "prop",
    "sort",
    "theorem",
    "true",
    "type",
    ".",
    ",",
    "-",
    "/",
    "=",
}


def _fallback_tokens(text: str) -> set[str]:
    return {
        token.lower()
        for token in TOKEN_RE.findall(text)
        if token.strip() and token.lower() not in STOP_TOKENS
    }


def _openprover_tokens(text: str) -> set[str] | None:
    """Use OpenProver's Lean-ish tokenizer if that local codebase is available."""
    if os.environ.get("AI_STATISTICIAN_USE_OPENPROVER_TOKENS") != "1":
        return None
    lean_tokens = _openprover_lean_tokens()
    if lean_tokens is None:
        return None
    return set(lean_tokens(text))


@lru_cache(maxsize=1)
def _openprover_lean_tokens():
    """Import OpenProver tokenization only when explicitly enabled.

    The local OpenProver checkout is useful as a reference implementation, but
    importing its retrieval module can recursively import a much larger prover
    stack.  Retrieval tokenization is on the hot path for paper and knowledge
    search, so the production default uses the local tokenizer above and keeps
    the direct OpenProver import as an opt-in compatibility hook.
    """
    openprover_src = Path(
        os.environ.get("OPENPROVER_SRC", "/Users/yukang/Documents/OpenProver/src")
    ).expanduser()
    if not openprover_src.exists():
        return None
    src = str(openprover_src)
    if src not in sys.path:
        sys.path.insert(0, src)
    try:
        from openprover.retrieval import lean_tokens
    except Exception:
        return None
    return lean_tokens


def tokens(text: str) -> set[str]:
    raw = _openprover_tokens(text) or _fallback_tokens(text)
    return {token for token in raw if token not in STOP_TOKENS and any(ch.isalnum() for ch in token)}


@dataclass(frozen=True)
class RetrievalQuery:
    text: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class RetrievalAuditRow:
    obligation_id: str
    rank: int | None
    top1: str | None
    hit: bool
    top_k_hits: tuple[RetrievalHit, ...]


@dataclass(frozen=True)
class LoogleAuditRow:
    obligation_id: str
    query: str
    expected_lemmas: tuple[str, ...]
    hits: tuple[str, ...]
    expected_lemma_hit: bool
    error: str | None = None


class ProofBankRetriever:
    """Small deterministic retriever over the local statistics proof bank.

    This is intentionally simple. Its role is to provide a production-safe
    scaffold and to reuse OpenProver's tokenization when the OpenProver checkout
    is present. More powerful systems such as Loogle, Lean Finder, or ReProver
    plug in beside this class.
    """

    source = "proof_bank+openprover_tokens"

    def retrieve(
        self,
        query: RetrievalQuery,
        *,
        candidates: list[FormalObligation] | None = None,
        k: int = 5,
    ) -> list[RetrievalHit]:
        q_tokens = tokens(" ".join([query.text, *query.tags]))
        tag_set = set(query.tags)
        rows: list[RetrievalHit] = []
        for obligation in candidates or all_obligations():
            haystack = " ".join(
                [
                    obligation.id,
                    obligation.title,
                    obligation.english,
                    " ".join(obligation.tags),
                    " ".join(obligation.expected_lemmas),
                    obligation.formal_statement,
                ]
            )
            o_tokens = tokens(haystack)
            overlap = q_tokens & o_tokens
            tag_bonus = len(tag_set & set(obligation.tags))
            score = len(overlap) + 2.0 * tag_bonus
            if score <= 0:
                continue
            rows.append(
                RetrievalHit(
                    obligation_id=obligation.id,
                    score=score,
                    source=self.source,
                    matched_terms=tuple(sorted(overlap)[:12]),
                )
            )
        return sorted(rows, key=lambda row: (-row.score, row.obligation_id))[:k]


def query_for_obligation(obligation: FormalObligation) -> RetrievalQuery:
    return RetrievalQuery(
        text=" ".join(
            [
                obligation.title,
                obligation.english,
                " ".join(obligation.expected_lemmas),
            ]
        ),
        tags=obligation.tags,
    )


def loogle_query_for_obligation(obligation: FormalObligation) -> str:
    """Identifier-oriented query for external Mathlib search.

    Loogle's JSON endpoint is best treated as a Lean declaration/name resolver,
    not as a semantic natural-language retriever. For the current proof bank, we
    therefore ask it to resolve expected lemma identifiers and record whether
    Mathlib namespaced declarations come back. Semantic retrieval remains a
    separate Lean Finder/ReProver-style integration target.
    """

    if obligation.expected_lemmas:
        return " | ".join(obligation.expected_lemmas)
    return " ".join([obligation.title, obligation.english, " ".join(obligation.tags)])


def audit_proof_bank_retrieval(
    out_dir: Path | None = None,
    *,
    k: int = 5,
    include_loogle: bool = False,
    loogle_retriever: object | None = None,
    loogle_k: int = 10,
    loogle_timeout_s: float = 8.0,
) -> dict[str, object]:
    """Evaluate whether local retrieval can recover each proof-bank obligation.

    This is not a proof checker. It is a premise-selection smoke test: for each
    Mathlib-backed obligation, build a natural-language/type-ish query and rank
    over the entire local statistics proof bank. Optional Loogle evidence is
    recorded beside the local gate but does not affect pass/fail status.
    """

    retriever = ProofBankRetriever()
    obligations = all_obligations()
    rows: list[RetrievalAuditRow] = []
    reciprocal_ranks: list[float] = []
    for obligation in obligations:
        hits = retriever.retrieve(query_for_obligation(obligation), candidates=obligations, k=max(k, len(obligations)))
        rank = next(
            (idx for idx, hit in enumerate(hits, start=1) if hit.obligation_id == obligation.id),
            None,
        )
        if rank is not None:
            reciprocal_ranks.append(1.0 / rank)
        rows.append(
            RetrievalAuditRow(
                obligation_id=obligation.id,
                rank=rank,
                top1=hits[0].obligation_id if hits else None,
                hit=rank is not None and rank <= k,
                top_k_hits=tuple(hits[:k]),
            )
        )
    n_top1 = sum(1 for row in rows if row.rank == 1)
    n_top_k = sum(1 for row in rows if row.hit)
    loogle_payload: dict[str, object] = {"enabled": False}
    if include_loogle:
        loogle = loogle_retriever or LoogleRetriever(timeout_s=loogle_timeout_s)
        loogle_rows: list[LoogleAuditRow] = []
        for obligation in obligations:
            query = loogle_query_for_obligation(obligation)
            try:
                hits = _loogle_hits_for_obligation(loogle, obligation, k=loogle_k)
                error = None
            except Exception as exc:
                hits = ()
                error = f"{type(exc).__name__}: {exc}"
            loogle_rows.append(
                LoogleAuditRow(
                    obligation_id=obligation.id,
                    query=query,
                    expected_lemmas=obligation.expected_lemmas,
                    hits=hits,
                    expected_lemma_hit=_any_expected_lemma_hit(hits, obligation.expected_lemmas),
                    error=error,
                )
            )
        n_expected_hits = sum(1 for row in loogle_rows if row.expected_lemma_hit)
        loogle_payload = {
            "enabled": True,
            "source": getattr(loogle, "source", "loogle"),
            "k": loogle_k,
            "n_queries": len(loogle_rows),
            "n_expected_lemma_hits": n_expected_hits,
            "expected_lemma_hit_rate": n_expected_hits / len(loogle_rows) if loogle_rows else 0.0,
            "n_errors": sum(1 for row in loogle_rows if row.error),
            "rows": [asdict(row) for row in loogle_rows],
        }
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "retriever": ProofBankRetriever.source,
        "proof_bank_fingerprint": proof_bank_fingerprint(),
        "k": k,
        "n_obligations": len(rows),
        "top1": n_top1,
        "top_k": n_top_k,
        "top1_rate": n_top1 / len(rows) if rows else 0.0,
        "top_k_rate": n_top_k / len(rows) if rows else 0.0,
        "mrr": sum(reciprocal_ranks) / len(rows) if rows else 0.0,
        "all_top_k": n_top_k == len(rows),
        "rows": [asdict(row) for row in rows],
        "loogle": loogle_payload,
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "retrieval_audit_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
    return payload


class LoogleRetriever:
    """Optional Loogle integration.

    The main system does not depend on this at runtime. It is here so production
    RAG can leverage an existing Mathlib search service instead of building a
    bespoke retriever.
    """

    source = "loogle"

    def __init__(self, endpoint: str = "https://loogle.lean-lang.org/json", timeout_s: float = 8.0):
        self.endpoint = endpoint
        self.timeout_s = timeout_s

    def search_names(self, query: str, k: int = 10) -> list[str]:
        params = urllib.parse.urlencode({"q": query})
        url = f"{self.endpoint}?{params}"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout_s) as response:
            data = response.read().decode("utf-8")
        import json

        parsed = json.loads(data)
        hits = parsed.get("hits") or parsed.get("results") or []
        out: list[str] = []
        for hit in hits[:k]:
            if isinstance(hit, dict):
                name = hit.get("name") or hit.get("declaration") or hit.get("decl")
                if name:
                    out.append(str(name))
            elif isinstance(hit, str):
                out.append(hit)
        for suggestion in parsed.get("suggestions", []):
            if isinstance(suggestion, str):
                out.append(suggestion)
            elif isinstance(suggestion, dict):
                name = suggestion.get("name") or suggestion.get("declaration") or suggestion.get("decl")
                if name:
                    out.append(str(name))
            if len(out) >= k:
                break
        return out


def _loogle_hits_for_obligation(loogle: object, obligation: FormalObligation, *, k: int) -> tuple[str, ...]:
    queries = obligation.expected_lemmas or (loogle_query_for_obligation(obligation),)
    hits: list[str] = []
    seen: set[str] = set()
    for query in queries:
        for hit in loogle.search_names(query, k=k):  # type: ignore[attr-defined]
            name = str(hit)
            if name in seen:
                continue
            seen.add(name)
            hits.append(name)
            if len(hits) >= k:
                return tuple(hits)
    return tuple(hits)


def _any_expected_lemma_hit(hits: tuple[str, ...], expected_lemmas: tuple[str, ...]) -> bool:
    return any(_lemma_name_matches(hit, expected) for hit in hits for expected in expected_lemmas)


def _lemma_name_matches(hit: str, expected: str) -> bool:
    hit_norm = hit.strip()
    expected_norm = expected.strip()
    return (
        hit_norm == expected_norm
        or hit_norm.endswith("." + expected_norm)
        or expected_norm.endswith("." + hit_norm)
    )
