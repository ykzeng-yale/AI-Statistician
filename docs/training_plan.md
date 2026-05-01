# Training Plan

The training plan is ordered to avoid wasting compute before the library and benchmark exist.

## Stage 1: SFT

Data:

- mathlib probability and analysis proof traces;
- Lean statistical learning theory seed projects;
- local `StatInference` proofs;
- benchmark subgoal completions.

Target formats:

- theorem statement plus retrieved premises to proof block;
- proof state plus retrieved premises to next tactic;
- failed proof plus diagnostics to repair patch.

## Stage 2: DPO

Preference pairs are generated automatically from Lean feedback.

Chosen examples:

- proof accepted;
- tactic locally valid;
- closes a goal;
- uses relevant local lemma;
- shorter proof with same theorem statement.

Rejected examples:

- syntax error;
- unknown identifier;
- timeout;
- no progress loop;
- introduces `sorry`, `admit`, `axiom`, or unsafe code;
- changes theorem statement meaning.

## Stage 3: Process-Reward GRPO

Reward components:

- proof completion;
- locally valid tactic count;
- closed goals;
- first-error position;
- retrieved premise use;
- local lemma reuse;
- no forbidden tokens;
- timeout and loop penalties.

Use TRL for small reward-debugging runs. Use `verl` plus Kimina Lean Server for serious distributed experiments.

## Stage 4: Expert Iteration

Accepted proofs are added to the training set after curation. Failed attempts are clustered into repair tasks and DPO negatives.

The system should retrain only after benchmark splits are frozen, otherwise evaluation will overstate progress.

