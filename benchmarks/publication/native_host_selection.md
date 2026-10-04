# Prospective Native-Host Selection Contract

The assigned research question is in `question.json`. Its description and public
estimator transport metadata define the scientific obligations, not an answer.
The registered paper/code/data inputs are in `sources/`, with identities in
`research_sources.json`. Preserve original inputs; put adaptations and working
drafts elsewhere. `native_execution.json` records the proposed local interpreter
and environment. These are prospective conditions, not a qualified official run.

Write substantive mathematics in Markdown/LaTeX. At termination, every ordinary
file in the following final directories is selected, without choosing a better
intermediate draft:

| Directory | Selected scope |
| --- | --- |
| `final/theory/` | Definitions, assumptions, claims and complete derivations |
| `final/code/` | Estimator source and all required local helpers |
| `final/empirical/` | Experiment source, protocols, raw results and uncertainty |
| `final/replication/` | Original-source execution evidence and reconstruction account |
| `final/report/` | Scientific report, limitations and unresolved gaps |

Use `final/code/main.py` for Python or `final/code/main.R` for R as the estimator
entrypoint implementing the supplied `run_estimator` interface. This is the
existing scientific executor's file ABI; choose all helper filenames and structure
within `final/code/`. Keep estimator source/support and mathematical source in
UTF-8. Put binary figures, PDFs and results in the empirical/report directories;
all collected bytes remain available to independent assessment. Identify source,
targets and output conventions in the report. This contract adds no formula or
empirical acceptance threshold. Keep
unselected exploratory drafts outside the final directories. Missing final
material remains missing. Distinguish exploratory evidence from frozen
confirmation, and published results from independently established claims.
