from __future__ import annotations

import heapq
from dataclasses import asdict, dataclass
from typing import Iterable

from .fingerprint import stable_hash
from .proof_bank import all_obligations
from .retrieval import tokens
from .schema import FormalObligation, ProofCheck, RetrievalHit
from .verifier import ProofVerifier


PROOF_SEARCH_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class ProofCandidate:
    candidate_id: str
    proof_body: str
    source: str
    score: float


@dataclass(frozen=True)
class ProofSearchNode:
    node_id: str
    candidate_id: str
    source: str
    score: float
    expanded_index: int
    ok: bool
    kernel_verified: bool
    verifier: str
    verification_strength: str
    elapsed_ms: int
    errors: tuple[str, ...]


@dataclass(frozen=True)
class ProofSearchResult:
    schema_version: int
    obligation_id: str
    solved: bool
    kernel_verified: bool
    selected_candidate_id: str
    selected_source: str
    selected_proof_body: str
    selected_verification_strength: str
    nodes_expanded: int
    candidates_total: int
    frontier_exhausted: bool
    verifier: str
    search_fingerprint: str
    nodes: tuple[ProofSearchNode, ...]


class BestFirstWholeProofSearchController:
    """Verifier-grounded whole-proof best-first search.

    This is intentionally not advertised as tactic-state search or MCTS. It is
    the first search-controller layer above one-shot obligation lookup: generate
    a bounded proof-body frontier, expand candidates by deterministic priority,
    and let the configured verifier be the final judge.
    """

    def __init__(
        self,
        verifier: ProofVerifier,
        *,
        proof_memory: Iterable[FormalObligation] | None = None,
    ) -> None:
        self.verifier = verifier
        self.proof_memory = tuple(proof_memory or all_obligations())

    async def solve(
        self,
        obligation: FormalObligation,
        *,
        max_nodes: int = 8,
        extra_candidates: Iterable[ProofCandidate] = (),
        retrieval_hits: list[RetrievalHit] | None = None,
        include_registered_proof: bool = True,
    ) -> ProofSearchResult:
        if max_nodes <= 0:
            raise ValueError("max_nodes must be positive")
        candidates = self._candidates(
            obligation,
            extra_candidates=extra_candidates,
            include_registered_proof=include_registered_proof,
        )
        frontier: list[tuple[float, str, ProofCandidate]] = []
        for candidate in candidates:
            heapq.heappush(frontier, (-candidate.score, candidate.candidate_id, candidate))
        nodes: list[ProofSearchNode] = []
        selected_check: ProofCheck | None = None
        selected_candidate: ProofCandidate | None = None
        seen: set[str] = set()
        while frontier and len(nodes) < max_nodes:
            _priority, _candidate_id, candidate = heapq.heappop(frontier)
            body_key = candidate.proof_body.strip()
            if not body_key or body_key in seen:
                continue
            seen.add(body_key)
            check = await self.verifier.verify(
                obligation,
                candidate.proof_body,
                retrieval_hits or [],
            )
            node = ProofSearchNode(
                node_id=f"{obligation.id}:node:{len(nodes) + 1}",
                candidate_id=candidate.candidate_id,
                source=candidate.source,
                score=candidate.score,
                expanded_index=len(nodes) + 1,
                ok=check.ok,
                kernel_verified=check.kernel_verified,
                verifier=check.verifier,
                verification_strength=check.verification_strength,
                elapsed_ms=check.elapsed_ms,
                errors=tuple(check.errors),
            )
            nodes.append(node)
            if check.ok:
                selected_check = check
                selected_candidate = candidate
                break
        solved = selected_check is not None and selected_candidate is not None
        selected_body = selected_candidate.proof_body if selected_candidate else ""
        selected_id = selected_candidate.candidate_id if selected_candidate else ""
        selected_source = selected_candidate.source if selected_candidate else ""
        selected_strength = selected_check.verification_strength if selected_check else ""
        fingerprint_payload = {
            "obligation_id": obligation.id,
            "max_nodes": max_nodes,
            "candidates": [asdict(row) for row in candidates],
            "nodes": [asdict(row) for row in nodes],
            "selected_candidate_id": selected_id,
        }
        return ProofSearchResult(
            schema_version=PROOF_SEARCH_SCHEMA_VERSION,
            obligation_id=obligation.id,
            solved=solved,
            kernel_verified=bool(selected_check.kernel_verified) if selected_check else False,
            selected_candidate_id=selected_id,
            selected_source=selected_source,
            selected_proof_body=selected_body,
            selected_verification_strength=selected_strength,
            nodes_expanded=len(nodes),
            candidates_total=len(candidates),
            frontier_exhausted=not solved and (not frontier or len(nodes) >= max_nodes),
            verifier=selected_check.verifier if selected_check else getattr(self.verifier, "name", "unknown"),
            search_fingerprint=stable_hash(fingerprint_payload),
            nodes=tuple(nodes),
        )

    def _candidates(
        self,
        obligation: FormalObligation,
        *,
        extra_candidates: Iterable[ProofCandidate],
        include_registered_proof: bool,
    ) -> list[ProofCandidate]:
        candidates: list[ProofCandidate] = []
        candidates.extend(extra_candidates)
        if include_registered_proof:
            candidates.append(
                ProofCandidate(
                    candidate_id=f"{obligation.id}:registered",
                    proof_body=obligation.proof_body,
                    source="registered_proof_body",
                    score=1000.0,
                )
            )
        for idx, lemma in enumerate(obligation.expected_lemmas):
            if not lemma or any(ch.isspace() for ch in lemma):
                continue
            candidates.append(
                ProofCandidate(
                    candidate_id=f"{obligation.id}:lemma_simpa:{idx}",
                    proof_body=f"by\n  simpa using {lemma}",
                    source="expected_lemma_template",
                    score=250.0 - idx,
                )
            )
            candidates.append(
                ProofCandidate(
                    candidate_id=f"{obligation.id}:lemma_exact:{idx}",
                    proof_body=f"by\n  exact {lemma}",
                    source="expected_lemma_template",
                    score=200.0 - idx,
                )
            )
        for idx, neighbor in enumerate(_rank_memory_neighbors(obligation, self.proof_memory)[:5]):
            if neighbor.id == obligation.id:
                continue
            candidates.append(
                ProofCandidate(
                    candidate_id=f"{obligation.id}:memory:{neighbor.id}",
                    proof_body=neighbor.proof_body,
                    source=f"proof_memory:{neighbor.id}",
                    score=100.0 - idx,
                )
            )
        return _dedupe_candidates(candidates)


def _rank_memory_neighbors(
    obligation: FormalObligation,
    proof_memory: Iterable[FormalObligation],
) -> list[FormalObligation]:
    query_tokens = tokens(
        " ".join(
            (
                obligation.id,
                obligation.title,
                obligation.english,
                " ".join(obligation.expected_lemmas),
                " ".join(obligation.tags),
            )
        )
    )
    expected = {row.lower() for row in obligation.expected_lemmas}
    tags = {row.lower() for row in obligation.tags}
    scored: list[tuple[float, str, FormalObligation]] = []
    for candidate in proof_memory:
        candidate_tokens = tokens(
            " ".join(
                (
                    candidate.id,
                    candidate.title,
                    candidate.english,
                    " ".join(candidate.expected_lemmas),
                    " ".join(candidate.tags),
                )
            )
        )
        overlap = len(query_tokens & candidate_tokens)
        expected_overlap = len(expected & {row.lower() for row in candidate.expected_lemmas})
        tag_overlap = len(tags & {row.lower() for row in candidate.tags})
        score = overlap + 4.0 * expected_overlap + 3.0 * tag_overlap
        if score > 0:
            scored.append((score, candidate.id, candidate))
    return [row[2] for row in sorted(scored, key=lambda item: (-item[0], item[1]))]


def _dedupe_candidates(candidates: Iterable[ProofCandidate]) -> list[ProofCandidate]:
    by_body: dict[str, ProofCandidate] = {}
    for candidate in candidates:
        key = candidate.proof_body.strip()
        if not key:
            continue
        previous = by_body.get(key)
        if previous is None or candidate.score > previous.score:
            by_body[key] = candidate
    return sorted(by_body.values(), key=lambda row: (-row.score, row.candidate_id))
