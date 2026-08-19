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
import shutil
import sys
import time
from pathlib import Path

from openintel_rfc.openintel_source import (
    AccessConfig,
    build_s3_client,
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

# Sizes come from the listing itself, not from a HEAD per object: knowing how
# many terabytes a range is before starting is the whole point of --list, and
# asking for it must not itself hammer the store.
sizes: dict[str, int] = {}
try:
    client = build_s3_client(config)
    paginator = client.get_paginator("list_objects_v2")
    for partition in partitions:
        total = 0
        for page in paginator.paginate(Bucket=config.bucket, Prefix=partition.prefix):
            for item in page.get("Contents", ()):
                if item["Key"].endswith(".gz.parquet"):
                    total += int(item.get("Size", 0))
        sizes[partition.partition_id] = total
except Exception as exc:  # listing sizes is informational, never fatal
    print(f"  (could not determine object sizes: {exc})")

for partition in partitions[:10]:
    size = sizes.get(partition.partition_id)
    size_text = f"{size / 1e9:8.2f} GB" if size else "        ?"
    print(f"  {partition.partition_id:<40} {len(partition.keys):>2} object(s) {size_text}")
if len(partitions) > 10:
    print(f"  ... and {len(partitions) - 10} more")

if sizes:
    total_bytes = sum(sizes.values())
    free_gb = shutil.disk_usage(config.cache_dir).free / 1e9
    print(f"\n  total download size : {total_bytes / 1e9:,.1f} GB")
    print(f"  free at cache dir   : {free_gb:,.1f} GB")
    if total_bytes / 1e9 > free_gb * 0.9:
        print("\n  WARNING: this range does not comfortably fit on the cache volume.")
        print("  Narrow the range, or point --cache-dir at a larger filesystem.")
        if os.environ["OPENINTEL_LIST_ONLY"] != "1" and os.environ["OPENINTEL_ASSUME_YES"] != "1":
            print("  Re-run with --yes to download anyway.")
            sys.exit(1)

if os.environ["OPENINTEL_LIST_ONLY"] == "1":
    print("\n--list given; nothing downloaded.")
    sys.exit(0)

warnings: list[str] = []
done = 0
for index, partition in enumerate(partitions, start=1):

    wait = 30

    for attempt in range(10):
        try:
            paths = materialize(partition, config, warnings=warnings)
            time.sleep(1)
            done += len(paths)
            print(f"[{index}/{len(partitions)}] {partition.partition_id}: {len(paths)} file(s)")
            break
        except Exception as exc:
            transient = any(
                token in str(exc).lower()
                for token in (
                    "503",
                    "500",
                    "502",
                    "504",
                    "slow down",
                    "timeout",
                    "connection reset",
                    "service unavailable",
                )
            )

            if not transient or attempt == 9:
                raise
            
            print(
                f"Retry {attempt+1}/10 for "
                f"{partition.partition_id} after: {exc}"
            )
            time.sleep(wait)
            wait *= 2

print(f"\nMaterialized {done} file(s) under {config.cache_dir}")
for message in warnings:
    print(f"warning: {message}")
PY

section "Done"
log "Now run the analysis against the cache:"
log "  ./scripts/run_full_analysis.sh --mode download --cache-dir ${CACHE_DIR} \\"
log "      --sources ${SOURCES} --start ${START} --end ${END}"
