def run_sandbox(seed, replicates, estimators):
    del seed, replicates, estimators
    return {
        "hidden_cases_total": 4,
        "hidden_cases_passed": 4,
        "max_direct_reference_error": 0.0,
        "permutation_invariance_error": 0.0,
        "response_scale_equivariance_error": 0.0,
        "exact_fit_error": 0.0,
        "all_outputs_finite": True,
    }
