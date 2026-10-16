"""Model-owned source iteration using the pinned upstream program operations."""

from __future__ import annotations

import json
import os
from pathlib import Path

from .agentic_api_workspace import FileAuthorWorkspace, FileGrant, author_tools
from .client_tool_loop import ClientToolExecutionResult, ClientToolInputError
from .model_backend import ClientToolDefinition


class ProgramWorkspace(FileAuthorWorkspace):
    instructions = (
        "You own the complete research candidate in this retained session. Develop its "
        "Markdown/LaTeX argument and scientific source with the file tools. evaluate_program "
        "runs the fixed official evaluator and independent review through the host; it is not "
        "an arbitrary execution tool or a proof certificate. The host already cloned program_1 "
        "and owns evaluation receipts, rubric statuses and campaign memory. Read its actual observations. "
        "After a failed evaluation, clone_program uses the upstream copy rules to create the "
        "next source version; you choose every revision. Evaluated files are immutable. "
        "Stop after acceptance, at the declared budget, or with an honest gap. Finish with "
        "candidate only after evaluating the current source. Numerical agreement and AI "
        "review do not establish a theorem or final external assessment."
    )

    def __init__(self, grants: tuple[FileGrant, ...], *, experiment: Path, max_evaluations: int,
                 timeout_seconds: int, attempt_id: str, idea_id: str,
                 memory_md: Path, memory_jsonl: Path, python_executable: str):
        from src.investigation.harness_incumbent import native_public_outputs

        if type(max_evaluations) is not int or max_evaluations < 1:
            raise ValueError("Declare a positive evaluation budget")
        if type(timeout_seconds) is not int or timeout_seconds < 1:
            raise ValueError("Declare a positive official evaluation timeout")
        self.experiment = experiment.resolve()
        self.max_evaluations, self.timeout_seconds = max_evaluations, timeout_seconds
        self.attempt_id, self.idea_id = attempt_id, idea_id
        self.memory_md, self.memory_jsonl = memory_md, memory_jsonl
        self.python_executable = python_executable
        self.current = 1
        self.consumed: set[int] = set()
        if any(self.experiment.glob("program_[1-9]*/evaluation_manifest.json")):
            raise FileExistsError("This source session already consumed an evaluation; do not restart it.")
        self.requirements = json.loads((self.experiment / "active_rubrics.json").read_text())
        public = [row["path"] for row in native_public_outputs(self.experiment)]
        observations = {
            "metrics.json", "correct.json", "rubric_status.json", "evaluation_manifest.json",
            "harness_evaluate_stdout.log", "harness_evaluate_stderr.log",
            "scientific_review.md", "scientific_review.json", *public,
            "scientific_review_stdout.log", "scientific_review_stderr.log",
        }
        grants = tuple(grant for grant in grants if not grant.name.startswith("program_1/"))
        for index in range(1, max_evaluations + 1):
            prefix, root = f"program_{index}", self.experiment / f"program_{index}"
            grants += (FileGrant(prefix + "/src", root / "src", directory=True, writable=True),
                       FileGrant(prefix + "/program_spec.toml", root / "program_spec.toml", writable=True))
            grants += tuple(FileGrant(prefix + "/" + name, root / name) for name in sorted(observations))
        super().__init__(grants)

    def tools(self) -> tuple[ClientToolDefinition, ...]:
        def operation(name, description):
            return ClientToolDefinition(name=name, description=description,
                input_schema={"type": "object", "properties": {}, "additionalProperties": False})
        return author_tools() + (
            operation("evaluate_program", "Run the fixed complete official evaluation once on the current source; preserve and return its real observations."),
            operation("clone_program", "Clone the failed, completed current candidate into the next source version with upstream program_clone. Never edit the consumed version."),
        )

    def _path(self, name: str, *, write=False) -> Path:
        path = super()._path(name, write=write)
        if write and name.startswith("program_"):
            if name.split("/", 1)[0] != f"program_{self.current}" or self.current in self.consumed:
                raise ClientToolInputError("Edit only the current unevaluated candidate; clone a completed failed version before revising.")
        return path

    def files(self, prefix=""):
        rows = super().files(prefix)
        for row in rows:
            if row["path"].startswith("program_"):
                row["writable"] = (row["writable"]
                    and row["path"].split("/", 1)[0] == f"program_{self.current}"
                    and self.current not in self.consumed)
        return rows

    def _evaluation(self, index: int):
        from src.investigation.harness_incumbent import read_native_evaluation
        return read_native_evaluation(self.experiment / f"program_{index}", self.requirements,
            attempt_id=self.attempt_id, idea_id=self.idea_id, require_mirror=index == self.current)

    def _execute(self, name: str, args: dict) -> ClientToolExecutionResult:
        if name not in {"evaluate_program", "clone_program"}:
            if name == "finish" and args["disposition"] == "candidate":
                if self.current not in self.consumed:
                    raise ClientToolInputError("Evaluate the current source before candidate handoff, or report a gap.")
                for index in sorted(self.consumed):
                    self._evaluation(index)
            return super()._execute(name, args)
        if name == "clone_program":
            from src.investigation.program_clone import main as clone_program
            if self.current not in self.consumed or self.current >= self.max_evaluations:
                raise ClientToolInputError("A completed failed evaluation and remaining declared budget are required for a new candidate.")
            for index in sorted(self.consumed):
                self._evaluation(index)
            source = self.experiment / f"program_{self.current}"
            destination = self.experiment / f"program_{self.current + 1}"
            try:
                clone_program(["--from", str(source), "--to", str(destination)])
            except ValueError as exc:
                raise ClientToolInputError(str(exc)) from exc
            self.current += 1
            return ClientToolExecutionResult(content={"current_program": destination.name,
                "source": source.name, "source_owner": "model"}, state_changed=True)
        from src.investigation.harness_eval import run_harness_evaluation
        if self.current in self.consumed:
            raise ClientToolInputError("This candidate's evaluation was consumed; inspect it, clone a new version or finish.")
        root = self.experiment / f"program_{self.current}"
        self.consumed.add(self.current)
        try:
            code = run_harness_evaluation(experiment_dir=self.experiment, attempt_id=self.attempt_id,
                idea_id=self.idea_id, rubrics_path=self.experiment / "active_rubrics.json",
                python_bin=self.python_executable, global_memory_md=self.memory_md,
                global_memory_jsonl=self.memory_jsonl, timeout_seconds=self.timeout_seconds,
                environment=dict(os.environ), program_index=self.current)
        except SystemExit as exc:
            if not (root / "evaluation_manifest.json").exists():
                self.consumed.remove(self.current)
            raise ClientToolInputError(str(exc)) from exc
        evaluation = self._evaluation(self.current)
        return ClientToolExecutionResult(content={"program_id": root.name, "exit_code": code,
            "rubric_status": evaluation.status, "scientific_acceptance": False,
            "observation_paths": [grant.name for grant in self.grants
                if grant.name.startswith(root.name + "/") and not grant.writable and grant.path.is_file()]},
            state_changed=True)
