"""Prospective reverse-revision ablation, not removal of local tool feedback."""

from dataclasses import replace

from ai_statistician.agent_runtime import EnvironmentObservation, agent_task_reference
from ai_statistician.architect_coordinator_llm import ARCHITECT_FEEDBACK_ROUTE_OPERATION
from ai_statistician.generated_code_semantic_review_scope import accepted_semantic_review_deferred_continuation
from ai_statistician.research_agent_runtime import RUNTIME_PRIMARY_EVIDENCE_SUBSYSTEMS, _runtime_transition_policy


NO_CROSS_ROLE_REVISION = "no_cross_role_revision_v1"


def no_cross_role_revision_policy(config):
    """Apply normal authority gates first, then withhold reverse author re-entry."""
    authors = {"TheoryDeveloper", *RUNTIME_PRIMARY_EVIDENCE_SUBSYSTEMS}
    visited_authors = set()
    last_model_role = None

    def policy(*, iteration, task, subsystem_name, result, blackboard):
        nonlocal last_model_role
        if iteration == 1:
            visited_authors.clear()
            last_model_role = None
        # RetrievalMemory is an environment tool, not another model author.
        if subsystem_name != "RetrievalMemory":
            last_model_role = subsystem_name
        if subsystem_name in authors:
            visited_authors.add(subsystem_name)
        routed = _runtime_transition_policy(iteration=iteration, task=task, subsystem_name=subsystem_name,
            result=result, blackboard=blackboard, runtime_config=config)
        next_task = routed.next_task
        if next_task is None:
            return routed
        accepted_source_resume = accepted_semantic_review_deferred_continuation(
            task=task, result=routed, next_task=next_task, blackboard=blackboard,
        ) and next_task.owner_subsystem == blackboard.artifacts.get(
            str(task.inputs.get("work_order_id", "") or ""), {},
        ).get("source_subsystem")
        reverse_revision = (next_task.owner_subsystem in visited_authors
                            and next_task.owner_subsystem != last_model_role and not accepted_source_resume)
        feedback_route = (next_task.owner_subsystem == "ArchitectCoordinator"
                          and next_task.inputs.get("runtime_architect_operation") == ARCHITECT_FEEDBACK_ROUTE_OPERATION)
        if not (reverse_revision or feedback_route):
            return routed
        observation = EnvironmentObservation(
            observation_type="publication_cross_role_revision_withheld",
            summary="The frozen ablation withholds this reverse revision before another model invocation.",
            payload={"intervention": NO_CROSS_ROLE_REVISION, "source_task_ref": agent_task_reference(task),
                     "withheld_next_task_ref": agent_task_reference(next_task), "original_status": routed.status,
                     "last_model_role": last_model_role, "runtime_authored_research_content": False,
                     "authority": "study_intervention_not_scientific_or_proof_evidence"},
        )
        return replace(routed, status="BLOCKED", next_task=None,
            rationale="The frozen study arm ended without cross-role author revision; all original material remains unchanged.",
            observations=routed.observations + (observation,),
            failure_classification="publication_cross_role_revision_disabled")

    return policy
