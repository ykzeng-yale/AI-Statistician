# Source Replication Task

Use the supplied licensed R source to reproduce its retrospective design analysis
for every row of `scenarios.csv` under the prepared local R environment. This is
source replication, not blind rediscovery or a request for a novel method.

Keep `source/Design_analysis_r.R` unchanged. Write an executable `reproduce.R`
that reads the scenario file and calls the published `retro_r` with every supplied
argument, including the seed and simulation count. Execute it locally. Write
`results.csv` with exactly these columns:

`scenario_id,power,typeM,typeS,crit_lower,crit_upper`

Use full numeric precision, one row per scenario and both returned critical
values. The evaluator will run the unchanged reference functions independently
in the same frozen environment. Report failures rather than manufacture values.

Write `research.md` with reviewable mathematical definitions and derivations for
what the simulation estimates, its assumptions, source provenance, execution
commands, uncertainty and limitations. Explain the distinction between source
replication and scientific verification. Do not claim independent mathematical
review or Lean proof if neither occurred. Lean is not requested.

Permitted research material is this task, `scenarios.csv`, `source/`, and any
installed statistical-research skill. Old paper outputs, caches, hidden evaluation
files and other agent sessions are not permitted context. The prepared `Rscript`
on PATH supplies MASS and docstring. There is no need to reconstruct the full
paper's PDF or install packages. Work only inside this fresh project. The six
scenarios belong to one paper, not six independent research successes.
