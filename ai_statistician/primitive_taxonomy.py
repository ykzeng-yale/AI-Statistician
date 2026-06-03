from __future__ import annotations


ASSUMPTION_INTERFACE_PRIMITIVES: frozenset[str] = frozenset(
    {
        # Causal exchangeability is an identifying assumption. The system should
        # formalize a reusable Lean predicate/interface for it and then use that
        # assumption in identification theorems; it should not "prove" the
        # assumption with a tautological proof-bank wrapper.
        "conditional_exchangeability",
    }
)


def primitive_kind(primitive: str) -> str:
    if primitive in ASSUMPTION_INTERFACE_PRIMITIVES:
        return "assumption_interface"
    return "theorem_primitive"


def is_assumption_interface_primitive(primitive: str) -> bool:
    return primitive_kind(primitive) == "assumption_interface"
