#!/usr/bin/env bash
#
# Nightly collection and analysis. Designed to be run from cron on the server:
#
#   15 3 * * *  /path/to/rfc_adoption/scripts/nightly.sh >> /var/log/rfc-nightly.log 2>&1
#
# Four stages, each independently resumable and each safe to interrupt:
#
#   1. reverse    fetch yesterday's RIPE reverse-delegation zones and ingest them
#   2. mirror     mirror any new OpenINTEL partitions to local disk
#   3. scan       scan whatever is on disk that has no checkpoint yet
#   4. report     re-derive the classification, charts and figures
#
# The design rule throughout: a nightly job that has to be watched is not a
# nightly job. Every stage skips what it already did, a stage that fails does not
# stop the ones after it that do not depend on it, and the run writes one status
# line per stage so a failure is visible in a log tail rather than by reading
# thousands of lines.
#
# A single run is small. The reverse archive is one ~100 MB tarball; the
# OpenINTEL delta is one day per source. The expensive part -- the historical
# backfill -- is a separate, one-time job (see --backfill).

set -uo pipefail   # NOT -e: a failing stage must not abort the ones after it.
# shellcheck source=./common.sh
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/common.sh"

# --------------------------------------------------------------------------- #
# Configuration -- override any of these from the environment or cron
# --------------------------------------------------------------------------- #

DATA_ROOT="${DATA_ROOT:-${PROJECT_ROOT}/out/nightly}"
REVERSE_CORPUS="${REVERSE_CORPUS:-${DATA_ROOT}/reverse/corpus}"
OPENINTEL_CACHE="${OPENINTEL_CACHE:-${DATA_ROOT}/openintel/cache}"
CHECKPOINTS="${CHECKPOINTS:-${DATA_ROOT}/checkpoints}"
ANALYSIS_OUT="${ANALYSIS_OUT:-${DATA_ROOT}/analysis}"
RUN_LOG_DIR="${RUN_LOG_DIR:-${DATA_ROOT}/logs}"

# OpenINTEL sources to track nightly. Keep this short: each one is a full day of
# partitions, and .se alone is ~2 GB/day.
OPENINTEL_SOURCES="${OPENINTEL_SOURCES:-gov,nu}"

# How many days back to look. OpenINTEL and RIPE both publish with a lag, and a
# window wider than one day is what makes a missed night self-healing rather than
# a permanent hole.
LOOKBACK_DAYS="${LOOKBACK_DAYS:-4}"

# Shard identity, for when several machines share the nightly load. The store's
# limiter is per endpoint, not per process -- see README.
SHARDS="${SHARDS:-1}"
SHARD="${SHARD:-0}"

# Retain raw reverse-zone tarballs? They are ~100 MB/day and the Parquet derived
# from them is ~6 MB, so the default discards them.
KEEP_ARCHIVES="${KEEP_ARCHIVES:-0}"

BACKFILL=0
SKIP_REVERSE=0
SKIP_OPENINTEL=0
DRY_RUN=0

usage() {
    cat <<'EOF'
Usage: nightly.sh [options]

Collects one night of DNSSEC measurement data and re-derives the analysis.
Every stage is resumable; re-running after a failure costs only the work that
did not finish.

Options:
  --backfill FROM..TO   One-time historical ingest instead of a nightly delta,
                        e.g. --backfill 2009-03-24..2026-08-01. Monthly sampling.
  --sources LIST        OpenINTEL sources (default: gov,nu)
  --lookback N          Days back to consider each night (default: 4)
  --shards N --shard I  Split the night's fetching across N machines, 0-based I
  --skip-reverse        Do not touch the RIPE reverse-zone archive
  --skip-openintel      Do not touch OpenINTEL
  --keep-archives       Keep the raw .tar.bz2 files after ingesting
  --data-root DIR       Where everything lives (default: <repo>/out/nightly)
  --dry-run             Print what each stage would do, change nothing
  --help

Environment overrides: DATA_ROOT, REVERSE_CORPUS, OPENINTEL_CACHE, CHECKPOINTS,
ANALYSIS_OUT, OPENINTEL_SOURCES, LOOKBACK_DAYS, SHARDS, SHARD, KEEP_ARCHIVES.
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --backfill)       BACKFILL_RANGE="${2:?}"; BACKFILL=1; shift ;;
        --sources)        OPENINTEL_SOURCES="${2:?}"; shift ;;
        --lookback)       LOOKBACK_DAYS="${2:?}"; shift ;;
        --shards)         SHARDS="${2:?}"; shift ;;
        --shard)          SHARD="${2:?}"; shift ;;
        --data-root)      DATA_ROOT="${2:?}"; shift ;;
        --skip-reverse)   SKIP_REVERSE=1 ;;
        --skip-openintel) SKIP_OPENINTEL=1 ;;
        --keep-archives)  KEEP_ARCHIVES=1 ;;
        --dry-run)        DRY_RUN=1 ;;
        --help|-h)        usage; exit 0 ;;
        *)                die "Unknown option: $1 (try --help)" ;;
    esac
    shift
done

# Re-derive the paths that hang off DATA_ROOT, in case --data-root moved it.
REVERSE_CORPUS="${DATA_ROOT}/reverse/corpus"
OPENINTEL_CACHE="${DATA_ROOT}/openintel/cache"
CHECKPOINTS="${DATA_ROOT}/checkpoints"
ANALYSIS_OUT="${DATA_ROOT}/analysis"
RUN_LOG_DIR="${DATA_ROOT}/logs"

# --------------------------------------------------------------------------- #
# Stage plumbing
# --------------------------------------------------------------------------- #

RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
STATUS_FILE="${RUN_LOG_DIR}/status-${RUN_ID}.txt"
declare -a STAGE_RESULTS=()

run_stage() {
    # run_stage <name> <command...>
    local name="$1"; shift
    section "${name}"
    if [[ "${DRY_RUN}" == "1" ]]; then
        log "dry-run: $*"
        STAGE_RESULTS+=("${name}=skipped(dry-run)")
        return 0
    fi
    local started elapsed rc
    started="$(date +%s)"
    "$@" 2>&1 | tee -a "${RUN_LOG_DIR}/${name}-${RUN_ID}.log"
    rc="${PIPESTATUS[0]}"
    elapsed=$(( $(date +%s) - started ))
    if [[ "${rc}" -eq 0 ]]; then
        ok "${name} finished in ${elapsed}s"
        STAGE_RESULTS+=("${name}=ok(${elapsed}s)")
    else
        # Deliberately not fatal. A night where the reverse archive is
        # unreachable should still scan and report on what is already local.
        warn "${name} exited ${rc} after ${elapsed}s; later stages continue"
        STAGE_RESULTS+=("${name}=FAILED(rc=${rc})")
    fi
    printf '%s\n' "${STAGE_RESULTS[-1]}" >> "${STATUS_FILE}"
    return 0
}

# Portable date arithmetic: GNU date and BSD date disagree, and the server may be
# either.
days_ago() {
    local n="$1"
    date -u -d "${n} days ago" +%Y-%m-%d 2>/dev/null \
        || date -u -v-"${n}"d +%Y-%m-%d 2>/dev/null \
        || python3 -c "import datetime,sys;print((datetime.date.today()-datetime.timedelta(days=int(sys.argv[1]))).isoformat())" "${n}"
}

# --------------------------------------------------------------------------- #
# Setup
# --------------------------------------------------------------------------- #

mkdir -p "${RUN_LOG_DIR}" "${REVERSE_CORPUS}" "${OPENINTEL_CACHE}" \
         "${CHECKPOINTS}" "${ANALYSIS_OUT}"

activate_venv
prepend_pythonpath "${PROJECT_ROOT}/src"
CLI=(python -m openintel_rfc.cli)

if [[ "${BACKFILL}" == "1" ]]; then
    START="${BACKFILL_RANGE%%..*}"
    END="${BACKFILL_RANGE##*..}"
    [[ "${START}" != "${END}" ]] || die "--backfill wants FROM..TO, got '${BACKFILL_RANGE}'"
else
    START="$(days_ago "${LOOKBACK_DAYS}")"
    END="$(days_ago 1)"
fi

info "Nightly run ${RUN_ID}"
log "window       : ${START} .. ${END}$( [[ ${BACKFILL} == 1 ]] && echo '  (backfill, monthly)')"
log "data root    : ${DATA_ROOT}"
log "openintel    : ${OPENINTEL_SOURCES}"
log "shard        : ${SHARD} of ${SHARDS}"
log "free space   : $(free_space_gb "${DATA_ROOT}") GB"

# --------------------------------------------------------------------------- #
# 1. RIPE reverse-delegation zones
# --------------------------------------------------------------------------- #

stage_reverse() {
    local args=(ingest-reverse --start "${START}" --end "${END}"
                --cache-dir "${REVERSE_CORPUS}")
    [[ "${BACKFILL}"      == "1" ]] && args+=(--monthly)
    [[ "${KEEP_ARCHIVES}" == "1" ]] && args+=(--keep-archives)
    "${CLI[@]}" "${args[@]}"
}

if [[ "${SKIP_REVERSE}" == "0" ]]; then
    run_stage reverse-ingest stage_reverse
else
    log "reverse-ingest skipped (--skip-reverse)"
fi

# --------------------------------------------------------------------------- #
# 2. OpenINTEL mirror
# --------------------------------------------------------------------------- #
# Mirroring rather than streaming: one request per object, paid once, after which
# the scan is local. See the "Mirror once, scan many times" section of the README.

stage_mirror() {
    "${CLI[@]}" mirror \
        --sources "${OPENINTEL_SOURCES}" \
        --start "${START}" --end "${END}" \
        --cache-dir "${OPENINTEL_CACHE}" \
        --shards "${SHARDS}" --shard "${SHARD}"
}

if [[ "${SKIP_OPENINTEL}" == "0" ]]; then
    run_stage openintel-mirror stage_mirror
else
    log "openintel-mirror skipped (--skip-openintel)"
fi

# --------------------------------------------------------------------------- #
# 3. Scan whatever is on disk
# --------------------------------------------------------------------------- #
# Both scans read local files only (--local-corpus), so this stage never touches
# the network and cannot be throttled. Partitions already checkpointed are
# skipped, which is what makes a re-run after a failed night cheap.

stage_scan_reverse() {
    "${CLI[@]}" scale \
        --sources afrinic,apnic,arin,lacnic,ripe \
        --start "${START}" --end "${END}" \
        --basis reverse --local-corpus --mode download \
        --cache-dir "${REVERSE_CORPUS}" \
        --out "${ANALYSIS_OUT}/reverse" \
        --checkpoint-dir "${CHECKPOINTS}/reverse" \
        --pace-seconds 0
}

stage_scan_openintel() {
    "${CLI[@]}" scale \
        --sources "${OPENINTEL_SOURCES}" \
        --start "${START}" --end "${END}" \
        --basis zonefile --local-corpus --mode download \
        --cache-dir "${OPENINTEL_CACHE}" \
        --out "${ANALYSIS_OUT}/openintel" \
        --checkpoint-dir "${CHECKPOINTS}/openintel" \
        --pace-seconds 0
}

[[ "${SKIP_REVERSE}"   == "0" ]] && run_stage scan-reverse   stage_scan_reverse
[[ "${SKIP_OPENINTEL}" == "0" ]] && run_stage scan-openintel stage_scan_openintel

# --------------------------------------------------------------------------- #
# 4. Re-derive the explainable outputs
# --------------------------------------------------------------------------- #
# Cheap and deterministic, so it runs every night regardless of what the earlier
# stages managed. It is also the stage that would surface a checklist edit: the
# classification is re-derived from the checklist and the dictionary, not cached.

stage_report() {
    "${CLI[@]}" schema-check --out "${ANALYSIS_OUT}/schema" || return 1
    python "${PROJECT_ROOT}/reporting/rfc_classification.py" \
        "${ANALYSIS_OUT}/schema/schema_check.json" \
        "${PROJECT_ROOT}/data/rfc_checklists/dnssec_rfc_checklists.json" \
        "${ANALYSIS_OUT}/classification" || return 1
    if [[ -d "${REVERSE_CORPUS}/reverse/_summary" ]]; then
        python "${PROJECT_ROOT}/reporting/reverse_adoption.py" \
            "${REVERSE_CORPUS}" "${CHECKPOINTS}/reverse" \
            "${ANALYSIS_OUT}/charts" || return 1
    fi
}

run_stage report stage_report

# --------------------------------------------------------------------------- #
# Summary
# --------------------------------------------------------------------------- #

section "Nightly ${RUN_ID} summary"
failed=0
for result in "${STAGE_RESULTS[@]}"; do
    case "${result}" in
        *FAILED*) warn "  ${result}"; failed=$((failed + 1)) ;;
        *)        ok   "  ${result}" ;;
    esac
done
log "status file  : ${STATUS_FILE}"
log "analysis     : ${ANALYSIS_OUT}"
log "disk used    : $(du -sh "${DATA_ROOT}" 2>/dev/null | cut -f1)"

if [[ "${failed}" -gt 0 ]]; then
    warn "${failed} stage(s) failed; the run is resumable -- re-run to retry only those."
    exit 1
fi
ok "All stages completed."
