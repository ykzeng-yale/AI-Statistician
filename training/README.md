# Training Artifacts

Training is intentionally downstream of the Lean library and benchmark.

Planned stages:

1. SFT on accepted proof traces.
2. DPO on Lean-labeled preference pairs.
3. GRPO with process rewards from Lean verification.
4. Expert iteration over accepted proofs and curated lemmas.

Large model checkpoints and rollout logs should not be committed to git.

