#!/usr/bin/env bash
# Shared helpers for the OpenINTEL RFC-adoption scripts.
# Sourced, never executed directly.

set -euo pipefail

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #

# Resolve the project root from this file's location, so the scripts work no
# matter which directory they are invoked from.
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
VENV_DIR="${VENV_DIR:-${PROJECT_ROOT}/.venv}"
LOG_DIR="${LOG_DIR:-${PROJECT_ROOT}/logs}"

export PROJECT_ROOT VENV_DIR LOG_DIR

# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #

if [[ -t 1 ]] && [[ -z "${NO_COLOR:-}" ]]; then
    C_RESET=$'\033[0m'; C_BOLD=$'\033[1m'; C_DIM=$'\033[2m'
    C_RED=$'\033[31m'; C_GREEN=$'\033[32m'; C_YELLOW=$'\033[33m'; C_BLUE=$'\033[34m'
else
    C_RESET=''; C_BOLD=''; C_DIM=''; C_RED=''; C_GREEN=''; C_YELLOW=''; C_BLUE=''
fi

log()      { printf '%s[%s]%s %s\n' "${C_DIM}" "$(date +%H:%M:%S)" "${C_RESET}" "$*"; }
info()     { printf '%s==>%s %s\n' "${C_BLUE}${C_BOLD}" "${C_RESET}" "$*"; }
ok()       { printf '%s  ok%s %s\n' "${C_GREEN}" "${C_RESET}" "$*"; }
warn()     { printf '%swarn%s %s\n' "${C_YELLOW}" "${C_RESET}" "$*" >&2; }
die()      { printf '%serror%s %s\n' "${C_RED}${C_BOLD}" "${C_RESET}" "$*" >&2; exit 1; }
section()  { printf '\n%s%s%s\n' "${C_BOLD}" "$*" "${C_RESET}"; }

# --------------------------------------------------------------------------- #
# Environment discovery
# --------------------------------------------------------------------------- #

detect_package_manager() {
    if   command -v apt-get >/dev/null 2>&1; then echo apt
    elif command -v dnf     >/dev/null 2>&1; then echo dnf
    elif command -v yum     >/dev/null 2>&1; then echo yum
    elif command -v zypper  >/dev/null 2>&1; then echo zypper
    elif command -v pacman  >/dev/null 2>&1; then echo pacman
    elif command -v apk     >/dev/null 2>&1; then echo apk
    else echo none
    fi
}

# Number of usable CPU cores.
cpu_count() {
    if command -v nproc >/dev/null 2>&1; then nproc
    elif [[ -r /proc/cpuinfo ]]; then grep -c '^processor' /proc/cpuinfo
    else echo 4
    fi
}

# Total system memory in whole GB (floor), 0 when it cannot be determined.
memory_gb() {
    if [[ -r /proc/meminfo ]]; then
        awk '/^MemTotal:/ {printf "%d", $2/1048576}' /proc/meminfo
    elif command -v sysctl >/dev/null 2>&1; then
        sysctl -n hw.memsize 2>/dev/null | awk '{printf "%d", $1/1073741824}'
    else
        echo 0
    fi
}

# Free space in GB at a path (the path need not exist yet).
free_space_gb() {
    local target="$1"
    while [[ ! -d "${target}" && "${target}" != "/" ]]; do target="$(dirname "${target}")"; done
    # `--output` is GNU coreutils only; fall back to POSIX df -P (1K blocks) so
    # this still reports something useful on BusyBox, Alpine or macOS.
    local gb
    gb="$(df -BG --output=avail "${target}" 2>/dev/null | tail -n1 | tr -dc '0-9')"
    if [[ -z "${gb}" ]]; then
        gb="$(df -Pk "${target}" 2>/dev/null | awk 'NR==2 {printf "%d", $4/1048576}')"
    fi
    echo "${gb:-0}"
}

have_sudo() {
    [[ "${NO_SUDO:-0}" == "1" ]] && return 1
    if [[ "$(id -u)" == "0" ]]; then return 0; fi
    command -v sudo >/dev/null 2>&1 && sudo -n true 2>/dev/null
}

as_root() {
    if [[ "$(id -u)" == "0" ]]; then "$@"; else sudo "$@"; fi
}

# --------------------------------------------------------------------------- #
# Python / virtualenv
# --------------------------------------------------------------------------- #

# Echo the best available interpreter that satisfies the >=3.10 requirement.
find_python() {
    local explicit="${PYTHON_BIN:-}"
    if [[ -n "${explicit}" ]]; then
        "${explicit}" -c 'import sys; sys.exit(0 if sys.version_info>=(3,10) else 1)' 2>/dev/null \
            && { echo "${explicit}"; return 0; }
        die "PYTHON_BIN=${explicit} is not a Python >= 3.10 interpreter."
    fi
    local candidate
    for candidate in python3.13 python3.12 python3.11 python3.10 python3 python; do
        if command -v "${candidate}" >/dev/null 2>&1 && \
           "${candidate}" -c 'import sys; sys.exit(0 if sys.version_info>=(3,10) else 1)' 2>/dev/null; then
            command -v "${candidate}"; return 0
        fi
    done
    return 1
}

activate_venv() {
    export PYTHONPATH="${PROJECT_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"

    # POSIX layout first, then the Windows/Git-Bash layout, so the scripts can be
    # exercised on a developer machine before they are trusted on the server.
    local activate
    for activate in "${VENV_DIR}/bin/activate" "${VENV_DIR}/Scripts/activate"; do
        if [[ -f "${activate}" ]]; then
            # shellcheck disable=SC1090
            source "${activate}"
            return 0
        fi
    done

    # No venv. That is not automatically an error: conda, pyenv and system-wide
    # installs are all legitimate, and refusing to run would be obstructive. Only
    # fail if the package genuinely cannot be imported.
    if python -c 'import openintel_rfc' >/dev/null 2>&1; then
        warn "No virtualenv at ${VENV_DIR}; using the ambient Python ($(command -v python))."
        return 0
    fi

    die "No virtualenv at ${VENV_DIR} and openintel_rfc is not importable from the
     ambient Python. Run scripts/setup.sh first, or activate the environment
     you installed it into."
}

# --------------------------------------------------------------------------- #
# Tuning
# --------------------------------------------------------------------------- #

# Cap on threads in stream mode. Measured on a real partition, a remote scan
# takes 5.6 s at 20 threads and 5.9 s at 2 -- a 1.07x spread, because the work is
# network-bound. But each thread issues its own HTTP range requests, and
# OpenINTEL rate-limits on request count, so the extra threads buy ~5% time and
# cost a much higher chance of being throttled off the store entirely.
STREAM_THREAD_CAP="${STREAM_THREAD_CAP:-8}"

# DuckDB settings derived from the machine, and from how the data is being read.
#
# Memory is capped at 70% of RAM so a long scan cannot push the box into the OOM
# killer, which on a multi-day run is the difference between a resumable
# checkpoint and losing the night's work.
#
# Pass the access mode ("stream" or "download") to get an appropriate thread
# count: a local scan is CPU-bound and wants every core, a remote one is not.
compute_tuning() {
    local mode="${1:-download}"
    local cores mem default_threads
    cores="$(cpu_count)"
    mem="$(memory_gb)"

    default_threads="${cores}"
    if [[ "${mode}" == "stream" ]] && [[ "${cores}" -gt "${STREAM_THREAD_CAP}" ]]; then
        default_threads="${STREAM_THREAD_CAP}"
    fi
    DUCKDB_THREADS="${DUCKDB_THREADS:-${default_threads}}"

    if [[ "${mem}" -gt 0 ]]; then
        DUCKDB_MEMORY_LIMIT="${DUCKDB_MEMORY_LIMIT:-$(( mem * 70 / 100 ))GB}"
    else
        DUCKDB_MEMORY_LIMIT="${DUCKDB_MEMORY_LIMIT:-8GB}"
    fi
    export DUCKDB_THREADS DUCKDB_MEMORY_LIMIT
}

ensure_log_dir() { mkdir -p "${LOG_DIR}"; }

# Confirm a destructive or long-running action unless --yes was passed.
confirm() {
    [[ "${ASSUME_YES:-0}" == "1" ]] && return 0
    local prompt="${1:-Continue?}"
    read -r -p "${prompt} [y/N] " reply
    [[ "${reply}" =~ ^[Yy] ]]
}
