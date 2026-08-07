import fs from "node:fs";
import { pathToFileURL } from "node:url";

function finiteJsonValue(value) {
  if (value === null || typeof value === "boolean" || typeof value === "string") {
    return true;
  }
  if (typeof value === "number") {
    return Number.isFinite(value);
  }
  if (Array.isArray(value)) {
    return value.every(finiteJsonValue);
  }
  if (typeof value === "object") {
    return Object.entries(value).every(
      ([key, item]) => typeof key === "string" && finiteJsonValue(item),
    );
  }
  return false;
}

function rValueToJson(node) {
  if (node === null || typeof node !== "object") {
    return node;
  }
  const values = Array.isArray(node.values) ? node.values : [];
  const names = Array.isArray(node.names) ? node.names : null;
  if (node.type === "list" || node.type === "dataframe") {
    const converted = values.map(rValueToJson);
    if (names && names.length === converted.length) {
      return Object.fromEntries(names.map((name, index) => [String(name), converted[index]]));
    }
    return converted;
  }
  const converted = values.map(rValueToJson);
  if (names && names.length === converted.length) {
    return Object.fromEntries(names.map((name, index) => [String(name), converted[index]]));
  }
  if (converted.length === 1) {
    return converted[0];
  }
  return converted;
}

async function runPython(request, source, estimatorSources) {
  const moduleUrl = pathToFileURL(request.runtime.pyodide_entry).href;
  const { loadPyodide } = await import(moduleUrl);
  const pyodide = await loadPyodide({ indexURL: `${request.runtime.pyodide_root}/` });
  if (request.dependencies.length > 0) {
    await pyodide.loadPackage(request.dependencies);
  }
  const bound = request.invocation_mode === "estimator_bound";
  const wrapped = bound
    ? `import json as _ai_stat_json\n` +
      `_ai_stat_simulation_source = ${JSON.stringify(source)}\n` +
      `_ai_stat_estimator_sources = _ai_stat_json.loads(${JSON.stringify(JSON.stringify(estimatorSources))})\n` +
      `_ai_stat_simulation_namespace = {}\n` +
      `exec(compile(_ai_stat_simulation_source, "<generated_simulation>", "exec"), _ai_stat_simulation_namespace, _ai_stat_simulation_namespace)\n` +
      `_ai_stat_invocation_counts = {key: 0 for key in _ai_stat_estimator_sources}\n` +
      `_ai_stat_runtime_failure = {"artifact_id": "", "error_message": ""}\n` +
      `_ai_stat_estimators = {}\n` +
      `def _ai_stat_json_native(_value):\n` +
      `    if _value is None or isinstance(_value, (bool, int, float, str)):\n` +
      `        return _value\n` +
      `    if isinstance(_value, dict):\n` +
      `        if not all(isinstance(_key, str) for _key in _value):\n` +
      `            raise TypeError("estimator request and response object keys must be strings")\n` +
      `        return {_key: _ai_stat_json_native(_item) for _key, _item in _value.items()}\n` +
      `    if isinstance(_value, (list, tuple)):\n` +
      `        return [_ai_stat_json_native(_item) for _item in _value]\n` +
      `    _tolist = getattr(_value, "tolist", None)\n` +
      `    if callable(_tolist):\n` +
      `        return _ai_stat_json_native(_tolist())\n` +
      `    _scalar_item = getattr(_value, "item", None)\n` +
      `    if callable(_scalar_item):\n` +
      `        return _ai_stat_json_native(_scalar_item())\n` +
      `    raise TypeError("estimator request and response values must be JSON-native or array-like")\n` +
      `def _ai_stat_bind_estimator(_artifact_id, _source):\n` +
      `    _namespace = {}\n` +
      `    exec(compile(_source, "<accepted_algorithm:" + _artifact_id + ">", "exec"), _namespace, _namespace)\n` +
      `    _implementation = _namespace.get("run_estimator")\n` +
      `    if not callable(_implementation):\n` +
      `        raise RuntimeError("accepted algorithm did not define callable run_estimator: " + _artifact_id)\n` +
      `    def _bound_estimator(request):\n` +
      `        if not isinstance(request, dict):\n` +
      `            raise TypeError("run_estimator request must be a dict: " + _artifact_id)\n` +
      `        try:\n` +
      `            normalized_request = _ai_stat_json_native(request)\n` +
      `            _ai_stat_json.dumps(normalized_request, allow_nan=False, sort_keys=True)\n` +
      `            raw_response = _implementation(normalized_request)\n` +
      `            if not isinstance(raw_response, dict):\n` +
      `                raise TypeError("run_estimator response must be a dict")\n` +
      `            response = _ai_stat_json_native(raw_response)\n` +
      `            _ai_stat_json.dumps(response, allow_nan=False, sort_keys=True)\n` +
      `        except Exception as exc:\n` +
      `            failure_message = "ACCEPTED_ESTIMATOR_RUNTIME_ERROR: " + _artifact_id + ": " + type(exc).__name__ + ": " + str(exc)\n` +
      `            if not _ai_stat_runtime_failure["artifact_id"]:\n` +
      `                _ai_stat_runtime_failure["artifact_id"] = _artifact_id\n` +
      `                _ai_stat_runtime_failure["error_message"] = failure_message\n` +
      `            raise RuntimeError(failure_message) from exc\n` +
      `        _ai_stat_invocation_counts[_artifact_id] += 1\n` +
      `        return response\n` +
      `    return _bound_estimator\n` +
      `for _ai_stat_id, _ai_stat_source in _ai_stat_estimator_sources.items():\n` +
      `    _ai_stat_estimators[_ai_stat_id] = _ai_stat_bind_estimator(_ai_stat_id, _ai_stat_source)\n` +
      `_ai_stat_run_sandbox = _ai_stat_simulation_namespace.get("run_sandbox")\n` +
      `if not callable(_ai_stat_run_sandbox):\n` +
      `    raise RuntimeError("generated simulation did not define callable run_sandbox")\n` +
      `_ai_stat_result = _ai_stat_run_sandbox(seed=${Number(request.seed)}, replicates=${Number(request.replicates)}, estimators=_ai_stat_estimators)\n` +
      `_ai_stat_json.dumps({"metrics": _ai_stat_result, "estimator_invocation_counts": _ai_stat_invocation_counts, "estimator_runtime_failure": _ai_stat_runtime_failure}, allow_nan=False, sort_keys=True)`
    : `${source}\n\nimport json as _ai_stat_json\n` +
      `_ai_stat_result = run_sandbox(seed=${Number(request.seed)}, replicates=${Number(request.replicates)})\n` +
      `_ai_stat_json.dumps({"metrics": _ai_stat_result, "estimator_invocation_counts": {}}, allow_nan=False, sort_keys=True)`;
  const serialized = await pyodide.runPythonAsync(wrapped);
  return JSON.parse(String(serialized));
}

async function runR(request, source, estimatorSources) {
  const moduleUrl = pathToFileURL(request.runtime.webr_entry).href;
  const { WebR } = await import(moduleUrl);
  const webR = new WebR();
  await webR.init();
  let result;
  try {
    const bound = request.invocation_mode === "estimator_bound";
    const estimatorRows = Object.entries(estimatorSources);
    const estimatorSourceList = estimatorRows
      .map(([artifactId, estimatorSource]) => `${JSON.stringify(artifactId)}=${JSON.stringify(estimatorSource)}`)
      .join(",");
    const wrapped = bound
      ? `local({\n` +
        `.ai_stat_simulation_source <- ${JSON.stringify(source)}\n` +
        `.ai_stat_estimator_sources <- list(${estimatorSourceList})\n` +
        `.ai_stat_simulation_environment <- new.env(parent=globalenv())\n` +
        `eval(parse(text=.ai_stat_simulation_source), envir=.ai_stat_simulation_environment)\n` +
        `.ai_stat_invocation_counts <- setNames(as.list(rep(0L, length(.ai_stat_estimator_sources))), names(.ai_stat_estimator_sources))\n` +
        `.ai_stat_runtime_failure <- list(artifact_id="", error_message="")\n` +
        `.ai_stat_json_finite <- function(value) {\n` +
        `  if (is.null(value)) return(TRUE)\n` +
        `  if (is.list(value)) return(all(vapply(value, .ai_stat_json_finite, logical(1))))\n` +
        `  if (is.numeric(value)) return(length(value) > 0L && all(is.finite(value)))\n` +
        `  if (is.character(value) || is.logical(value)) return(length(value) > 0L && !anyNA(value))\n` +
        `  FALSE\n` +
        `}\n` +
        `.ai_stat_estimators <- lapply(names(.ai_stat_estimator_sources), function(.artifact_id) {\n` +
        `  local({\n` +
        `    .id <- .artifact_id\n` +
        `    .environment <- new.env(parent=globalenv())\n` +
        `    eval(parse(text=.ai_stat_estimator_sources[[.id]]), envir=.environment)\n` +
        `    if (!exists("run_estimator", envir=.environment, mode="function", inherits=FALSE)) stop(paste("accepted algorithm did not define callable run_estimator:", .id))\n` +
        `    .implementation <- get("run_estimator", envir=.environment, inherits=FALSE)\n` +
        `    function(request) {\n` +
        `      if (!is.list(request) || is.null(names(request))) stop(paste("run_estimator request must be a named list:", .id))\n` +
        `      if (!.ai_stat_json_finite(request)) stop(paste("run_estimator request must contain finite JSON-compatible values:", .id))\n` +
        `      .response <- tryCatch({\n` +
        `        .candidate <- .implementation(request)\n` +
        `        if (!is.list(.candidate) || is.null(names(.candidate))) stop("run_estimator response must be a named list")\n` +
        `        if (!.ai_stat_json_finite(.candidate)) stop("run_estimator response must contain finite JSON-compatible values")\n` +
        `        .candidate\n` +
        `      }, error=function(.error) {\n` +
        `        .message <- paste0("ACCEPTED_ESTIMATOR_RUNTIME_ERROR: ", .id, ": ", class(.error)[[1]], ": ", conditionMessage(.error))\n` +
        `        if (!nzchar(.ai_stat_runtime_failure$artifact_id)) .ai_stat_runtime_failure <<- list(artifact_id=.id, error_message=.message)\n` +
        `        stop(.message, call.=FALSE)\n` +
        `      })\n` +
        `      .ai_stat_invocation_counts[[.id]] <<- .ai_stat_invocation_counts[[.id]] + 1L\n` +
        `      .response\n` +
        `    }\n` +
        `  })\n` +
        `})\n` +
        `names(.ai_stat_estimators) <- names(.ai_stat_estimator_sources)\n` +
        `if (!exists("run_sandbox", envir=.ai_stat_simulation_environment, mode="function", inherits=FALSE)) stop("generated simulation did not define callable run_sandbox")\n` +
        `.ai_stat_result <- get("run_sandbox", envir=.ai_stat_simulation_environment, inherits=FALSE)(seed=${Number(request.seed)}, replicates=${Number(request.replicates)}, estimators=.ai_stat_estimators)\n` +
        `list(metrics=.ai_stat_result, estimator_invocation_counts=.ai_stat_invocation_counts, estimator_runtime_failure=.ai_stat_runtime_failure)\n` +
        `})`
      : `${source}\n\n` +
        `local({ .ai_stat_result <- run_sandbox(seed=${Number(request.seed)}, replicates=${Number(request.replicates)}); list(metrics=.ai_stat_result, estimator_invocation_counts=list()) })`;
    result = await webR.evalR(wrapped);
    return rValueToJson(await result.toJs());
  } finally {
    if (result) {
      await webR.destroy(result);
    }
    webR.close();
  }
}

function parseArgs(argv) {
  const args = {};
  for (let index = 0; index < argv.length; index += 2) {
    args[argv[index]] = argv[index + 1];
  }
  return args;
}

const args = parseArgs(process.argv.slice(2));
const requestPath = args["--request"];
const outputPath = args["--out"];
if (!requestPath || !outputPath) {
  throw new Error("scientific sandbox runner requires --request and --out");
}

const request = JSON.parse(fs.readFileSync(requestPath, "utf8"));
const source = fs.readFileSync(request.code_path, "utf8");
const estimatorSources = Object.fromEntries(
  (Array.isArray(request.estimators) ? request.estimators : []).map((row) => [
    String(row.artifact_id),
    fs.readFileSync(row.code_path, "utf8"),
  ]),
);
const startedAt = new Date().toISOString();
let envelope;
try {
  const execution = request.language === "r"
    ? await runR(request, source, estimatorSources)
    : await runPython(request, source, estimatorSources);
  const metrics = execution?.metrics;
  const estimatorInvocationCounts = execution?.estimator_invocation_counts || {};
  const estimatorRuntimeFailure = execution?.estimator_runtime_failure || {};
  const estimatorRuntimeFailureId = String(estimatorRuntimeFailure.artifact_id || "");
  const estimatorRuntimeFailureMessage = String(estimatorRuntimeFailure.error_message || "");
  if (!metrics || typeof metrics !== "object" || Array.isArray(metrics)) {
    throw new Error("run_sandbox must return a named dictionary/list object");
  }
  if (!finiteJsonValue(metrics)) {
    throw new Error("run_sandbox returned a non-finite or non-JSON metric value");
  }
  envelope = estimatorRuntimeFailureId
    ? {
        schema_version: 1,
        artifact_kind: "ScientificSandboxExecutionEnvelope",
        ok: false,
        language: request.language,
        backend: request.backend,
        metrics,
        estimator_invocation_counts: estimatorInvocationCounts,
        error_type: "AcceptedEstimatorRuntimeError",
        error_message: estimatorRuntimeFailureMessage,
        error_stack: "",
        error_origin: "accepted_estimator",
        error_artifact_id: estimatorRuntimeFailureId,
        caught_by_generated_simulation: true,
        started_at: startedAt,
        completed_at: new Date().toISOString(),
      }
    : {
        schema_version: 1,
        artifact_kind: "ScientificSandboxExecutionEnvelope",
        ok: true,
        language: request.language,
        backend: request.backend,
        metrics,
        estimator_invocation_counts: estimatorInvocationCounts,
        started_at: startedAt,
        completed_at: new Date().toISOString(),
      };
} catch (error) {
  const errorMessage = String(error?.message || error);
  const estimatorRuntimePrefix = "ACCEPTED_ESTIMATOR_RUNTIME_ERROR: ";
  const failedEstimatorId = Object.keys(estimatorSources).find((artifactId) =>
    errorMessage.includes(`${estimatorRuntimePrefix}${artifactId}: `),
  );
  envelope = {
    schema_version: 1,
    artifact_kind: "ScientificSandboxExecutionEnvelope",
    ok: false,
    language: request.language,
    backend: request.backend,
    metrics: {},
    error_type: error?.constructor?.name || "Error",
    error_message: errorMessage,
    error_stack: String(error?.stack || "").slice(0, 8000),
    error_origin: failedEstimatorId ? "accepted_estimator" : "generated_simulation",
    error_artifact_id: failedEstimatorId || "",
    started_at: startedAt,
    completed_at: new Date().toISOString(),
  };
}
fs.writeFileSync(outputPath, `${JSON.stringify(envelope, null, 2)}\n`, "utf8");
console.log(JSON.stringify(envelope));
if (!envelope.ok) {
  process.exitCode = 1;
}
