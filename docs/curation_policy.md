# Curation Policy

A verified Lean proof is not automatically a useful statistics lemma. The Library Curator must enforce the following gates.

## Hard Rejections

- Contains `sorry`, `admit`, unreviewed `axiom`, or unsafe shortcut.
- Weakens the theorem statement to make the proof trivial.
- Encodes the conclusion as an assumption.
- Duplicates a known mathlib theorem without adding domain value.
- Adds broad imports without justification.

## Required Metadata

- statistical meaning;
- motivating task or theorem cluster;
- explicit assumptions;
- downstream reuse expectation;
- proof strategy note;
- imported modules.

## Promotion Levels

- `draft`: compiles but not semantically reviewed.
- `candidate`: semantically reviewed and used by one task.
- `curated`: reused or unlocks a planned theorem cluster.
- `upstream_candidate`: general enough to propose to mathlib or a seed project.

