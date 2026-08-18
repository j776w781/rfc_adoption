#!/usr/bin/env bash
#
# Run a real OpenINTEL RFC-adoption analysis across one or more TLDs and a date
# range. Resumable: every partition is checkpointed, so re-running after an
# interruption continues where it stopped rather than starting over.
#
#   ./scripts/run_full_analysis.sh --sources nu --start 2018-05-01 --end 2018-05-01 --dry-run
#   ./scripts/run_full_analysis.sh --sources nu,se,nl --start 2015-01-01 --end 2021-12-31
#
# Long runs should go in tmux:  tmux new -s openintel

set -euo pipefail
# shellcheck source=./common.sh
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/common.sh"

SOURCES=""
START=""
END=""
BASIS="zonefile"
MODE="stream"
OUT="${PROJECT_ROOT}/output_real"
CHECKPOINT_DIR=""
CACHE_DIR=""
DRY_RUN=0
MAX_PARTITIONS=""
NO_RESUME=0
PARTITION_RETRIES=""
RETRY_WAIT=""
PACE_SECONDS=""
MAX_PACE_SECONDS=""
SHARDS=""
CHECKLISTS="${PROJECT_ROOT}/data/rfc_checklists/dnssec_rfc_checklists.json"
DICTIONARY="${PROJECT_ROOT}/data/openintel_dictionary/sample_openintel_dictionary.json"

usage() {
    cat <<'EOF'
Usage: run_full_analysis.sh --sources <list> --start <date> --end <date> [options]

Required:
  --sources LIST       Comma-separated OpenINTEL sources, e.g. nu,se,nl,com
  --start  YYYY-MM-DD  First measurement day (inclusive)
  --end    YYYY-MM-DD  Last measurement day (inclusive)

Options:
  --mode stream|download   stream: query object.openintel.nl directly (default,
                           no local storage). download: fetch partitions first.
  --basis zonefile|toplist Measurement basis (default: zonefile)
  --out DIR                Output directory (default: ./output_real)
  --checkpoint-dir DIR     Checkpoints (default: <out>/checkpoints)
  --cache-dir DIR          Local Parquet cache for --mode download
  --max-partitions N       Stop after N partitions (useful for a bounded trial)
  --partition-retries N    Retries per partition on a 503/timeout (default: 5)
  --retry-wait SECONDS     First retry wait; doubles thereafter (default: 30)
  --pace-seconds SECONDS   Smallest gap between partitions (default: 0.5). The
                           gap is adaptive: it widens when the store pushes back
                           and relaxes when it stops
  --max-pace-seconds SECS  Ceiling for that adaptive gap (default: 60)
  --shards N               How many processes share the store's budget with this
                           one, INCLUDING this one. Set it whenever you run more
                           than one shard at a time: the limiter is ~1 request
                           per second per endpoint, not per process, so N shards
                           each pacing for the whole budget is N times over it
  --threads N              DuckDB threads (default: all cores)
  --memory-limit SIZE      DuckDB memory limit, e.g. 64GB (default: 70% of RAM)
  --checklists PATH        RFC checklist DB
  --dictionary PATH        OpenINTEL dictionary
  --dry-run                Discover partitions, probe the schema, estimate the
                           run, then stop without scanning any data
  --no-resume              Ignore existing checkpoints and recompute everything
  --yes                    Do not prompt
  --help

Always --dry-run first. It reports how many partitions and roughly how many
rows the range covers, and which normalized fields actually resolve against the
real schema, before you commit hours of compute.
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --sources)         SOURCES="${2:?}"; shift ;;
        --start)           START="${2:?}"; shift ;;
        --end)             END="${2:?}"; shift ;;
        --basis)           BASIS="${2:?}"; shift ;;
        --mode)            MODE="${2:?}"; shift ;;
        --out)             OUT="${2:?}"; shift ;;
        --checkpoint-dir)  CHECKPOINT_DIR="${2:?}"; shift ;;
        --cache-dir)       CACHE_DIR="${2:?}"; shift ;;
        --max-partitions)  MAX_PARTITIONS="${2:?}"; shift ;;
        --partition-retries) PARTITION_RETRIES="${2:?}"; shift ;;
        --retry-wait)      RETRY_WAIT="${2:?}"; shift ;;
        --pace-seconds)    PACE_SECONDS="${2:?}"; shift ;;
        --max-pace-seconds) MAX_PACE_SECONDS="${2:?}"; shift ;;
        --shards)          SHARDS="${2:?}"; shift ;;
        --threads)         DUCKDB_THREADS="${2:?}"; export DUCKDB_THREADS; shift ;;
        --memory-limit)    DUCKDB_MEMORY_LIMIT="${2:?}"; export DUCKDB_MEMORY_LIMIT; shift ;;
        --checklists)      CHECKLISTS="${2:?}"; shift ;;
        --dictionary)      DICTIONARY="${2:?}"; shift ;;
        --dry-run)         DRY_RUN=1 ;;
        --no-resume)       NO_RESUME=1 ;;
        --yes|-y)          ASSUME_YES=1; export ASSUME_YES ;;
        --help|-h)         usage; exit 0 ;;
        *)                 die "Unknown option: $1 (try --help)" ;;
    esac
    shift
done

[[ -n "${SOURCES}" ]] || { usage; die "--sources is required"; }
[[ -n "${START}"   ]] || { usage; die "--start is required"; }
[[ -n "${END}"     ]] || { usage; die "--end is required"; }
[[ "${MODE}" == "stream" || "${MODE}" == "download" ]] || die "--mode must be stream or download"
[[ -f "${CHECKLISTS}" ]] || die "Checklist DB not found: ${CHECKLISTS}"
[[ -f "${DICTIONARY}" ]] || die "Dictionary not found: ${DICTIONARY}"

cd "${PROJECT_ROOT}"
activate_venv
compute_tuning "${MODE}"
ensure_log_dir

CHECKPOINT_DIR="${CHECKPOINT_DIR:-${OUT}/checkpoints}"
if [[ "${MODE}" == "download" ]]; then
    CACHE_DIR="${CACHE_DIR:-${PROJECT_ROOT}/openintel_cache}"
fi
mkdir -p "${OUT}" "${CHECKPOINT_DIR}"

RUN_LOG="${LOG_DIR}/analysis-$(date +%Y%m%d-%H%M%S).log"

section "OpenINTEL RFC-adoption — real analysis"
log "sources      : ${SOURCES}"
log "range        : ${START} .. ${END}  (basis=${BASIS})"
log "mode         : ${MODE}"
log "output       : ${OUT}"
log "checkpoints  : ${CHECKPOINT_DIR}"
[[ -n "${CACHE_DIR}" ]] && log "cache        : ${CACHE_DIR}"
log "duckdb       : threads=${DUCKDB_THREADS} memory_limit=${DUCKDB_MEMORY_LIMIT}"
log "log          : ${RUN_LOG}"

# Warn about an obviously enormous range before it is too late to reconsider.
if command -v python >/dev/null 2>&1; then
    DAYS="$(python - "$START" "$END" <<'PY'
import sys, datetime
a = datetime.date.fromisoformat(sys.argv[1])
b = datetime.date.fromisoformat(sys.argv[2])
print((b - a).days + 1)
PY
)"
    N_SOURCES="$(awk -F, '{print NF}' <<<"${SOURCES}")"
    PARTITIONS=$(( DAYS * N_SOURCES ))
    log "span         : ${DAYS} day(s) x ${N_SOURCES} source(s) = ~${PARTITIONS} partitions"

    # Measured on a real partition: streaming costs ~71 s, downloading costs
    # ~14 s to fetch plus ~21 s to scan locally, and a re-scan of the cache is
    # ~21 s. Streaming also issues thousands of small range requests per object
    # against a store that rate-limits on request count. Past a handful of
    # partitions, download mode is both faster and far less likely to be
    # throttled -- so say so before a long run rather than after it fails.
    if [[ "${DRY_RUN}" == "0" && "${MODE}" == "stream" && "${PARTITIONS}" -gt 10 ]]; then
        EST_STREAM_MIN=$(( PARTITIONS * 71 / 60 ))
        EST_DOWNLOAD_MIN=$(( PARTITIONS * 35 / 60 ))
        warn ""
        warn "${PARTITIONS} partitions in stream mode is likely to be throttled and is"
        warn "roughly twice as slow: ~${EST_STREAM_MIN} min streaming vs ~${EST_DOWNLOAD_MIN} min downloading"
        warn "(and ~$(( PARTITIONS * 21 / 60 )) min for any later re-scan of the cache)."
        warn "Consider:"
        warn "  --mode download --cache-dir /path/on/a/large/volume --pace-seconds 2"
        warn "See docs/running_at_scale.md section 4a. Continuing with stream mode."
        warn ""
    fi
fi

# Download mode needs real disk. A .nu day is ~370 MB and a .se day ~2 GB, so a
# multi-year multi-source range is easily terabytes; refusing to start is kinder
# than filling the volume at 3am.
if [[ "${MODE}" == "download" ]]; then
    CACHE_FREE_GB="$(free_space_gb "${CACHE_DIR}")"
    log "cache free   : ${CACHE_FREE_GB} GB"
    if [[ "${CACHE_FREE_GB}" -lt 20 ]]; then
        warn "Only ${CACHE_FREE_GB} GB free at ${CACHE_DIR}. One OpenINTEL day is"
        warn "0.4-2 GB per source; run ./scripts/fetch_openintel.sh --list first to"
        warn "size the range, or point --cache-dir at a larger volume."
    fi
fi

CMD=(python -m openintel_rfc.cli scale
     --sources "${SOURCES}"
     --start "${START}"
     --end "${END}"
     --basis "${BASIS}"
     --mode "${MODE}"
     --checklists "${CHECKLISTS}"
     --dictionary "${DICTIONARY}"
     --out "${OUT}"
     --checkpoint-dir "${CHECKPOINT_DIR}"
     --threads "${DUCKDB_THREADS}"
     --memory-limit "${DUCKDB_MEMORY_LIMIT}")

[[ -n "${CACHE_DIR}"      ]] && CMD+=(--cache-dir "${CACHE_DIR}")
[[ -n "${MAX_PARTITIONS}" ]] && CMD+=(--max-partitions "${MAX_PARTITIONS}")
[[ -n "${PARTITION_RETRIES}" ]] && CMD+=(--partition-retries "${PARTITION_RETRIES}")
[[ -n "${RETRY_WAIT}"      ]] && CMD+=(--retry-wait "${RETRY_WAIT}")
[[ -n "${PACE_SECONDS}"    ]] && CMD+=(--pace-seconds "${PACE_SECONDS}")
[[ -n "${MAX_PACE_SECONDS}" ]] && CMD+=(--max-pace-seconds "${MAX_PACE_SECONDS}")
[[ -n "${SHARDS}"          ]] && CMD+=(--shards "${SHARDS}")
[[ "${NO_RESUME}" == "1"  ]] && CMD+=(--no-resume)
[[ "${DRY_RUN}"   == "1"  ]] && CMD+=(--dry-run)

if [[ "${DRY_RUN}" == "0" ]]; then
    section "This will scan real OpenINTEL data and can run for hours or days."
    log "It is resumable: re-run the same command to continue from ${CHECKPOINT_DIR}."
    confirm "Start the run?" || { log "aborted"; exit 0; }
fi

section "Running"
set +e
"${CMD[@]}" 2>&1 | tee -a "${RUN_LOG}"
STATUS="${PIPESTATUS[0]}"
set -e

if [[ "${STATUS}" != "0" ]]; then
    warn "Run exited with status ${STATUS}. Completed partitions are checkpointed in"
    warn "${CHECKPOINT_DIR}; re-run the same command to resume."
    exit "${STATUS}"
fi

section "Done"
cat <<EOF

  Artefacts : ${OUT}
  Log       : ${RUN_LOG}

  Inspect the results:
      streamlit run dashboard/app.py --server.port 8501 --server.address 0.0.0.0
      (then point the sidebar at ${OUT})

  Or read the report directly:
      less ${OUT}/report.md

EOF
