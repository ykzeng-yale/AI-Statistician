from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from .fingerprint import stable_hash
from .formal_source_index import FormalDeclaration, FormalSourceRetriever
from .proof_bank import all_obligations, proof_bank_fingerprint
from .retrieval import ProofBankRetriever, RetrievalQuery
from .schema import FormalObligation


PROOF_BANK_FORMAL_SOURCE_BOUNDARY = (
    "A proof-bank retrieval hit is reusable Lean context and a candidate proof "
    "body, not proof evidence for the current theorem. Any selected candidate "
    "must be instantiated for the exact target and rerun under the configured "
    "local Lean/AXLE kernel gate."
)


@dataclass(frozen=True)
class ProofBankFormalSourceHit:
    declaration: FormalDeclaration
    score: float
    matched_terms: tuple[str, ...]
    provenance: Mapping[str, Any] = field(default_factory=dict)


class ProofBankFormalSourceRetriever:
    """Expose calibrated proof-bank obligations through formal-source RAG."""

    name = "ai_statistician_proof_bank_formal_source"

    def __init__(
        self,
        *,
        obligations: Sequence[FormalObligation] | None = None,
        retriever: ProofBankRetriever | None = None,
    ) -> None:
        using_full_bank = obligations is None
        self.obligations = tuple(all_obligations() if using_full_bank else obligations)
        self._obligations_by_id = {row.id: row for row in self.obligations}
        self.retriever = retriever or ProofBankRetriever()
        self.fingerprint = (
            proof_bank_fingerprint()
            if using_full_bank
            else stable_hash([_obligation_fingerprint_row(row) for row in self.obligations])
        )

    def descriptor(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "source": "ai_statistician/proof_bank.py",
            "n_obligations": len(self.obligations),
            "proof_bank_fingerprint": self.fingerprint,
            "ranking": "ProofBankRetriever",
            "available": bool(self.obligations),
            "boundary": PROOF_BANK_FORMAL_SOURCE_BOUNDARY,
        }

    def search(self, query: str, *, k: int = 10) -> list[ProofBankFormalSourceHit]:
        limit = max(int(k), 0)
        if limit == 0 or not self.obligations:
            return []
        rows = self.retriever.retrieve(
            RetrievalQuery(text=query),
            candidates=list(self.obligations),
            k=limit,
        )
        hits: list[ProofBankFormalSourceHit] = []
        for row in rows:
            obligation = self._obligations_by_id.get(row.obligation_id)
            if obligation is None:
                continue
            candidate_fingerprint = stable_hash(
                [obligation.id, obligation.formal_statement, obligation.proof_body]
            )
            hits.append(
                ProofBankFormalSourceHit(
                    declaration=FormalDeclaration(
                        source_id=f"ai_statistician_proof_bank:{self.fingerprint[:20]}",
                        source_type="lean_proof_bank_obligation",
                        path="ai_statistician/proof_bank.py",
                        line=0,
                        kind="proof_obligation",
                        name=obligation.id,
                        namespace="",
                        signature=obligation.formal_statement,
                    ),
                    score=float(row.score),
                    matched_terms=tuple(row.matched_terms),
                    provenance={
                        "provider": self.name,
                        "obligation_id": obligation.id,
                        "proof_bank_fingerprint": self.fingerprint,
                        "candidate_fingerprint": candidate_fingerprint,
                        "candidate_proof_body": obligation.proof_body,
                        "tags": list(obligation.tags),
                        "expected_lemmas": list(obligation.expected_lemmas),
                        "depends_on": list(obligation.depends_on),
                        "upstream_source": obligation.source,
                        "proof_evidence_status": (
                            "PROOF_BANK_RETRIEVAL_NOT_PROOF_EVIDENCE"
                        ),
                        "proof_evidence_boundary": (
                            PROOF_BANK_FORMAL_SOURCE_BOUNDARY
                        ),
                        "required_verification": (
                            "Instantiate the candidate for the exact target and rerun "
                            "it under the configured local Lean/AXLE kernel gate."
                        ),
                    },
                )
            )
        return hits


def build_default_formal_source_retriever(
    *,
    additional_providers: Sequence[Any] = (),
    local_retriever: Any | None = None,
    proof_bank_retriever: Any | None = None,
) -> Any:
    """Build the shared AgentRuntime retrieval topology."""

    from .lean_agent_providers import CompositeFormalSourceRetriever

    return CompositeFormalSourceRetriever(
        (
            (
                local_retriever
                if local_retriever is not None
                else FormalSourceRetriever()
            ),
            (
                proof_bank_retriever
                if proof_bank_retriever is not None
                else ProofBankFormalSourceRetriever()
            ),
            *tuple(additional_providers),
        )
    )


def _obligation_fingerprint_row(obligation: FormalObligation) -> dict[str, Any]:
    return {
        "id": obligation.id,
        "title": obligation.title,
        "english": obligation.english,
        "formal_statement": obligation.formal_statement,
        "proof_body": obligation.proof_body,
        "tags": list(obligation.tags),
        "expected_lemmas": list(obligation.expected_lemmas),
        "source": obligation.source,
        "depends_on": list(obligation.depends_on),
    }
