from __future__ import annotations

from ai_statistician.research_knowledge import retrieve_problem_knowledge
from ai_statistician.research_schema import (
    OpenResearchQuestion,
    ResearchProblemSpec,
    TheoremGoal,
)


def test_generic_architect_problem_class_keeps_domain_and_formal_knowledge() -> None:
    question = OpenResearchQuestion(
        id="generic-anytime-question",
        title="Anytime-valid Bernoulli inference",
        description=(
            "Construct an e-process for optional stopping under a Bernoulli null."
        ),
        tags=("sequential", "anytime", "optional_stopping"),
    )
    problem = ResearchProblemSpec(
        question_id=question.id,
        problem_class="architect_defined_frontier_problem",
        dgp="An iid Bernoulli sequence with an optional stopping time.",
        estimand="An anytime-valid sequential test.",
        assumptions=("The null success probability is one half.",),
        asymptotic_regime="Sequential monitoring without a fixed horizon.",
        diagnostics=(),
        stress_tests=(),
    )
    goals = [
        TheoremGoal(
            id="anytime-validity",
            title="Anytime validity",
            informal_statement=(
                "A nonnegative e-process controls threshold crossing under the null."
            ),
            proof_strategy="Use a test-martingale maximal inequality.",
            required_primitives=(),
            proof_obligations=(),
            status="FORMAL_GAP",
        )
    ]

    cards = retrieve_problem_knowledge(question, problem, goals, k=8)
    card_ids = [card.id for card in cards]

    assert card_ids[0] == "anytime_valid_eprocesses"
    assert card_ids[2] == "sequential_changepoint_post_detection"
    assert "local_mathlib_probability" in card_ids
    assert any(card.source_type == "statistical_method" for card in cards)
    assert any(card.source_type != "statistical_method" for card in cards)


def test_problem_knowledge_zero_budget_returns_no_cards() -> None:
    question = OpenResearchQuestion(
        id="zero-budget",
        title="Zero retrieval budget",
        description="Do not retrieve a card when the caller supplies no budget.",
    )
    problem = ResearchProblemSpec(
        question_id=question.id,
        problem_class="architect_defined_frontier_problem",
        dgp="Unspecified.",
        estimand="Unspecified.",
        assumptions=(),
        asymptotic_regime="Unspecified.",
        diagnostics=(),
        stress_tests=(),
    )

    assert retrieve_problem_knowledge(question, problem, [], k=0) == []
