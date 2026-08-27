# Statsmodels ADF/KPSS source replication L1 v1 operator audit

Date: 2026-08-26

## Immutable identity

- Task: `statsmodels_adf_kpss_sunspots_public_replication`
- Family: `time_series_stationarity_source_replication`
- Activation commits: `b0ce95568be18cde682d8e57b1de6141c8e35acd` and
  `85c5db1bbe65b9be10d0a7029f5ef75c0d5b70a7`
- Public source commit: `40e6a84d26ac74623c6b94b718f0987ef0351c53`
- Source snapshot hash:
  `83a0acc9580245724b081e5aca45bedde3feb3ffd95966b5049a05b71bb6ee0c`
- Run:
  `runs/main_worker_research_l1_statsmodels_adf_kpss_replication_20260826_v1_codex_harness_document_critic_exact_haiku`
- Runtime model: exact `claude-haiku-4-5-20251001` for all seven enabled
  roles; no Sonnet, Opus, or automatic escalation
- Runtime result: `ACCEPTED` after three outer traces
- Frozen automated full-task result: `1/1`
- Trustworthy capability result: `0/1`
- Operator disposition:
  `OPERATOR_INVALIDATED_SOURCE_REPORT_AND_REVIEWER_FALSE_ACCEPTANCE`
- Future-task shared mechanism commit:
  `e5cccbb276bb1ef66bb5f387b1bc992b4dfaa74c`

The task received exactly one product draw and one post-runtime hidden
evaluation. Both are closed and immutable. It must not be resumed, rerun,
repaired, hidden-evaluated again, rescored, or resampled.

Immutable SHA-256 values:

- Runtime manifest:
  `d440821558dfbd67a8d53c5058f2a4842a3d4bf704326abe122d954e25558f73`
- Runtime result:
  `f598ebb1f274956bf24ac8587a5dfeb6b7be6c4c156e2617b5ea007e5529506c`
- Runtime model topology:
  `67da4d6e1c361c1505514fce54ac204903d3b7f889bff2a50bfc9451c38e327e`
- Runtime progress:
  `e0684fab1e7ea9a42db25c50f5f8469c8e88b8bd31da21895072380db2052982`
- Runtime traces:
  `e8eefe7ff21d9dfc084dec3e493e2227a862a0e2c8f2a780b8d01f46fc331342`
- Runtime handoffs:
  `0ea11caeb3033b867a0f11f67385fc461c67ba47ceec1455391f606d34d6a917`
- Runtime observations:
  `65288b9938bb11c66b7361e97ea2e0b287b2c8b8929dba7797afda0bee8898f3`
- Hidden gold evaluation:
  `40b7f86ee13b38c3793ef5b2ae87283fe74068a4927a070bb6d13795b9167e65`
- Model-authored report:
  `55d35229318ce5fa47e2c5ed80f012b76fe34be59d7e2a74a0c766d21acd8c1a`
- Runtime Critic proposal:
  `839613bccb8bc9d9c4cdffc01d5f78bbb2e27542b4399c1c9274333a62b36ff8`
- Hidden semantic result:
  `4fae01a89bb0c126d91a2fbf3b23cb97398e795ebd4f3daa6616c30bf4c574c3`

## Runtime result

One Architect call selected the source-replication workspace. The persistent
source owner then used 22 exact-Haiku model turns and 28 model-selected tools:
14 source searches, 10 exact source reads, one workspace read, one unchanged
source execution, one Markdown report write, and one checkpoint commit. All 28
tools executed. The document-session Critic used another 15 model turns and 15
tools, inspected all 12 externalized evidence documents through 14 document
accesses, and submitted one terminal judgment. The complete product draw used 38
model calls, three outer traces, two handoffs, and no outer-runtime tool call.

The source owner committed one 436-line, 22,262-byte Markdown report and the
following durable identities:

- source manifest: `source_replication:4dd743dbf4f8f2948282`, manifest hash
  `816cceb37deacf8b878c3bb08b4df7cfc5d04573ea5b5dc532b49a5e1ac7f5c8`;
- workspace evidence: `source_replication_workspace:817aaf1476ffb526f462`,
  content hash
  `957aa84b0b6289d6301dc97a74192768f703316888da9e48296e7a2a2596dd25`;
- checkpoint: `source_replication_checkpoint:306394b6b7889958d8f0`;
- immutable report path:
  `theory_workspaces/theory_workspace-88f80029b9292de42841/.immutable_checkpoints/ed1c2f988fb31768827d5ab8ae39c4f05377943b6c84a39808d5fd82957887bc/source_replication_report.md`.

Formalization was correctly not applicable. No generated estimator, simulation,
Formalizer proposal, Lean proof, or kernel evidence was produced.

## Frozen evaluation

The mechanical hidden source harness passed `11/11`. It verified the frozen
source and environment, no-argument execution, return status, exact stdout and
stderr, warning, artifacts, and report lineage. This remains valid scoped
source-execution evidence.

The independently calibrated exact-Haiku semantic judge repeated its `9/9`
calibration result and marked all ten report claims `SATISFIED`, so the frozen
automated artifact says `1/1`. That record remains immutable. Its semantic pass
is a false acceptance and receives no trustworthy capability credit.

## Operator findings

The authoritative report contains material statistical, source-identity, and
internal-consistency errors:

1. Lines 208-215 assign the sole `InterpolationWarning` to the original-series
   KPSS result. Lines 390-392 repeat that attribution and say the actual p value
   may be smaller. The immutable stderr says the actual p value is *greater*
   than the returned value. The warning belongs to the differenced KPSS call,
   whose displayed p value is the lookup-table cap `0.1`; the report itself
   records the correct direction at line 260.
2. Lines 295 and 310 turn the original ADF failure to reject into the conclusion
   that the series is nonstationary. Lines 328 and 336 likewise turn rejection
   of an ADF unit-root null and nonrejection of a KPSS level-stationarity null
   into unqualified stationarity conclusions. Those test decisions are
   evidence in their specified models, not acceptance or proof of the null or
   alternative.
3. Line 245 calls the differenced series "strongly stationary." Lines 341 and
   369 similarly overstate the joint tests. ADF and KPSS do not establish strict
   stationarity, and absence of a unit root alone is not a general stationarity
   proof.
4. Line 316 correctly identifies the original 5 percent decisions as the
   source's Case 1, not Case 3. Lines 319 and 425 then call the source's
   trend-stationarity inference reasonable and say differencing is consistent
   with trend stationarity. Exact KPSS used `regression="c"`, not the `"ct"`
   trend-stationarity null, and first differencing is not deterministic
   detrending. The observed calls do not support the source's Case 3 claim.
5. Line 427 defines strict stationarity as "all moments constant." Strict
   stationarity is invariance of all finite-dimensional distributions under
   time shifts. The same paragraph minimizes the source's unsupported leap as
   standard terminology instead of rejecting it.
6. The report does not identify Seabold and Perktold, the 2010 software article
   DOI, or the frozen source snapshot ID and hash, despite the visible source-
   identity requirement. Repository release and commit alone do not satisfy
   that requirement.
7. Line 5 says outputs were compared with the published source, while line 419
   says published notebook outputs were not compared. The final claim of a
   faithful published-source replication does not resolve that contradiction.
8. Line 239 describes 300 ADF observations as 308 observations minus eight
   lags, although the selected lag count is seven. The additional observation
   loss comes from the lagged-difference construction, so the wording is
   misleading.
9. Line 402 says `.plot()` constructs Figure objects. Pandas returns axes while
   creating figure/axes state. The important no-save/no-show/no-result-artifact
   boundary is otherwise correctly disclosed.
10. Line 435 calls the source prose largely consistent with only minor
    imprecisions. The wrong KPSS null description, wrong four-case assignment,
    differencing/detrending conflation, strict-stationarity leap, and forecast-
    readiness claim are material scientific errors.

Correct caveats elsewhere do not cancel these active contradictory assertions.

## Reviewer failure and shared correction

This task was the first disjoint test of the Codex-inspired Critic document
session introduced after Task 54. The mechanism itself worked: long evidence was
hash-bound outside the opening prompt, the same reviewer selected reads and
searches, exact observations returned to its transcript, and it inspected every
externalized document before terminal submission. Context transport and tool
access were therefore not the measured blocker.

The exact-Haiku Critic nevertheless repeated the report's false warning
attribution, trend-stationarity defense, and incorrect strict-stationarity
definition, then returned `SUPPORTED`. The one-shot hidden semantic judge also
false-accepted all ten explicit rubric claims. Adding another document tool,
synonymous contradiction instruction, task phrase detector, deterministic
stationarity parser, report repair path, or reviewer vote is not justified by
this evidence.

Commit `e5cccbb2` instead corrects the production model allocation. The terminal
scientific Critic now defaults to the same Sonnet tier as TheoryDeveloper,
AlgorithmEngineer, SimulationEngineer, and the scientific semantic reviewers.
Frozen `research_eval` and `capability_eval` modes still pin every enabled role,
including Critic, to exact `claude-haiku-4-5-20251001`; Opus remains prohibited.
No prompt, tool, schema, model call, agent, scheduler, retry, source rule, content
parser, or repair path was added. Focused model, CLI, client-tool, and Critic
tests passed `133/133` before the commit was pushed to both canonical refs. The
final focused panel passed `186/186`, and the complete repository passed
`945/945` in 82.62 seconds. Compile-all, JSON, diff hygiene, model-policy,
secret, and architecture-budget checks passed. Top-level production Python is
149,868 lines and `research_agent_runtime.py` remains 24,986 lines.

The official `openai/codex` checkout was also incrementally audited from
`daa3eaf` through `f374188`. Its relevant new change permits standalone
function-call outputs to enter turn routing while preserving them as passive
conversation items. AI Statistician already returns client-tool observations to
the same source-owning session. The remaining upstream changes concern
permissions, MCP provenance, browser cleanup, retained-image budgeting,
Guardian, proxy hardening, and platform telemetry; none warrants embedding
Codex core, App Server, Responses transport, or a second research scheduler.

## Capability accounting

This is the fifty-fifth consumed scored task. The immutable automated result is
recorded as `1/1`, but required report semantics and source identity are false,
so the trustworthy full-task score is `0/1`. Four of 55 tasks retain full-task
capability credit. Task 55 retains mechanical `11/11` source-execution evidence
but receives neither a source-replication component pass nor a full-task pass.

No post-run shared change can alter this disposition. Task 55 is permanently
closed from rerun, resume, report repair, hidden reevaluation, rescore, or
resampling.
