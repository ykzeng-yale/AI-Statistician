from __future__ import annotations

import heapq
from dataclasses import asdict, dataclass
from typing import Iterable

from .fingerprint import stable_hash
from .proof_bank import all_obligations
from .proof_policy_model import ProofPolicyModel
from .proof_search_value_model import ProofSearchValueModel
from .retrieval import tokens
from .schema import FormalObligation, ProofCheck, RetrievalHit
from .verifier import ProofVerifier


PROOF_SEARCH_SCHEMA_VERSION = 4


@dataclass(frozen=True)
class ProofCandidate:
    candidate_id: str
    proof_body: str
    source: str
    score: float
    policy_score: float | None = None
    value_score: float | None = None
    base_score: float | None = None
    origin_obligation_id: str = ""
    expected_lemmas: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    policy_prompt: str = ""


@dataclass(frozen=True)
class ProofSearchNode:
    node_id: str
    candidate_id: str
    proof_body: str
    source: str
    score: float
    policy_score: float | None
    value_score: float | None
    base_score: float | None
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
    retrieval_candidates_total: int
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
        proof_policy_model: ProofPolicyModel | None = None,
        proof_policy_weight: float = 100.0,
        proof_value_model: ProofSearchValueModel | None = None,
        proof_value_weight: float = 1000.0,
    ) -> None:
        if proof_policy_weight < 0:
            raise ValueError("proof_policy_weight must be nonnegative")
        if proof_value_weight < 0:
            raise ValueError("proof_value_weight must be nonnegative")
        self.verifier = verifier
        self.proof_memory = tuple(proof_memory or all_obligations())
        self.proof_policy_model = proof_policy_model
        self.proof_policy_weight = proof_policy_weight
        self.proof_value_model = proof_value_model
        self.proof_value_weight = proof_value_weight

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
            retrieval_hits=retrieval_hits or [],
        )
        candidates = self._apply_policy_scores(obligation, candidates)
        candidates = self._apply_value_scores(obligation, candidates)
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
                proof_body=candidate.proof_body,
                source=candidate.source,
                score=candidate.score,
                policy_score=candidate.policy_score,
                value_score=candidate.value_score,
                base_score=candidate.base_score,
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
            retrieval_candidates_total=sum(1 for row in candidates if row.source.startswith("proof_retrieval:")),
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
        retrieval_hits: Iterable[RetrievalHit],
    ) -> list[ProofCandidate]:
        candidates: list[ProofCandidate] = []
        candidates.extend(extra_candidates)
        query_metadata = _metadata_for_obligation(obligation)
        memory_by_id = {row.id: row for row in self.proof_memory}
        if include_registered_proof:
            candidates.append(
                ProofCandidate(
                    candidate_id=f"{obligation.id}:registered",
                    proof_body=obligation.proof_body,
                    source="registered_proof_body",
                    score=1000.0,
                    base_score=1000.0,
                    value_score=None,
                    origin_obligation_id=obligation.id,
                    expected_lemmas=tuple(obligation.expected_lemmas),
                    tags=tuple(obligation.tags),
                    policy_prompt=query_metadata["prompt"],
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
                    base_score=250.0 - idx,
                    value_score=None,
                    origin_obligation_id=obligation.id,
                    expected_lemmas=tuple(obligation.expected_lemmas),
                    tags=tuple(obligation.tags),
                    policy_prompt=query_metadata["prompt"],
                )
            )
            candidates.append(
                ProofCandidate(
                    candidate_id=f"{obligation.id}:lemma_exact:{idx}",
                    proof_body=f"by\n  exact {lemma}",
                    source="expected_lemma_template",
                    score=200.0 - idx,
                    base_score=200.0 - idx,
                    value_score=None,
                    origin_obligation_id=obligation.id,
                    expected_lemmas=tuple(obligation.expected_lemmas),
                    tags=tuple(obligation.tags),
                    policy_prompt=query_metadata["prompt"],
                )
            )
        for idx, neighbor in enumerate(_rank_memory_neighbors(obligation, self.proof_memory)[:5]):
            if neighbor.id == obligation.id:
                continue
            neighbor_metadata = _metadata_for_obligation(neighbor)
            candidates.append(
                ProofCandidate(
                    candidate_id=f"{obligation.id}:memory:{neighbor.id}",
                    proof_body=neighbor.proof_body,
                    source=f"proof_memory:{neighbor.id}",
                    score=100.0 - idx,
                    base_score=100.0 - idx,
                    value_score=None,
                    origin_obligation_id=neighbor.id,
                    expected_lemmas=tuple(neighbor.expected_lemmas),
                    tags=tuple(neighbor.tags),
                    policy_prompt=neighbor_metadata["prompt"],
                )
            )
        for idx, hit in enumerate(retrieval_hits):
            neighbor = memory_by_id.get(hit.obligation_id)
            if neighbor is None or neighbor.id == obligation.id:
                continue
            neighbor_metadata = _metadata_for_obligation(neighbor)
            score = 120.0 + float(hit.score) - idx
            candidates.append(
                ProofCandidate(
                    candidate_id=f"{obligation.id}:retrieval:{neighbor.id}",
                    proof_body=neighbor.proof_body,
                    source=f"proof_retrieval:{hit.source}:{neighbor.id}",
                    score=score,
                    base_score=score,
                    origin_obligation_id=neighbor.id,
                    expected_lemmas=tuple(neighbor.expected_lemmas),
                    tags=tuple(neighbor.tags),
                    policy_prompt=neighbor_metadata["prompt"],
                )
            )
        return _dedupe_candidates(candidates)

    def _apply_policy_scores(
        self,
        obligation: FormalObligation,
        candidates: Iterable[ProofCandidate],
    ) -> list[ProofCandidate]:
        rows = list(candidates)
        if self.proof_policy_model is None:
            return rows
        query = _policy_query_for_obligation(obligation)
        scored: list[ProofCandidate] = []
        for candidate in rows:
            base_score = candidate.base_score if candidate.base_score is not None else candidate.score
            policy_score = self.proof_policy_model.score(query, _policy_candidate_dict(candidate))
            scored.append(
                ProofCandidate(
                    candidate_id=candidate.candidate_id,
                    proof_body=candidate.proof_body,
                    source=candidate.source,
                    score=base_score + self.proof_policy_weight * policy_score,
                    policy_score=round(policy_score, 6),
                    value_score=candidate.value_score,
                    base_score=base_score,
                    origin_obligation_id=candidate.origin_obligation_id,
                    expected_lemmas=candidate.expected_lemmas,
                    tags=candidate.tags,
                    policy_prompt=candidate.policy_prompt,
                )
            )
        return _dedupe_candidates(scored)

    def _apply_value_scores(
        self,
        obligation: FormalObligation,
        candidates: Iterable[ProofCandidate],
    ) -> list[ProofCandidate]:
        rows = list(candidates)
        if self.proof_value_model is None:
            return rows
        scored: list[ProofCandidate] = []
        for candidate in rows:
            base_score = candidate.base_score if candidate.base_score is not None else candidate.score
            value_score = self.proof_value_model.score(
                _value_candidate_dict(obligation, candidate)
            )
            scored.append(
                ProofCandidate(
                    candidate_id=candidate.candidate_id,
                    proof_body=candidate.proof_body,
                    source=candidate.source,
                    score=candidate.score + self.proof_value_weight * value_score,
                    policy_score=candidate.policy_score,
                    value_score=round(value_score, 6),
                    base_score=base_score,
                    origin_obligation_id=candidate.origin_obligation_id,
                    expected_lemmas=candidate.expected_lemmas,
                    tags=candidate.tags,
                    policy_prompt=candidate.policy_prompt,
                )
            )
        return _dedupe_candidates(scored)


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


def _policy_query_for_obligation(obligation: FormalObligation) -> dict[str, object]:
    metadata = _metadata_for_obligation(obligation)
    return {
        "example_id": f"{obligation.id}:search_query",
        "obligation_id": obligation.id,
        "prompt": metadata["prompt"],
        "completion": "",
        "expected_lemmas": tuple(obligation.expected_lemmas),
        "retrieved_obligations": tuple(row.id for row in _rank_memory_neighbors(obligation, all_obligations())[:8]),
        "tags": tuple(obligation.tags),
    }


def _policy_candidate_dict(candidate: ProofCandidate) -> dict[str, object]:
    return {
        "example_id": candidate.candidate_id,
        "obligation_id": candidate.origin_obligation_id or candidate.candidate_id,
        "prompt": candidate.policy_prompt,
        "completion": candidate.proof_body.strip(),
        "expected_lemmas": tuple(candidate.expected_lemmas),
        "retrieved_obligations": (),
        "tags": tuple(candidate.tags),
    }


def _value_candidate_dict(
    obligation: FormalObligation,
    candidate: ProofCandidate,
) -> dict[str, object]:
    errors: tuple[str, ...] = ()
    return {
        "obligation_id": obligation.id,
        "candidate_id": candidate.candidate_id,
        "candidate_source": candidate.source,
        "candidate_score": candidate.score,
        "expanded_index": 0,
        "prompt": "\n".join(
            [
                f"Obligation: {obligation.title}",
                f"Candidate source: {candidate.source}",
                f"Candidate score: {candidate.score}",
                "Candidate proof body:",
                candidate.proof_body.strip(),
            ]
        ),
        "errors": errors,
        "first_error": "",
    }


def _metadata_for_obligation(obligation: FormalObligation) -> dict[str, str]:
    expected = "\n".join(f"- {lemma}" for lemma in obligation.expected_lemmas) or "- none"
    tags = ", ".join(obligation.tags) or "none"
    return {
        "prompt": "\n".join(
            [
                f"Obligation: {obligation.title}",
                f"Tags: {tags}",
                f"English: {obligation.english}",
                "Expected useful lemmas:",
                expected,
                "Formal statement:",
                obligation.formal_statement,
            ]
        )
    }


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
