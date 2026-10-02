"""Publication controls and final-artifact readers, not a second research runtime."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import asdict, replace
from pathlib import Path, PurePosixPath
from subprocess import CompletedProcess
from typing import Any, Callable, Mapping

from .client_tool_loop import (
    CLIENT_TOOL_SESSION_DIRECTORY,
    ClientToolExecutionResult,
    ClientToolInputError,
    ClientToolLoopResult,
    PreparedClientToolWorkspace,
    client_tool_session_contract_fingerprint,
    prepare_shared_client_tool_workspace,
    read_client_tool_observation,
    read_hash_bound_utf8_file,
)
from .fingerprint import stable_hash
from .model_backend import ClientToolDefinition, ClientToolTurnRequest
from .research_schema import OpenResearchQuestion, research_question_payload


RESEARCH_CONTROL_SUBMISSION_TOOL = "submit_research_result"
RESEARCH_CONTROL_INPUTS_TOOL = "select_workspace_inputs"


def collect_native_research_submission(
    *, question: OpenResearchQuestion, workspace_root: Path,
    artifact_paths: Mapping[str, list[str] | tuple[str, ...]],
    host_result: CompletedProcess, snapshot_dir: Path,
) -> dict[str, Any]:
    """Snapshot frozen final paths after the caller's native host has terminated.

    The trusted study runner supplies the completed process and predeclared paths.
    This neither runs a host nor infers its model/tools, isolation or scientific success.
    A fresh evaluator-owned directory outside the author workspace prevents overwrites.
    """

    if not isinstance(host_result, CompletedProcess) or type(host_result.returncode) is not int:
        raise ValueError("native submission requires a completed host process")
    root, store = workspace_root.resolve(), snapshot_dir.resolve()
    if not root.is_dir() or store.is_relative_to(root) or root.is_relative_to(store):
        raise ValueError("native submission store must be separate from the author workspace")
    if any(not isinstance(paths, (list, tuple)) or any(not isinstance(path, str) for path in paths)
           or len(paths) != len(set(paths)) for paths in artifact_paths.values()):
        raise ValueError("native submission requires explicit, non-duplicate final path lists")
    requested = {scope: list(paths) for scope, paths in artifact_paths.items()}
    for paths in requested.values():
        for path in paths:
            pure = PurePosixPath(path)
            if (not path or "\\" in path or "\x00" in path or pure.is_absolute()
                or path != pure.as_posix() or any(part in {".", ".."} for part in pure.parts)):
                raise ValueError("native submission paths must be canonical and relative")
    store.mkdir(parents=True, exist_ok=False)
    blobs = store / "files"
    blobs.mkdir()
    refs, missing = {}, {}
    for scope, paths in requested.items():
        refs[scope], missing[scope] = {}, []
        for relative in paths:
            path = (root / relative).resolve()
            if not path.is_relative_to(root):
                raise ValueError("native submission file escapes its workspace")
            if not path.is_file():
                missing[scope].append(relative)
                continue
            raw = path.read_bytes()
            sha = hashlib.sha256(raw).hexdigest()
            target = blobs / sha
            if not target.exists():
                target.write_bytes(raw)
            refs[scope][relative] = {"path": str(target), "sha256": sha, "byte_size": len(raw)}
    public = research_question_payload(question, include_task_intent=True)
    body = {"question_id": question.id, "question_hash": stable_hash(public),
            "task_intent": deepcopy(public.get("task_intent", {})), "requested_artifacts": requested,
            "artifact_refs": refs, "missing_artifacts": missing, "evidence_role": "submission_not_scientific_acceptance",
            "host_process": {"args_hash": stable_hash(host_result.args), "returncode": host_result.returncode,
                             **{field + "_sha256": None if value is None else hashlib.sha256(
                                 value if isinstance(value, bytes) else value.encode("utf-8")).hexdigest()
                                for field, value in (("stdout", host_result.stdout), ("stderr", host_result.stderr))}}}
    raw = json.dumps(body, sort_keys=True, ensure_ascii=False).encode("utf-8")
    record = store / "submission.json"
    record.write_bytes(raw)
    return {"path": str(record), "sha256": hashlib.sha256(raw).hexdigest(), "byte_size": len(raw)}


def load_native_research_submission(
    reference: Mapping[str, Any], *, question: OpenResearchQuestion,
    artifact_paths: Mapping[str, list[str] | tuple[str, ...]], snapshot_dir: Path,
) -> dict[str, Any]:
    """Resolve a trusted native snapshot; absent final artifacts remain absent."""

    store = snapshot_dir.resolve()
    if Path(reference["path"]).resolve() != store / "submission.json":
        raise ValueError("native submission reference escapes its store")
    text, errors = read_hash_bound_utf8_file(reference)
    if errors:
        raise ValueError("native submission identity mismatch: " + ",".join(errors))
    body = json.loads(text)
    public = research_question_payload(question, include_task_intent=True)
    requested = {scope: list(paths) for scope, paths in artifact_paths.items()}
    if (body.get("question_hash") != stable_hash(public) or body.get("question_id") != question.id
        or body.get("task_intent") != public.get("task_intent", {}) or body.get("requested_artifacts") != requested):
        raise ValueError("native submission differs from the frozen question or final paths")
    contents = {}
    for scope, paths in requested.items():
        refs, missing = body["artifact_refs"][scope], body["missing_artifacts"][scope]
        if set(refs) | set(missing) != set(paths) or set(refs) & set(missing):
            raise ValueError("native submission artifact inventory mismatch")
        contents[scope] = {}
        for relative, ref in refs.items():
            path = Path(ref["path"]).resolve()
            if path != store / "files" / ref["sha256"]:
                raise ValueError("native artifact reference escapes its store")
            raw = path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != ref["sha256"] or len(raw) != ref["byte_size"]:
                raise ValueError("native artifact identity mismatch: " + relative)
            contents[scope][relative] = raw
    return {**body, "artifact_bytes": contents}


def load_research_control_submission(
    result: ClientToolLoopResult, *, question: OpenResearchQuestion, session_dir: Path,
) -> dict[str, Any]:
    """Resolve only a final submission's exact observed artifacts, without judging them.

    The caller supplies the trusted terminated loop and frozen public question.
    Partial submissions remain partial; this never executes or resumes an evaluation.
    """

    submission = deepcopy(dict(result.terminal_payload))
    public_question = research_question_payload(question, include_task_intent=True)
    if (submission.get("question_id") != public_question["id"]
        or submission.get("question_hash") != stable_hash(public_question)
        or submission.get("task_intent") != public_question.get("task_intent", {})
        or not isinstance(submission.get("selected_checkpoints"), Mapping)):
        raise ValueError("research submission differs from the frozen question")
    observations = [json.loads(read_client_tool_observation(ref, session_dir=session_dir))
                    for ref in result.observation_refs]
    if (not observations or observations[-1].get("tool_name") != RESEARCH_CONTROL_SUBMISSION_TOOL
        or observations[-1].get("is_error") is not False
        or observations[-1].get("terminal_payload") != submission):
        raise ValueError("research submission is not the final observed action")
    report_ref = submission["report_ref"]
    report_path = Path(report_ref["path"]).resolve()
    report_root = session_dir.resolve() / CLIENT_TOOL_SESSION_DIRECTORY / "reports"
    if report_path.parent != report_root or report_path.name != report_ref["sha256"] + ".md":
        raise ValueError("research report reference escapes its store")
    report, errors = read_hash_bound_utf8_file(report_ref)
    if errors:
        raise ValueError("research report identity mismatch: " + ",".join(errors))
    payloads = {}
    for scope, reference in submission["selected_checkpoints"].items():
        matches = [row for row in observations[:-1]
                   if row.get("is_error") is False and row.get("tool_name", "").startswith(scope + "__")
                   and isinstance(row.get("terminal_payload"), Mapping)
                   and stable_hash(row["terminal_payload"]) == reference["payload_hash"]
                   and row.get("model_content_blocks")
                   and json.loads(row["model_content_blocks"][-1]["text"]).get("shared_checkpoint_ref") == reference]
        if not matches:
            raise ValueError("selected research checkpoint was not observed: " + scope)
        payloads[scope] = deepcopy(matches[-1]["terminal_payload"])
    return {**submission, "report_markdown": report, "checkpoint_payloads": payloads}


def prepare_research_control_workspace(
    *,
    question: OpenResearchQuestion,
    request: ClientToolTurnRequest,
    workspaces: Mapping[str, PreparedClientToolWorkspace[Any]],
    checkpoint_bindings: Callable[[str, Mapping[str, Any]], Mapping[str, Any] | None],
    session_dir: Path,
    session_id: str,
    max_turns: int,
    max_tool_calls: int,
    max_no_progress_turns: int,
    workflow_instructions: str = "",
    input_workspace_preparers: Mapping[str, Callable[
        [Mapping[str, Mapping[str, Any]], Mapping[str, Any] | None],
        PreparedClientToolWorkspace[Any],
    ]] | None = None,
) -> PreparedClientToolWorkspace[ClientToolLoopResult]:
    """Bind a public question, exact input joins and a model-authored MD report.

    The trusted extractor returns produced ``resources`` (ID -> content hash)
    and consumed ``inputs`` (scope -> {payload_hash, resources}). It must cover
    actual files, interfaces and other premises used by component executors;
    the model cannot supply or change these bindings at submission.
    A consistent selection is not scientific acceptance. External evaluation
    must still check the frozen task and exact artifacts in every study arm.
    Returning None keeps a gap/progress observation without treating it as a
    dependent-input checkpoint. Input preparers receive selected raw payloads
    and the target's prior checkpoint; they call the actual production binding.
    ``provided_inputs`` records supplied context, not inferred model reasoning.
    """

    workspaces = dict(workspaces)
    public_question = research_question_payload(question, include_task_intent=True)
    question_hash = stable_hash(public_question)
    control_mode = "same_workflow" if workflow_instructions else "free_planning"
    checkpoints: dict[str, dict[str, dict[str, Any]]] = {scope: {} for scope in workspaces}
    payloads: dict[str, dict[str, dict[str, Any]]] = {scope: {} for scope in workspaces}
    preparers = dict(input_workspace_preparers or {})
    if set(preparers) - set(workspaces):
        raise ValueError("input preparer requires a configured component scope")
    active_workspaces = dict(workspaces)
    input_selections: dict[str, dict[str, Any]] = {}
    latest_checkpoints: dict[str, str] = {}

    def execute_component(scope, call, context):
        if scope in preparers and scope not in input_selections:
            raise ClientToolInputError("select this workspace's exact inputs before using its actions")
        return active_workspaces[scope].execute_tool(call, context)

    bound_workspaces = {
        scope: replace(workspace, execute_tool=lambda call, context, scope=scope: execute_component(scope, call, context))
        if scope in preparers else workspace
        for scope, workspace in workspaces.items()
    }

    def observe(scope: str, result: ClientToolExecutionResult) -> Mapping[str, Any] | None:
        payload = result.terminal_payload
        bindings = checkpoint_bindings(scope, deepcopy(dict(payload)))
        if bindings is None:
            return None
        resources = deepcopy(dict(bindings["resources"]))
        inputs = deepcopy(dict(bindings["inputs"]))
        for input_scope, binding in inputs.items():
            input_hash = binding["payload_hash"]
            if input_scope == scope or input_scope not in checkpoints or input_hash not in checkpoints[input_scope]:
                raise ValueError("component execution input is not a prior cross-workspace checkpoint")
            available = checkpoints[input_scope][input_hash]["resources"]
            if not binding["resources"] or any(
                resource not in available or available[resource] != content_hash
                for resource, content_hash in binding["resources"].items()
            ):
                raise ValueError("component execution inputs do not match their observed producer resources")
            if scope in preparers and input_hash != input_selections[scope].get(input_scope, {}).get("payload_hash"):
                raise ValueError("component execution used an input other than its selected workspace context")
        payload_hash = stable_hash(payload)
        reference = {"scope": scope, "payload_hash": payload_hash, "resources": resources, "inputs": inputs}
        if scope in preparers:
            reference["provided_inputs"] = deepcopy(input_selections[scope])
        prior = checkpoints[scope].get(payload_hash)
        if prior is not None and prior != reference:
            raise ValueError("identical checkpoint payload has conflicting execution inputs")
        checkpoints[scope][payload_hash] = reference
        payloads[scope][payload_hash] = deepcopy(dict(payload))
        latest_checkpoints[scope] = payload_hash
        return deepcopy(reference)

    def select_inputs(call):
        if set(call.input) != {"scope", "selected_checkpoints"}:
            raise ClientToolInputError("workspace input selection requires a scope and exact checkpoints")
        scope, selection = call.input["scope"], call.input["selected_checkpoints"]
        if not isinstance(scope, str) or scope not in preparers or not isinstance(selection, Mapping):
            raise ClientToolInputError("workspace input selection is not a configured dependent component")
        selected = {}
        for parent, payload_hash in selection.items():
            if parent == scope or parent not in checkpoints or not isinstance(payload_hash, str) or payload_hash not in checkpoints[parent]:
                raise ClientToolInputError("workspace input selection is not an observed cross-component checkpoint")
            selected[parent] = {
                "reference": deepcopy(checkpoints[parent][payload_hash]),
                "payload": deepcopy(payloads[parent][payload_hash]),
            }
        provided = {parent: {"payload_hash": row["reference"]["payload_hash"],
                             "resources": deepcopy(row["reference"]["resources"])}
                    for parent, row in selected.items()}
        unchanged = input_selections.get(scope) == provided
        if unchanged:
            workspace = active_workspaces[scope]
        else:
            previous = payloads[scope].get(latest_checkpoints.get(scope, ""))
            workspace = preparers[scope](selected, deepcopy(previous))
        original = workspaces[scope]
        if workspace.request.tools != original.request.tools or any(
            getattr(workspace.request, field) != getattr(original.request, field)
            for field in ("model", "temperature", "thinking_budget_tokens")
        ):
            raise ValueError("selected-input preparation changed the frozen tool or model contract")
        active_workspaces[scope] = workspace
        input_selections[scope] = provided
        return ClientToolExecutionResult(
            content={"scope": scope, "provided_inputs": provided,
                     "initial_workspace_context": deepcopy(dict(workspace.initial_context)),
                     "component_request_contract": client_tool_session_contract_fingerprint(workspace.request),
                     "independent_role_review": False},
            state_changed=not unchanged,
            observation_key="workspace-input-selection:" + stable_hash([scope, provided, workspace.initial_context]),
        )

    submit = ClientToolDefinition(
        name=RESEARCH_CONTROL_SUBMISSION_TOOL,
        description=(
            "Submit a model-authored Markdown research report and explicitly select exact "
            "shared_checkpoint_ref payload hashes by scope. Selected producer resources must "
            "match the exact inputs consumed by each selected checkpoint. Unrelated changes "
            "do not invalidate those inputs. You may select an earlier consistent set. This ends "
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
        if call.name == RESEARCH_CONTROL_INPUTS_TOOL:
            return select_inputs(call)
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
            for input_scope, binding in (*reference.get("provided_inputs", {}).items(), *reference["inputs"].items()):
                available = selected.get(input_scope, {}).get("resources", {})
                if any(resource not in available or available[resource] != content_hash
                       for resource, content_hash in binding["resources"].items()):
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
    control_tools = (submit,)
    if preparers:
        control_tools += (ClientToolDefinition(
            name=RESEARCH_CONTROL_INPUTS_TOOL,
            description=(
                "Select observed checkpoint payload hashes as inputs before using a dependent workspace. "
                "Its production tools are rebound to those exact files and interfaces; read the returned "
                "context before authoring source. Rebinding retains only the prior committed component "
                "checkpoint, not uncommitted edits, and does not execute source or grant review credit."
            ),
            input_schema={"type": "object", "additionalProperties": False,
                          "properties": {"scope": {"type": "string", "enum": list(preparers)},
                                         "selected_checkpoints": {"type": "object", "additionalProperties": False,
                                                                  "properties": {scope: {"type": "string", "minLength": 1}
                                                                                 for scope in workspaces}}},
                          "required": ["scope", "selected_checkpoints"]},
        ),)
    return prepare_shared_client_tool_workspace(
        request=shared_request, workspaces=bound_workspaces, control_tools=control_tools,
        execute_control_tool=finish, observe_checkpoint=observe,
        max_turns=max_turns, max_tool_calls=max_tool_calls, max_no_progress_turns=max_no_progress_turns,
        session_dir=session_dir, session_id=session_id,
    )


def prepare_single_context_research_workspace(
    *,
    question: OpenResearchQuestion,
    request: ClientToolTurnRequest,
    theory_agent: Any,
    algorithm_agent: Any,
    simulation_agent: Any,
    estimator_id: str,
    session_dir: Path,
    session_id: str,
    n_runs: int,
    seed: int,
    timeout_s: int,
    max_turns: int,
    max_tool_calls: int,
    max_no_progress_turns: int,
    workflow_instructions: str = "",
) -> PreparedClientToolWorkspace[ClientToolLoopResult]:
    """Assemble actual Theory/estimator/exploratory-simulation actions.

    This single-estimator exploratory comparison arm is not another product scheduler.
    Source checkpoints and their supplied contexts are not isolated-role receipts
    or independent acceptance. Confirmation and optional/required Lean evaluation
    must be configured separately; this entry point supplies no formal capability.
    """

    from .estimator_interface_contract import project_executable_estimator_spec
    from .research_agent_runtime import _estimator_spec, _run_generated_code_sandbox, _run_generated_simulation_sandbox
    from .scientific_sandbox import scientific_project_hash
    from .theory_derivation_trace import document_authoritative_theory_context
    from .theory_workspace import load_theory_workspace_documents

    question = deepcopy(question)
    if question.task_intent.get("formal") == "required":
        raise ValueError("this comparison arm has no required-formal executor")
    if not estimator_id.strip() or min(n_runs, timeout_s) < 1:
        raise ValueError("research control requires an estimator identity and positive execution limits")
    frozen_estimator_id = question.estimator_execution_contract.get("estimator_id")
    if frozen_estimator_id and estimator_id != frozen_estimator_id:
        raise ValueError("comparison estimator identity differs from the frozen question ABI")
    sources = theory_agent.research_sources
    discovery = theory_agent.research_source_discovery
    theory = theory_agent.prepare_workspace(question, theory_workspace_root=session_dir / "theory")

    def prepare_source(scope, selected, previous):
        allowed = {"theory"} if scope == "algorithm" else {"theory", "algorithm"}
        if set(selected) - allowed:
            raise ClientToolInputError("selected inputs are not dependencies of this source workspace")
        core = selected.get("theory", {}).get("payload", {}).get("core_packet", {})
        theory_context = document_authoritative_theory_context(core)
        spec = _estimator_spec(core, estimator_id)
        provided = {parent: {"payload_hash": row["reference"]["payload_hash"],
                             "resources": deepcopy(row["reference"]["resources"])}
                    for parent, row in selected.items()}
        inputs = {}
        if scope == "algorithm" and "theory" in selected:
            inputs["theory"] = {"payload_hash": provided["theory"]["payload_hash"],
                                "resources": {"estimator:" + estimator_id: stable_hash(spec)}}
        context = {"theory_context": theory_context, "execution_phase": "exploratory_diagnostic",
                   "estimator_spec": project_executable_estimator_spec(spec),
                   "independent_role_review": False}
        handoff = {}
        if "algorithm" in selected:
            draft = selected["algorithm"]["payload"]["code_draft"]
            project_hash = scientific_project_hash(language=draft["language"], code=draft["code"],
                                                   project_files=draft.get("project_files", []))
            handoff = {"independent_role_review": False, "exact_algorithm_artifacts": [{
                "estimator_id": estimator_id, "language": draft["language"],
                "dependencies": draft["dependencies"], "exact_source_code": draft["code"],
                "exact_source_hash": stable_hash(draft["code"]), "exact_project_hash": project_hash,
                "exact_project_files": deepcopy(draft.get("project_files", [])),
            }]}
            inputs["algorithm"] = {"payload_hash": provided["algorithm"]["payload_hash"],
                                   "resources": {"project": project_hash}}
            context["upstream_estimator"] = {"id": estimator_id, "language": draft["language"],
                                             "project_hash": project_hash,
                                             "estimator_interface_contract": context["estimator_spec"].get("estimator_interface_contract", {})}
        context["run_sandbox_contract"] = (
            "run_sandbox(seed, replicates, estimators) returns named JSON-finite exploratory measurements. "
            "The estimators mapping binds estimator IDs to callables accepting one request object."
            if handoff else "run_sandbox(seed, replicates) returns named JSON-finite developer diagnostics."
        )
        context["required_callable_exports"] = ["run_estimator", "run_sandbox"] if scope == "algorithm" else ["run_sandbox"]
        execution_dir = session_dir / "execution" / scope / stable_hash(provided)

        def check(candidate):
            if scope == "algorithm":
                row, tool = _run_generated_code_sandbox(
                    sandbox_dir=execution_dir, estimator_id=estimator_id, spec=spec, code_draft=candidate,
                    required_callable_exports=("run_estimator",), n_runs=n_runs, seed=seed, timeout_s=timeout_s,
                )
            else:
                row, tool = _run_generated_simulation_sandbox(
                    sandbox_dir=execution_dir, simulation_id=session_id + ":simulation", code_draft=candidate,
                    upstream_algorithm_handoff=handoff, n_runs=n_runs, seed=seed, timeout_s=timeout_s,
                )
            row["execution_phase"] = "exploratory_diagnostic"
            return {"code_draft_hash": stable_hash(candidate), "accepted": row["smoke_passed"],
                    "prototype": row, "checkpoint_inputs": deepcopy(inputs),
                    "tool_call": asdict(tool), "independent_role_review": False,
                    "empirical_evidence_status": "EXPLORATORY_NOT_CONFIRMATORY"}

        agent = algorithm_agent if scope == "algorithm" else simulation_agent
        return agent.prepare_code_workspace(
            question=question, artifact_id=session_id + ":" + scope,
            code_draft=previous["code_draft"] if previous else None, initial_observation={},
            workspace_context=context, check_candidate=check,
            workspace_operation="targeted_revision" if previous else "initial_authoring",
            allow_current_source_run=True, session_dir=session_dir / scope,
            research_sources=sources, research_source_discovery=discovery,
        )

    def bindings(scope, payload):
        if scope == "theory":
            if "core_packet" not in payload:
                return None
            core = payload["core_packet"]
            resources = {path: hashlib.sha256(body.encode()).hexdigest()
                         for path, body in load_theory_workspace_documents(core).items()}
            resources.update({name: stable_hash(core.get(name, {}))
                              for name in ("problem_card", "theory_derivation_packet", "estimator_specs", "simulation_ademp_spec")})
            resources["estimator:" + estimator_id] = stable_hash(_estimator_spec(core, estimator_id))
            return {"resources": resources, "inputs": {}}
        return {"resources": {"project": payload["check_result"]["prototype"]["project_hash"]},
                "inputs": payload["check_result"]["checkpoint_inputs"]}

    return prepare_research_control_workspace(
        question=question, request=request,
        workspaces={"theory": theory, "algorithm": prepare_source("algorithm", {}, None),
                    "simulation": prepare_source("simulation", {}, None)},
        input_workspace_preparers={scope: lambda selected, previous, scope=scope: prepare_source(scope, selected, previous)
                                  for scope in ("algorithm", "simulation")},
        checkpoint_bindings=bindings, session_dir=session_dir, session_id=session_id,
        max_turns=max_turns, max_tool_calls=max_tool_calls, max_no_progress_turns=max_no_progress_turns,
        workflow_instructions=workflow_instructions,
    )
