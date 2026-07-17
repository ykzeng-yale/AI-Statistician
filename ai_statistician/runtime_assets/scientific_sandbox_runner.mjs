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

async function runPython(request, source) {
  const moduleUrl = pathToFileURL(request.runtime.pyodide_entry).href;
  const { loadPyodide } = await import(moduleUrl);
  const pyodide = await loadPyodide({ indexURL: `${request.runtime.pyodide_root}/` });
  if (request.dependencies.length > 0) {
    await pyodide.loadPackage(request.dependencies);
  }
  const wrapped = `${source}\n\nimport json as _ai_stat_json\n` +
    `_ai_stat_result = run_sandbox(seed=${Number(request.seed)}, replicates=${Number(request.replicates)})\n` +
    `_ai_stat_json.dumps(_ai_stat_result, allow_nan=False, sort_keys=True)`;
  const serialized = await pyodide.runPythonAsync(wrapped);
  return JSON.parse(String(serialized));
}

async function runR(request, source) {
  const moduleUrl = pathToFileURL(request.runtime.webr_entry).href;
  const { WebR } = await import(moduleUrl);
  const webR = new WebR();
  await webR.init();
  let result;
  try {
    const wrapped = `${source}\n\n` +
      `local({ .ai_stat_result <- run_sandbox(seed=${Number(request.seed)}, replicates=${Number(request.replicates)}); .ai_stat_result })`;
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
const startedAt = new Date().toISOString();
let envelope;
try {
  const metrics = request.language === "r"
    ? await runR(request, source)
    : await runPython(request, source);
  if (!metrics || typeof metrics !== "object" || Array.isArray(metrics)) {
    throw new Error("run_sandbox must return a named dictionary/list object");
  }
  if (!finiteJsonValue(metrics)) {
    throw new Error("run_sandbox returned a non-finite or non-JSON metric value");
  }
  envelope = {
    schema_version: 1,
    artifact_kind: "ScientificSandboxExecutionEnvelope",
    ok: true,
    language: request.language,
    backend: request.backend,
    metrics,
    started_at: startedAt,
    completed_at: new Date().toISOString(),
  };
} catch (error) {
  envelope = {
    schema_version: 1,
    artifact_kind: "ScientificSandboxExecutionEnvelope",
    ok: false,
    language: request.language,
    backend: request.backend,
    metrics: {},
    error_type: error?.constructor?.name || "Error",
    error_message: String(error?.message || error),
    error_stack: String(error?.stack || "").slice(0, 8000),
    started_at: startedAt,
    completed_at: new Date().toISOString(),
  };
}
fs.writeFileSync(outputPath, `${JSON.stringify(envelope, null, 2)}\n`, "utf8");
console.log(JSON.stringify(envelope));
if (!envelope.ok) {
  process.exitCode = 1;
}
