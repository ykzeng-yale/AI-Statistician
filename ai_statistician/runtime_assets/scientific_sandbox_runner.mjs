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
  const requiredCallableExports = Array.isArray(request.required_callable_exports)
    ? request.required_callable_exports.map(String)
    : [];
  const wrapped = bound
    ? `import json as _ai_stat_json\n` +
      `_ai_stat_simulation_source = ${JSON.stringify(source)}\n` +
      `_ai_stat_estimator_sources = _ai_stat_json.loads(${JSON.stringify(JSON.stringify(estimatorSources))})\n` +
      `_ai_stat_simulation_namespace = {}\n` +
      `exec(compile(_ai_stat_simulation_source, "<generated_simulation>", "exec"), _ai_stat_simulation_namespace, _ai_stat_simulation_namespace)\n` +
      `_ai_stat_invocation_counts = {key: 0 for key in _ai_stat_estimator_sources}\n` +
      `_ai_stat_invocation_samples = {key: [] for key in _ai_stat_estimator_sources}\n` +
      `_ai_stat_runtime_failure = {"artifact_id": "", "error_message": ""}\n` +
      `_ai_stat_estimators = {}\n` +
      `def _ai_stat_json_native(_value):\n` +
      `    if _value is None or isinstance(_value, (bool, int, float, str)):\n` +
      `        return _value\n` +
      `    if isinstance(_value, dict):\n` +
      `        for _key in _value:\n` +
      `            if not isinstance(_key, str):\n` +
      `                raise TypeError("estimator request and response object keys must be strings; received key type " + type(_key).__name__)\n` +
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
      `def _ai_stat_trace_preview(_value, _depth=0):\n` +
      `    if _depth >= 4:\n` +
      `        return {"__preview__": "depth_limit", "type": type(_value).__name__}\n` +
      `    if _value is None or isinstance(_value, (bool, int, float)):\n` +
      `        return _value\n` +
      `    if isinstance(_value, str):\n` +
      `        return _value if len(_value) <= 300 else _value[:300] + "..."\n` +
      `    if isinstance(_value, dict):\n` +
      `        _keys = list(_value)\n` +
      `        _preview = {_key: _ai_stat_trace_preview(_value[_key], _depth + 1) for _key in _keys[:16]}\n` +
      `        if len(_keys) > 16:\n` +
      `            _preview["__truncated_keys__"] = len(_keys) - 16\n` +
      `        return _preview\n` +
      `    if isinstance(_value, (list, tuple)):\n` +
      `        if len(_value) <= 8:\n` +
      `            return [_ai_stat_trace_preview(_item, _depth + 1) for _item in _value]\n` +
      `        return {"__preview__": "sequence", "length": len(_value), "head": [_ai_stat_trace_preview(_item, _depth + 1) for _item in _value[:5]], "tail": [_ai_stat_trace_preview(_item, _depth + 1) for _item in _value[-2:]]}\n` +
      `    return _ai_stat_trace_preview(_ai_stat_json_native(_value), _depth + 1)\n` +
      `def _ai_stat_trace_shape(_value, _depth=0):\n` +
      `    if _value is None:\n` +
      `        return {"type": "null"}\n` +
      `    if isinstance(_value, bool):\n` +
      `        return {"type": "boolean"}\n` +
      `    if isinstance(_value, int):\n` +
      `        return {"type": "integer"}\n` +
      `    if isinstance(_value, float):\n` +
      `        return {"type": "number"}\n` +
      `    if isinstance(_value, str):\n` +
      `        return {"type": "string"}\n` +
      `    if _depth >= 4:\n` +
      `        return {"type": type(_value).__name__, "depth_limited": True}\n` +
      `    if isinstance(_value, dict):\n` +
      `        _keys = list(_value)\n` +
      `        _shape = {"type": "object", "fields": {str(_key): _ai_stat_trace_shape(_value[_key], _depth + 1) for _key in _keys[:16]}}\n` +
      `        if len(_keys) > 16:\n` +
      `            _shape["fields_truncated"] = True\n` +
      `        return _shape\n` +
      `    if isinstance(_value, (list, tuple)):\n` +
      `        return {"type": "array", "element_types": sorted({str(_ai_stat_trace_shape(_item, _depth + 1).get("type", "unknown")) for _item in _value[:16]})}\n` +
      `    _array_shape = getattr(_value, "shape", None)\n` +
      `    if _array_shape is not None:\n` +
      `        try:\n` +
      `            return {"type": "array", "rank": len(_array_shape), "element_type": str(getattr(_value, "dtype", type(_value).__name__))}\n` +
      `        except Exception:\n` +
      `            pass\n` +
      `    return {"type": type(_value).__name__}\n` +
      `def _ai_stat_bind_estimator(_artifact_id, _source):\n` +
      `    _namespace = {}\n` +
      `    exec(compile(_source, "<accepted_algorithm:" + _artifact_id + ">", "exec"), _namespace, _namespace)\n` +
      `    _implementation = _namespace.get("run_estimator")\n` +
      `    if not callable(_implementation):\n` +
      `        raise RuntimeError("ACCEPTED_ESTIMATOR_BINDING_ERROR: " + _artifact_id + ": accepted algorithm did not define callable run_estimator")\n` +
      `    def _bound_estimator(request):\n` +
      `        if not isinstance(request, dict):\n` +
      `            raise TypeError("run_estimator request must be a dict: " + _artifact_id)\n` +
      `        request_shape = _ai_stat_trace_shape(request)\n` +
      `        try:\n` +
      `            normalized_request = _ai_stat_json_native(request)\n` +
      `            _ai_stat_json.dumps(normalized_request, allow_nan=False, sort_keys=True)\n` +
      `            raw_response = _implementation(normalized_request)\n` +
      `            if not isinstance(raw_response, dict):\n` +
      `                raise TypeError("run_estimator response must be a dict")\n` +
      `            response = _ai_stat_json_native(raw_response)\n` +
      `            _ai_stat_json.dumps(response, allow_nan=False, sort_keys=True)\n` +
      `        except Exception as exc:\n` +
      `            failure_message = "ACCEPTED_ESTIMATOR_RUNTIME_ERROR: " + _artifact_id + ": " + type(exc).__name__ + ": " + str(exc) + "; request_shape=" + _ai_stat_json.dumps(request_shape, separators=(",", ":"), sort_keys=True)\n` +
      `            _ai_stat_invocation_samples[_artifact_id] = [{"invocation_index": _ai_stat_invocation_counts[_artifact_id] + 1, "request_shape": request_shape, "response_status": "ERROR", "error_type": type(exc).__name__}]\n` +
      `            if not _ai_stat_runtime_failure["artifact_id"]:\n` +
      `                _ai_stat_runtime_failure["artifact_id"] = _artifact_id\n` +
      `                _ai_stat_runtime_failure["error_message"] = failure_message\n` +
      `            raise RuntimeError(failure_message) from exc\n` +
      `        if len(_ai_stat_invocation_samples[_artifact_id]) < 3:\n` +
      `            _ai_stat_invocation_samples[_artifact_id].append({"invocation_index": _ai_stat_invocation_counts[_artifact_id] + 1, "request": _ai_stat_trace_preview(normalized_request), "response": _ai_stat_trace_preview(response)})\n` +
      `        _ai_stat_invocation_counts[_artifact_id] += 1\n` +
      `        return response\n` +
      `    return _bound_estimator\n` +
      `for _ai_stat_id, _ai_stat_source in _ai_stat_estimator_sources.items():\n` +
      `    _ai_stat_estimators[_ai_stat_id] = _ai_stat_bind_estimator(_ai_stat_id, _ai_stat_source)\n` +
      `_ai_stat_run_sandbox = _ai_stat_simulation_namespace.get("run_sandbox")\n` +
      `if not callable(_ai_stat_run_sandbox):\n` +
      `    raise RuntimeError("generated simulation did not define callable run_sandbox")\n` +
      `_ai_stat_result = _ai_stat_run_sandbox(seed=${Number(request.seed)}, replicates=${Number(request.replicates)}, estimators=_ai_stat_estimators)\n` +
      `_ai_stat_json.dumps({"metrics": _ai_stat_result, "estimator_invocation_counts": _ai_stat_invocation_counts, "estimator_invocation_samples": _ai_stat_invocation_samples, "estimator_runtime_failure": _ai_stat_runtime_failure}, allow_nan=False, sort_keys=True)`
    : `import json as _ai_stat_json\n` +
      `_ai_stat_source = ${JSON.stringify(source)}\n` +
      `_ai_stat_namespace = {}\n` +
      `exec(compile(_ai_stat_source, "<generated_source>", "exec"), _ai_stat_namespace, _ai_stat_namespace)\n` +
      `_ai_stat_required_callable_exports = _ai_stat_json.loads(${JSON.stringify(JSON.stringify(requiredCallableExports))})\n` +
      `for _ai_stat_export in _ai_stat_required_callable_exports:\n` +
      `    if not callable(_ai_stat_namespace.get(_ai_stat_export)):\n` +
      `        raise RuntimeError("generated source did not export callable " + _ai_stat_export)\n` +
      `def _ai_stat_json_native(_value):\n` +
      `    if _value is None or isinstance(_value, (bool, int, float, str)):\n` +
      `        return _value\n` +
      `    if isinstance(_value, dict):\n` +
      `        for _key in _value:\n` +
      `            if not isinstance(_key, str):\n` +
      `                raise TypeError("sandbox result object keys must be strings; received key type " + type(_key).__name__)\n` +
      `        return {_key: _ai_stat_json_native(_item) for _key, _item in _value.items()}\n` +
      `    if isinstance(_value, (list, tuple)):\n` +
      `        return [_ai_stat_json_native(_item) for _item in _value]\n` +
      `    _tolist = getattr(_value, "tolist", None)\n` +
      `    if callable(_tolist):\n` +
      `        return _ai_stat_json_native(_tolist())\n` +
      `    _scalar_item = getattr(_value, "item", None)\n` +
      `    if callable(_scalar_item):\n` +
      `        return _ai_stat_json_native(_scalar_item())\n` +
      `    raise TypeError("sandbox result values must be JSON-native or array-like")\n` +
      `_ai_stat_run_sandbox = _ai_stat_namespace.get("run_sandbox")\n` +
      `if not callable(_ai_stat_run_sandbox):\n` +
      `    raise RuntimeError("generated source did not export callable run_sandbox")\n` +
      `_ai_stat_result = _ai_stat_json_native(_ai_stat_run_sandbox(seed=${Number(request.seed)}, replicates=${Number(request.replicates)}))\n` +
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
    const requiredCallableExports = Array.isArray(request.required_callable_exports)
      ? request.required_callable_exports.map(String)
      : [];
    const requiredCallableExportVector = requiredCallableExports.length > 0
      ? `c(${requiredCallableExports.map((value) => JSON.stringify(value)).join(",")})`
      : "character()";
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
        `.ai_stat_invocation_samples <- setNames(lapply(.ai_stat_estimator_sources, function(value) list()), names(.ai_stat_estimator_sources))\n` +
        `.ai_stat_runtime_failure <- list(artifact_id="", error_message="")\n` +
        `.ai_stat_json_finite <- function(value) {\n` +
        `  if (is.null(value)) return(TRUE)\n` +
        `  if (is.list(value)) return(all(vapply(value, .ai_stat_json_finite, logical(1))))\n` +
        `  if (is.numeric(value)) return(length(value) > 0L && all(is.finite(value)))\n` +
        `  if (is.character(value) || is.logical(value)) return(length(value) > 0L && !anyNA(value))\n` +
        `  FALSE\n` +
        `}\n` +
        `.ai_stat_trace_preview <- function(value, depth=0L) {\n` +
        `  if (depth >= 4L) return(list(.preview="depth_limit", type=class(value)[[1]]))\n` +
        `  if (is.null(value)) return(NULL)\n` +
        `  if (is.character(value)) {\n` +
        `    text <- as.character(value)\n` +
        `    return(ifelse(nchar(text) <= 300L, text, paste0(substr(text, 1L, 300L), "...")))\n` +
        `  }\n` +
        `  if (is.atomic(value) && length(value) <= 8L) return(value)\n` +
        `  if (is.atomic(value)) return(list(.preview="sequence", length=length(value), head=unname(as.list(head(value, 5L))), tail=unname(as.list(tail(value, 2L)))))\n` +
        `  if (is.list(value)) {\n` +
        `    keys <- names(value)\n` +
        `    if (is.null(keys)) {\n` +
        `      if (length(value) <= 8L) return(lapply(value, .ai_stat_trace_preview, depth=depth + 1L))\n` +
        `      return(list(.preview="sequence", length=length(value), head=lapply(head(value, 5L), .ai_stat_trace_preview, depth=depth + 1L), tail=lapply(tail(value, 2L), .ai_stat_trace_preview, depth=depth + 1L)))\n` +
        `    }\n` +
        `    kept <- head(seq_along(value), 16L)\n` +
        `    preview <- lapply(value[kept], .ai_stat_trace_preview, depth=depth + 1L)\n` +
        `    if (length(value) > 16L) preview$.truncated_keys <- length(value) - 16L\n` +
        `    return(preview)\n` +
        `  }\n` +
        `  list(.preview="unsupported", type=class(value)[[1]])\n` +
        `}\n` +
        `.ai_stat_trace_shape <- function(value, depth=0L) {\n` +
        `  if (is.null(value)) return(list(type="null"))\n` +
        `  if (is.logical(value) && length(value) == 1L) return(list(type="boolean"))\n` +
        `  if (is.integer(value) && length(value) == 1L) return(list(type="integer"))\n` +
        `  if (is.numeric(value) && length(value) == 1L) return(list(type="number"))\n` +
        `  if (is.character(value) && length(value) == 1L) return(list(type="string"))\n` +
        `  if (depth >= 4L) return(list(type=class(value)[[1]], depth_limited=TRUE))\n` +
        `  if (is.list(value) && !is.null(names(value))) {\n` +
        `    kept <- head(seq_along(value), 16L)\n` +
        `    fields <- lapply(value[kept], .ai_stat_trace_shape, depth=depth + 1L)\n` +
        `    shape <- list(type="object", fields=fields)\n` +
        `    if (length(value) > 16L) shape$fields_truncated <- TRUE\n` +
        `    return(shape)\n` +
        `  }\n` +
        `  if (is.list(value)) {\n` +
        `    element_types <- sort(unique(vapply(head(value, 16L), function(item) .ai_stat_trace_shape(item, depth + 1L)$type, character(1))))\n` +
        `    return(list(type="array", element_types=unname(element_types)))\n` +
        `  }\n` +
        `  if (is.atomic(value)) {\n` +
        `    element_type <- if (is.logical(value)) "boolean" else if (is.integer(value)) "integer" else if (is.numeric(value)) "number" else if (is.character(value)) "string" else class(value)[[1]]\n` +
        `    return(list(type="array", element_types=element_type))\n` +
        `  }\n` +
        `  list(type=class(value)[[1]])\n` +
        `}\n` +
        `.ai_stat_estimators <- lapply(names(.ai_stat_estimator_sources), function(.artifact_id) {\n` +
        `  local({\n` +
        `    .id <- .artifact_id\n` +
        `    .environment <- new.env(parent=globalenv())\n` +
        `    eval(parse(text=.ai_stat_estimator_sources[[.id]]), envir=.environment)\n` +
        `    if (!exists("run_estimator", envir=.environment, mode="function", inherits=FALSE)) stop(paste0("ACCEPTED_ESTIMATOR_BINDING_ERROR: ", .id, ": accepted algorithm did not define callable run_estimator"))\n` +
        `    .implementation <- get("run_estimator", envir=.environment, inherits=FALSE)\n` +
        `    function(request) {\n` +
        `      if (!is.list(request) || is.null(names(request))) stop(paste("run_estimator request must be a named list:", .id))\n` +
        `      if (!.ai_stat_json_finite(request)) stop(paste("run_estimator request must contain finite JSON-compatible values:", .id))\n` +
        `      .request_shape <- .ai_stat_trace_shape(request)\n` +
        `      .response <- tryCatch({\n` +
        `        .candidate <- .implementation(request)\n` +
        `        if (!is.list(.candidate) || is.null(names(.candidate))) stop("run_estimator response must be a named list")\n` +
        `        if (!.ai_stat_json_finite(.candidate)) stop("run_estimator response must contain finite JSON-compatible values")\n` +
        `        .candidate\n` +
        `      }, error=function(.error) {\n` +
        `        .shape_text <- paste(capture.output(dput(.request_shape)), collapse="")\n` +
        `        .message <- paste0("ACCEPTED_ESTIMATOR_RUNTIME_ERROR: ", .id, ": ", class(.error)[[1]], ": ", conditionMessage(.error), "; request_shape=", .shape_text)\n` +
        `        .ai_stat_invocation_samples[[.id]] <<- list(list(invocation_index=.ai_stat_invocation_counts[[.id]] + 1L, request_shape=.request_shape, response_status="ERROR", error_type=class(.error)[[1]]))\n` +
        `        if (!nzchar(.ai_stat_runtime_failure$artifact_id)) .ai_stat_runtime_failure <<- list(artifact_id=.id, error_message=.message)\n` +
        `        stop(.message, call.=FALSE)\n` +
        `      })\n` +
        `      if (length(.ai_stat_invocation_samples[[.id]]) < 3L) {\n` +
        `        .ai_stat_invocation_samples[[.id]] <<- c(.ai_stat_invocation_samples[[.id]], list(list(invocation_index=.ai_stat_invocation_counts[[.id]] + 1L, request=.ai_stat_trace_preview(request), response=.ai_stat_trace_preview(.response))))\n` +
        `      }\n` +
        `      .ai_stat_invocation_counts[[.id]] <<- .ai_stat_invocation_counts[[.id]] + 1L\n` +
        `      .response\n` +
        `    }\n` +
        `  })\n` +
        `})\n` +
        `names(.ai_stat_estimators) <- names(.ai_stat_estimator_sources)\n` +
        `if (!exists("run_sandbox", envir=.ai_stat_simulation_environment, mode="function", inherits=FALSE)) stop("generated simulation did not define callable run_sandbox")\n` +
        `.ai_stat_result <- get("run_sandbox", envir=.ai_stat_simulation_environment, inherits=FALSE)(seed=${Number(request.seed)}, replicates=${Number(request.replicates)}, estimators=.ai_stat_estimators)\n` +
        `list(metrics=.ai_stat_result, estimator_invocation_counts=.ai_stat_invocation_counts, estimator_invocation_samples=.ai_stat_invocation_samples, estimator_runtime_failure=.ai_stat_runtime_failure)\n` +
        `})`
      : `local({\n` +
        `.ai_stat_source <- ${JSON.stringify(source)}\n` +
        `.ai_stat_environment <- new.env(parent=globalenv())\n` +
        `eval(parse(text=.ai_stat_source), envir=.ai_stat_environment)\n` +
        `.ai_stat_required_callable_exports <- ${requiredCallableExportVector}\n` +
        `for (.ai_stat_export in .ai_stat_required_callable_exports) {\n` +
        `  if (!exists(.ai_stat_export, envir=.ai_stat_environment, mode="function", inherits=FALSE)) stop(paste("generated source did not export callable", .ai_stat_export))\n` +
        `}\n` +
        `if (!exists("run_sandbox", envir=.ai_stat_environment, mode="function", inherits=FALSE)) stop("generated source did not export callable run_sandbox")\n` +
        `.ai_stat_result <- get("run_sandbox", envir=.ai_stat_environment, inherits=FALSE)(seed=${Number(request.seed)}, replicates=${Number(request.replicates)})\n` +
        `list(metrics=.ai_stat_result, estimator_invocation_counts=list())\n` +
        `})`;
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
  const estimatorInvocationSamples = execution?.estimator_invocation_samples || {};
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
        estimator_invocation_samples: estimatorInvocationSamples,
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
        estimator_invocation_samples: estimatorInvocationSamples,
        started_at: startedAt,
        completed_at: new Date().toISOString(),
      };
} catch (error) {
  const errorMessage = String(error?.message || error);
  const estimatorRuntimePrefix = "ACCEPTED_ESTIMATOR_RUNTIME_ERROR: ";
  const estimatorBindingPrefix = "ACCEPTED_ESTIMATOR_BINDING_ERROR: ";
  const failedRuntimeEstimatorId = Object.keys(estimatorSources).find((artifactId) =>
    errorMessage.includes(`${estimatorRuntimePrefix}${artifactId}: `),
  );
  const failedBindingEstimatorId = Object.keys(estimatorSources).find((artifactId) =>
    errorMessage.includes(`${estimatorBindingPrefix}${artifactId}: `),
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
    error_origin: failedBindingEstimatorId
      ? "accepted_estimator_binding"
      : failedRuntimeEstimatorId
        ? "accepted_estimator"
        : "generated_source",
    error_artifact_id: failedBindingEstimatorId || failedRuntimeEstimatorId || "",
    started_at: startedAt,
    completed_at: new Date().toISOString(),
  };
}
fs.writeFileSync(outputPath, `${JSON.stringify(envelope, null, 2)}\n`, "utf8");
console.log(JSON.stringify(envelope));
if (!envelope.ok) {
  process.exitCode = 1;
}
