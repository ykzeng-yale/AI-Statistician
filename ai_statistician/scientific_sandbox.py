from __future__ import annotations

import ast
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
)
R_SCIENTIFIC_DEPENDENCIES = (
    "base",
    "stats",
    "utils",
    "methods",
)
_PYTHON_PACKAGE_IMPORT_ROOTS = {
    "numpy": {"numpy"},
    "scipy": {"scipy"},
    "pandas": {"pandas"},
    "scikit-learn": {"sklearn"},
    "statsmodels": {"statsmodels", "patsy"},
}
_PYTHON_PACKAGE_CACHE_PREFIXES = {
    "numpy": ("numpy-",),
    "scipy": ("scipy-",),
    "pandas": ("pandas-", "python_dateutil-", "pytz-", "six-"),
    "scikit-learn": ("scikit_learn-", "joblib-", "threadpoolctl-"),
    "statsmodels": ("statsmodels-", "patsy-", "packaging-"),
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
    execution_envelope_path: str = ""
    execution_envelope_hash: str = ""
    invocation_mode: str = "standalone"
    estimator_code_paths: dict[str, str] = field(default_factory=dict)
    estimator_code_hashes: dict[str, str] = field(default_factory=dict)
    estimator_invocation_counts: dict[str, int] = field(default_factory=dict)
    estimator_binding_hash: str = ""
    estimator_binding_errors: tuple[str, ...] = ()
    estimator_runtime_failure_ids: tuple[str, ...] = ()
    estimator_runtime_errors: tuple[str, ...] = ()
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


def generated_code_execution_contract_errors(draft: Mapping[str, Any]) -> list[str]:
    language = normalized_generated_code_language(draft.get("language"))
    profile = normalized_generated_code_profile(
        draft.get("execution_profile"),
        language=language,
    )
    dependencies = normalized_scientific_dependencies(
        draft.get("dependencies", []),
        language=language,
    )
    errors: list[str] = []
    if language not in SCIENTIFIC_SANDBOX_LANGUAGES:
        errors.append("generated code language must be python or r")
    if profile not in SCIENTIFIC_SANDBOX_PROFILES:
        errors.append("generated code execution_profile must be stdlib or scientific_wasm")
    if language == "r" and profile != SCIENTIFIC_WASM_SANDBOX_PROFILE:
        errors.append("generated R code requires execution_profile scientific_wasm")
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
    if str(draft.get("entrypoint", "") or "").strip() != "run_sandbox":
        errors.append("generated code entrypoint must be run_sandbox")
    code = str(draft.get("code", "") or "")
    if not code.strip():
        errors.append("generated code draft is empty")
    if len(code) > 40000:
        errors.append("generated code draft exceeds 40000 characters")
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


def scientific_python_safety_errors(
    code: str,
    *,
    dependencies: Sequence[str],
    required_functions: Sequence[str] = ("run_sandbox",),
) -> list[str]:
    if not str(code or "").strip():
        return ["empty generated scientific Python draft"]
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return [f"generated scientific Python draft syntax error: {exc}"]
    allowed_roots = {"math", "random", "statistics"}
    for dependency in dependencies:
        allowed_roots.update(_PYTHON_PACKAGE_IMPORT_ROOTS.get(dependency, set()))
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
        "open",
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
                if root not in allowed_roots or root in forbidden_roots:
                    errors.append(
                        "generated scientific Python import is not declared: " + alias.name
                    )
        elif isinstance(node, ast.ImportFrom):
            root = str(node.module or "").split(".", 1)[0]
            if node.level or root not in allowed_roots or root in forbidden_roots:
                errors.append(
                    "generated scientific Python from-import is not declared: "
                    + str(node.module or "")
                )
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            errors.append("generated scientific Python cannot use global/nonlocal")
        elif isinstance(node, ast.Name) and node.id.startswith("__"):
            errors.append("generated scientific Python cannot access dunder names")
        elif isinstance(node, ast.Attribute) and node.attr.startswith("_"):
            errors.append(
                "generated scientific Python cannot access private attributes: "
                + node.attr
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
                "boundary": "Existing pure-Python conservative AST sandbox.",
            },
            SCIENTIFIC_WASM_SANDBOX_PROFILE: {
                "languages": ["python", "r"],
                "python_dependencies": list(PYTHON_SCIENTIFIC_DEPENDENCIES),
                "r_dependencies": list(R_SCIENTIFIC_DEPENDENCIES),
                "entrypoint": "run_sandbox",
                "function_contract": (
                    "run_sandbox(seed, replicates) returns a named JSON-finite metric object"
                ),
                "estimator_binding_contract": (
                    "A confirmatory DGP harness defines run_sandbox(seed, replicates, "
                    "estimators). Each exact reviewed algorithm defines "
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
            "Use stdlib for genuinely small self-contained procedures."
        ),
        "proof_evidence_status": "SCIENTIFIC_SANDBOX_CONTRACT_NOT_PROOF_EVIDENCE",
    }


def generated_code_draft_json_schema(
    *,
    artifact_properties: Mapping[str, Any],
    artifact_required: Sequence[str],
    code_max_length: int = 12000,
) -> dict[str, Any]:
    """Bind generated-code metadata to one executable sandbox profile."""

    common_required = [
        *[str(value) for value in artifact_required],
        "language",
        "execution_profile",
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
    }

    def branch(
        *,
        language: str,
        execution_profile: str,
        dependencies: Sequence[str] | None,
    ) -> dict[str, Any]:
        properties = {
            **common_properties,
            "language": {"type": "string", "enum": [language]},
            "execution_profile": {
                "type": "string",
                "enum": [execution_profile],
            },
        }
        required = list(common_required)
        if dependencies is not None:
            properties["dependencies"] = {
                "type": "array",
                "uniqueItems": True,
                "items": {
                    "type": "string",
                    "enum": [str(value) for value in dependencies],
                },
            }
            required.append("dependencies")
        return {
            "type": "object",
            "additionalProperties": False,
            "required": required,
            "properties": properties,
        }

    return {
        "anyOf": [
            branch(
                language="python",
                execution_profile=STDLIB_SANDBOX_PROFILE,
                dependencies=None,
            ),
            branch(
                language="python",
                execution_profile=SCIENTIFIC_WASM_SANDBOX_PROFILE,
                dependencies=PYTHON_SCIENTIFIC_DEPENDENCIES,
            ),
            branch(
                language="r",
                execution_profile=SCIENTIFIC_WASM_SANDBOX_PROFILE,
                dependencies=R_SCIENTIFIC_DEPENDENCIES,
            ),
        ]
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
    resource_limits: Mapping[str, int],
    estimator_bindings: Sequence[ScientificEstimatorBinding] = (),
    estimator_binding_errors: Sequence[str] = (),
) -> ScientificSandboxExecution:
    backend = "webr" if language == "r" else "pyodide"
    estimator_code_hashes = {
        binding.artifact_id: binding.code_hash for binding in estimator_bindings
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
        stderr_summary="; ".join(errors)[:4000],
        result_parse_error="",
        code_path="",
        request_path="",
        result_path="",
        code_hash=code_hash,
        request_hash="",
        result_hash="",
        subprocess_environment_keys=tuple(
            sorted(_scientific_sandbox_environment(sandbox_dir))
        ),
        resource_limits=dict(resource_limits),
        invocation_mode="estimator_bound" if estimator_bindings else "standalone",
        estimator_code_hashes=estimator_code_hashes,
        estimator_binding_hash=(
            stable_hash(estimator_code_hashes) if estimator_code_hashes else ""
        ),
        estimator_binding_errors=tuple(estimator_binding_errors),
    )


def execute_scientific_sandbox(
    *,
    sandbox_dir: Path,
    artifact_id: str,
    language: str,
    code: str,
    dependencies: Sequence[str],
    seed: int,
    replicates: int,
    timeout_s: int,
    max_output_bytes: int = 16 * 1024 * 1024,
    max_node_heap_mb: int = 768,
    runtime: ScientificSandboxRuntime | None = None,
    estimator_bindings: Sequence[ScientificEstimatorBinding] = (),
) -> ScientificSandboxExecution:
    language = normalized_generated_code_language(language)
    dependencies = normalized_scientific_dependencies(
        dependencies,
        language=language,
    )
    normalized_bindings = tuple(
        ScientificEstimatorBinding(
            artifact_id=str(binding.artifact_id or "").strip(),
            language=normalized_generated_code_language(binding.language),
            code=str(binding.code or ""),
            code_hash=str(binding.code_hash or "").strip(),
            dependencies=normalized_scientific_dependencies(
                binding.dependencies,
                language=normalized_generated_code_language(binding.language),
            ),
        )
        for binding in estimator_bindings
    )
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
            "entrypoint": "run_sandbox",
            "code": code,
        }
    )
    if language == "python":
        contract_errors.extend(
            scientific_python_safety_errors(code, dependencies=dependencies)
        )
    binding_contract_errors: list[str] = []
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
            binding_contract_errors.extend(
                scientific_python_safety_errors(
                    binding.code,
                    dependencies=binding.dependencies,
                    required_functions=("run_estimator",),
                )
            )
    contract_errors.extend(binding_contract_errors)
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
            resource_limits=limits,
            estimator_bindings=normalized_bindings,
            estimator_binding_errors=sorted(set(binding_contract_errors)),
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
            resource_limits=limits,
            estimator_bindings=normalized_bindings,
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
            resource_limits=limits,
            estimator_bindings=normalized_bindings,
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
            "language": language,
            "dependencies": list(all_dependencies),
            "seed": int(seed),
            "replicates": int(replicates),
            "code_hash": code_hash,
            "estimator_bindings": {
                binding.artifact_id: binding.code_hash
                for binding in normalized_bindings
            },
        }
    )[:16]
    code_path = sandbox_dir / f"{safe_id}_{execution_key}_generated_draft.{extension}"
    request_path = sandbox_dir / f"{safe_id}_{execution_key}_scientific_request.json"
    result_path = sandbox_dir / f"{safe_id}_{execution_key}_scientific_result.json"
    metrics_path = sandbox_dir / f"{safe_id}_{execution_key}_scientific_metrics.json"
    stdout_path = sandbox_dir / f"{safe_id}_{execution_key}_stdout.txt"
    stderr_path = sandbox_dir / f"{safe_id}_{execution_key}_stderr.txt"
    code_path.write_text(code, encoding="utf-8")
    estimator_code_paths: dict[str, Path] = {}
    for index, binding in enumerate(normalized_bindings):
        estimator_path = sandbox_dir / (
            f"{safe_id}_{execution_key}_estimator_{index}.{extension}"
        )
        estimator_path.write_text(binding.code, encoding="utf-8")
        estimator_code_paths[binding.artifact_id] = estimator_path
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
        "invocation_mode": (
            "estimator_bound" if normalized_bindings else "standalone"
        ),
        "estimators": [
            {
                "artifact_id": binding.artifact_id,
                "language": binding.language,
                "dependencies": list(binding.dependencies),
                "code_path": str(estimator_code_paths[binding.artifact_id].resolve()),
                "code_hash": binding.code_hash,
            }
            for binding in normalized_bindings
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
                *estimator_code_paths.values(),
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
    if metrics:
        metrics_path.write_text(
            json.dumps(metrics, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    errors: list[str] = []
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
        if str(envelope.get("error_origin", "") or "") == "accepted_estimator":
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
        stdout_summary=stdout[:4000],
        stderr_summary=(stderr + "\n" + str(envelope.get("error_stack", ""))).strip()[:8000],
        result_parse_error=result_parse_error,
        code_path=str(code_path),
        request_path=str(request_path),
        result_path=str(metrics_path if metrics else result_path),
        code_hash=code_hash,
        request_hash=request_hash,
        result_hash=stable_hash(metrics) if metrics else "",
        subprocess_environment_keys=tuple(sorted(environment)),
        resource_limits=dict(limits),
        execution_envelope_path=str(result_path),
        execution_envelope_hash=stable_hash(envelope) if envelope else "",
        invocation_mode=(
            "estimator_bound" if normalized_bindings else "standalone"
        ),
        estimator_code_paths={
            artifact_id: str(path)
            for artifact_id, path in estimator_code_paths.items()
        },
        estimator_code_hashes=estimator_code_hashes,
        estimator_invocation_counts=estimator_invocation_counts,
        estimator_binding_hash=(
            stable_hash(estimator_code_hashes) if estimator_code_hashes else ""
        ),
        estimator_runtime_failure_ids=estimator_runtime_failure_ids,
        estimator_runtime_errors=estimator_runtime_errors,
    )
