"""Source-bound AI review at the existing upstream evaluation boundary."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .agentic_api_workspace import FileAuthorWorkspace, FileGrant, _atomic_bytes, author_tools, run_file_session
from .client_tool_loop import ClientToolExecutionResult, ClientToolInputError
from .model_backend import ClientToolDefinition


class ScientificReviewWorkspace(FileAuthorWorkspace):
    instructions = (
        "You independently review the supplied candidate files and frozen requirements. "
        "Only your Markdown review is writable. Do not author a replacement argument or code. "
        "Read the relevant source, write review.md, then submit_review with a disposition for each "
        "requirement. PASS means your AI assessment supports that requirement, not proof, empirical "
        "confirmation, human endorsement or error-free correctness. Preserve uncertainty."
    )

    def __init__(self, grants: tuple[FileGrant, ...], requirement_ids: tuple[str, ...]):
        if (not requirement_ids or not all(isinstance(item, str) and item.strip() for item in requirement_ids)
            or len(set(requirement_ids)) != len(requirement_ids)):
            raise ValueError("Review requirements must have distinct nonempty IDs.")
        self.requirement_ids = requirement_ids
        super().__init__(grants)
        self.initial_inputs = [row for row in self.files() if not row["writable"]]

    def tools(self) -> tuple[ClientToolDefinition, ...]:
        submission = ClientToolDefinition(
            name="submit_review", description="Submit the exact Markdown report and per-requirement AI judgments; not proof.",
            terminal=True, input_schema={"type": "object", "additionalProperties": False,
                "properties": {"verdicts": {"type": "array", "items": {
                    "type": "object", "additionalProperties": False,
                    "properties": {"id": {"enum": list(self.requirement_ids)},
                                   "status": {"enum": ["PASS", "FAIL", "UNCERTAIN"]}},
                    "required": ["id", "status"]}}}, "required": ["verdicts"]},
        )
        return tuple(tool for tool in author_tools() if tool.name != "finish") + (submission,)

    def _execute(self, name: str, args: dict) -> ClientToolExecutionResult:
        if name != "submit_review":
            return super()._execute(name, args)
        ids = [row["id"] for row in args["verdicts"]]
        if len(ids) != len(self.requirement_ids) or set(ids) != set(self.requirement_ids):
            raise ClientToolInputError("Submit each frozen review requirement exactly once.")
        if [row for row in self.files() if not row["writable"]] != self.initial_inputs:
            raise ClientToolInputError("Reviewed inputs changed; this review cannot assess their new identity.")
        report = self._path("review.md").read_bytes()
        if not report.decode("utf-8").strip():
            raise ClientToolInputError("Write the substantive Markdown review before submitting its dispositions.")
        payload = {"verdicts": args["verdicts"], "report_sha256": hashlib.sha256(report).hexdigest(),
                   "scope": "AI source review, not proof or independent empirical confirmation."}
        return ClientToolExecutionResult(content=payload, terminal=True, terminal_payload=payload)


def run_scientific_review(*, backend, program: Path, task: Path, rubrics_file: Path,
                          sources: Path, config: dict, deployment_identity: dict, prompt: str) -> dict:
    program, task = program.resolve(), task.resolve()
    if (program.parent != task or not program.name.startswith("program_")
        or not program.name[8:].isdigit() or int(program.name[8:]) < 1
        or program.name != f"program_{int(program.name[8:])}"):
        raise ValueError("Review must address an upstream candidate in its experiment.")
    if any((program / name).exists() or (program / name).is_symlink() for name in
           ("scientific_review.json", "scientific_review.md", ".scientific-review")):
        raise FileExistsError("Scientific review already exists; do not reassess a consumed candidate.")
    rubrics = json.loads(rubrics_file.read_text())
    review_ids = tuple(row["id"] for row in rubrics if row.get("type") == "review")
    source_records = json.loads((program / "evaluation_manifest.json").read_text())["source_records"]
    if not isinstance(source_records, dict) or not source_records:
        raise ValueError("Native evaluation source identity is required.")
    grants = (
        *(FileGrant("candidate/" + name, program / name) for name in sorted(source_records)),
        FileGrant("task.md", task / "task.md"), FileGrant("requirements.json", rubrics_file),
        FileGrant("sources", sources / "resources/search", directory=True),
        FileGrant("review.md", program / "scientific_review.md", writable=True),
    )
    workspace = ScientificReviewWorkspace(grants, review_ids)
    for name, expected in source_records.items():
        if hashlib.sha256(workspace._path("candidate/" + name).read_bytes()).hexdigest() != expected:
            raise ValueError("Candidate differs from the evaluated source identity.")
    result = run_file_session(
        backend=backend, workspace=workspace, prompt=prompt, model=config["model"],
        max_tokens=config["max_tokens"], temperature=config["temperature"], max_turns=config["max_turns"],
        session_dir=program / ".scientific-review/session", session_id="scientific-review",
        deployment_identity={**deployment_identity, "stage": "review"},
    )
    receipt = {"schema_version": 1, "kind": "ai_scientific_review", "model": result.model,
        "task_sha256": hashlib.sha256((task / "task.md").read_bytes()).hexdigest(),
        "rubrics_sha256": hashlib.sha256(json.dumps(rubrics, sort_keys=True, allow_nan=False).encode()).hexdigest(),
        "source_records": source_records, "verdicts": result.terminal_payload["verdicts"],
        "report": {"path": "scientific_review.md", "sha256": result.terminal_payload["report_sha256"]},
        "session": {"path": ".scientific-review/session/result.json", "sha256": hashlib.sha256(
            (program / ".scientific-review/session/result.json").read_bytes()).hexdigest()},
        "scope": result.terminal_payload["scope"]}
    _atomic_bytes(program / "scientific_review.json", (json.dumps(receipt, indent=2) + "\n").encode())
    return receipt
