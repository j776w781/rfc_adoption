#!/usr/bin/env bash
#
# Pre-download OpenINTEL partitions to local disk.
#
# Only needed for --mode download. Streaming mode reads object.openintel.nl
# directly and needs no local copy. Downloading is worth it when you will scan
# the same range repeatedly (checklist iteration), or when the link to Utwente
# is unreliable enough that a multi-day streaming run would not survive it.
#
#   ./scripts/fetch_openintel.sh --sources nu --start 2018-05-01 --end 2018-05-07
#
# Resumable: an object already present with a non-zero size is skipped.

set -euo pipefail
# shellcheck source=./common.sh
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/common.sh"

SOURCES=""
START=""
END=""
BASIS="zonefile"
CACHE_DIR="${PROJECT_ROOT}/openintel_cache"
LIST_ONLY=0

usage() {
    cat <<'EOF'
Usage: fetch_openintel.sh --sources <list> --start <date> --end <date> [options]

Required:
  --sources LIST       Comma-separated sources, e.g. nu,se,nl
  --start  YYYY-MM-DD
  --end    YYYY-MM-DD

Options:
  --basis zonefile|toplist   Measurement basis (default: zonefile)
  --cache-dir DIR            Destination (default: ./openintel_cache)
  --list                     List matching objects and total size, download nothing
  --yes                      Do not prompt
  --help

Run with --list first: it reports how many objects and how many bytes the range
covers, so you can check it against free disk before starting.
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --sources)    SOURCES="${2:?}"; shift ;;
        --start)      START="${2:?}"; shift ;;
        --end)        END="${2:?}"; shift ;;
        --basis)      BASIS="${2:?}"; shift ;;
        --cache-dir)  CACHE_DIR="${2:?}"; shift ;;
        --list)       LIST_ONLY=1 ;;
        --yes|-y)     ASSUME_YES=1; export ASSUME_YES ;;
        --help|-h)    usage; exit 0 ;;
        *)            die "Unknown option: $1 (try --help)" ;;
    esac
    shift
done

[[ -n "${SOURCES}" ]] || { usage; die "--sources is required"; }
[[ -n "${START}"   ]] || { usage; die "--start is required"; }
[[ -n "${END}"     ]] || { usage; die "--end is required"; }

cd "${PROJECT_ROOT}"
activate_venv
ensure_log_dir
mkdir -p "${CACHE_DIR}"

FETCH_LOG="${LOG_DIR}/fetch-$(date +%Y%m%d-%H%M%S).log"
DISK_GB="$(free_space_gb "${CACHE_DIR}")"

section "OpenINTEL fetch"
log "sources   : ${SOURCES}"
log "range     : ${START} .. ${END} (basis=${BASIS})"
log "cache dir : ${CACHE_DIR}"
log "free disk : ${DISK_GB} GB"
log "log       : ${FETCH_LOG}"

export OPENINTEL_SOURCES="${SOURCES}" OPENINTEL_START="${START}" \
       OPENINTEL_END="${END}" OPENINTEL_BASIS="${BASIS}" \
       OPENINTEL_CACHE="${CACHE_DIR}" OPENINTEL_LIST_ONLY="${LIST_ONLY}" \
       OPENINTEL_ASSUME_YES="${ASSUME_YES:-0}"

python - <<'PY' 2>&1 | tee -a "${FETCH_LOG}"
"""Discover the requested partitions, report their size, then materialize them."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from openintel_rfc.openintel_source import (
    AccessConfig,
    discover_partitions,
    materialize,
)

sources = [s.strip() for s in os.environ["OPENINTEL_SOURCES"].split(",") if s.strip()]
config = AccessConfig(
    mode="download",
    cache_dir=Path(os.environ["OPENINTEL_CACHE"]),
)

partitions = discover_partitions(
    config,
    sources,
    os.environ["OPENINTEL_START"],
    os.environ["OPENINTEL_END"],
    basis=os.environ["OPENINTEL_BASIS"],
)

if not partitions:
    print("No partitions matched. Check the sources and the date range: OpenINTEL")
    print("does not publish every source on every day.")
    sys.exit(1)

total_objects = sum(len(p.keys) for p in partitions)
print(f"{len(partitions)} partition(s), {total_objects} object(s)")
for partition in partitions[:10]:
    print(f"  {partition.partition_id:<40} {len(partition.keys)} object(s)")
if len(partitions) > 10:
    print(f"  ... and {len(partitions) - 10} more")

if os.environ["OPENINTEL_LIST_ONLY"] == "1":
    print("\n--list given; nothing downloaded.")
    sys.exit(0)

warnings: list[str] = []
done = 0
for index, partition in enumerate(partitions, start=1):
    paths = materialize(partition, config, warnings=warnings)
    done += len(paths)
    print(f"[{index}/{len(partitions)}] {partition.partition_id}: {len(paths)} file(s)")

print(f"\nMaterialized {done} file(s) under {config.cache_dir}")
for message in warnings:
    print(f"warning: {message}")
PY

section "Done"
log "Now run the analysis against the cache:"
log "  ./scripts/run_full_analysis.sh --mode download --cache-dir ${CACHE_DIR} \\"
log "      --sources ${SOURCES} --start ${START} --end ${END}"
