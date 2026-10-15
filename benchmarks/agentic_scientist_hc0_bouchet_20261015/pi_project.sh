#!/bin/bash
set -euo pipefail
# Use YCRC's public launch boundary, scoped to one fresh arm, not the whole repo.
invocation_dir="$(pwd -P)"
root="${AISTAT_ARM_ROOT:?Set the fresh arm directory}"
root="$(realpath -e "$root")"
case "$invocation_dir/" in
  "$root/"*) ;;
  *) printf 'Invocation is outside the declared arm directory\n' >&2; exit 2 ;;
esac
context="The upstream task working directory is $invocation_dir. Resolve every relative path in the task and its skills against that directory, using absolute file-tool paths and explicit cd in shell tools. The public TASK_SOURCE_DIR is $root/task. Your container launch directory is only the common project root; it is not the task working directory. Other comparison arms are not mounted."
cd "$root"
exec /apps/software/system/software/pi-local/1.1/pi \
  --skill "$invocation_dir/.pi/agent/skills" \
  --append-system-prompt "$context" "$@"
