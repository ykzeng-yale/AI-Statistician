def evaluate_artifact(candidate, *, seed, replicates):
    del seed, replicates
    return {
        "theory_gold_ok": bool(
            candidate.get("artifact_kind") == "TheoryDerivationPacket"
            and candidate.get("serious_theory_mode") is True
        )
    }
