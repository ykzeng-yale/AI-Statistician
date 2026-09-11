from __future__ import annotations

import ast
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from .fingerprint import stable_hash
from .scientific_project import (
    ScientificProjectFile,
    normalized_scientific_project_files,
    scientific_main_path,
    scientific_project_file_errors,
    scientific_project_files_json_schema,
    scientific_project_hash,
    scientific_python_local_import_roots,
)

try:  # POSIX execution is required only when an isolation provider is available.
    import resource
except ImportError:  # pragma: no cover - exercised on non-POSIX hosts
    resource = None  # type: ignore[assignment]


STDLIB_SANDBOX_PROFILE = "stdlib"
SCIENTIFIC_WASM_SANDBOX_PROFILE = "scientific_wasm"
SCIENTIFIC_SANDBOX_LANGUAGES = ("python", "r")
SCIENTIFIC_SANDBOX_PROFILES = (
    STDLIB_SANDBOX_PROFILE,
    SCIENTIFIC_WASM_SANDBOX_PROFILE,
)
MAX_SCIENTIFIC_INPUT_ARTIFACT_BYTES = 64 * 1024 * 1024
SCIENTIFIC_SANDBOX_BOUNDARY = (
    "Generated scientific code executes as untrusted WebAssembly in a separate "
    "secret-free, resource-bounded process with network denial and a host-filesystem "
    "allowlist. The host runtime supplies only pinned package names and execution "
    "artifacts. Successful execution is empirical engineering evidence, not production "
    "promotion and not theorem proof evidence."
)

PYTHON_SCIENTIFIC_DEPENDENCIES = (
    "numpy",
    "scipy",
    "pandas",
    "scikit-learn",
    "statsmodels",
    "sympy",
)
R_SCIENTIFIC_PRELOADED_NAMESPACES = (
    "base",
    "datasets",
    "grdevices",
    "graphics",
    "methods",
    "stats",
    "utils",
    "webr",
)
R_SCIENTIFIC_DEPENDENCIES = (
    "base",
    "compiler",
    "datasets",
    "grdevices",
    "graphics",
    "grid",
    "methods",
    "parallel",
    "splines",
    "stats",
    "stats4",
    "tools",
    "utils",
)
_PYTHON_PACKAGE_IMPORT_ROOTS = {
    "numpy": {"numpy"},
    "scipy": {"scipy"},
    "pandas": {"pandas"},
    "scikit-learn": {"sklearn"},
    "statsmodels": {"statsmodels", "patsy"},
    "sympy": {"sympy", "isympy"},
}
_PYTHON_PACKAGE_CACHE_PREFIXES = {
    "numpy": ("numpy-",),
    "scipy": ("scipy-",),
    "pandas": ("pandas-", "python_dateutil-", "pytz-", "six-"),
    "scikit-learn": ("scikit_learn-", "joblib-", "threadpoolctl-"),
    "statsmodels": ("statsmodels-", "patsy-", "packaging-"),
    "sympy": ("sympy-", "mpmath-"),
}


@dataclass(frozen=True)
class ScientificSandboxRuntime:
    node_executable: str = ""
    pyodide_entry: str = ""
    pyodide_root: str = ""
    webr_entry: str = ""
    runner_path: str = ""
    isolation_provider: str = ""
    python_available: bool = False
    r_available: bool = False

    @property
    def available(self) -> bool:
        return bool(
            self.node_executable
            and self.runner_path
            and self.isolation_provider
            and (self.python_available or self.r_available)
        )


@dataclass(frozen=True)
class ScientificEstimatorBinding:
    """Exact reviewed estimator source supplied to a generated DGP harness."""

    artifact_id: str
    language: str
    code: str
    code_hash: str
    dependencies: tuple[str, ...] = ()
    project_files: tuple[ScientificProjectFile, ...] = ()
    project_hash: str = ""


@dataclass(frozen=True)
class ScientificInputArtifactBinding:
    """Exact immutable data supplied separately from executable source."""

    artifact_id: str
    content: str
    content_sha256: str
    media_type: str = "text/plain"


@dataclass(frozen=True)
class ScientificSandboxExecution:
    status: str
    language: str
    execution_profile: str
    backend: str
    isolation_provider: str
    dependencies: tuple[str, ...]
    execution_attempted: bool
    returncode: int
    metrics: dict[str, Any]
    errors: tuple[str, ...]
    stdout_summary: str
    stderr_summary: str
    result_parse_error: str
    code_path: str
    request_path: str
    result_path: str
    code_hash: str
    request_hash: str
    result_hash: str
    subprocess_environment_keys: tuple[str, ...]
    resource_limits: dict[str, int]
    project_hash: str = ""
    project_file_paths: dict[str, str] = field(default_factory=dict)
    project_file_hashes: dict[str, str] = field(default_factory=dict)
    execution_envelope_path: str = ""
    execution_envelope_hash: str = ""
    invocation_mode: str = "standalone"
    required_callable_exports: tuple[str, ...] = ()
    estimator_code_paths: dict[str, str] = field(default_factory=dict)
    estimator_code_hashes: dict[str, str] = field(default_factory=dict)
    estimator_project_hashes: dict[str, str] = field(default_factory=dict)
    estimator_invocation_counts: dict[str, int] = field(default_factory=dict)
    estimator_invocation_samples: dict[str, list[dict[str, Any]]] = field(
        default_factory=dict
    )
    estimator_binding_hash: str = ""
    estimator_binding_errors: tuple[str, ...] = ()
    estimator_runtime_failure_ids: tuple[str, ...] = ()
    estimator_runtime_errors: tuple[str, ...] = ()
    input_artifact_paths: dict[str, str] = field(default_factory=dict)
    input_artifact_hashes: dict[str, str] = field(default_factory=dict)
    input_artifact_binding_hash: str = ""
    boundary: str = SCIENTIFIC_SANDBOX_BOUNDARY

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


def normalized_generated_code_language(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in {"", "py", "py3", "python3", "python 3"}:
        return "python"
    if text in {"rscript", "r language", "r-lang"}:
        return "r"
    return text


def normalized_generated_code_profile(value: Any, *, language: str) -> str:
    text = str(value or "").strip().lower().replace("-", "_")
    if not text:
        return (
            SCIENTIFIC_WASM_SANDBOX_PROFILE
            if normalized_generated_code_language(language) == "r"
            else STDLIB_SANDBOX_PROFILE
        )
    aliases = {
        "pure_python": STDLIB_SANDBOX_PROFILE,
        "python_stdlib": STDLIB_SANDBOX_PROFILE,
        "scientific": SCIENTIFIC_WASM_SANDBOX_PROFILE,
        "wasm": SCIENTIFIC_WASM_SANDBOX_PROFILE,
        "webassembly": SCIENTIFIC_WASM_SANDBOX_PROFILE,
    }
    return aliases.get(text, text)


def normalized_scientific_dependencies(
    values: Any,
    *,
    language: str,
) -> tuple[str, ...]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        return ()
    normalized: list[str] = []
    for value in values:
        text = str(value or "").strip().lower().replace("_", "-")
        if normalized_generated_code_language(language) == "python" and text == "sklearn":
            text = "scikit-learn"
        if text and text not in normalized:
            normalized.append(text)
    return tuple(normalized)


def generated_code_execution_contract_errors(
    draft: Mapping[str, Any], *, required_entrypoint: str | None = "run_sandbox"
) -> list[str]:
    language = normalized_generated_code_language(draft.get("language"))
    profile = normalized_generated_code_profile(
        draft.get("execution_profile"),
        language=language,
    )
    raw_dependencies = draft.get("dependencies", [])
    dependencies = normalized_scientific_dependencies(
        raw_dependencies,
        language=language,
    )
    errors: list[str] = []
    if language not in SCIENTIFIC_SANDBOX_LANGUAGES:
        errors.append("generated code language must be python or r")
    if profile not in SCIENTIFIC_SANDBOX_PROFILES:
        errors.append("generated code execution_profile must be stdlib or scientific_wasm")
    if language == "r" and profile != SCIENTIFIC_WASM_SANDBOX_PROFILE:
        errors.append("generated R code requires execution_profile scientific_wasm")
    if "dependencies" in draft and (
        not isinstance(raw_dependencies, Sequence)
        or isinstance(raw_dependencies, (str, bytes))
    ):
        errors.append("generated code dependencies must be an array")
    if profile == SCIENTIFIC_WASM_SANDBOX_PROFILE and "dependencies" not in draft:
        errors.append("scientific_wasm generated code must declare dependencies as an array")
    if profile == STDLIB_SANDBOX_PROFILE and dependencies:
        errors.append("stdlib generated code cannot declare scientific dependencies")
    allowed_dependencies = (
        set(PYTHON_SCIENTIFIC_DEPENDENCIES)
        if language == "python"
        else set(R_SCIENTIFIC_DEPENDENCIES)
        if language == "r"
        else set()
    )
    unsupported = sorted(set(dependencies) - allowed_dependencies)
    if unsupported:
        errors.append(
            "generated code declares unsupported dependencies: " + ", ".join(unsupported)
        )
    if (
        required_entrypoint is not None
        and str(draft.get("entrypoint", "") or "").strip() != required_entrypoint
    ):
        errors.append("generated code entrypoint must be " + required_entrypoint)
    code = str(draft.get("code", "") or "")
    if not code.strip():
        errors.append("generated code draft is empty")
    if len(code) > 100_000:
        errors.append("generated code draft exceeds artifact-size boundary")
    errors.extend(
        scientific_project_file_errors(
            draft.get("project_files", []),
            language=language,
        )
    )
    return sorted(set(errors))


def generated_python_syntax_errors(code: str) -> list[str]:
    """Return parser diagnostics without proposing a source-code repair."""

    if not str(code or "").strip():
        return []
    try:
        ast.parse(str(code), mode="exec")
    except SyntaxError as exc:
        return [f"generated Python draft syntax error: {exc}"]
    return []


def _python_ast_diagnostic_location(code: str, node: ast.AST) -> str:
    line = getattr(node, "lineno", None)
    column = getattr(node, "col_offset", None)
    location = ""
    if isinstance(line, int):
        location = f" at line {line}"
        if isinstance(column, int):
            location += f", column {column + 1}"
    source = " ".join((ast.get_source_segment(code, node) or "").split())
    if source:
        if len(source) > 180:
            source = source[:177] + "..."
        location += f": {source}"
    return location


def scientific_python_safety_errors(
    code: str,
    *,
    dependencies: Sequence[str],
    required_functions: Sequence[str] = ("run_sandbox",),
    local_import_roots: Sequence[str] = (),
) -> list[str]:
    if not str(code or "").strip():
        return (
            ["empty generated scientific Python draft"]
            if tuple(required_functions)
            else []
        )
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return [f"generated scientific Python draft syntax error: {exc}"]
    declared_package_roots: set[str] = set()
    for dependency in dependencies:
        declared_package_roots.update(
            _PYTHON_PACKAGE_IMPORT_ROOTS.get(dependency, set())
        )
    stdlib_roots = set(getattr(sys, "stdlib_module_names", ()))
    stdlib_roots.add("__future__")
    local_roots = {str(value) for value in local_import_roots if str(value)}
    forbidden_calls = {
        "__import__",
        "breakpoint",
        "compile",
        "delattr",
        "eval",
        "exec",
        "getattr",
        "globals",
        "help",
        "input",
        "locals",
        "setattr",
        "vars",
    }
    forbidden_roots = {
        "builtins",
        "ctypes",
        "importlib",
        "js",
        "os",
        "pathlib",
        "pyodide",
        "resource",
        "shutil",
        "signal",
        "socket",
        "subprocess",
        "sys",
    }
    forbidden_runtime_attributes = {
        "ag_frame",
        "cr_frame",
        "f_back",
        "f_builtins",
        "f_globals",
        "f_locals",
        "gi_frame",
        "tb_frame",
    }
    forbidden_introspection_attributes = {
        "__base__",
        "__bases__",
        "__builtins__",
        "__class__",
        "__closure__",
        "__code__",
        "__dict__",
        "__func__",
        "__getattribute__",
        "__globals__",
        "__mro__",
        "__self__",
        "__subclasses__",
    }
    forbidden_introspection_names = {"__builtins__"}
    function_names = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }
    errors: list[str] = []
    for function_name in required_functions:
        if function_name not in function_names:
            errors.append(
                "generated scientific Python draft must define " + function_name
            )
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                if root in forbidden_roots:
                    errors.append(
                        "generated scientific Python import is forbidden in the "
                        "isolated runtime: "
                        + alias.name
                    )
                elif root not in stdlib_roots and root not in declared_package_roots:
                    if root not in local_roots:
                        errors.append(
                            "generated scientific Python third-party import is not "
                            "declared: "
                            + alias.name
                        )
        elif isinstance(node, ast.ImportFrom):
            root = str(node.module or "").split(".", 1)[0]
            if node.level and not local_roots:
                errors.append(
                    "generated scientific Python relative import is forbidden: "
                    + str(node.module or "")
                )
            elif root in forbidden_roots:
                errors.append(
                    "generated scientific Python from-import is forbidden in the "
                    "isolated runtime: "
                    + str(node.module or "")
                )
            elif (
                not node.level
                and root not in stdlib_roots
                and root not in declared_package_roots
                and root not in local_roots
            ):
                errors.append(
                    "generated scientific Python third-party from-import is not "
                    "declared: "
                    + str(node.module or "")
                )
        elif (
            isinstance(node, ast.Name)
            and node.id in forbidden_introspection_names
        ):
            errors.append(
                "generated scientific Python cannot access runtime introspection "
                "name: "
                + node.id
                + _python_ast_diagnostic_location(code, node)
            )
        elif (
            isinstance(node, ast.Attribute)
            and node.attr in forbidden_runtime_attributes
        ):
            errors.append(
                "generated scientific Python cannot access runtime frame attribute: "
                + node.attr
                + _python_ast_diagnostic_location(code, node)
            )
        elif (
            isinstance(node, ast.Attribute)
            and node.attr in forbidden_introspection_attributes
        ):
            errors.append(
                "generated scientific Python cannot access runtime introspection "
                "attribute: "
                + node.attr
                + _python_ast_diagnostic_location(code, node)
            )
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in forbidden_calls:
                errors.append(
                    "generated scientific Python cannot call: " + node.func.id
                )
    return sorted(set(errors))


def scientific_sandbox_contract(
    runtime: ScientificSandboxRuntime | None = None,
) -> dict[str, Any]:
    runtime = runtime or discover_scientific_sandbox_runtime()
    return {
        "profiles": {
            STDLIB_SANDBOX_PROFILE: {
                "languages": ["python"],
                "dependencies": [],
                "boundary": (
                    "Pure-Python code with no third-party dependencies executes in "
                    "the same isolated WebAssembly runtime."
                ),
            },
            SCIENTIFIC_WASM_SANDBOX_PROFILE: {
                "languages": ["python", "r"],
                "python_dependencies": list(PYTHON_SCIENTIFIC_DEPENDENCIES),
                "r_dependencies": list(R_SCIENTIFIC_DEPENDENCIES),
                "r_preloaded_namespaces": list(
                    R_SCIENTIFIC_PRELOADED_NAMESPACES
                ),
                "r_dependency_enforcement": (
                    "Every non-preloaded WebR namespace active after source load or "
                    "execution must be present in the model-authored dependency list."
                ),
                "entrypoint": "run_sandbox",
                "function_contract": (
                    "run_sandbox(seed, replicates) returns a named JSON-finite metric object"
                ),
                "project_contract": (
                    "The main source may import/source code and read model-authored UTF-8 "
                    "data, configuration, or fixtures by relative path from one isolated "
                    "hash-bound Python/R project."
                ),
                "estimator_binding_contract": (
                    "A confirmatory DGP harness defines run_sandbox(seed, replicates, "
                    "estimators). Each exact reviewed algorithm exports module-level "
                    "run_estimator(request), where request and response are named "
                    "JSON-finite objects. AgentRuntime injects a mapping from immutable "
                    "estimator_id to callable and records invocation counts."
                ),
                "runtime_available": runtime.available,
                "python_available": runtime.python_available,
                "r_available": runtime.r_available,
                "isolation_provider": runtime.isolation_provider,
                "preparation_command": "npm ci && npm run prepare:scientific-sandbox",
                "boundary": SCIENTIFIC_SANDBOX_BOUNDARY,
            },
        },
        "selection_policy": (
            "Use scientific_wasm when mature numerical/statistical libraries or R "
            "materially improve fidelity. Declare only packages actually imported. "
            "Use stdlib for genuinely small self-contained Python procedures; both "
            "profiles execute under the same isolation boundary."
        ),
        "proof_evidence_status": "SCIENTIFIC_SANDBOX_CONTRACT_NOT_PROOF_EVIDENCE",
    }


def generated_code_draft_json_schema(
    *,
    artifact_properties: Mapping[str, Any],
    artifact_required: Sequence[str],
    code_max_length: int = 100_000,
) -> dict[str, Any]:
    """Return a compact provider schema; runtime validates profile compatibility."""

    common_required = [
        *[str(value) for value in artifact_required],
        "language",
        "execution_profile",
        "dependencies",
        "entrypoint",
        "code",
    ]
    common_properties = {
        **dict(artifact_properties),
        "entrypoint": {"type": "string", "enum": ["run_sandbox"]},
        "code": {
            "type": "string",
            "minLength": 1,
            "maxLength": max(1, int(code_max_length)),
        },
        "project_files": scientific_project_files_json_schema(),
    }

    dependency_values = list(
        dict.fromkeys(
            [*PYTHON_SCIENTIFIC_DEPENDENCIES, *R_SCIENTIFIC_DEPENDENCIES]
        )
    )
    return {
        "type": "object",
        "additionalProperties": False,
        "required": common_required,
        "properties": {
            **common_properties,
            "language": {
                "type": "string",
                "enum": list(SCIENTIFIC_SANDBOX_LANGUAGES),
                "description": (
                    "Select python for Python source and r for R source. The "
                    "dependency list must use only the corresponding language's "
                    "allowed packages."
                ),
            },
            "execution_profile": {
                "type": "string",
                "enum": list(SCIENTIFIC_SANDBOX_PROFILES),
            },
            "dependencies": {
                "type": "array",
                "uniqueItems": True,
                "description": (
                    "For language=python, use only: "
                    + ", ".join(PYTHON_SCIENTIFIC_DEPENDENCIES)
                    + ". For language=r, use only: "
                    + ", ".join(R_SCIENTIFIC_DEPENDENCIES)
                    + ". Never mix Python and R dependency names."
                ),
                "items": {
                    "type": "string",
                    "enum": dependency_values,
                },
            },
        },
    }


def discover_scientific_sandbox_runtime(
    *,
    project_root: Path | None = None,
) -> ScientificSandboxRuntime:
    node_executable = str(shutil.which("node") or "")
    root = (project_root or Path(__file__).resolve().parents[1]).resolve()
    candidates: list[Path] = []
    configured = str(
        os.environ.get("AI_STATISTICIAN_SCIENTIFIC_SANDBOX_NODE_MODULES", "") or ""
    ).strip()
    if configured:
        candidates.append(Path(configured).expanduser())
    candidates.extend([root / "node_modules", Path.cwd() / "node_modules"])
    node_modules = next(
        (
            candidate.resolve()
            for candidate in candidates
            if (candidate / "pyodide" / "pyodide.mjs").exists()
            or (candidate / "webr" / "dist" / "webr.mjs").exists()
        ),
        None,
    )
    pyodide_root = node_modules / "pyodide" if node_modules else None
    webr_root = node_modules / "webr" if node_modules else None
    runner_path = (
        Path(__file__).resolve().parent
        / "runtime_assets"
        / "scientific_sandbox_runner.mjs"
    )
    sandbox_exec = str(shutil.which("sandbox-exec") or "")
    isolation_provider = (
        "macos_sandbox_exec+wasm"
        if sys.platform == "darwin" and sandbox_exec
        else ""
    )
    return ScientificSandboxRuntime(
        node_executable=node_executable,
        pyodide_entry=(
            str(pyodide_root / "pyodide.mjs")
            if pyodide_root and (pyodide_root / "pyodide.mjs").exists()
            else ""
        ),
        pyodide_root=str(pyodide_root or ""),
        webr_entry=(
            str(webr_root / "dist" / "webr.mjs")
            if webr_root and (webr_root / "dist" / "webr.mjs").exists()
            else ""
        ),
        runner_path=str(runner_path) if runner_path.exists() else "",
        isolation_provider=isolation_provider,
        python_available=bool(
            node_executable
            and isolation_provider
            and pyodide_root
            and (pyodide_root / "pyodide.mjs").exists()
        ),
        r_available=bool(
            node_executable
            and isolation_provider
            and webr_root
            and (webr_root / "dist" / "webr.mjs").exists()
        ),
    )


def scientific_python_dependency_cache_errors(
    runtime: ScientificSandboxRuntime,
    dependencies: Sequence[str],
) -> list[str]:
    pyodide_root = Path(runtime.pyodide_root)
    if not pyodide_root.exists():
        return ["Pyodide runtime is unavailable"]
    filenames = {path.name for path in pyodide_root.glob("*.whl")}
    errors: list[str] = []
    for dependency in dependencies:
        prefixes = _PYTHON_PACKAGE_CACHE_PREFIXES.get(dependency, ())
        missing = [
            prefix
            for prefix in prefixes
            if not any(name.startswith(prefix) for name in filenames)
        ]
        if missing:
            errors.append(
                f"scientific Python dependency {dependency} is not prepared locally; "
                "run npm run prepare:scientific-sandbox"
            )
    return errors


def _resource_limit_payload(
    timeout_s: int,
    max_output_bytes: int,
    max_node_heap_mb: int,
) -> dict[str, int]:
    return {
        "cpu_seconds": max(2, int(math.ceil(timeout_s)) + 1),
        "file_size_bytes": max_output_bytes,
        "node_heap_mb": max(128, int(max_node_heap_mb)),
        "open_files": 64,
    }


def _resource_limiter(limits: Mapping[str, int]):
    def apply_limits() -> None:
        if resource is None:  # pragma: no cover - runtime is unavailable there
            return
        os.setsid()
        resource.setrlimit(
            resource.RLIMIT_CPU,
            (limits["cpu_seconds"], limits["cpu_seconds"]),
        )
        resource.setrlimit(
            resource.RLIMIT_FSIZE,
            (limits["file_size_bytes"], limits["file_size_bytes"]),
        )
        resource.setrlimit(
            resource.RLIMIT_NOFILE,
            (limits["open_files"], limits["open_files"]),
        )

    return apply_limits


def _scientific_sandbox_environment(sandbox_dir: Path) -> dict[str, str]:
    environment = {
        "HOME": str(sandbox_dir),
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": os.defpath,
        "TMPDIR": str(sandbox_dir),
        "TZ": "UTC",
    }
    for key in ("SYSTEMROOT", "WINDIR"):
        value = str(os.environ.get(key, "") or "").strip()
        if value:
            environment[key] = value
    return environment


def _seatbelt_value(value: str | Path) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


def _seatbelt_path(value: str | Path) -> str:
    return _seatbelt_value(Path(value).expanduser().resolve())


def _macos_sandbox_profile(
    *,
    runtime: ScientificSandboxRuntime,
    readable_paths: Sequence[Path],
    writable_paths: Sequence[Path],
) -> str:
    read_subpaths = {
        "/Library/Apple/System/Library",
        "/System",
        "/private/var/db/timezone",
        "/usr/lib",
        "/usr/share",
    }
    if runtime.pyodide_root:
        read_subpaths.add(_seatbelt_path(runtime.pyodide_root))
    if runtime.webr_entry:
        read_subpaths.add(_seatbelt_path(Path(runtime.webr_entry).parents[1]))
    read_literals = {
        "/",
        "/dev/null",
        "/dev/random",
        "/dev/urandom",
        "/etc/localtime",
        _seatbelt_path(runtime.node_executable),
        _seatbelt_path(runtime.runner_path),
        *(_seatbelt_path(path) for path in readable_paths),
        *(_seatbelt_path(path.parent) for path in readable_paths),
        *(_seatbelt_path(path.parent) for path in writable_paths),
    }
    metadata_literals = {"/etc", "/tmp", "/var"}
    metadata_literals.update(_seatbelt_path(path) for path in writable_paths)
    for path in read_subpaths | read_literals | {
        _seatbelt_path(path) for path in writable_paths
    }:
        metadata_literals.update(str(parent) for parent in Path(path).parents)
    read_rules = " ".join(
        f'(subpath "{path}")' for path in sorted(read_subpaths)
    ) + " " + " ".join(
        f'(literal "{path}")' for path in sorted(read_literals)
    )
    metadata_rules = " ".join(
        f'(literal "{_seatbelt_value(path)}")'
        for path in sorted(metadata_literals)
    )
    write_rules = " ".join(
        f'(literal "{_seatbelt_path(path)}")' for path in writable_paths
    )
    node_executable = _seatbelt_path(runtime.node_executable)
    return (
        "(version 1) (allow default) "
        "(deny network*) "
        "(deny process-fork) "
        "(deny process-exec) "
        f'(allow process-exec (literal "{node_executable}")) '
        "(deny file-read*) "
        f"(allow file-read* {read_rules}) "
        f"(allow file-read-metadata {metadata_rules}) "
        "(deny file-write*) "
        f"(allow file-write* {write_rules})"
    )


def _empty_execution(
    *,
    status: str,
    language: str,
    dependencies: Sequence[str],
    runtime: ScientificSandboxRuntime,
    errors: Sequence[str],
    sandbox_dir: Path,
    code_hash: str,
    project_hash: str,
    resource_limits: Mapping[str, int],
    project_files: Sequence[ScientificProjectFile] = (),
    estimator_bindings: Sequence[ScientificEstimatorBinding] = (),
    estimator_binding_errors: Sequence[str] = (),
    input_artifacts: Sequence[ScientificInputArtifactBinding] = (),
    required_callable_exports: Sequence[str] = (),
    invocation_mode: str = "standalone",
) -> ScientificSandboxExecution:
    backend = "webr" if language == "r" else "pyodide"
    estimator_code_hashes = {
        binding.artifact_id: binding.code_hash for binding in estimator_bindings
    }
    estimator_project_hashes = {
        binding.artifact_id: binding.project_hash for binding in estimator_bindings
    }
    input_artifact_hashes = {
        binding.artifact_id: binding.content_sha256
        for binding in input_artifacts
    }
    return ScientificSandboxExecution(
        status=status,
        language=language,
        execution_profile=SCIENTIFIC_WASM_SANDBOX_PROFILE,
        backend=backend,
        isolation_provider=runtime.isolation_provider,
        dependencies=tuple(dependencies),
        execution_attempted=False,
        returncode=-1,
        metrics={},
        errors=tuple(errors),
        stdout_summary="",
        stderr_summary="; ".join(errors),
        result_parse_error="",
        code_path="",
        request_path="",
        result_path="",
        code_hash=code_hash,
        project_hash=project_hash,
        project_file_hashes={row.path: row.content_sha256 for row in project_files},
        request_hash="",
        result_hash="",
        subprocess_environment_keys=tuple(
            sorted(_scientific_sandbox_environment(sandbox_dir))
        ),
        resource_limits=dict(resource_limits),
        invocation_mode=invocation_mode,
        required_callable_exports=tuple(required_callable_exports),
        estimator_code_hashes=estimator_code_hashes,
        estimator_project_hashes=estimator_project_hashes,
        estimator_binding_hash=(
            stable_hash(estimator_project_hashes)
            if estimator_project_hashes
            else ""
        ),
        estimator_binding_errors=tuple(estimator_binding_errors),
        input_artifact_hashes=input_artifact_hashes,
        input_artifact_binding_hash=(
            stable_hash(input_artifact_hashes)
            if input_artifact_hashes
            else ""
        ),
    )


def execute_scientific_sandbox(
    *,
    sandbox_dir: Path,
    artifact_id: str,
    language: str,
    code: str,
    project_files: Sequence[ScientificProjectFile | Mapping[str, Any]] = (),
    dependencies: Sequence[str],
    seed: int,
    replicates: int,
    timeout_s: int,
    max_output_bytes: int = 16 * 1024 * 1024,
    max_node_heap_mb: int = 768,
    runtime: ScientificSandboxRuntime | None = None,
    estimator_bindings: Sequence[ScientificEstimatorBinding] = (),
    estimator_transport: str = "json_finite",
    input_artifacts: Sequence[ScientificInputArtifactBinding] = (),
    required_callable_exports: Sequence[str] = (),
    entrypoint: str | None = "run_sandbox",
    script_path: str = "",
) -> ScientificSandboxExecution:
    invocation_mode = (
        "script" if entrypoint is None
        else "estimator_bound" if estimator_bindings else "standalone"
    )
    language = normalized_generated_code_language(language)
    dependencies = normalized_scientific_dependencies(
        dependencies,
        language=language,
    )
    project_file_errors = scientific_project_file_errors(
        project_files,
        language=language,
    )
    normalized_project_files = (
        ()
        if project_file_errors
        else normalized_scientific_project_files(project_files, language=language)
    )
    computed_project_hash = (
        scientific_project_hash(
            language=language,
            code=code,
            project_files=normalized_project_files,
        )
        if not project_file_errors
        else ""
    )
    normalized_binding_rows: list[ScientificEstimatorBinding] = []
    binding_project_errors: list[str] = []
    for binding in estimator_bindings:
        binding_language = normalized_generated_code_language(binding.language)
        raw_binding_files = tuple(binding.project_files or ())
        file_errors = scientific_project_file_errors(
            raw_binding_files,
            language=binding_language,
        )
        if file_errors:
            binding_project_errors.extend(
                f"estimator binding {binding.artifact_id}: {error}"
                for error in file_errors
            )
            normalized_binding_files: tuple[ScientificProjectFile, ...] = ()
            computed_binding_project_hash = ""
        else:
            normalized_binding_files = normalized_scientific_project_files(
                raw_binding_files,
                language=binding_language,
            )
            computed_binding_project_hash = scientific_project_hash(
                language=binding_language,
                code=str(binding.code or ""),
                project_files=normalized_binding_files,
            )
        supplied_project_hash = str(binding.project_hash or "").strip()
        if (
            supplied_project_hash
            and computed_binding_project_hash
            and supplied_project_hash != computed_binding_project_hash
        ):
            binding_project_errors.append(
                "estimator binding project hash mismatch: "
                + str(binding.artifact_id or "").strip()
            )
        normalized_binding_rows.append(
            ScientificEstimatorBinding(
                artifact_id=str(binding.artifact_id or "").strip(),
                language=binding_language,
                code=str(binding.code or ""),
                code_hash=str(binding.code_hash or "").strip(),
                dependencies=normalized_scientific_dependencies(
                    binding.dependencies,
                    language=binding_language,
                ),
                project_files=normalized_binding_files,
                project_hash=computed_binding_project_hash,
            )
        )
    normalized_bindings = tuple(normalized_binding_rows)
    normalized_input_artifacts = tuple(
        ScientificInputArtifactBinding(
            artifact_id=str(binding.artifact_id or "").strip(),
            content=str(binding.content or ""),
            content_sha256=str(binding.content_sha256 or "").strip(),
            media_type=str(binding.media_type or "text/plain").strip(),
        )
        for binding in input_artifacts
    )
    normalized_required_callable_exports = tuple(
        dict.fromkeys(
            str(value or "").strip()
            for value in required_callable_exports
            if str(value or "").strip()
        )
    )
    estimator_transport = str(estimator_transport or "json_finite").strip().lower()
    runtime = runtime or discover_scientific_sandbox_runtime()
    limits = _resource_limit_payload(
        timeout_s,
        max_output_bytes,
        max_node_heap_mb,
    )
    code_hash = stable_hash(code)
    contract_errors = generated_code_execution_contract_errors(
        {
            "language": language,
            "execution_profile": SCIENTIFIC_WASM_SANDBOX_PROFILE,
            "dependencies": list(dependencies),
            "entrypoint": entrypoint,
            "code": code,
            "project_files": [row.to_json() for row in normalized_project_files],
        },
        required_entrypoint=entrypoint,
    )
    if entrypoint is not None and entrypoint != "run_sandbox":
        contract_errors.append("scientific entrypoint must be run_sandbox or None")
    if not isinstance(script_path, str) or (script_path and (
        entrypoint is not None
        or script_path not in {scientific_main_path(language), *(row.path for row in normalized_project_files)}
        or not script_path.lower().endswith(".r" if language == "r" else ".py")
    )):
        contract_errors.append("script_path must select an exact current source file in script mode")
    if entrypoint is None and (
        normalized_bindings or normalized_required_callable_exports
    ):
        contract_errors.append(
            "script execution cannot bind estimators or required callable exports"
        )
    contract_errors.extend(project_file_errors)
    if language == "python":
        local_import_roots = (*scientific_python_local_import_roots(normalized_project_files),
                              Path(scientific_main_path(language)).stem)
        contract_errors.extend(
            scientific_python_safety_errors(
                code,
                dependencies=dependencies,
                required_functions=() if entrypoint is None else ("run_sandbox",),
                local_import_roots=local_import_roots,
            )
        )
        for project_file in normalized_project_files:
            if Path(project_file.path).suffix.lower() != ".py":
                continue
            contract_errors.extend(
                scientific_python_safety_errors(
                    project_file.content,
                    dependencies=dependencies,
                    required_functions=(),
                    local_import_roots=local_import_roots,
                )
            )
    binding_contract_errors: list[str] = []
    binding_contract_errors.extend(binding_project_errors)
    binding_ids: set[str] = set()
    for binding in normalized_bindings:
        if not binding.artifact_id:
            binding_contract_errors.append("estimator binding artifact_id is required")
        elif binding.artifact_id in binding_ids:
            binding_contract_errors.append(
                "duplicate estimator binding artifact_id: " + binding.artifact_id
            )
        binding_ids.add(binding.artifact_id)
        if binding.language != language:
            binding_contract_errors.append(
                "estimator binding language must match simulation language: "
                + binding.artifact_id
            )
        if not binding.code.strip():
            binding_contract_errors.append(
                "estimator binding source is empty: " + binding.artifact_id
            )
        if binding.code_hash != stable_hash(binding.code):
            binding_contract_errors.append(
                "estimator binding source hash mismatch: " + binding.artifact_id
            )
        allowed_binding_dependencies = (
            set(PYTHON_SCIENTIFIC_DEPENDENCIES)
            if binding.language == "python"
            else set(R_SCIENTIFIC_DEPENDENCIES)
            if binding.language == "r"
            else set()
        )
        unsupported_binding_dependencies = sorted(
            set(binding.dependencies) - allowed_binding_dependencies
        )
        if unsupported_binding_dependencies:
            binding_contract_errors.append(
                "estimator binding declares unsupported dependencies for "
                + binding.artifact_id
                + ": "
                + ", ".join(unsupported_binding_dependencies)
            )
        if binding.language == "python":
            binding_local_import_roots = scientific_python_local_import_roots(
                binding.project_files
            )
            binding_contract_errors.extend(
                scientific_python_safety_errors(
                    binding.code,
                    dependencies=binding.dependencies,
                    required_functions=("run_estimator",),
                    local_import_roots=binding_local_import_roots,
                )
            )
            for project_file in binding.project_files:
                binding_contract_errors.extend(
                    scientific_python_safety_errors(
                        project_file.content,
                        dependencies=binding.dependencies,
                        required_functions=(),
                        local_import_roots=binding_local_import_roots,
                    )
                )
    contract_errors.extend(binding_contract_errors)
    if estimator_transport not in {"json_finite", "native"}:
        contract_errors.append("estimator transport must be json_finite or native")
    input_artifact_errors: list[str] = []
    input_artifact_ids: set[str] = set()
    total_input_artifact_bytes = 0
    for binding in normalized_input_artifacts:
        if not binding.artifact_id:
            input_artifact_errors.append("input artifact_id is required")
        elif binding.artifact_id in input_artifact_ids:
            input_artifact_errors.append(
                "duplicate input artifact_id: " + binding.artifact_id
            )
        input_artifact_ids.add(binding.artifact_id)
        encoded = binding.content.encode("utf-8")
        total_input_artifact_bytes += len(encoded)
        if binding.content_sha256 != hashlib.sha256(encoded).hexdigest():
            input_artifact_errors.append(
                "input artifact content hash mismatch: " + binding.artifact_id
            )
        if not binding.media_type:
            input_artifact_errors.append(
                "input artifact media_type is required: " + binding.artifact_id
            )
    if total_input_artifact_bytes > MAX_SCIENTIFIC_INPUT_ARTIFACT_BYTES:
        input_artifact_errors.append(
            "input artifacts exceed aggregate artifact-size boundary"
        )
    contract_errors.extend(input_artifact_errors)
    all_dependencies = tuple(
        dict.fromkeys(
            [
                *dependencies,
                *(
                    dependency
                    for binding in normalized_bindings
                    for dependency in binding.dependencies
                ),
            ]
        )
    )
    if contract_errors:
        return _empty_execution(
            status="REJECTED_CONTRACT",
            language=language,
            dependencies=all_dependencies,
            runtime=runtime,
            errors=sorted(set(contract_errors)),
            sandbox_dir=sandbox_dir,
            code_hash=code_hash,
            project_hash=computed_project_hash,
            resource_limits=limits,
            project_files=normalized_project_files,
            estimator_bindings=normalized_bindings,
            estimator_binding_errors=sorted(set(binding_contract_errors)),
            input_artifacts=normalized_input_artifacts,
            required_callable_exports=normalized_required_callable_exports,
            invocation_mode=invocation_mode,
        )
    language_available = (
        runtime.python_available if language == "python" else runtime.r_available
    )
    if not runtime.available or not language_available:
        return _empty_execution(
            status="RUNTIME_UNAVAILABLE",
            language=language,
            dependencies=all_dependencies,
            runtime=runtime,
            errors=(
                "scientific WASM runtime is unavailable; run npm ci and use "
                "a supported no-network isolation provider",
            ),
            sandbox_dir=sandbox_dir,
            code_hash=code_hash,
            project_hash=computed_project_hash,
            resource_limits=limits,
            project_files=normalized_project_files,
            estimator_bindings=normalized_bindings,
            input_artifacts=normalized_input_artifacts,
            required_callable_exports=normalized_required_callable_exports,
            invocation_mode=invocation_mode,
        )
    cache_errors = (
        scientific_python_dependency_cache_errors(runtime, all_dependencies)
        if language == "python"
        else []
    )
    if cache_errors:
        return _empty_execution(
            status="DEPENDENCY_CACHE_UNPREPARED",
            language=language,
            dependencies=all_dependencies,
            runtime=runtime,
            errors=cache_errors,
            sandbox_dir=sandbox_dir,
            code_hash=code_hash,
            project_hash=computed_project_hash,
            resource_limits=limits,
            project_files=normalized_project_files,
            estimator_bindings=normalized_bindings,
            input_artifacts=normalized_input_artifacts,
            required_callable_exports=normalized_required_callable_exports,
            invocation_mode=invocation_mode,
        )

    sandbox_dir.mkdir(parents=True, exist_ok=True)
    safe_id = "".join(
        character if character.isalnum() or character in {"-", "_"} else "_"
        for character in artifact_id
    ).strip("_") or "scientific_draft"
    extension = "R" if language == "r" else "py"
    execution_key = stable_hash(
        {
            "artifact_id": artifact_id,
            "invocation_mode": invocation_mode,
            **({"script_path": script_path} if script_path else {}),
            "language": language,
            "dependencies": list(all_dependencies),
            "seed": int(seed),
            "replicates": int(replicates),
            "code_hash": code_hash,
            "project_hash": computed_project_hash,
            "estimator_bindings": {
                binding.artifact_id: binding.project_hash
                for binding in normalized_bindings
            },
            "estimator_transport": estimator_transport,
            "input_artifacts": {
                binding.artifact_id: binding.content_sha256
                for binding in normalized_input_artifacts
            },
            "required_callable_exports": list(
                normalized_required_callable_exports
            ),
        }
    )[:16]
    code_path = sandbox_dir / f"{safe_id}_{execution_key}_generated_draft.{extension}"
    request_path = sandbox_dir / f"{safe_id}_{execution_key}_scientific_request.json"
    result_path = sandbox_dir / f"{safe_id}_{execution_key}_scientific_result.json"
    metrics_path = sandbox_dir / f"{safe_id}_{execution_key}_scientific_metrics.json"
    stdout_path = sandbox_dir / f"{safe_id}_{execution_key}_stdout.txt"
    stderr_path = sandbox_dir / f"{safe_id}_{execution_key}_stderr.txt"
    code_path.write_text(code, encoding="utf-8")
    project_root = sandbox_dir / f"{safe_id}_{execution_key}_project"
    project_file_paths: dict[str, Path] = {}
    for project_file in normalized_project_files:
        support_path = project_root / project_file.path
        support_path.parent.mkdir(parents=True, exist_ok=True)
        support_path.write_text(project_file.content, encoding="utf-8")
        project_file_paths[project_file.path] = support_path
    estimator_code_paths: dict[str, Path] = {}
    estimator_project_file_paths: dict[str, dict[str, Path]] = {}
    for index, binding in enumerate(normalized_bindings):
        estimator_path = sandbox_dir / (
            f"{safe_id}_{execution_key}_estimator_{index}.{extension}"
        )
        estimator_path.write_text(binding.code, encoding="utf-8")
        estimator_code_paths[binding.artifact_id] = estimator_path
        estimator_project_root = sandbox_dir / (
            f"{safe_id}_{execution_key}_estimator_{index}_project"
        )
        estimator_project_file_paths[binding.artifact_id] = {}
        for project_file in binding.project_files:
            support_path = estimator_project_root / project_file.path
            support_path.parent.mkdir(parents=True, exist_ok=True)
            support_path.write_text(project_file.content, encoding="utf-8")
            estimator_project_file_paths[binding.artifact_id][
                project_file.path
            ] = support_path
    input_artifact_paths: dict[str, Path] = {}
    for index, binding in enumerate(normalized_input_artifacts):
        input_path = sandbox_dir / (
            f"{safe_id}_{execution_key}_input_{index}.txt"
        )
        input_path.write_text(binding.content, encoding="utf-8")
        input_artifact_paths[binding.artifact_id] = input_path
    result_path.unlink(missing_ok=True)
    metrics_path.unlink(missing_ok=True)
    stdout_path.unlink(missing_ok=True)
    stderr_path.unlink(missing_ok=True)
    request = {
        "schema_version": 1,
        "artifact_kind": "ScientificSandboxExecutionRequest",
        "artifact_id": artifact_id,
        "language": language,
        "execution_profile": SCIENTIFIC_WASM_SANDBOX_PROFILE,
        "backend": "webr" if language == "r" else "pyodide",
        "dependencies": list(all_dependencies),
        "seed": int(seed),
        "replicates": int(replicates),
        "code_path": str(code_path.resolve()),
        "code_hash": code_hash,
        "code_sha256": hashlib.sha256(code.encode("utf-8")).hexdigest(),
        "main_path": scientific_main_path(language),
        "project_hash": computed_project_hash,
        "project_files": [
            {
                "path": project_file.path,
                "content_path": str(
                    project_file_paths[project_file.path].resolve()
                ),
                "sha256": project_file.content_sha256,
            }
            for project_file in normalized_project_files
        ],
        "invocation_mode": invocation_mode,
        **({"script_path": script_path} if script_path else {}),
        "estimator_transport": estimator_transport,
        "required_callable_exports": list(
            normalized_required_callable_exports
        ),
        "estimators": [
            {
                "artifact_id": binding.artifact_id,
                "language": binding.language,
                "dependencies": list(binding.dependencies),
                "code_path": str(estimator_code_paths[binding.artifact_id].resolve()),
                "code_hash": binding.code_hash,
                "code_sha256": hashlib.sha256(
                    binding.code.encode("utf-8")
                ).hexdigest(),
                "main_path": scientific_main_path(binding.language),
                "project_hash": binding.project_hash,
                "project_files": [
                    {
                        "path": project_file.path,
                        "content_path": str(
                            estimator_project_file_paths[binding.artifact_id][
                                project_file.path
                            ].resolve()
                        ),
                        "sha256": project_file.content_sha256,
                    }
                    for project_file in binding.project_files
                ],
            }
            for binding in normalized_bindings
        ],
        "input_artifacts": [
            {
                "artifact_id": binding.artifact_id,
                "media_type": binding.media_type,
                "path": str(
                    input_artifact_paths[binding.artifact_id].resolve()
                ),
                "sha256": binding.content_sha256,
                "size_bytes": len(binding.content.encode("utf-8")),
            }
            for binding in normalized_input_artifacts
        ],
        "runtime": {
            "pyodide_entry": runtime.pyodide_entry,
            "pyodide_root": runtime.pyodide_root,
            "webr_entry": runtime.webr_entry,
        },
        "network_access": False,
        "secret_environment_inherited": False,
        "host_filesystem_policy": (
            "read pinned runtimes plus exact code/request artifacts; write exact "
            "result/log artifacts only"
        ),
        "resource_limits": limits,
        "proof_evidence_status": "SCIENTIFIC_SANDBOX_REQUEST_NOT_PROOF_EVIDENCE",
    }
    request_path.write_text(
        json.dumps(request, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    request_hash = stable_hash(request)
    node_command = [
        runtime.node_executable,
        f"--max-old-space-size={max(128, int(max_node_heap_mb))}",
        runtime.runner_path,
        "--request",
        str(request_path.resolve()),
        "--out",
        str(result_path.resolve()),
    ]
    command = [
        str(shutil.which("sandbox-exec")),
        "-p",
        _macos_sandbox_profile(
            runtime=runtime,
            readable_paths=(
                code_path,
                request_path,
                *project_file_paths.values(),
                *estimator_code_paths.values(),
                *(
                    path
                    for paths in estimator_project_file_paths.values()
                    for path in paths.values()
                ),
                *input_artifact_paths.values(),
            ),
            writable_paths=(result_path, stdout_path, stderr_path),
        ),
        *node_command,
    ]
    environment = _scientific_sandbox_environment(sandbox_dir)
    returncode = -1
    stdout = ""
    stderr = ""
    try:
        with stdout_path.open("w", encoding="utf-8") as stdout_file, stderr_path.open(
            "w", encoding="utf-8"
        ) as stderr_file:
            completed = subprocess.run(
                command,
                cwd=str(sandbox_dir),
                env=environment,
                check=False,
                stdout=stdout_file,
                stderr=stderr_file,
                text=True,
                timeout=max(1, int(timeout_s)),
                preexec_fn=_resource_limiter(limits),
            )
        returncode = int(completed.returncode)
    except subprocess.TimeoutExpired:
        returncode = 124
        stderr = f"timeout after {timeout_s}s"
    except Exception as exc:  # pragma: no cover - defensive transport failure
        returncode = 125
        stderr = repr(exc)
    if stdout_path.exists():
        stdout = stdout_path.read_text(encoding="utf-8", errors="replace").strip()
    if stderr_path.exists():
        persisted_stderr = stderr_path.read_text(
            encoding="utf-8", errors="replace"
        ).strip()
        stderr = "\n".join(row for row in (stderr, persisted_stderr) if row)

    envelope: dict[str, Any] = {}
    result_parse_error = ""
    if result_path.exists():
        try:
            loaded = json.loads(result_path.read_text(encoding="utf-8"))
            envelope = dict(loaded) if isinstance(loaded, Mapping) else {}
        except Exception as exc:  # pragma: no cover - defensive artifact parsing
            result_parse_error = repr(exc)
    if invocation_mode == "script" and envelope:
        stdout = str(envelope.get("stdout", ""))
    metrics = (
        dict(envelope.get("metrics", {}))
        if isinstance(envelope.get("metrics", {}), Mapping)
        else {}
    )
    raw_invocation_counts = envelope.get("estimator_invocation_counts", {})
    estimator_invocation_counts = (
        {
            str(key): max(0, int(value or 0))
            for key, value in raw_invocation_counts.items()
        }
        if isinstance(raw_invocation_counts, Mapping)
        else {}
    )
    raw_invocation_samples = envelope.get("estimator_invocation_samples", {})
    estimator_invocation_samples = (
        {
            str(key): [
                dict(row)
                for row in list(value)[:3]
                if isinstance(row, Mapping)
            ]
            for key, value in raw_invocation_samples.items()
            if isinstance(value, (list, tuple))
        }
        if isinstance(raw_invocation_samples, Mapping)
        else {}
    )
    if metrics:
        metrics_path.write_text(
            json.dumps(metrics, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    errors: list[str] = []
    runtime_estimator_binding_errors: tuple[str, ...] = ()
    estimator_runtime_failure_ids: tuple[str, ...] = ()
    estimator_runtime_errors: tuple[str, ...] = ()
    if not envelope:
        errors.append("scientific sandbox did not produce an execution envelope")
    elif envelope.get("ok") is not True:
        envelope_error = (
            str(envelope.get("error_type", "ScientificSandboxError") or "")
            + ": "
            + str(envelope.get("error_message", "execution failed") or "")
        )
        errors.append(envelope_error)
        error_origin = str(envelope.get("error_origin", "") or "")
        if error_origin == "accepted_estimator_binding":
            runtime_estimator_binding_errors = (envelope_error,)
        elif error_origin == "accepted_estimator":
            failure_id = str(
                envelope.get("error_artifact_id", "") or ""
            ).strip()
            if failure_id:
                estimator_runtime_failure_ids = (failure_id,)
                estimator_runtime_errors = (envelope_error,)
    if returncode != 0 and not errors:
        errors.append(f"scientific sandbox subprocess exited {returncode}")
    if result_parse_error:
        errors.append("scientific sandbox result parse failed: " + result_parse_error)
    if normalized_bindings:
        missing_invocations = [
            binding.artifact_id
            for binding in normalized_bindings
            if estimator_invocation_counts.get(binding.artifact_id, 0) <= 0
        ]
        if missing_invocations:
            errors.append(
                "bound estimator source was not invoked: "
                + ", ".join(missing_invocations)
            )
    status = (
        "EXECUTED"
        if returncode == 0 and envelope.get("ok") is True and not errors
        else "FAILED"
    )
    estimator_code_hashes = {
        binding.artifact_id: binding.code_hash for binding in normalized_bindings
    }
    estimator_project_hashes = {
        binding.artifact_id: binding.project_hash for binding in normalized_bindings
    }
    input_artifact_hashes = {
        binding.artifact_id: binding.content_sha256
        for binding in normalized_input_artifacts
    }
    return ScientificSandboxExecution(
        status=status,
        language=language,
        execution_profile=SCIENTIFIC_WASM_SANDBOX_PROFILE,
        backend="webr" if language == "r" else "pyodide",
        isolation_provider=runtime.isolation_provider,
        dependencies=tuple(all_dependencies),
        execution_attempted=True,
        returncode=returncode,
        metrics=metrics,
        errors=tuple(errors),
        stdout_summary=stdout,
        stderr_summary=(stderr + "\n" + str(envelope.get("error_stack", ""))).strip(),
        result_parse_error=result_parse_error,
        code_path=str(code_path),
        request_path=str(request_path),
        result_path=str(metrics_path if metrics else result_path),
        code_hash=code_hash,
        project_hash=computed_project_hash,
        project_file_paths={
            path: str(file_path) for path, file_path in project_file_paths.items()
        },
        project_file_hashes={
            row.path: row.content_sha256 for row in normalized_project_files
        },
        request_hash=request_hash,
        result_hash=(
            stable_hash(envelope) if invocation_mode == "script" and envelope
            else stable_hash(metrics) if metrics else ""
        ),
        subprocess_environment_keys=tuple(sorted(environment)),
        resource_limits=dict(limits),
        execution_envelope_path=str(result_path),
        execution_envelope_hash=stable_hash(envelope) if envelope else "",
        invocation_mode=invocation_mode,
        required_callable_exports=normalized_required_callable_exports,
        estimator_code_paths={
            artifact_id: str(path)
            for artifact_id, path in estimator_code_paths.items()
        },
        estimator_code_hashes=estimator_code_hashes,
        estimator_project_hashes=estimator_project_hashes,
        estimator_invocation_counts=estimator_invocation_counts,
        estimator_invocation_samples=estimator_invocation_samples,
        estimator_binding_hash=(
            stable_hash(estimator_project_hashes)
            if estimator_project_hashes
            else ""
        ),
        estimator_binding_errors=runtime_estimator_binding_errors,
        estimator_runtime_failure_ids=estimator_runtime_failure_ids,
        estimator_runtime_errors=estimator_runtime_errors,
        input_artifact_paths={
            artifact_id: str(path)
            for artifact_id, path in input_artifact_paths.items()
        },
        input_artifact_hashes=input_artifact_hashes,
        input_artifact_binding_hash=(
            stable_hash(input_artifact_hashes)
            if input_artifact_hashes
            else ""
        ),
    )
