# Declared Report Examination

2026-10-16. The operator Codex examined all five complete, hash-matched public
Markdown reports once against the frozen question, obligations, reference and
prewritten key. This is the protocol's declared examination, not another model
request, a human panel, a repaired report or a second score. No private model
reasoning was read. The original labels and `LABEL_MISMATCH` outcome stand.

## Observed Decisions

| Case | Expected | Observed | Examination of the main decision |
| --- | --- | --- | --- |
| 01: conditioning argument | PASS | PASS | The two actual affine-residual branches and normalization support the target. |
| 02: bias-identity alternative | PASS | PASS | The equivalent decomposition and its branchwise cancellation are valid. |
| 03: unrestricted working models | FAIL | FAIL | The zero-mean-product inference is invalid; the report's different finite-support counterexample is valid. |
| 04: honest missing argument | UNCERTAIN | FAIL | The report rejects an unmet derivation obligation while explicitly recognizing that the candidate asserts no false equation. |
| 05: correct proof plus false extra claim | FAIL | FAIL | The report correctly derives the comparison-group conditional weight mean and rejects the active extra assertion without rejecting the valid main argument. |

These are five purposive, source-assisted controls, not an accuracy estimate over
independent mathematical tasks. Native session/observation hashes were checked:
all five sessions handed off; their 30/8/13/9/16 turns total 76. Each session's
read observations deliver the entire question, requirements, reference and exact
candidate file(s) from offset zero to EOF. The key was not an input. This verifies
delivery and identity, not mathematical correctness.

## Evaluation Semantics

Case 04 is not evidence that the model mistook an unknown theorem for a false one.
Its report expressly separates the absent proof from false assertion. The native
rubric asks whether a candidate *establishes* the identification result; under
that completion reading, its FAIL has a defensible meaning. The prewritten key
instead expects epistemic uncertainty for honest incompleteness. The frozen
whole-candidate mapping therefore mixes completion and claim truth. It failed
its declared exact-label requirement and is not retrospectively reinterpreted as
a passing qualification.

Future study requirements should state which question each criterion asks:
delivery/completeness or scientific support/falsity/uncertainty. The existing
per-requirement reviewer can express these separately. Do not add a runtime
keyword rule forcing UNCERTAIN for missing proofs, weaken an acceptance gate,
or rerun these consumed reports to obtain a preferred label.

## Auxiliary Mathematical Errors

The main decisions above do not make the reports error-free. Four concrete
problems occur in the referee's added reasoning, not in the corresponding valid
candidate arguments. The following exact checks diagnose those reports only;
they do not edit agent output, become product rules or establish a new theorem.

**Case 01, report lines 140--143: an infeasible boundary check.** The report
claims compatibility when `eta = 1-epsilon`. But the frozen assumptions imply

\[
\epsilon<\nu\leq1-\epsilon\ \Longrightarrow\ \epsilon<1/2,
\qquad
\eta\leq\pi(X)\leq1-\eta\ \Longrightarrow\ \eta\leq1/2.
\]

The proposed equality would instead give `eta=1-epsilon>1/2`. The alleged
boundary case is inadmissible. This does not refute the candidate's actual proof.

**Case 02, report line 87: a wrong lower bound.** The printed lower bound uses
`nu` where the control probability is needed. Directly from the definitions,

\[
\begin{aligned}
\kappa
&=E\left[\frac{\pi(X)}{1-\pi(X)}(1-D)\right]\\
&\geq E\left[\frac{\eta}{1-\eta}(1-D)\right]
&&\text{(the odds function is increasing)}\\
&=\frac{\eta}{1-\eta}E[1-D]\\
&=\frac{\eta}{1-\eta}(1-\nu).
\end{aligned}
\]

For constant `pi=eta`, constant `p=nu>1/2`, zero potential outcomes and `q=0`,
choose positive epsilon below `min(nu,1-nu)` and `0<eta<1/2`. All maintained
conditions hold, but kappa is strictly smaller than the report's claimed
`eta*nu/(1-eta)`. The valid bound still gives positivity; the main bias identity
and its two cancellation arguments are unaffected.

**Case 04, report line 137: a conditional-mean substitution needs an affine
restriction.** The general printed expression replaces `f(X,Delta Y)` by
`f(X,m_1(X))` inside an expectation. That is not true for unrestricted f.
Take constant X, independent binary D of probability 1/2 and symmetric
Rademacher U; put `Y_0(0)=0`, `Y_1(0)=Y_1(1)=U`, `pi=1/2` and `q=0`.
Take epsilon and eta equal to 1/4. Then `Delta Y=U`, `m_1=0`, and for
`f(X,z)=z^2`,

\[
\begin{aligned}
E[w_1(\Delta Y)^2]
&=E[2D U^2]\\
&=E[2D]\\
&=2E[D]\\
&=1,
\end{aligned}
\qquad
E[p(X)m_1(X)^2]/\nu=0.
\]

All task assumptions hold. The identity does hold for the actual affine residual
`Delta Y-q(X)`, so this is overgeneralized referee notation, not a counterexample
to the requested identification result.

**Case 05, report lines 81--82 (also asserted in Case 02): weighted integrability
does not imply marginal integrability of delta.** Let X and V be independent
uniform variables on `(0,1)`, `D=1{V<=X/2}`, `Y_0(0)=Y_1(0)=0`,
`Y_1(1)=1{V<=X/2}/X`, `pi=1/2`, and `q=0`. These potential outcomes and treatment
are jointly defined from pretreatment latent variables. Here `p(X)=X/2`,
`nu=1/4`, and epsilon `1/8` and eta `1/4` satisfy the task's bounds. Parallel
trends and no anticipation hold. Nevertheless,

\[
\begin{aligned}
E|Y_1(1)|
&=E[D/X]\\
&=E[E[D/X\mid X]]\\
&=E[p(X)/X]\\
&=E[(X/2)/X]\\
&=E[1/2]\\
&=1/2.
\end{aligned}
\]

On the treated support,

\[
\begin{aligned}
\delta(X)
&=E[Y_1(1)-Y_1(0)\mid D=1,X]\\
&=E[Y_1(1)\mid D=1,X]\\
&=E[1/X\mid D=1,X]\\
&=1/X.
\end{aligned}
\]

Consequently,

\[
\begin{aligned}
E[p(X)|\delta(X)|]
&=E[p(X)/X]\\
&=E[(X/2)/X]\\
&=E[1/2]\\
&=1/2,
\end{aligned}
\qquad
\begin{aligned}
E|\delta(X)|
&=E[1/X]\\
&=\int_0^1x^{-1}\,dx\\
&=\infty.
\end{aligned}
\]

The population proof uses the weighted quantity, not the unnecessary marginal
integrability claim. The report's decisive rejection of the false supplementary
normalization identity remains valid.

## Consequence

The fixed deployment served native API/tool requests and completed the entire
planned panel. Scientific qualification is **not established**: its exact-label
condition failed, and the reports contain the auxiliary precision defects above.
Do not infer an isolated model-size effect from the older 4B record, which used
a different runtime/interface. No official H/S study or complete research task
is credited.

The next work is a complete known-method native investigation with qualified
sources and actual scientific artifacts, using internal AI review as fallible
feedback, not final truth. Broader reference-bound assessment remains required
before official comparisons. Do not turn this diagnostic into another repair
agent, a mathematical exception registry, or a sequence of label-tuning retries.
