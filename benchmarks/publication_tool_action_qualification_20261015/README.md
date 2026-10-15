# Server-Schema Action Observation

Prospective condition, 2026-10-15. The completed StepMix development draw
showed a prose-only terminal response after a structurally valid handoff. This
engineering observation checks an explicit action format supported by the local
server's existing JSON Schema endpoint. It supplies no statistical answers.

The experimental adapter requests an `actions` array of tool names and arguments.
The server's schema constrains its syntax. The same retained loop dispatches the
model's selected calls and returns unmodified tool observations. The inherited
`finish` fixture returns its first 16 error strings and total error count; the
operator's final file check retains the complete error list. Terminal success still
requires the model to call `finish` and deliver the exact files. The adapter
authors no file, mathematical content or repair; there is one request per turn
and no fallback. It remains outside the production backend during qualification.
Malformed or truncated responses retain their original text and usage without
dispatching an action. Per-turn action receipts record parsing failures. A separate
post-run receipt checks that port 8081 has no listener after owned-server cleanup.

The [plan](plan.json) fixes one new artificial file task: eight input pages,
32 opaque receipts/statuses and two authored files. It reuses the existing file
fixture, session store, model recorder and server lifecycle from
`publication_deployment_qualification_20261003/observe_retained_session.py`.
Those earlier source files and consumed outputs are unchanged. Actual token
counts and all failed actions remain observable; the declared minimum input
threshold does not stand in for useful research reasoning.

Use only the existing pinned local Qwen deployment. The new input ID gives new
artificial receipts; it does not create a scientific test family or a randomized
comparison. Commit this condition before calls. Run it once:

```sh
.venv/bin/python -m benchmarks.publication_tool_action_qualification_20261015.observe \
  --plan benchmarks/publication_tool_action_qualification_20261015/plan.json
```

The output directory is exclusive. Preserve the terminal result, whether it
succeeds or fails. A passing action fixture is only evidence for this transport
and exact file contract. Product integration, actual workspace behavior and
complete scientific work need separate verification under their full scopes.
