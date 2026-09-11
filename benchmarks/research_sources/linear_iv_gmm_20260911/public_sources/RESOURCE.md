# Pinned IV/GMM Resource

This snapshot contains selected unchanged files from `bashtage/linearmodels`
version 7.0, commit `28af72ed08b1df00157d08a12a16a6c18f31a358`, under its NCSA
license. `run_iv_source.py` and the environment lock are operator-authored.

The launcher checks installed implementation, test and data bytes, then runs three
unchanged heteroskedastic weight-matrix tests and the first eleven unchanged code
cells of `examples/iv_advanced-examples.ipynb`. That prefix loads complete MEPS
observations, specifies controls and instruments, fits OLS and IV alternatives,
and finishes at two-step heteroskedastic IVGMM. The launcher prints that fit and
writes `iv_source_result.json`. Later clustered, CUE and LIML cells are not run.

Report actual observed results and their limitations. This is a public software
example reproduction, not reproduction of every Hansen (1982) result or experiment,
newly generated code validation, confirmatory simulation, or proof that the
empirical instruments identify a causal effect. Hidden reference mathematics and
evaluation results are not part of this snapshot.

Primary theoretical reference: Lars Peter Hansen (1982), *Large Sample Properties
of Generalized Method of Moments Estimators*, Econometrica 50(4), 1029-1054,
DOI 10.2307/1912775. The research question selects iid linear overidentification;
the original paper's more general dependent setting is not silently assumed.
