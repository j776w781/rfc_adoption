#!/usr/bin/env bash
# Full-system verification. Every check prints PASS or FAIL and the suite
# returns non-zero if anything failed, so this is usable as a gate.
set -uo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
# shellcheck source=./common.sh
source "$ROOT/scripts/common.sh"
TMP="$(mktemp -d 2>/dev/null || echo "$ROOT/.verify_tmp")"
trap 'rm -rf "$TMP"' EXIT
activate_venv

# The live OpenINTEL checks need outbound HTTPS to object.openintel.nl. They are
# skipped rather than failed when it is unreachable, so this stays usable as an
# offline gate.
OFFLINE=0
python -c "
import socket, sys
try:
    socket.create_connection(('object.openintel.nl', 443), timeout=8).close()
except OSError:
    sys.exit(1)
" >/dev/null 2>&1 || OFFLINE=1
rm -rf "$TMP" && mkdir -p "$TMP"

PASS=0; FAIL=0; FAILED_NAMES=()
check() {  # check <name> <expected> <actual>
    if [[ "$2" == "$3" ]]; then
        printf '  PASS  %-52s %s\n' "$1" "$3"; PASS=$((PASS+1))
    else
        printf '  FAIL  %-52s got=%s want=%s\n' "$1" "$3" "$2"; FAIL=$((FAIL+1)); FAILED_NAMES+=("$1")
    fi
}
checkcmd() {  # checkcmd <name> <command...>
    local name="$1"; shift
    if "$@" >"$TMP/last.out" 2>&1; then
        printf '  PASS  %s\n' "$name"; PASS=$((PASS+1))
    else
        printf '  FAIL  %s (see %s)\n' "$name" "$TMP/last.out"; FAIL=$((FAIL+1)); FAILED_NAMES+=("$name")
        tail -4 "$TMP/last.out" | sed 's/^/          /'
    fi
}
section() { printf '\n\033[1m%s\033[0m\n' "$1"; }

# --------------------------------------------------------------------------- #
section "A. Environment"
# --------------------------------------------------------------------------- #
check "python >= 3.10" "ok" \
  "$(python -c 'import sys;print("ok" if sys.version_info>=(3,10) else "no")')"
for mod in pandas pyarrow duckdb pydantic streamlit plotly boto3 pytest; do
    check "import $mod" "ok" "$(python -c "import $mod" 2>/dev/null && echo ok || echo MISSING)"
done
check "openintel_rfc importable" "ok" \
  "$(python -c 'import openintel_rfc' 2>/dev/null && echo ok || echo no)"
check "duckdb httpfs loads" "ok" \
  "$(python -c "import duckdb;c=duckdb.connect();c.execute('INSTALL httpfs');c.execute('LOAD httpfs')" 2>/dev/null && echo ok || echo no)"

# --------------------------------------------------------------------------- #
section "B. Test suite"
# --------------------------------------------------------------------------- #
python -m pytest >"$TMP/pytest.out" 2>&1; PYTEST_RC=$?
sed -i 's/\[[0-9;]*m//g' "$TMP/pytest.out"
PYTEST_LINE="$(grep -oE '[0-9]+ (passed|failed).*' "$TMP/pytest.out" | tail -1)"
check "pytest exit status" "0" "$PYTEST_RC"
printf '        %s\n' "${PYTEST_LINE:-no summary found}"
check "no test failures" "0" "$(grep -cE '^FAILED|[0-9]+ failed' "$TMP/pytest.out")"

# --------------------------------------------------------------------------- #
section "C. Clean demo from scratch"
# --------------------------------------------------------------------------- #
find demo_output -type f ! -name '.gitkeep' -delete
checkcmd "create_sample_parquet.py" python data/sample_parquet/create_sample_parquet.py
checkcmd "cli tool-survey" python -m openintel_rfc.cli tool-survey --out "$TMP/survey.md"
checkcmd "cli schema-check" python -m openintel_rfc.cli schema-check \
    --checklists data/rfc_checklists/dnssec_rfc_checklists.json \
    --dictionary data/openintel_dictionary/sample_openintel_dictionary.json \
    --out demo_output
for f in queryable_indicators.json non_queryable_indicators.json \
         schema_check_report.md schema_check.csv schema_check.json; do
    check "schema-check wrote $f" "yes" "$([[ -s demo_output/$f ]] && echo yes || echo NO)"
done
checkcmd "cli analyze" python -m openintel_rfc.cli analyze \
    --checklists data/rfc_checklists/dnssec_rfc_checklists.json \
    --dictionary data/openintel_dictionary/sample_openintel_dictionary.json \
    --parquet data/sample_parquet/sample_openintel.parquet \
    --out demo_output
for f in observed_signals.json rfc_matches.json reasoning_traces.json \
         review_queue.json adoption_timeline.json ranked_candidates.json \
         report.md run_manifest.json rfc_matches.csv review_queue.csv \
         adoption_timeline.csv observed_signals.csv reasoning_traces.csv; do
    check "analyze wrote $f" "yes" "$([[ -s demo_output/$f ]] && echo yes || echo NO)"
done

section "C2. Demo results match the documented expectations"
python - <<'PY' > "$TMP/expect.txt"
import json
c = json.load(open('demo_output/ranked_candidates.json'))['candidates']
t = json.load(open('demo_output/reasoning_traces.json'))['traces']
r = json.load(open('demo_output/review_queue.json'))['review_items']
s = json.load(open('demo_output/observed_signals.json'))['signals']
from collections import Counter
d = Counter(x['decision'] for x in t)
by = {x['rfc_id']: x for x in c}
print(f"signals={len(s)}")
print(f"traces={len(t)}")
print(f"candidates={len(c)}")
print(f"review={len(r)}")
print(f"valid={d['valid_match']}")
print(f"tsinvalid={d['timestamp_invalid']}")
print(f"rank1={c[0]['rfc_id']}")
print(f"rank1score={c[0]['score']}")
print(f"rfc8078={by['RFC 8078']['score']}")
print(f"rfc7344={by['RFC 7344']['score']}")
print(f"rfc5155={by['RFC 5155']['score']}")
print(f"rfc4509={by['RFC 4509']['score']}")
print(f"rfc6605={by['RFC 6605']['score']}")
specific = ["RFC 4509","RFC 5155","RFC 6605","RFC 7344","RFC 8078","RFC 8080"]
base_rank = by['RFC 4033']['rank']
print(f"rfc4033below={'yes' if all(by[r]['rank'] < base_rank for r in specific if r in by) else 'NO'}")
lim = "This pipeline does not prove RFC adoption by itself."
print(f"limitation={'yes' if lim in open('demo_output/report.md',encoding='utf-8').read() else 'NO'}")
PY
get() { grep -oP "(?<=^$1=).*" "$TMP/expect.txt"; }
check "observed signals"            "73"       "$(get signals)"
# One trace per (signal x RFC). Checklist 0.2.0 carries 30 RFCs, so 73 x 30.
check "reasoning traces (73x30)"    "2190"     "$(get traces)"
check "ranked candidates"           "11"       "$(get candidates)"
check "review items"                "105"      "$(get review)"
check "valid matches"               "179"      "$(get valid)"
# Rose with the checklist: the added algorithm RFCs are older than several of the
# sample observations, and an observation predating its RFC is withheld by design.
check "timestamp-invalid"           "120"      "$(get tsinvalid)"
check "rank 1 is RFC 8078"          "RFC 8078" "$(get rank1)"
check "RFC 8078 score"              "17.25"    "$(get rfc8078)"
check "RFC 7344 score"              "11.25"    "$(get rfc7344)"
check "RFC 5155 score"              "17.25"    "$(get rfc5155)"
check "RFC 4509 score"              "11.25"    "$(get rfc4509)"
check "RFC 6605 score"              "13.125"   "$(get rfc6605)"
check "base DNSSEC below every specific RFC" "yes" "$(get rfc4033below)"
check "limitation sentence verbatim" "yes"     "$(get limitation)"

# --------------------------------------------------------------------------- #
section "D. Engine equivalence (duckdb vs pandas)"
# --------------------------------------------------------------------------- #
for eng in duckdb pandas; do
    OPENINTEL_RFC_DETERMINISTIC=1 python -m openintel_rfc.cli analyze \
        --checklists data/rfc_checklists/dnssec_rfc_checklists.json \
        --dictionary data/openintel_dictionary/sample_openintel_dictionary.json \
        --parquet data/sample_parquet/sample_openintel.parquet \
        --engine "$eng" --out "$TMP/eng_$eng" >/dev/null 2>&1
done
check "duckdb == pandas: rfc_matches" "same" \
  "$(cmp -s "$TMP/eng_duckdb/rfc_matches.json" "$TMP/eng_pandas/rfc_matches.json" && echo same || echo DIFFERENT)"
check "duckdb == pandas: traces" "same" \
  "$(cmp -s "$TMP/eng_duckdb/reasoning_traces.json" "$TMP/eng_pandas/reasoning_traces.json" && echo same || echo DIFFERENT)"
check "duckdb == pandas: candidates" "same" \
  "$(cmp -s "$TMP/eng_duckdb/ranked_candidates.json" "$TMP/eng_pandas/ranked_candidates.json" && echo same || echo DIFFERENT)"

# --------------------------------------------------------------------------- #
section "E. Determinism"
# --------------------------------------------------------------------------- #
for run in a b; do
    OPENINTEL_RFC_DETERMINISTIC=1 python -m openintel_rfc.cli analyze \
        --checklists data/rfc_checklists/dnssec_rfc_checklists.json \
        --dictionary data/openintel_dictionary/sample_openintel_dictionary.json \
        --parquet data/sample_parquet/sample_openintel.parquet \
        --out "$TMP/det_$run" >/dev/null 2>&1
done
DIFFS=0
for f in rfc_matches.json reasoning_traces.json ranked_candidates.json \
         adoption_timeline.json review_queue.json observed_signals.json; do
    cmp -s "$TMP/det_a/$f" "$TMP/det_b/$f" || DIFFS=$((DIFFS+1))
done
check "6 artefacts byte-identical across runs" "0" "$DIFFS"

# --------------------------------------------------------------------------- #
section "F. Run config resolves from any location"
# --------------------------------------------------------------------------- #
cp examples/sample_run_config.json ./root_cfg.json
mkdir -p deep/nested && cp examples/sample_run_config.json deep/nested/cfg.json
cp examples/sample_run_config.json "$TMP/outside_cfg.json"
for cfg in examples/sample_run_config.json ./root_cfg.json deep/nested/cfg.json "$TMP/outside_cfg.json"; do
    n=$(python -m openintel_rfc.cli analyze --config "$cfg" --out "$TMP/cfg" 2>&1 | grep -oE '^[0-9]+ signals' | grep -oE '[0-9]+')
    check "config: $(basename "$(dirname "$cfg")")/$(basename "$cfg")" "73" "${n:-ERROR}"
done
rm -f root_cfg.json && rm -rf deep

# --------------------------------------------------------------------------- #
section "G. Dashboard (headless, all pages)"
# --------------------------------------------------------------------------- #
python - . > "$TMP/dash.out" 2>&1 <<'DASHPY'
import pathlib, sys
from streamlit.testing.v1 import AppTest

root = pathlib.Path(sys.argv[1])
pages = [root / "dashboard" / "app.py"] + sorted((root / "dashboard" / "pages").glob("*.py"))
failures = 0
for page in pages:
    try:
        app = AppTest.from_file(str(page), default_timeout=180).run()
        if app.exception:
            print(f"FAIL {page.name}: {app.exception[0].message[:160]}")
            failures += 1
    except Exception as exc:  # noqa: BLE001 - a smoke test reports, it does not raise
        print(f"ERROR {page.name}: {type(exc).__name__}: {str(exc)[:160]}")
        failures += 1
print(f"failures: {failures} of {len(pages)}")
DASHPY
check "dashboard page failures" "failures: 0 of 10" "$(grep -oE 'failures: [0-9]+ of [0-9]+' "$TMP/dash.out")"

# --------------------------------------------------------------------------- #
section "H. Shell scripts"
# --------------------------------------------------------------------------- #
for f in scripts/*.sh; do
    check "bash -n $(basename "$f")" "ok" "$(bash -n "$f" 2>/dev/null && echo ok || echo SYNTAX_ERROR)"
done
SH_COUNT="$(git ls-files scripts/ | grep -c '\.sh$')"
check "every script executable in git index" "$SH_COUNT" "$(git ls-files -s scripts/ | grep -c 100755)"
check "scripts have no CR bytes in index" "0" \
  "$(for f in $(git ls-files scripts/); do git show ":$f" | tr -d '\n' | tr -cd '\r'; done | wc -c | tr -d ' ')"

# --------------------------------------------------------------------------- #
section "I. Live OpenINTEL S3"
if (( OFFLINE )); then
  printf "  SKIP  object.openintel.nl unreachable; live checks skipped\n"
else
# --------------------------------------------------------------------------- #
DRY="$(bash scripts/run_full_analysis.sh --sources nu --start 2018-05-01 --end 2018-05-01 \
        --out "$TMP/dry" --dry-run 2>&1)"
check "dry-run discovers the real partition" "1" \
  "$(echo "$DRY" | grep -oE '^[0-9]+ partition\(s\) match' | grep -oE '[0-9]+')"
check "dry-run probes the real schema (98 cols)" "98" \
  "$(echo "$DRY" | grep -oE 'Real schema of [^:]+: [0-9]+ columns' | grep -oE '[0-9]+ columns' | grep -oE '[0-9]+')"
# `set -o pipefail` makes the pipeline inherit the CLI's non-zero exit, which is
# exactly what a correct rejection produces -- so the && branch never ran and the
# check reported the opposite of the truth. Capture output first, then match.
python -m openintel_rfc.cli scale --sources nu,nl --start 2018-05-01 --end 2018-05-01     --out "$TMP/bad" --dry-run >"$TMP/bad.out" 2>&1 || true
check "bad source is rejected up front" "rejected"   "$(grep -q 'does not publish' "$TMP/bad.out" && echo rejected || echo ACCEPTED)"

section "I2. Real scale run (1 partition, download mode)"
bash scripts/run_full_analysis.sh --sources nu --start 2018-05-01 --end 2018-05-01 \
    --mode download --cache-dir "$TMP/cache" \
    --out "$TMP/real" --yes > "$TMP/real.log" 2>&1
check "scale run exit status" "0" "$?"
python - "$TMP/real" <<'PY' > "$TMP/real.txt"
import json, sys
from pathlib import Path
out = Path(sys.argv[1])
c = {x['rfc_id']: x for x in json.loads((out/'ranked_candidates.json').read_text())['candidates']}
m = json.loads((out/'run_manifest.json').read_text())
print(f"rows={m['counts']['rows']}")
print(f"sampled={str(m['counts'].get('sampled')).lower()}")
print(f"rfc5155={c.get('RFC 5155',{}).get('supporting_signal_count')}")
print(f"rfc4509={c.get('RFC 4509',{}).get('supporting_signal_count')}")
print(f"rfc6605={c.get('RFC 6605',{}).get('supporting_signal_count')}")
print(f"rfc7344={c.get('RFC 7344',{}).get('supporting_signal_count')}")
print(f"rfc4033={c.get('RFC 4033',{}).get('supporting_signal_count')}")
PY
rget() { grep -oP "(?<=^$1=).*" "$TMP/real.txt"; }
check "rows scanned (not exemplar count)" "2621052" "$(rget rows)"
check "manifest flags the run as sampled" "true"  "$(rget sampled)"
check "RFC 5155 = NSEC3+NSEC3PARAM"       "408997"  "$(rget rfc5155)"
check "RFC 4509 = DS/CDS digest_type=2"   "131626"  "$(rget rfc4509)"
check "RFC 6605 = algorithm 13/14"        "27631"   "$(rget rfc6605)"
check "RFC 7344 = CDS+CDNSKEY"            "179"     "$(rget rfc7344)"
check "RFC 4033 = DNSKEY+DS+RRSIG+NSEC"   "2211876" "$(rget rfc4033)"

fi

# --------------------------------------------------------------------------- #
section "J. Artefact integrity"
# --------------------------------------------------------------------------- #
check "every demo JSON parses" "ok" \
  "$(python -c "
import json,glob,sys
for f in glob.glob('demo_output/*.json'):
    json.load(open(f,encoding='utf-8'))
print('ok')" 2>&1 | tail -1)"
check "every demo CSV parses" "ok" \
  "$(python -c "
import csv,glob
for f in glob.glob('demo_output/*.csv'):
    list(csv.DictReader(open(f,newline='',encoding='utf-8')))
print('ok')" 2>&1 | tail -1)"
check "no stale path references (tracked)" "0"   "$(git grep -Il 'openintel_rfc_pipeline' -- . ':!scripts/verify_all.sh' | wc -l | tr -d ' ')"
git checkout -- demo_output 2>/dev/null || true
check "working tree clean (after restoring demo_output)" "clean" "$([[ -z "$(git status --porcelain)" ]] && echo clean || echo DIRTY)"

# --------------------------------------------------------------------------- #
printf '\n\033[1m===== RESULT =====\033[0m\n'
printf '  passed: %d\n  failed: %d\n' "$PASS" "$FAIL"
if (( FAIL )); then
    printf '\n  failures:\n'
    for n in "${FAILED_NAMES[@]}"; do printf '    - %s\n' "$n"; done
    exit 1
fi
printf '\n  ALL CHECKS PASSED\n'
