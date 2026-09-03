import hashlib
import re
from typing import Any, Mapping


EXPECTED_QUESTION_ID = "betareg_jss_gasoline_precision_public_replication"
EXPECTED_BENCHMARK_ID = (
    "research-l1-betareg-jss-gasoline-precision-20260903-v1"
)
EXPECTED_EXECUTION_ID = (
    "betareg-jss-2010-gasoline-precision-source-execution-20260903-v1"
)
EXPECTED_EXECUTION_SPEC_SHA256 = (
    "51849a14f42d7c660a2da75c4e2047858072b3b07530c6c95e4e082aa0c2d050"
)
EXPECTED_SOURCE_SNAPSHOT_ID = (
    "betareg-jss-2010-r-public-replication-20260829-v1"
)
EXPECTED_SOURCE_SNAPSHOT_HASH = (
    "3c4c642b44ea9413b8b29f456606568a356e2b9c0b6301b8829ae3d640b67c8b"
)
EXPECTED_SOURCE_MANIFEST_SHA256 = (
    "a3af9e0459f026a34bf305f4685676501c0422bc1ed82b22448ed80c002c2582"
)
EXPECTED_ENTRYPOINT_SHA256 = (
    "0725416e1d260a76acf2f27db9a028ee5cf8366a1bb766e3e8115c5b381de57d"
)
EXPECTED_STDOUT_SHA256 = (
    "c2fceb0f5a7bcc98b084218d34948070f19dc3e3aa4372e6083ba206c8d160d6"
)
EXPECTED_STDERR_SHA256 = (
    "09b5f760bfc97c43a30cfd34283ac29d90fdf786d078d04273fbbeb1ca94ebe9"
)
EXPECTED_PACKAGE_VERSIONS = {
    "Formula": "1.0.0",
    "betareg": "2.2.0",
    "lmtest": "0.9.40",
    "sandwich": "3.1.0",
    "strucchange": "1.5.4",
    "zoo": "1.8.15",
}


def _text(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _precision_values(stdout: str) -> tuple[float, float] | None:
    values = re.findall(
        r"(?m)^\(Intercept\)\s*$\n^\s*([0-9]+(?:\.[0-9]+)?)\s*$",
        stdout,
    )
    if len(values) < 2:
        return None
    return float(values[0]), float(values[1])


def _result_artifact(candidate: Mapping[str, Any]) -> Mapping[str, Any]:
    artifacts = candidate.get("result_artifacts", [])
    if not isinstance(artifacts, list) or len(artifacts) != 1:
        return {}
    artifact = artifacts[0]
    return artifact if isinstance(artifact, Mapping) else {}


def evaluate_artifact(
    candidate: Mapping[str, Any], *, seed: int, replicates: int
) -> dict[str, Any]:
    del seed, replicates
    stdout = _text(candidate.get("raw_stdout"))
    stderr = _text(candidate.get("raw_stderr"))
    precision_values = _precision_values(stdout)
    result_artifact = _result_artifact(candidate)

    source_identity_valid = all(
        (
            candidate.get("source_snapshot_id") == EXPECTED_SOURCE_SNAPSHOT_ID,
            candidate.get("source_snapshot_hash") == EXPECTED_SOURCE_SNAPSHOT_HASH,
            candidate.get("source_manifest_sha256")
            == EXPECTED_SOURCE_MANIFEST_SHA256,
            candidate.get("source_commit")
            == "jss-v034i02-official-source-2010-04-05",
            candidate.get("entrypoint_document_id")
            == "betareg-jss-official-r-example",
            candidate.get("executed_entrypoint_sha256")
            == EXPECTED_ENTRYPOINT_SHA256,
        )
    )
    execution_clean = all(
        (
            candidate.get("execution_attempted") is True,
            candidate.get("execution_status") == "EXECUTED",
            candidate.get("returncode") == 0,
            candidate.get("errors") == [],
            candidate.get("source_mutated") is False,
            candidate.get("staged_source_inputs_mutated") is False,
            candidate.get("runtime_edited_source") is False,
            candidate.get("command_owned_by_model") is False,
            candidate.get("network_access") is False,
            candidate.get("secret_environment_inherited") is False,
            candidate.get("unexpected_workspace_artifacts") == [],
            candidate.get("execution_workspace_mode")
            == "staged_copy_on_write",
        )
    )
    runtime_identity_valid = all(
        (
            candidate.get("runtime_language") == "r",
            candidate.get("runtime_version")
            == "R version 4.4.3 (2025-02-28)",
            candidate.get("package_versions") == EXPECTED_PACKAGE_VERSIONS,
        )
    )
    stdout_identity_valid = all(
        (
            candidate.get("stdout_sha256") == EXPECTED_STDOUT_SHA256,
            _sha256_text(stdout) == EXPECTED_STDOUT_SHA256,
            candidate.get("stderr_sha256") == EXPECTED_STDERR_SHA256,
            _sha256_text(stderr) == EXPECTED_STDERR_SHA256,
        )
    )
    gasoline_model_output_valid = all(
        fragment in stdout
        for fragment in (
            "betareg(formula = yield ~ batch + temp, data = GasolineYield)",
            "Coefficients (mean model with logit link):",
            "Phi coefficients (precision model with identity link):",
            "Log-likelihood:  84.8 on 12 Df",
            "Pseudo R-squared: 0.9617",
        )
    )
    precision_values_valid = bool(
        precision_values is not None
        and abs(precision_values[0] - 440.2783) <= 1e-7
        and abs(precision_values[1] - 577.7907) <= 1e-7
        and precision_values[1] > precision_values[0]
    )
    artifact_contract_valid = all(
        (
            candidate.get("declared_result_artifact_paths") == ["Rplots.pdf"],
            result_artifact.get("relative_path") == "Rplots.pdf",
            result_artifact.get("content_encoding") == "binary_not_embedded",
            result_artifact.get("size_bytes") == 59037,
            isinstance(result_artifact.get("sha256"), str),
            len(_text(result_artifact.get("sha256"))) == 64,
        )
    )

    return {
        "artifact_kind_valid": (
            candidate.get("schema_version") == 3
            and candidate.get("artifact_kind") == "SourceReplicationManifest"
        ),
        "task_identity_valid": candidate.get("question_id")
        == EXPECTED_QUESTION_ID,
        "execution_identity_valid": all(
            (
                candidate.get("benchmark_id") == EXPECTED_BENCHMARK_ID,
                candidate.get("execution_id") == EXPECTED_EXECUTION_ID,
                candidate.get("execution_spec_sha256")
                == EXPECTED_EXECUTION_SPEC_SHA256,
            )
        ),
        "source_identity_valid": source_identity_valid,
        "execution_clean": execution_clean,
        "runtime_identity_valid": runtime_identity_valid,
        "stdout_identity_valid": stdout_identity_valid,
        "gasoline_model_output_valid": gasoline_model_output_valid,
        "precision_values_valid": precision_values_valid,
        "precision_before": (
            precision_values[0] if precision_values is not None else None
        ),
        "precision_after_omitting_observation_4": (
            precision_values[1] if precision_values is not None else None
        ),
        "artifact_contract_valid": artifact_contract_valid,
        "raw_pdf_hash_identity_required": False,
        "proof_evidence_status": "SOURCE_REPLICATION_EVALUATION_NOT_PROOF_EVIDENCE",
    }
