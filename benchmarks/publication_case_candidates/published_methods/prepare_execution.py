"""Bind existing candidate inputs/environments without running a source or model."""

import argparse
from email.parser import Parser
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess

from ai_statistician.fingerprint import stable_hash
from ai_statistician.research_source_library import load_research_source_execution_spec, load_research_source_snapshot
from ai_statistician.scientific_sandbox import load_native_r_runtime


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PROCESS_KEYS = ("environment_root", "interpreter_executable_relative_path",
                "interpreter_executable_sha256", "runtime_read_roots",
                "runtime_executables", "runtime_environment")


def ref(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {"path": str(path), "sha256": sha256(raw).hexdigest(), "byte_size": len(raw)}


def write_json(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def file_inventory(root):
    rows = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            rows.append({"path": path.relative_to(root).as_posix(), "kind": "symlink",
                         "sha256": sha256(os.readlink(path).encode()).hexdigest()})
        elif path.is_file():
            rows.append({"path": path.relative_to(root).as_posix(), "kind": "file",
                         "sha256": sha256(path.read_bytes()).hexdigest()})
    return rows


def r_package_versions(libraries):
    versions = {}
    for library in libraries:
        for path in sorted(library.glob("*/DESCRIPTION")):
            fields = Parser().parsestr(path.read_text(encoding="utf-8"))
            name, version = fields["Package"], fields["Version"]
            if not name or not version:
                raise ValueError(f"Incomplete installed DESCRIPTION: {path}")
            versions.setdefault(name.strip(), version.strip())
    return versions


def prepare(out):
    out = Path(out).resolve()
    if out.exists():
        raise FileExistsError("use a fresh execution preparation directory")
    prepared = json.loads((HERE / "input_preparation.json").read_bytes())
    originals = {row["question_id"]: row for row in prepared["candidates"]}
    plan = json.loads((HERE / "execution_plan.json").read_bytes())
    if {row["question_id"] for row in plan} != set(originals) or len(plan) != len(originals):
        raise ValueError("execution plan must bind each source candidate once")
    out.mkdir(parents=True, exist_ok=False)
    results = []
    for row in plan:
        original = originals[row["question_id"]]
        source = load_research_source_snapshot(Path(original["manifest_ref"]["path"]))
        if source.identity_errors() or source.descriptor() != original["snapshot"]:
            raise ValueError("original candidate source identity mismatch")
        destination = out / source.snapshot_id
        root = destination / "sources"
        shutil.copytree(source.source_root, root)
        documents = json.loads(source.manifest_path.read_bytes())["documents"]
        for document in source.documents:
            if ref(root / document.relative_path)["sha256"] != document.sha256:
                raise ValueError("source byte identity was lost")
        environment = root / "environment"
        environment.mkdir()
        if row["runtime_language"] == "python":
            envroot = (REPO / row["environment_root"]).resolve()
            executable = envroot / row["interpreter_executable_relative_path"]
            readiness = json.loads((REPO / row["environment_readiness"]).read_bytes())
            process = {"environment_root": str(envroot),
                "interpreter_executable_relative_path": row["interpreter_executable_relative_path"],
                "interpreter_executable_sha256": row["interpreter_executable_sha256"],
                "runtime_read_roots": [str(executable.resolve().parents[1])],
                "runtime_executables": {}, "runtime_environment": {}}
            versions = {item["name"]: item["version"] for item in readiness["installed"]}
            libraries = [envroot]
            runtime_version = readiness["python_version"]
            probe_id = ""
        else:
            base = load_native_r_runtime(REPO / row["base_runtime_config"])
            declared = json.loads((REPO / row["base_runtime_config"]).read_bytes())
            process = {key: declared[key] for key in PROCESS_KEYS}
            owned = (REPO / row["owned_library"]).resolve()
            envroot = base.process.environment_root
            base_library = envroot / "R.framework/Resources/library"
            libraries = [owned, base_library.resolve()]
            versions = r_package_versions(libraries)
            process["runtime_read_roots"] = [str(owned), "/private/var/select"]
            process["runtime_environment"] = {**process["runtime_environment"],
                "R_LIBS_USER": str(owned), "R_LIBS_SITE": "/nonexistent"}
            runtime_version = base.runtime_version
            probe_id = "environment/environment_probe.R"
            shutil.copyfile(HERE / "environment_probe.R", root / probe_id)
            native = {**process, "schema_version": 1, "runtime_version": runtime_version,
                      "package_versions": versions}
            write_json(destination / "native_r_runtime.json", native)
            load_native_r_runtime(destination / "native_r_runtime.json")
            process = {**process, "runtime_environment": {**process["runtime_environment"],
                "AI_STATISTICIAN_SOURCE_PACKAGES": ",".join(row["package_distributions"])}}
        inventories = []
        for index, library in enumerate(libraries):
            inventory = environment / f"file_inventory_{index}.json"
            files = file_inventory(library)
            write_json(inventory, {"root": str(library), "files": files})
            inventories.append({**ref(inventory), "file_count": len(files), "tree_hash": stable_hash(files)})
        lock = {"runtime_language": row["runtime_language"], "runtime_version": runtime_version,
            "package_versions": versions, "process": process, "inventories": inventories,
            "status": "Adapted local environment, not the historical author lock or a clean reconstruction.",
            "generated_execution_environment": row["generated_execution_environment"]}
        write_json(environment / "runtime.json", lock)
        for path in sorted(environment.glob("*")):
            relative = path.relative_to(root).as_posix()
            documents.append({"document_id": relative, "title": "Candidate execution environment: " + path.name,
                "source_kind": "execution_environment", "relative_path": relative,
                "sha256": ref(path)["sha256"], "byte_size": path.stat().st_size,
                "model_visible": True, "content_mode": "text", "media_type": "text/plain"})
        manifest = destination / "research_sources.json"
        write_json(manifest, {"schema_version": 1, "snapshot_id": source.snapshot_id + "_execution_v1",
            "source_horizon": "published author assets plus adapted local environment, 2026-10-03",
            "source_root": "sources", "documents": sorted(documents, key=lambda item: item["document_id"])})
        snapshot = load_research_source_snapshot(manifest)
        spec = {"schema_version": 4, "artifact_kind": "ResearchSourceExecutionSpec",
            "execution_id": source.snapshot_id + "_execution_v1", "benchmark_id": row["question_id"],
            "source_snapshot_id": snapshot.snapshot_id, "source_snapshot_hash": snapshot.snapshot_hash,
            "source_manifest_sha256": snapshot.manifest_sha256,
            "source_commit": "archive-sha256:" + original["original_assets"]["replication"]["sha256"],
            "entrypoint_document_id": row["entrypoint_document_id"],
            "environment_lock_document_id": "environment/runtime.json",
            "environment_probe_document_id": probe_id, "runtime_language": row["runtime_language"],
            **process, "interpreter_arguments": ["--vanilla"] if row["runtime_language"] == "r" else [],
            "working_directory_relative": row["working_directory_relative"], "arguments": row["arguments"],
            "package_distributions": row["package_distributions"], "timeout_seconds": row["timeout_seconds"],
            "max_output_bytes": 16777216,
            "execution_workspace_mode": "staged_copy_on_write" if row["result_artifact_paths"] else "immutable_source",
            "result_artifact_paths": row["result_artifact_paths"], "command_selection_mode": "model_selected"}
        execution_path = destination / "source_execution.json"
        write_json(execution_path, spec)
        execution = load_research_source_execution_spec(execution_path, research_sources=snapshot)
        if snapshot.identity_errors():
            raise ValueError("prepared execution input identity mismatch")
        results.append({"question_id": row["question_id"], "parent_manifest_ref": original["manifest_ref"],
            "source_snapshot_ref": ref(manifest), "snapshot_hash": snapshot.snapshot_hash,
            "document_count": len(snapshot.documents), "source_execution_ref": ref(execution_path),
            "native_r_runtime_ref": ref(destination / "native_r_runtime.json") if row["runtime_language"] == "r" else None,
            "preserved_parent_documents": len(source.documents), "environment_inventory_refs": inventories,
            "timeout_seconds": execution.timeout_seconds, "command_selection_mode": execution.command_selection_mode,
            "source_commit_field": "Original replication archive SHA-256; not a Git commit or invented author history.",
            "generated_execution_environment": row["generated_execution_environment"]})
    record = {"scope": "candidate_execution_binding_preparation_only", "model_calls": 0,
        "scientific_scripts_executed": 0, "source_probes_executed": 0, "study_activated": False,
        "plan_ref": ref(HERE / "execution_plan.json"), "input_preparation_ref": ref(HERE / "input_preparation.json"),
        "preparer_ref": ref(Path(__file__)),
        "code_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
        "candidates": results,
        "remaining": ["actual study/native parallel execution", "generated Python import environment",
            "final estimator interfaces and common scientific assessment", "actual matched arms and source/PDF access",
            "rights, roster/precision and prospective study freeze"]}
    write_json(out / "execution_preparation.json", record)
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    record = prepare(parser.parse_args().out)
    print(json.dumps({"scope": record["scope"], "model_calls": 0,
        "candidates": [{"question_id": row["question_id"], "documents": row["document_count"],
                        "source_execution_ref": row["source_execution_ref"]} for row in record["candidates"]]}))
