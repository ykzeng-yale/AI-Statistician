// Qualification fixture only: detached process lifetime is not contained on macOS.
import { spawn } from "node:child_process";
import fs from "node:fs";
import { SandboxManager, SandboxRuntimeConfigSchema } from "@anthropic-ai/sandbox-runtime";

const request = JSON.parse(fs.readFileSync(0, "utf8"));
const result = { executed: false, returncode: null, signal: null,
  timed_out: false, output_truncated: false, errors: [] };
let child;
let timer;
let bytes = 0;

function terminate() {
  if (child?.pid) {
    try { process.kill(-child.pid, "SIGKILL"); }
    catch (error) { if (error.code !== "ESRCH") throw error; }
  }
}

for (const signal of ["SIGTERM", "SIGINT"]) {
  process.on(signal, () => { terminate(); process.exit(128); });
}

try {
  const work = fs.realpathSync(request.project_dir);
  const home = fs.realpathSync(process.env.HOME);
  const tmp = fs.realpathSync(process.env.CLAUDE_CODE_TMPDIR);
  const systemReads = process.platform === "darwin"
    ? ["/bin", "/sbin", "/usr/bin", "/usr/sbin", "/usr/lib", "/usr/share", "/System", "/Library/Apple/System/Library",
      "/private/etc/ssl", "/private/etc/hosts", "/private/etc/localtime", "/private/var/db/timezone"]
    : ["/bin", "/sbin", "/usr/bin", "/usr/sbin", "/usr/lib", "/usr/share", "/lib", "/lib64", "/etc/ssl", "/etc/hosts", "/etc/ld.so.cache"];
  const config = SandboxRuntimeConfigSchema.parse({
    filesystem: {
      denyRead: ["/"],
      allowRead: [...systemReads, "/dev/null", "/dev/random", "/dev/urandom",
        work, home, tmp, ...request.runtime_read_roots],
      allowWrite: [work, home, tmp],
      denyWrite: ["/tmp/claude", "/private/tmp/claude"],
    },
    network: { allowedDomains: request.allowed_domains, deniedDomains: [],
      strictAllowlist: true, allowUnixSockets: [], allowAllUnixSockets: false,
      allowLocalBinding: false },
    allowPty: false,
  });
  await SandboxManager.initialize(config);
  const { argv, env } = await SandboxManager.wrapWithSandboxArgv(
    request.command, "/bin/bash", undefined, undefined, work,
    { commandId: request.invocation_id, commandText: request.command },
  );
  child = spawn(argv[0], argv.slice(1), {
    cwd: work, env, detached: true, stdio: ["ignore", "pipe", "pipe"],
  });
  const forward = (stream, destination) => {
    stream.on("data", chunk => {
      const remaining = Math.max(0, request.max_output_bytes - bytes);
      bytes += chunk.length;
      destination.write(chunk.subarray(0, remaining));
      if (bytes > request.max_output_bytes) {
        result.output_truncated = true;
        terminate();
      }
    });
  };
  forward(child.stdout, process.stdout);
  forward(child.stderr, process.stderr);
  timer = setTimeout(() => {
    result.timed_out = true;
    terminate();
  }, request.timeout_seconds * 1000);
  await new Promise((resolve, reject) => {
    child.once("spawn", () => { result.executed = true; });
    child.once("error", reject);
    child.once("close", (code, signal) => {
      result.returncode = code;
      result.signal = signal;
      resolve();
    });
  });
} catch (error) {
  result.errors.push(String(error.stack ?? error));
} finally {
  clearTimeout(timer);
  terminate();
  await SandboxManager.reset();
  fs.writeFileSync(request.result_path, JSON.stringify(result) + "\n", { flag: "wx" });
}
