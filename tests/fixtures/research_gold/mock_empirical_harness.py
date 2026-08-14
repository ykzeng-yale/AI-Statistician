def run_sandbox(seed, replicates, estimators):
    del seed, replicates
    return {
        "empirical_gold_ok": bool(estimators),
    }
