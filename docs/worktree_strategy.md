# Worktree Strategy

The repository uses git worktrees to isolate code-writing agents.

## Branch Naming

```text
agent/<agent-key>
```

Examples:

```text
agent/formalization
agent/tactic-synthesizer
agent/benchmark-generator
```

## Directory Layout

```text
.worktrees/
  formalization/
  tactic-synthesizer/
  benchmark-generator/
```

The root checkout is the integration checkout. Agents should not directly mutate it unless acting as the integrator.

## Ownership Rules

- Each agent receives explicit path ownership.
- Agents must not edit paths owned by another active agent.
- The Worktree Steward creates worktrees and records assignments.
- The Library Curator reviews reusable lemma patches before integration.
- The Verifier must run before any Lean proof patch is merged.

## Local Preview

```bash
statlean assign-worktree --agent formalization --base main --dry-run
```

To create a real worktree:

```bash
statlean assign-worktree --agent formalization --base main
```

## Merge Gate

Before merging an agent worktree:

1. `git diff --check`
2. `pytest`
3. `lake build` when Lean dependencies are available
4. curation check for any new lemma
5. semantic review for any new statistical definition

