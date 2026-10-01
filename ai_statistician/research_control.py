"""Single-conversation study control using existing prepared research actions."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from typing import Any, Callable, Mapping

from .client_tool_loop import (
    CLIENT_TOOL_SESSION_DIRECTORY,
    ClientToolExecutionResult,
    ClientToolInputError,
    ClientToolLoopResult,
    PreparedClientToolWorkspace,
    prepare_shared_client_tool_workspace,
)
from .fingerprint import stable_hash
from .model_backend import ClientToolDefinition, ClientToolTurnRequest
from .research_schema import OpenResearchQuestion, research_question_payload


RESEARCH_CONTROL_SUBMISSION_TOOL = "submit_research_result"


def prepare_research_control_workspace(
    *,
    question: OpenResearchQuestion,
    request: ClientToolTurnRequest,
    workspaces: Mapping[str, PreparedClientToolWorkspace[Any]],
    checkpoint_inputs: Callable[[str, Mapping[str, Any]], Mapping[str, str]],
    session_dir: Path,
    session_id: str,
    max_turns: int,
    max_tool_calls: int,
    max_no_progress_turns: int,
    workflow_instructions: str = "",
) -> PreparedClientToolWorkspace[ClientToolLoopResult]:
    """Bind a public question, exact input joins and a model-authored MD report.

    Component executors supply actual checkpoint-input identities through the
    caller's extractor; the model cannot supply or change them at submission.
    A consistent selection is not scientific acceptance. External evaluation
    must still check the frozen task and exact artifacts in every study arm.
    """

    public_question = research_question_payload(question, include_task_intent=True)
    question_hash = stable_hash(public_question)
    control_mode = "same_workflow" if workflow_instructions else "free_planning"
    checkpoints: dict[str, dict[str, dict[str, Any]]] = {scope: {} for scope in workspaces}

    def observe(scope: str, result: ClientToolExecutionResult) -> Mapping[str, Any]:
        payload = result.terminal_payload
        inputs = dict(checkpoint_inputs(scope, deepcopy(dict(payload))))
        for input_scope, input_hash in inputs.items():
            if input_scope == scope or input_scope not in checkpoints or input_hash not in checkpoints[input_scope]:
                raise ValueError("component execution input is not a prior cross-workspace checkpoint")
        payload_hash = stable_hash(payload)
        reference = {"scope": scope, "payload_hash": payload_hash, "inputs": deepcopy(inputs)}
        prior = checkpoints[scope].get(payload_hash)
        if prior is not None and prior != reference:
            raise ValueError("identical checkpoint payload has conflicting execution inputs")
        checkpoints[scope][payload_hash] = reference
        return deepcopy(reference)

    submit = ClientToolDefinition(
        name=RESEARCH_CONTROL_SUBMISSION_TOOL,
        description=(
            "Submit a model-authored Markdown research report and explicitly select exact "
            "shared_checkpoint_ref payload hashes by scope. Selected inputs must match their "
            "recorded execution versions. You may select an earlier consistent set. This ends "
            "the conversation without independent-review or scientific-acceptance credit."
        ),
        input_schema={
            "type": "object", "additionalProperties": False,
            "properties": {
                "report_markdown": {"type": "string", "minLength": 1},
                "selected_checkpoints": {
                    "type": "object", "additionalProperties": False,
                    "properties": {scope: {"type": "string", "minLength": 1} for scope in workspaces},
                },
            },
            "required": ["report_markdown", "selected_checkpoints"],
        }, terminal=True,
    )

    def finish(call, context):
        if set(call.input) != {"report_markdown", "selected_checkpoints"}:
            raise ClientToolInputError("submission requires a report and exact checkpoint selection")
        report = call.input["report_markdown"]
        selection = call.input["selected_checkpoints"]
        if not isinstance(report, str) or not report.strip() or not isinstance(selection, Mapping):
            raise ClientToolInputError("submission report or selection is malformed")
        selected = {}
        for scope, payload_hash in selection.items():
            if scope not in checkpoints or not isinstance(payload_hash, str) or payload_hash not in checkpoints[scope]:
                raise ClientToolInputError("selection is not an observed component checkpoint")
            selected[scope] = deepcopy(checkpoints[scope][payload_hash])
        for reference in selected.values():
            for input_scope, input_hash in reference["inputs"].items():
                if selection.get(input_scope) != input_hash:
                    raise ClientToolInputError(
                        "selected checkpoint inputs do not match: " + reference["scope"] + " <- " + input_scope
                    )
        encoded = report.encode("utf-8")
        report_hash = hashlib.sha256(encoded).hexdigest()
        root = session_dir.resolve()
        path = (root / CLIENT_TOOL_SESSION_DIRECTORY / "reports" / (report_hash + ".md")).resolve()
        if not path.is_relative_to(root):
            raise ValueError("research report escapes its authorized session")
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            if path.read_bytes() != encoded:
                raise ValueError("research report contains different bytes")
        else:
            with path.open("xb") as stream:
                stream.write(encoded)
        result = {
            "question_id": public_question["id"], "question_hash": question_hash,
            "task_intent": deepcopy(public_question.get("task_intent", {})), "control_mode": control_mode,
            "report_ref": {"path": str(path), "sha256": report_hash,
                           "byte_size": len(encoded), "media_type": "text/markdown"},
            "selected_checkpoints": selected,
            "independent_role_review": False,
            "evidence_role": "submission_not_scientific_acceptance",
        }
        return ClientToolExecutionResult(content=result, terminal=True, terminal_payload=result)

    shared_request = replace(
        request,
        messages=(*request.messages, {"role": "user", "content": json.dumps({
            "research_question": public_question,
            **({"workflow_instructions": workflow_instructions} if workflow_instructions else {}),
        }, sort_keys=True, ensure_ascii=False)}),
        metadata={**dict(request.metadata), "control_mode": control_mode,
                  "question_hash": question_hash, "workflow_instructions_hash": stable_hash(workflow_instructions)},
    )
    return prepare_shared_client_tool_workspace(
        request=shared_request, workspaces=workspaces, terminal_tools=(submit,),
        execute_terminal_tool=finish, observe_checkpoint=observe,
        max_turns=max_turns, max_tool_calls=max_tool_calls, max_no_progress_turns=max_no_progress_turns,
        session_dir=session_dir, session_id=session_id,
    )
