from __future__ import annotations

from dataclasses import dataclass

from .algorithms import get_algorithm
from .proof_bank import get_obligation
from .questions import derive_estimator_for_question
from .retrieval import ProofBankRetriever, RetrievalQuery
from .schema import AlgorithmSpec, EstimatorSpec, ProofCheck, StatisticalQuestion
from .verifier import ProofVerifier


class TheoryDeveloperAgent:
    """Chooses an estimator and declares formal obligations.

    Production v1 is template-based because the formal side must be honest:
    only Mathlib-backed obligations are emitted. A Claude/OpenAI theory proposer
    can be added as another implementation, but it should still pass through
    this obligation registry before being considered verified.
    """

    def develop(self, question: StatisticalQuestion) -> EstimatorSpec:
        return derive_estimator_for_question(question)


class AlgorithmEngineerAgent:
    """Selects a vetted algorithm implementation for an estimator spec."""

    def implement(self, estimator: EstimatorSpec) -> AlgorithmSpec:
        record = get_algorithm(estimator.algorithm)
        return AlgorithmSpec(
            id=record.id,
            estimator_id=estimator.id,
            code_summary=record.summary,
            implementation_hash=record.implementation_hash(),
            registry_status=record.registry_status,
            version=record.version,
        )


@dataclass
class FormalVerifierAgent:
    verifier: ProofVerifier
    retriever: ProofBankRetriever

    async def verify_estimator(self, estimator: EstimatorSpec) -> list[ProofCheck]:
        checks: list[ProofCheck] = []
        for obligation_id in estimator.formal_obligation_ids:
            obligation = get_obligation(obligation_id)
            query = RetrievalQuery(
                text=" ".join(
                    [
                        estimator.formula,
                        estimator.guarantee,
                        obligation.english,
                        " ".join(obligation.expected_lemmas),
                    ]
                ),
                tags=obligation.tags,
            )
            hits = self.retriever.retrieve(query, k=5)
            # Retrieval ranks over the full curated stats proof bank. The
            # estimator still names required obligations explicitly, and the
            # verifier remains the final correctness gate.
            check = await self.verifier.verify(obligation, obligation.proof_body, hits)
            checks.append(check)
        return checks
