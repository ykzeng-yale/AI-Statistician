#!/bin/bash
# Archive the unchanged pinned environment once, before allocating another GPU.
set -euo pipefail
umask 077
root="${1:?Supply the existing deployment root}"
archive="$root/serve-env-node-local.tar"
test ! -e "$archive"
test ! -e "$archive.partial"
test -s "$root/runtime-29685758/environment.txt"
tar -cf "$archive.partial" -C "$root" serve-env
mv "$archive.partial" "$archive"
sha256sum "$archive"
du -h "$archive"
