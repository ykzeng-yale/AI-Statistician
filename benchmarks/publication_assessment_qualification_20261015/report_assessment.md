# Declared Report-Level Examination

Examined once on 2026-10-15 after the qualification stopped. This is the operator
AI's examination specified before inference, not a new model judgment, human
review, mathematical certification or retrospective change to native verdicts.
Exact reports, scripts, output and the incomplete response remain unchanged in
the private output referenced by [observed_results.json](observed_results.json).

## Completed Reports

**c1: native PASS.** The report recognizes both correctness branches, conditional
parallel trends and the propensity normalization. Its central reasoning agrees
with the prewritten source-bound key. It stays at population identification and
does not infer consistency or inference for estimated nuisances. This is one
completed review of a valid argument, not general assessor reliability.

**c2: native PASS, with inaccurate computational corroboration.** The report
recognizes the equivalent bias-decomposition argument. Its displayed analytic
coefficient is correct: setting q=m0 removes the residual, and setting pi=p with
the established kappa=nu removes the coefficient. That central reasoning agrees
with the key; no native verdict is changed here.

However, its claim that the executed symbolic scratch confirms both cases is
overstated. The unchanged scratch transcribes the working-propensity denominator
as `(1-p)` rather than `(1-pi)` and does not substitute `kappa=nu` in its second
branch. Its actual output is:

```text
Case 1 (q = m0): 0
Case 2 (pi = p): p*(kappa - nu)*(m0 - q)/(kappa*nu)
```

The second expression vanishes under kappa=nu, as the analytic argument says;
it does not disprove the theorem. But the executed script is not a literal check
of the full bias functional or a direct two-zero result. This discrepancy limits
the report's computational evidence. Neither execution success nor this scratch
establishes a proof. No script, source, output or report was repaired or rerun.

## Incomplete And Unrun Cases

**c3: incomplete, no verdict.** The first turn read the candidate and issued seven
searches. The next wire response reached 16384 output tokens with
`finish_reason=length`. Its `run_theory_scratchpad` arguments contain an unfinished
49551-character JSON string. Parsing raised JSONDecodeError before tool dispatch.
There was no scratch execution, submitted referee report or verdict for this
case. Do not interpret the partial code as a proof, a rejection of the false
claim, or its acceptance. The retained pending session is not resumed.

**c4, candidate-negative and candidate-positive: NOT_RUN.** The declared first-
failure stop left them unobserved. They are not counted as correct or incorrect;
there is no observed false-positive rate, six-case accuracy or successful
candidate-mode check.

## Decision And Scope

**Scientific qualification is not established.** Only two of four calibration
reviews completed, one also overstating its scratch evidence; the negative,
underspecified and candidate-mode obligations did not all complete. No activation
judgment was emitted. This does not certify the full DRDID method, research-E2E,
either paper or a limitation of every possible local Qwen condition.

The generic incomplete-session row labels the provider exception but says
`provider_output_truncated=false`; the retained wire and metadata explicitly show
the output limit. That is a transport-metadata loss, not a mathematical finding.
A future shared fix should preserve received stop/usage metadata through decoding
failure without repairing content, executing partial calls, retrying this draw or
changing scientific acceptance. No production code is changed by this record.

The owned server was stopped and PID/port absence verified. Raw controls, reports,
wire responses and all earlier outcomes are retained. No official H/S study,
research draw, source-family replacement or checklist credit follows.
