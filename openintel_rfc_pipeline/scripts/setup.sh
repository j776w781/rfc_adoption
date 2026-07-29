#!/usr/bin/env bash
#
# Set up the OpenINTEL RFC-adoption pipeline on a Linux server.
#
# Idempotent: safe to re-run. Installs system build dependencies (with sudo,
# unless --no-sudo), creates a virtualenv, installs Python dependencies,
# verifies the install by running the full offline demo and the test suite, and
# prints machine-derived tuning for the real run.
#
#   ./scripts/setup.sh                 # full setup + verification
#   ./scripts/setup.sh --no-sudo       # skip system packages
#   ./scripts/setup.sh --skip-tests    # faster; skips pytest
#   ./scripts/setup.sh --minimal       # deps only, no demo, no tests
#   ./scripts/setup.sh --help

set -euo pipefail
# shellcheck source=./common.sh
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/common.sh"

SKIP_SYSTEM=0
SKIP_DEMO=0
SKIP_TESTS=0
WITH_DASHBOARD=1

usage() {
    sed -n '2,/^set -euo/p' "$0" | sed 's/^# \{0,1\}//; $d'
    cat <<'EOF'
Options:
  --no-sudo          Do not install system packages (assumes Python 3.10+ present)
  --skip-demo        Do not run the offline demo after installing
  --skip-tests       Do not run pytest after installing
  --minimal          Implies --skip-demo --skip-tests
  --no-dashboard     Do not install streamlit/plotly (headless analysis only)
  --venv PATH        Virtualenv location (default: ./.venv)
  --python PATH      Interpreter to build the venv from
  --yes              Do not prompt
  --help             Show this message

Environment:
  VENV_DIR, PYTHON_BIN, DUCKDB_THREADS, DUCKDB_MEMORY_LIMIT, NO_COLOR
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --no-sudo)      SKIP_SYSTEM=1; NO_SUDO=1; export NO_SUDO ;;
        --skip-demo)    SKIP_DEMO=1 ;;
        --skip-tests)   SKIP_TESTS=1 ;;
        --minimal)      SKIP_DEMO=1; SKIP_TESTS=1 ;;
        --no-dashboard) WITH_DASHBOARD=0 ;;
        --venv)         VENV_DIR="${2:?--venv needs a path}"; shift ;;
        --python)       PYTHON_BIN="${2:?--python needs a path}"; export PYTHON_BIN; shift ;;
        --yes|-y)       ASSUME_YES=1; export ASSUME_YES ;;
        --help|-h)      usage; exit 0 ;;
        *)              die "Unknown option: $1 (try --help)" ;;
    esac
    shift
done

cd "${PROJECT_ROOT}"
ensure_log_dir
SETUP_LOG="${LOG_DIR}/setup-$(date +%Y%m%d-%H%M%S).log"

section "OpenINTEL RFC-adoption pipeline — setup"
log "project root : ${PROJECT_ROOT}"
log "virtualenv   : ${VENV_DIR}"
log "log file     : ${SETUP_LOG}"

# --------------------------------------------------------------------------- #
section "1. Machine"
# --------------------------------------------------------------------------- #

CORES="$(cpu_count)"
MEM_GB="$(memory_gb)"
DISK_GB="$(free_space_gb "${PROJECT_ROOT}")"
compute_tuning

log "cores        : ${CORES}"
log "memory       : ${MEM_GB} GB"
log "free disk    : ${DISK_GB} GB (at ${PROJECT_ROOT})"
log "duckdb       : threads=${DUCKDB_THREADS} memory_limit=${DUCKDB_MEMORY_LIMIT}"

# A multi-TLD multi-year run in download mode needs real disk. Streaming mode
# needs almost none, so this is a warning rather than a hard failure.
if [[ "${DISK_GB}" -lt 50 ]]; then
    warn "Only ${DISK_GB} GB free. Download mode will need far more than that for a"
    warn "multi-year run; prefer --mode stream, or point --cache-dir at a large volume."
fi

# --------------------------------------------------------------------------- #
section "2. System packages"
# --------------------------------------------------------------------------- #

if [[ "${SKIP_SYSTEM}" == "1" ]]; then
    log "skipped (--no-sudo)"
elif ! have_sudo; then
    warn "No usable sudo; skipping system packages."
    warn "If the venv step fails, install python3-venv and build tools by hand."
else
    PM="$(detect_package_manager)"
    log "package manager: ${PM}"
    case "${PM}" in
        apt)
            as_root apt-get update -qq
            as_root apt-get install -y -qq \
                python3 python3-venv python3-dev python3-pip \
                build-essential ca-certificates curl git tmux >>"${SETUP_LOG}" 2>&1
            ;;
        dnf|yum)
            as_root "${PM}" install -y \
                python3 python3-devel python3-pip gcc gcc-c++ make \
                ca-certificates curl git tmux >>"${SETUP_LOG}" 2>&1
            ;;
        zypper)
            as_root zypper --non-interactive install \
                python3 python3-devel python3-pip gcc gcc-c++ make \
                ca-certificates curl git tmux >>"${SETUP_LOG}" 2>&1
            ;;
        pacman)
            as_root pacman -Sy --noconfirm \
                python python-pip base-devel ca-certificates curl git tmux >>"${SETUP_LOG}" 2>&1
            ;;
        apk)
            as_root apk add --no-cache \
                python3 python3-dev py3-pip build-base ca-certificates curl git tmux >>"${SETUP_LOG}" 2>&1
            ;;
        none)
            warn "No known package manager; skipping. Ensure Python 3.10+ and a C toolchain exist."
            ;;
    esac
    [[ "${PM}" == "none" ]] || ok "system packages present"
fi

# --------------------------------------------------------------------------- #
section "3. Python virtualenv"
# --------------------------------------------------------------------------- #

PY="$(find_python)" || die "No Python >= 3.10 found. Install it, or pass --python /path/to/python3.12"
log "interpreter  : ${PY} ($(${PY} -c 'import platform;print(platform.python_version())'))"

if [[ -x "${VENV_DIR}/bin/python" ]]; then
    log "reusing existing virtualenv"
else
    "${PY}" -m venv "${VENV_DIR}" \
        || die "Could not create a virtualenv. On Debian/Ubuntu: apt-get install python3-venv"
    ok "created ${VENV_DIR}"
fi

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"
python -m pip install --quiet --upgrade pip setuptools wheel >>"${SETUP_LOG}" 2>&1
ok "pip $(python -m pip --version | awk '{print $2}')"

# --------------------------------------------------------------------------- #
section "4. Python dependencies"
# --------------------------------------------------------------------------- #

log "installing core requirements (this is the slow step)"
python -m pip install --quiet -r requirements.txt >>"${SETUP_LOG}" 2>&1 \
    || die "pip install failed. See ${SETUP_LOG}"
ok "core requirements installed"

# boto3 is only needed to reach the real OpenINTEL S3 corpus, so it is not in
# the MVP requirements. A server setup always wants it.
log "installing boto3 (real OpenINTEL S3 access)"
python -m pip install --quiet 'boto3>=1.34' 'botocore>=1.34' >>"${SETUP_LOG}" 2>&1 \
    || die "Could not install boto3. See ${SETUP_LOG}"
ok "boto3 installed"

if [[ "${WITH_DASHBOARD}" == "0" ]]; then
    log "dashboard deps skipped (--no-dashboard)"
fi

export PYTHONPATH="${PROJECT_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"

# --------------------------------------------------------------------------- #
section "5. Verifying the install"
# --------------------------------------------------------------------------- #

python - <<'PY' || die "Import check failed — the environment is not usable."
import importlib, sys

required = ["pandas", "pyarrow", "duckdb", "pydantic", "boto3"]
optional = ["streamlit", "plotly", "pytest"]
missing = []
for name in required:
    try:
        module = importlib.import_module(name)
        print(f"  {name:<12} {getattr(module, '__version__', '?')}")
    except ImportError:
        missing.append(name)
for name in optional:
    try:
        module = importlib.import_module(name)
        print(f"  {name:<12} {getattr(module, '__version__', '?')} (optional)")
    except ImportError:
        print(f"  {name:<12} not installed (optional)")
if missing:
    print("MISSING:", ", ".join(missing), file=sys.stderr)
    sys.exit(1)

import openintel_rfc
print(f"  openintel_rfc {openintel_rfc.__version__}")
PY

# DuckDB httpfs is what stream mode needs. Probe it now rather than three hours
# into a run.
python - <<'PY' || warn "DuckDB httpfs is unavailable; --mode stream will not work (use --mode download)."
import duckdb
con = duckdb.connect()
con.execute("INSTALL httpfs")
con.execute("LOAD httpfs")
print("  duckdb httpfs ready")
con.close()
PY

ok "environment verified"

# --------------------------------------------------------------------------- #
section "6. Offline demo"
# --------------------------------------------------------------------------- #

if [[ "${SKIP_DEMO}" == "1" ]]; then
    log "skipped"
else
    python data/sample_parquet/create_sample_parquet.py >>"${SETUP_LOG}" 2>&1
    python -m openintel_rfc.cli tool-survey --out docs/open_source_tool_survey.md >>"${SETUP_LOG}" 2>&1
    python -m openintel_rfc.cli schema-check \
        --checklists data/rfc_checklists/dnssec_rfc_checklists.json \
        --dictionary data/openintel_dictionary/sample_openintel_dictionary.json \
        --out demo_output >>"${SETUP_LOG}" 2>&1
    python -m openintel_rfc.cli analyze \
        --checklists data/rfc_checklists/dnssec_rfc_checklists.json \
        --dictionary data/openintel_dictionary/sample_openintel_dictionary.json \
        --parquet data/sample_parquet/sample_openintel.parquet \
        --out demo_output 2>/dev/null | grep -E 'signals x|^  [0-9]\.' || true
    ok "demo artefacts in demo_output/"
fi

# --------------------------------------------------------------------------- #
section "7. Tests"
# --------------------------------------------------------------------------- #

if [[ "${SKIP_TESTS}" == "1" ]]; then
    log "skipped"
else
    if python -m pytest -q 2>&1 | tail -n 3; then
        ok "test suite passed"
    else
        die "Tests failed. The environment is installed but the pipeline is not trustworthy here."
    fi
fi

# --------------------------------------------------------------------------- #
section "Setup complete"
# --------------------------------------------------------------------------- #

cat <<EOF

  Activate the environment:
      source ${VENV_DIR}/bin/activate
      export PYTHONPATH=${PROJECT_ROOT}/src

  1. See what the real corpus holds, without scanning anything:
      ./scripts/run_full_analysis.sh --sources nu --start 2018-05-01 --end 2018-05-01 --dry-run

     This reports the available sources, the partition count, and whether the
     real schema can actually answer the checklist. Do it before every new range.

  2. Smoke-test one real TLD-day end to end (~1 minute):
      ./scripts/run_full_analysis.sh --sources nu --start 2018-05-01 --end 2018-05-01

  3. Size the range you actually want, then fetch it:
      ./scripts/fetch_openintel.sh --sources nu,se --start 2015-01-01 --end 2021-12-31 --list
      ./scripts/fetch_openintel.sh --sources nu,se --start 2015-01-01 --end 2021-12-31 \\
          --cache-dir /large/volume

  4. The real run. Use tmux: this takes hours to days, and it resumes.
      tmux new -s openintel
      ./scripts/run_full_analysis.sh --mode download --cache-dir /large/volume \\
          --sources nu,se --start 2015-01-01 --end 2021-12-31 --pace-seconds 2

     --mode download is deliberate, not a fallback. Measured on a real partition
     it is ~2x faster than streaming cold and ~3.3x faster on a re-scan, and it
     issues one sequential request per object instead of thousands of small range
     reads against a store that rate-limits on request count. See
     docs/running_at_scale.md section 4a.

  5. Inspect the results:
      streamlit run dashboard/app.py --server.port 8501 --server.address 0.0.0.0

  Tuning for this machine: memory_limit=${DUCKDB_MEMORY_LIMIT}, threads=${CORES}
  local / ${STREAM_THREAD_CAP} when streaming (extra threads buy ~5% on a
  network-bound scan and materially raise the chance of being throttled).

  Full setup log: ${SETUP_LOG}

EOF
