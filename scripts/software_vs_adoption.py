"""Phase 7: each program's update timeline against the adoption data.

Redoes docs/releases_vs_adoption.md, docs/release_scan.md and
scripts/program_rfc_cases.py on the verified timelines (Phase 2/3) and the
Phase 4 normalised default rows (as corrected after Phase 5).

Five questions, spec in docs/handoff/07_phase7_brief.md:

  q1  per program, per stable release: 3-month detrended change around every
      release, program-level superposed-epoch mean against a circular-shift null
  q2  per default row with an observable: 12-month detrended event study, with
      a chance band from random event months
  q3  manual against automatic: reverse-ledger action sizes and levels in the
      months after a signer default-algorithm change, permutation over months
  q4  adoption spikes (program_rfc_cases.spikes), attributed or not, with the
      chance of a random month having a relevant default change before it
  q5  successor RFC published while the predecessor is still deploying

Inputs (read-only): data/software/timelines/*.json,
out/analysis/cross_program_defaults_normalised.csv, cross_program_q3_topics.csv,
out/server_run/timeline_monthly.parquet, out/panel_run/timeline_monthly.parquet,
out/analysis/delegation_changes.parquet, delegation_change_clusters.parquet,
delegation_change_levels.parquet, data/rfc_checklists/dnssec_rfc_checklists.json.

Deterministic: every null uses numpy default_rng([20260929, crc32(test key)])
with 1,000 draws, so a question's numbers do not depend on which other
questions ran. Output is saved after each question.

    python scripts/software_vs_adoption.py              # all five questions
    python scripts/software_vs_adoption.py --only q2    # one question, others kept
"""
from __future__ import annotations

import argparse
import functools
import json
import math
import re
import sys
import zlib
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from program_rfc_cases import spikes as _spikes  # noqa: E402  (the spike rule, reused verbatim)
import _run_paths  # noqa: E402  (which server / panel run to read; env-configurable)

SEED = 20260929
N_DRAWS = 1000
PANEL = "_pooled-afrinic-arin"
FORWARD_TLDS = ["se", "nu", "gov", "fed.us", "ee", "ch", "li"]   # order kept for reproducibility;
# main() appends any other zonefile source a run contains (e.g. the full server corpus), so none is dropped.
RIRS = ["afrinic", "apnic", "arin", "lacnic", "ripe"]
MIN_DEN = 30            # signed zones / delegations / NSEC3 names needed for a share
SHARE_COL = "domain_days"   # shares = mean daily share; spike counts keep domains_peak
Q1_W = 3                # months either side, question 1
Q2_W = 12               # months either side, question 2
WINDOW = 3              # "within 3 months" for q3 and q4
TREND_WIN = 25          # centred rolling median, months
TREND_MIN = 13          # minimum months in the rolling window (half-window at series ends)
FORWARD_FLOOR, REVERSE_FLOOR = 300, 30
BAND = (5.0, 95.0)      # 90% chance band
MIN_PRESENT = 12        # q1: months in which the value must be present for a program test
STEP_PRE, STEP_POST = 24, 12   # step test: months of pre-trend fit, months after
REV_EVENT_LAG = 1       # reverse label M = state at 00:00 UTC on the 1st of M: a release in month r is
                        # before label r+1, so the reverse event index is r+1
Q1_TESTS = ("step12", "transient3")
ALL_STABLE = "all stable public releases"
FEATURE_SET = "x.y.0 feature releases"
FEATURE_TAG = re.compile(r"v9\.\d+\.0")
Q2_MIN_PLACEBOS = 24    # q2: placebo months outside the event's window needed for a test
Q2_TESTS = ("step12", "transient12")
TEST_ROLE = {"step12": "primary: departure from the pre-event trend",
             "transient3": "secondary: transient deviation, blind to a lasting step",
             "transient12": "secondary: transient deviation, blind to a lasting step"}
PEAK_MIN_DEN = 300      # q5: a peak is taken only over months with at least this many in the denominator
Q1_MIN_WINDOW = 24      # q1: the testable window must span at least this many months
Q1_MAX_OCC = 0.75       # q1: and release months may fill at most this share of it
CALIB_REPS = 1000       # synthetic replications for the null calibration
SIZE_BINS = [(1, 1, "1"), (2, 4, "2-4"), (5, 9, "5-9"), (10, 49, "10-49"),
             (50, 99, "50-99"), (100, 10 ** 9, "100+")]
LARGE_ACTION = 10       # delegations: an action this size or larger is "large"
ERA = 36                # q3 sensitivity: permute within +-36 months of the window

OUT = ROOT / "out/analysis"
JSON_OUT = OUT / "software_vs_adoption.json"
FORWARD_NOTE = ("Forward corpus: the forward TLDs are four TLD pairs and singles run by a few registries; the "
                "large forward moves fall in four TLDs run by two registries, and the operators of the changed "
                "zones cannot be identified from the monthly counts. A forward event study measures whether a "
                "small number of organisations moved, not whether a market responded.")

# ------------------------------------------------------------------ months --


def m2i(m: str) -> int:
    return int(m[:4]) * 12 + int(m[5:7]) - 1


def i2m(i: int) -> str:
    return f"{i // 12:04d}-{i % 12 + 1:02d}"


def rng_for(key: str) -> np.random.Generator:
    return np.random.default_rng([SEED, zlib.crc32(key.encode("utf-8"))])


def r6(x):
    if x is None:
        return None
    if isinstance(x, (float, np.floating)):
        if not math.isfinite(float(x)):
            return None
        return round(float(x), 6)
    if isinstance(x, (np.integer,)):
        return int(x)
    return x


# -------------------------------------------------------------- observables --
#: Each observable: forward (numerator, denominator) and reverse (panel) spec,
#: or None where the corpus cannot see it. A numerator is (dimension, values)
#: where values is a list of codepoints, ("gt", n) or ("eq", n) on a numeric value.
OBSERVABLES = {
    "alg1": dict(label="RSAMD5 (algorithm 1) share of signed zones / delegations",
                 fwd=(("algorithm_dnskey", ["1"]), ("algorithm_dnskey", "_total")),
                 rev=(("algorithm_ds", ["1"]), ("algorithm_ds", "_total")), algs={"1"}),
    "alg3_6": dict(label="DSA (algorithms 3, 6) share",
                   fwd=(("algorithm_dnskey", ["3", "6"]), ("algorithm_dnskey", "_total")),
                   rev=(("algorithm_ds", ["3", "6"]), ("algorithm_ds", "_total")), algs={"3", "6"}),
    "alg5": dict(label="RSASHA1 (algorithm 5) share",
                 fwd=(("algorithm_dnskey", ["5"]), ("algorithm_dnskey", "_total")),
                 rev=(("algorithm_ds", ["5"]), ("algorithm_ds", "_total")), algs={"5"}),
    "alg5_7": dict(label="RSASHA1 family (algorithms 5, 7) share",
                   fwd=(("algorithm_dnskey", ["5", "7"]), ("algorithm_dnskey", "_total")),
                   rev=(("algorithm_ds", ["5", "7"]), ("algorithm_ds", "_total")), algs={"5", "7"}),
    "alg7": dict(label="RSASHA1-NSEC3-SHA1 (algorithm 7) share",
                 fwd=(("algorithm_dnskey", ["7"]), ("algorithm_dnskey", "_total")),
                 rev=(("algorithm_ds", ["7"]), ("algorithm_ds", "_total")), algs={"7"}),
    "alg8": dict(label="RSASHA256 (algorithm 8) share",
                 fwd=(("algorithm_dnskey", ["8"]), ("algorithm_dnskey", "_total")),
                 rev=(("algorithm_ds", ["8"]), ("algorithm_ds", "_total")), algs={"8"}),
    "alg8_13": dict(label="RFC 8624 MUST algorithms (8, 13) share",
                    fwd=(("algorithm_dnskey", ["8", "13"]), ("algorithm_dnskey", "_total")),
                    rev=(("algorithm_ds", ["8", "13"]), ("algorithm_ds", "_total")), algs={"8", "13"}),
    "alg12": dict(label="ECC-GOST (algorithm 12) share",
                  fwd=(("algorithm_dnskey", ["12"]), ("algorithm_dnskey", "_total")),
                  rev=(("algorithm_ds", ["12"]), ("algorithm_ds", "_total")), algs={"12"}),
    "alg13": dict(label="ECDSAP256SHA256 (algorithm 13) share",
                  fwd=(("algorithm_dnskey", ["13"]), ("algorithm_dnskey", "_total")),
                  rev=(("algorithm_ds", ["13"]), ("algorithm_ds", "_total")), algs={"13"}),
    "digest1": dict(label="SHA-1 DS (digest 1) share of DS-carrying delegations",
                    fwd=(("digest_type_ds", ["1"]), ("digest_type_ds", "_total")),
                    rev=(("digest_type_ds", ["1"]), ("digest_type_ds", "_total"))),
    "digest2": dict(label="SHA-256 DS (digest 2) share",
                    fwd=(("digest_type_ds", ["2"]), ("digest_type_ds", "_total")),
                    rev=(("digest_type_ds", ["2"]), ("digest_type_ds", "_total"))),
    "digest4": dict(label="SHA-384 DS (digest 4) share",
                    fwd=(("digest_type_ds", ["4"]), ("digest_type_ds", "_total")),
                    rev=(("digest_type_ds", ["4"]), ("digest_type_ds", "_total"))),
    "rsa1024": dict(label="1024-bit RSA keys, share of names with an RSA key (forward only)",
                    fwd=(("rsa_key_bitsize", ["1024"]), ("rsa_key_bitsize", "_total")), rev=None),
    "rsa_lt1024": dict(label="RSA keys under 1024 bits, share of names with an RSA key (forward only)",
                       fwd=(("rsa_key_bitsize", ("lt", 1024)), ("rsa_key_bitsize", "_total")), rev=None),
    "nsec3param": dict(label="zones with NSEC3PARAM over signed zones (forward only)",
                       fwd=(("rr_type", ["NSEC3PARAM"]), ("algorithm_dnskey", "_total")), rev=None),
    "optout": dict(label="NSEC3 owner names with the opt-out flag (forward only; owner names, not zones)",
                   fwd=(("nsec3_optout", ["1"]), ("nsec3_optout", "_total")), rev=None),
    "iter0": dict(label="NSEC3 owner names with 0 iterations, share of NSEC3 owner names (forward only)",
                  fwd=(("nsec3_iterations", ("eq", 0)), ("nsec3_iterations", "_total")), rev=None),
    "iter5": dict(label="NSEC3 owner names with 5 iterations (forward only)",
                  fwd=(("nsec3_iterations", ("eq", 5)), ("nsec3_iterations", "_total")), rev=None),
    "iter10": dict(label="NSEC3 owner names with 10 iterations (forward only)",
                   fwd=(("nsec3_iterations", ("eq", 10)), ("nsec3_iterations", "_total")), rev=None),
    "iter_gt0": dict(label="NSEC3 owner names with more than 0 iterations (forward only)",
                     fwd=(("nsec3_iterations", ("gt", 0)), ("nsec3_iterations", "_total")), rev=None),
    "iter_gt50": dict(label="NSEC3 owner names above 50 iterations (forward only)",
                      fwd=(("nsec3_iterations", ("gt", 50)), ("nsec3_iterations", "_total")), rev=None),
    "iter_gt100": dict(label="NSEC3 owner names above 100 iterations (forward only)",
                       fwd=(("nsec3_iterations", ("gt", 100)), ("nsec3_iterations", "_total")), rev=None),
    "iter_gt150": dict(label="NSEC3 owner names above 150 iterations (forward only)",
                       fwd=(("nsec3_iterations", ("gt", 150)), ("nsec3_iterations", "_total")), rev=None),
    "iter_gt256": dict(label="NSEC3 owner names above 256 iterations (forward only)",
                       fwd=(("nsec3_iterations", ("gt", 256)), ("nsec3_iterations", "_total")), rev=None),
    "iter_gt500": dict(label="NSEC3 owner names above 500 iterations (forward only)",
                       fwd=(("nsec3_iterations", ("gt", 500)), ("nsec3_iterations", "_total")), rev=None),
    "iter_gt2500": dict(label="NSEC3 owner names above 2500 iterations (forward only)",
                        fwd=(("nsec3_iterations", ("gt", 2500)), ("nsec3_iterations", "_total")), rev=None),
    "cds": dict(label="zones publishing CDS over signed zones (forward only)",
                fwd=(("rr_type", ["CDS"]), ("algorithm_dnskey", "_total")), rev=None),
}

#: Row -> [(observable, expected direction, relation)]. direction +1 = the
#: default should raise the share for newly signed zones, -1 = lower it.
#: relation: "direct" (signer default), "direct-auth-clamp" (authoritative
#: server rewrites what it serves), "indirect-validator-cap" (a validator
#: limit that acts on zones only by making non-compliant zones fail).
ROW_MAP = {
    # bind9
    "d02-keygen-default-alg-rsasha1": [("alg5", +1, "direct")],
    "d03-signzone-nsec3-iterations-100-to-10": [("iter10", +1, "direct")],
    "d06-keygen-no-default-alg": [("alg5", -1, "direct")],
    "d08-rsamd5-removed": [("alg1", -1, "direct")],
    "d09-gost-removed": [("alg12", -1, "direct")],
    "d10-dsa-removed": [("alg3_6", -1, "direct")],
    "d13-ds-cds-sha1-dropped": [("digest1", -1, "direct")],
    "d14-keygen-rsa-zsk-2048": [("rsa1024", -1, "direct")],
    "d15-dnssec-policy-default-ecdsap256": [("alg13", +1, "direct")],
    "d16-dnssec-policy-default-key-size-2048": [("rsa1024", -1, "direct")],
    "d17-nsec3param-default-in-policy": [("iter5", +1, "direct")],
    "d18-nsec3param-default-0-0": [("iter0", +1, "direct")],
    "d20-dnssec-cds-sha2-only": [("digest1", -1, "direct")],
    "d21-signzone-nsec3-iterations-0": [("iter0", +1, "direct")],
    "l01-nsec3-max-iterations-150": [("iter_gt150", -1, "indirect-validator-cap")],
    "l02-nsec3-max-iterations-50": [("iter_gt50", -1, "indirect-validator-cap")],
    # knot
    "knot[1]@2.0.0": [("alg8", +1, "direct")],
    "knot[2]@2.1.0": [("alg13", +1, "direct")],
    "knot[3]@2.2.0": [("rsa1024", -1, "direct")],
    "knot[7]@2.6.0": [("alg3_6", -1, "direct")],
    "knot[8]@2.7.0": [("rsa_lt1024", -1, "direct")],
    "knot[10]@2.8.0": [("cds", -1, "direct")],
    "knot[11]@2.8.0": [("digest1", -1, "direct")],
    "knot[12]@3.0.2": [("alg5_7", -1, "direct")],
    "knot[14]@3.2.0": [("iter0", +1, "direct")],
    "knot[19]@3.6.0": [("iter_gt256", -1, "direct")],
    # kresd (validator caps)
    "kresd[9]@5.3.1": [("iter_gt150", -1, "indirect-validator-cap")],
    "kresd[12]@5.7.1": [("iter_gt50", -1, "indirect-validator-cap")],
    "kresd[15]@6.0.6": [("iter_gt50", -1, "indirect-validator-cap")],
    # opendnssec
    "opendnssec[3]@1.1.0rc1": [("optout", -1, "direct")],
    "opendnssec[5]@1.2.0b1": [("alg8", +1, "direct"), ("alg7", -1, "direct")],
    "opendnssec[13]@2.1.0": [("digest1", -1, "direct")],
    # pdns-auth
    "pdns-auth[0]@3.2": [("alg8", +1, "direct")],
    "pdns-auth[1]@3.3": [("optout", -1, "direct")],
    "pdns-auth[3]@3.4.0": [("iter_gt500", -1, "direct-auth-clamp")],
    "pdns-auth[4]@3.4.7": [("iter_gt500", -1, "direct-auth-clamp")],
    "pdns-auth[7]@4.0.0": [("alg13", +1, "direct")],
    "pdns-auth[8]@4.0.0": [("alg13", +1, "direct")],
    "pdns-auth[9]@4.0.0": [("rsa1024", -1, "direct")],
    "pdns-auth[10]@4.5.0": [("iter_gt100", -1, "direct-auth-clamp")],
    "pdns-auth[11]@4.6.0": [("iter0", +1, "direct")],
    # pdns-rec (validator caps)
    "nsec3-max-iterations-2500": [("iter_gt2500", -1, "indirect-validator-cap")],
    "nsec3-max-iterations-150": [("iter_gt150", -1, "indirect-validator-cap")],
    "nsec3-max-iterations-50": [("iter_gt50", -1, "indirect-validator-cap")],
    # unbound (validator caps)
    "unbound[1]@0.5": [("iter_gt150", -1, "indirect-validator-cap")],
    "unbound[20]@1.13.2": [("iter_gt150", -1, "indirect-validator-cap")],
}

#: Signer default changes that name a target algorithm: the q3 events.
Q3_ALG_ROWS = {
    "d02-keygen-default-alg-rsasha1": "5",
    "knot[1]@2.0.0": "8",
    "knot[2]@2.1.0": "13",
    "opendnssec[5]@1.2.0b1": "8",
    "pdns-auth[0]@3.2": "8",
    "pdns-auth[7]@4.0.0": "13",
    "pdns-auth[8]@4.0.0": "13",
    "d15-dnssec-policy-default-ecdsap256": "13",
}

#: Why an unmapped row has no observable. Specific rows first, then by mechanism.
NOT_OBSERVABLE_ROW = {
    "d19-dnskey-kskonly-yes": "which key signs the DNSKEY RRset is not recorded; only algorithm and flags are",
    "d22-cdns-cdnskey-options": "not a default change (value_changed false); excluded",
    "knot[4]@2.3.0": "salt re-salting: nsec3_salt_empty carries only 'present', equal to _total in all 404 "
                     "forward source-months, so salt length is not observable",
    "knot[18]@3.5.0": "salt length: nsec3_salt_empty carries only 'present' (equal to _total), not observable",
    "knot[13]@3.1.0": "NSEC/NSEC3 TTLs are not recorded",
    "opendnssec[6]@1.3.11": "NSEC3PARAM TTL is not recorded",
    "opendnssec[7]@1.4.0b2": "NSEC3PARAM TTL is not recorded",
    "opendnssec[9]@1.3.17": "NSEC3 at empty non-terminals is not separable in the monthly counts",
    "opendnssec[10]@1.4.4": "NSEC3 at empty non-terminals is not separable in the monthly counts",
    "pdns-auth[2]@3.3.2": "extra NSEC3 in wildcard answers is a response-time behaviour, not zone content",
    "nsd[4]@3.1.0": "NSD serves what the zone holds; a compile default is not a signer default",
    "unbound[24]@1.19.1": "caps NSEC3 hash computations per message, not iterations; no zone-side observable",
    "kresd[5]@2.4.0": "validator aggressive NSEC3 caching: validation behaviour, not observable in zone data",
    "unbound[10]@1.4.19": "validator algorithm support (RSAMD5 treated as unsupported): not observable in zone data",
    "unbound[18]@1.10.0": "validator algorithm support (DSA off by default): not observable in zone data",
    "kresd[2]@2.0.0": "validator aggressive NSEC caching: validation behaviour, not observable in zone data",
    "kresd[8]@4.1.0": "validator aggressive caching rule: validation behaviour, not observable in zone data",
    "kresd[11]@5.6.0": "resolver forwarding behaviour: not observable in zone data",
}
NOT_OBSERVABLE_MECH = {
    "validation": "validation behaviour: not observable in zone data",
    "trust-anchor": "trust-anchor handling: not observable in zone data",
    "trust-anchor-5011": "trust-anchor handling: not observable in zone data",
    "rrsig": "signature timing, answer composition or serving option: RRSIG inception, expiry and "
             "refresh are not recorded in the monthly counts",
    "dnskey": "key-management state (standby, retirement, readiness, validator key use): not observable",
    "nsec3": "NSEC3 serving detail not observable in the monthly counts",
    "other": "no zone-data observable",
    "alg-rsa-sha2": "validator algorithm support: not observable in zone data",
    "alg-ecdsa": "validator algorithm support: not observable in zone data",
    "alg-eddsa": "validator algorithm support: not observable in zone data",
    "alg-gost": "validator algorithm support: not observable in zone data",
    "ds-digest": "validator DS-digest handling: not observable in zone data",
    "nsec3-iterations": "no zone-side observable",
    "cds-cdnskey": "no zone-side observable",
}

EXCLUDED_UPSTREAM = [
    {"row_id": "pdns-auth[5]@4.0.0", "reason": "stable tag null; excluded by Phase 4 (pre-release only state)"},
    {"row_id": "pdns-auth[6]@4.0.0", "reason": "stable tag null; excluded by Phase 4 (pre-release only state)"},
]

# ------------------------------------------------------------------ inputs --


def load_rows() -> pd.DataFrame:
    d = pd.read_csv(OUT / "cross_program_defaults_normalised.csv", dtype=str, keep_default_na=False)
    for c in ("opt_in", "applies_on_upgrade", "is_default_change"):
        d[c] = d[c].map({"True": True, "False": False})
    d["timing_month"] = d.timing_date.str[:7]
    return d


def load_releases() -> dict:
    """Stable, publicly shipped releases per program: [(tag, date)]."""
    out = {}
    for f in sorted((ROOT / "data/software/timelines").glob("*.json")):
        d = json.loads(f.read_text("utf-8"))
        rows = []
        for r in d["releases"]:
            if not r.get("stable"):
                continue
            if r.get("alias_of"):
                continue
            note = (r.get("stability_note") or "").lower()
            if "never released publicly" in note:
                continue
            rows.append((r["tag"], r["released"][:10]))
        out[f.stem] = sorted(rows, key=lambda x: (x[1], x[0]))
    return out


class Data:
    def __init__(self):
        self.srv = pd.read_parquet(_run_paths.server_timeline())
        self.pan = pd.read_parquet(_run_paths.panel_timeline())
        self._cache = {}

    def pivot(self, which: str, source: str, dim: str, col: str = "domains_peak") -> pd.DataFrame:
        key = (which, source, dim, col)
        if key not in self._cache:
            df = self.srv if which == "srv" else self.pan
            d = df[(df.source == source) & (df.dimension == dim)]
            self._cache[key] = d.pivot_table(index="month", columns="value", values=col,
                                             aggfunc="sum").fillna(0)
        return self._cache[key]

    def months(self, which: str, source: str) -> list:
        df = self.srv if which == "srv" else self.pan
        return sorted(df[df.source == source].month.unique())


def _num(pv: pd.DataFrame, values) -> pd.Series:
    if isinstance(values, tuple):
        op, n = values
        cols = []
        for c in pv.columns:
            try:
                v = float(c)
            except (TypeError, ValueError):
                continue
            if (op == "gt" and v > n) or (op == "eq" and v == n) or (op == "lt" and v < n):
                cols.append(c)
    else:
        cols = [c for c in values if c in pv.columns]
    if not cols:
        return pd.Series(0.0, index=pv.index)
    return pv[cols].sum(axis=1).astype(float)


def share_series(data: Data, obs: str, corpus: str, source: str):
    """(share Series on a complete month index, numerator counts, denominator) or None.

    corpus 'forward' reads the server run's zonefile basis per TLD; corpus
    'reverse_panel' reads only the strict panel `_pooled-afrinic-arin`. Shares
    are never built from summed RIRs."""
    spec = OBSERVABLES[obs]["fwd" if corpus == "forward" else "rev"]
    if spec is None:
        return None
    (ndim, nval), (ddim, dval) = spec
    which = "srv" if corpus == "forward" else "pan"
    if corpus == "reverse_panel":
        assert source == PANEL, "reverse shares must use the strict panel"
    months = data.months(which, source)
    if not months:
        return None
    # Shares use domain_days (sum over measured days of the daily distinct count), i.e. the
    # month's mean daily share. It is additive across values within a day; domains_peak is
    # not (per-value peaks fall on different days: se 2019-06 NSEC3 value peaks sum to 115%
    # of the _total peak while zones moved from 1 to 5 iterations). The MIN_DEN floor is
    # applied to the peak denominator. For the reverse corpus measured_days is 1, so both agree.
    npv = data.pivot(which, source, ndim, SHARE_COL)
    dpv = data.pivot(which, source, ddim, SHARE_COL)
    dpk = data.pivot(which, source, ddim)
    num = _num(npv, nval).reindex(months, fill_value=0.0)
    den = (dpv[dval] if dval in dpv.columns else pd.Series(0.0, index=dpv.index)).reindex(months, fill_value=0.0)
    denpk = (dpk[dval] if dval in dpk.columns else pd.Series(0.0, index=dpk.index)).reindex(months, fill_value=0.0)
    full = [i2m(i) for i in range(m2i(months[0]), m2i(months[-1]) + 1)]
    share = (100.0 * num / den.where(denpk >= MIN_DEN)).reindex(full)   # percent
    return share, num.reindex(full), denpk.reindex(full)


def detrend(share: pd.Series) -> pd.Series:
    trend = share.rolling(TREND_WIN, center=True, min_periods=TREND_MIN).median()
    return share - trend


def window_stat(x: np.ndarray, w: int) -> np.ndarray:
    """Transient statistic. For every index e: mean(x[e:e+w]) - mean(x[e-w:e]); NaN when the
    series does not cover e-w .. e+w-1 or fewer than 2/3 of either side is valid."""
    n = len(x)
    valid = ~np.isnan(x)
    if not valid.any():
        return np.full(n, np.nan)
    first, last = np.argmax(valid), n - 1 - np.argmax(valid[::-1])
    need = math.ceil(2 * w / 3)
    out = np.full(n, np.nan)
    for e in range(n):
        if e - w < first or e + w - 1 > last:
            continue
        b, a = x[e - w:e], x[e:e + w]
        if (~np.isnan(b)).sum() < need or (~np.isnan(a)).sum() < need:
            continue
        out[e] = np.nanmean(a) - np.nanmean(b)
    return out


def step_stat(x: np.ndarray, pre: int = STEP_PRE, post: int = STEP_POST) -> np.ndarray:
    """Step-sensitive statistic. For every index e: fit a least-squares line to x[e-pre:e],
    extrapolate it over e..e+post-1, and return the mean of actual minus extrapolated. A lasting
    level shift at e shows up in full, unlike the detrended transient statistic. NaN when the series
    does not cover e-pre .. e+post-1 or fewer than 2/3 of either side is valid."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    valid = ~np.isnan(x)
    out = np.full(n, np.nan)
    if not valid.any():
        return out
    first, last = np.argmax(valid), n - 1 - np.argmax(valid[::-1])
    need_b, need_a = math.ceil(2 * pre / 3), math.ceil(2 * post / 3)
    tb = np.arange(-pre, 0, dtype=float)
    ta = np.arange(0, post, dtype=float)
    for e in range(n):
        if e - pre < first or e + post - 1 > last:
            continue
        b, a = x[e - pre:e], x[e:e + post]
        okb, oka = ~np.isnan(b), ~np.isnan(a)
        if okb.sum() < need_b or oka.sum() < need_a:
            continue
        slope, icpt = np.polyfit(tb[okb], b[okb], 1)
        out[e] = float(np.mean(a[oka] - (icpt + slope * ta[oka])))
    return out


#: statistic key -> (months before, months after) the event index
STAT_SPAN = {"step12": (STEP_PRE, STEP_POST), "transient3": (Q1_W, Q1_W), "transient12": (Q2_W, Q2_W)}


class Series:
    """A share series with its event statistics.

    Dating: a reverse label M is the state at 00:00 UTC on the 1st of M, so for a release in calendar
    month r the reverse event index is label r+1 (states up to label r are before the release). A
    forward label is the calendar month of measurement; the event index is r itself. `at()` and
    `testable_months()` take and return calendar release months."""

    def __init__(self, data, obs, corpus, source):
        self.obs, self.corpus, self.source = obs, corpus, source
        self.lag = REV_EVENT_LAG if corpus == "reverse_panel" else 0
        r = share_series(data, obs, corpus, source)
        self.ok = r is not None
        if not self.ok:
            return
        self.share, self.num, self.den = r
        self.start = m2i(self.share.index[0])
        valid = self.share.dropna()
        self.first_valid = valid.index[0] if len(valid) else None
        self.last_valid = valid.index[-1] if len(valid) else None
        self.ever_nonzero = bool((valid > 0).any()) if len(valid) else False
        self.present_months = int((valid > 0).sum())
        sh = self.share.to_numpy(dtype=float)
        det = detrend(self.share).to_numpy(dtype=float)
        self.det = det
        self.stat = {"transient3": window_stat(det, Q1_W), "transient12": window_stat(det, Q2_W),
                     "step12": step_stat(sh)}

    def idx(self, month_i: int) -> int:
        return month_i + self.lag - self.start

    def at(self, key: str, month_i: int) -> float:
        k = self.idx(month_i)
        if k < 0 or k >= len(self.det):
            return float("nan")
        return float(self.stat[key][k])

    def at_arr(self, key: str, months: np.ndarray) -> np.ndarray:
        k = np.asarray(months, dtype=int) + self.lag - self.start
        ok = (k >= 0) & (k < len(self.det))
        out = np.full(len(k), np.nan)
        out[ok] = self.stat[key][k[ok]]
        return out

    def testable_months(self, key: str) -> np.ndarray:
        """Calendar release months at which the statistic is defined."""
        return np.flatnonzero(~np.isnan(self.stat[key])) + self.start - self.lag

    def why_untestable(self, key: str, month_i: int) -> str:
        if self.first_valid is None:
            return f"no month with at least {MIN_DEN} in the denominator"
        if not self.ever_nonzero:
            return "the value never appears in this series"
        before, after = STAT_SPAN[key]
        e = month_i + self.lag
        fv, lv = m2i(self.first_valid), m2i(self.last_valid)
        if e - before < fv:
            return f"no before-period: series valid from {self.first_valid}, needs {i2m(e - before)}"
        if e + after - 1 > lv:
            return f"no after-period: series valid to {self.last_valid}, needs {i2m(e + after - 1)}"
        return "too many gap months in the window"


def corpora_for(obs: str):
    out = []
    if OBSERVABLES[obs]["fwd"] is not None:
        out += [("forward", t) for t in FORWARD_TLDS]
    if OBSERVABLES[obs]["rev"] is not None:
        out.append(("reverse_panel", PANEL))
    return out


def pct_rank(null: np.ndarray, obs: float) -> float:
    """Mid-rank percentile: ties count half, so an all-tied null gives 50, not 100."""
    return float((np.mean(null < obs) + 0.5 * np.mean(null == obs)) * 100)


def two_sided(null: np.ndarray, obs: float) -> float:
    return float(min(1.0, 2 * min(np.mean(null <= obs), np.mean(null >= obs))))


def placebo_months(tm: np.ndarray, e: int, before: int, after: int) -> np.ndarray:
    """Eligible placebo event months: testable months outside the event's own window
    e-before .. e+after, so the event month and its neighbours, whose windows carry the same step,
    are excluded."""
    tm = np.asarray(tm, dtype=int)
    return tm[(tm < e - before) | (tm > e + after)]


def shift_test(values_at, rel_months, a: int, b: int, rng, lo: float, hi: float,
               before: int = 0, after: int = 0) -> dict | None:
    """Program-level test. Release months inside the coverage window [a, b] are circularly shifted
    by one uniform offset within that window, N_DRAWS times. The offset k is restricted so that every
    shifted month falls outside its own event's window [-before, +after]: after < k < L - before. The
    zero offset, the event months themselves, is therefore excluded. values_at(months) returns the
    event statistic (NaN where untestable). Returns the observed mean, its null and the share of
    release months outside the single-release band [lo, hi] with its null; {"no_offsets": True} when
    the window is too short for any allowed offset."""
    rm = np.array([m for m in rel_months if a <= m <= b], dtype=int)
    if len(rm) == 0:
        return None
    v = values_at(rm)
    ok = ~np.isnan(v)
    if ok.sum() == 0:
        return None
    obs_mean = float(v[ok].mean())
    obs_out = float(np.mean((v[ok] < lo) | (v[ok] > hi)))
    L = b - a + 1
    k_lo, k_hi = after + 1, L - before - 1
    if k_hi < k_lo:
        return {"no_offsets": True}
    ks = rng.integers(k_lo, k_hi + 1, size=N_DRAWS)
    shifted = a + ((rm[None, :] - a + ks[:, None]) % L)
    V = values_at(shifted.ravel()).reshape(shifted.shape)
    null_mean, null_out = [], []
    for row in V:
        row = row[~np.isnan(row)]
        if len(row) == 0:
            continue
        null_mean.append(row.mean())
        null_out.append(np.mean((row < lo) | (row > hi)))
    null_mean, null_out = np.array(null_mean), np.array(null_out)
    return {"no_offsets": False, "allowed_offsets": int(k_hi - k_lo + 1),
            "months_in_window": int(len(rm)), "months_tested": int(ok.sum()), "obs_mean": obs_mean,
            "obs_out": obs_out, "null_mean": null_mean, "null_out": null_out,
            "tested_months": rm[ok]}


# ---------------------------------------------------------------- mapping --


def mapping_table(rows: pd.DataFrame):
    mapped, unmapped = [], []
    ids = set(rows.row_id)
    for rid in ROW_MAP:
        assert rid in ids, f"ROW_MAP names unknown row {rid}"
    for _, r in rows.iterrows():
        if r.row_id in ROW_MAP and r.is_default_change:
            for obs, direction, rel in ROW_MAP[r.row_id]:
                o = OBSERVABLES[obs]
                mapped.append({
                    "program": r.program, "row_id": r.row_id, "mechanism": r.mechanism,
                    "timing_tag": r.timing_tag, "timing_date": r.timing_date,
                    "opt_in": r.opt_in, "applies_on_upgrade": r.applies_on_upgrade,
                    "observable": obs, "observable_label": o["label"],
                    "expected_direction": direction, "relation": rel,
                    "forward": _spec_text(o["fwd"]), "reverse": _spec_text(o["rev"], panel=True)})
        else:
            reason = NOT_OBSERVABLE_ROW.get(r.row_id)
            if reason is None and not r.is_default_change:
                reason = "not a default change (is_default_change false); excluded"
            if reason is None:
                reason = NOT_OBSERVABLE_MECH[r.mechanism]
            unmapped.append({"program": r.program, "row_id": r.row_id, "mechanism": r.mechanism,
                             "timing_date": r.timing_date, "reason": reason})
    return mapped, unmapped


def _spec_text(spec, panel=False):
    if spec is None:
        return "not observable"
    (nd, nv), (dd, dv) = spec
    nvt = f"{nv[0]} {nv[1]}" if isinstance(nv, tuple) else "/".join(nv)
    return f"{nd} {nvt} over {dd} {dv}" + (f" ({PANEL})" if panel else "")


MECH_TABLE = [
    {"mechanism / topic": "alg-ecdsa (ECDSA P-256 default)", "forward": "algorithm_dnskey 13 share of signed zones",
     "reverse": "algorithm_ds 13 share of signed delegations (panel)"},
    {"mechanism / topic": "alg-rsa-sha2 (RSASHA256 default)", "forward": "algorithm_dnskey 8", "reverse": "algorithm_ds 8"},
    {"mechanism / topic": "dnskey: RSASHA1 keygen default added or removed (extension)",
     "forward": "algorithm_dnskey 5", "reverse": "algorithm_ds 5"},
    {"mechanism / topic": "algorithm removal in a signer: RSAMD5, GOST, DSA (extension)",
     "forward": "algorithm_dnskey 1 / 12 / 3+6", "reverse": "algorithm_ds 1 / 12 / 3+6"},
    {"mechanism / topic": "crypto-policy SHA-1 refusal in a signer library (extension)",
     "forward": "algorithm_dnskey 5+7", "reverse": "algorithm_ds 5+7"},
    {"mechanism / topic": "ds-digest (SHA-1 DS no longer generated)", "forward": "digest_type_ds 1 share",
     "reverse": "digest_type_ds 1 share"},
    {"mechanism / topic": "ds-digest (SHA-256 / SHA-384 DS)", "forward": "digest_type_ds 2 / 4", "reverse": "digest_type_ds 2 / 4"},
    {"mechanism / topic": "RSA key-size defaults (extension)", "forward": "rsa_key_bitsize 1024 (or under 1024) "
     "over rsa_key_bitsize _total", "reverse": "not observable (a DS carries no key size)"},
    {"mechanism / topic": "nsec3 opt-out default (extension)", "forward": "nsec3_optout 1 over nsec3_optout _total "
     "(owner names)", "reverse": "not observable"},
    {"mechanism / topic": "nsec3, nsec3-iterations (signer NSEC3 defaults)",
     "forward": "nsec3_iterations owner names at the new value over nsec3_iterations _total; "
                "rr_type NSEC3PARAM over algorithm_dnskey _total for NSEC3 use", "reverse": "not observable"},
    {"mechanism / topic": "NSEC3 salt, NSEC/NSEC3 TTLs", "forward": "not observable (nsec3_salt_empty only "
     "holds 'present' = _total; no TTLs)", "reverse": "not observable"},
    {"mechanism / topic": "validator or authoritative NSEC3 iteration caps (indirect / clamp)",
     "forward": "nsec3_iterations owner names above the cap over _total, labelled indirect", "reverse": "not observable"},
    {"mechanism / topic": "cds-cdnskey", "forward": "rr_type CDS over algorithm_dnskey _total",
     "reverse": "not observable"},
    {"mechanism / topic": "validation, trust-anchor, trust-anchor-5011, validator limits and algorithm support",
     "forward": "not observable in zone data", "reverse": "not observable"},
    {"mechanism / topic": "rrsig timing, key-management state", "forward": "not observable", "reverse": "not observable"},
]


# -------------------------------------------------------------------- q1 --


def q1(rows, releases, data):
    mapped, _ = mapping_table(rows)
    by_prog = {}
    for m in mapped:
        by_prog.setdefault(m["program"], {}).setdefault(m["observable"], []).append(m["row_id"])
    summary, per_release, tables = [], [], {}
    event_sets = [(prog, prog, releases[prog], ALL_STABLE) for prog in sorted(releases)]
    # BIND ships in nearly every month, so every-stable-release schedules have no contrast. Its
    # feature releases, tags vX.Y.0 with no patch suffix, give a sparse schedule that can be tested.
    event_sets.append(("bind9_feature_releases", "bind9",
                       [(t, d) for t, d in releases["bind9"] if FEATURE_TAG.fullmatch(t)], FEATURE_SET))
    for tab_key, prog, rel, event_set in event_sets:
        rel_months = sorted({m2i(d[:7]) for _, d in rel})
        obs_map = by_prog.get(prog, {})
        prog_tab = {"program": prog, "event_set": event_set, "stable_public_releases": len(rel),
                    "release_months": len(rel_months),
                    "span": [i2m(rel_months[0]), i2m(rel_months[-1])], "observables": {}, "tests": []}
        if not obs_map:
            prog_tab["note"] = "no default row of this program maps to a zone-data observable; nothing to test"
        for obs in sorted(obs_map):
            prog_tab["observables"][obs] = sorted(obs_map[obs])
            for corpus, src in corpora_for(obs):
                s = Series(data, obs, corpus, src)
                for test in Q1_TESTS:
                    key = (f"q1|{test}|{prog}|{obs}|{corpus}|{src}" if event_set == ALL_STABLE
                           else f"q1|{test}|{prog}|x.y.0|{obs}|{corpus}|{src}")
                    base = {"program": prog, "event_set": event_set, "test": test, "role": TEST_ROLE[test],
                            "observable": obs,
                            "corpus": corpus, "source": src, "rows_touching": ";".join(sorted(obs_map[obs])),
                            "releases_total": len(rel), "release_months_total": len(rel_months)}
                    if not s.ok or s.first_valid is None or s.present_months < MIN_PRESENT:
                        why = ("no series" if not s.ok else
                               s.why_untestable(test, rel_months[0]) if (s.first_valid is None or not s.ever_nonzero)
                               else f"the value is present in only {s.present_months} months of this series "
                                    f"(fewer than {MIN_PRESENT})")
                        summary.append({**base, "status": "no test", "reason": why})
                        prog_tab["tests"].append(summary[-1])
                        continue
                    tm = s.testable_months(test)
                    if len(tm) == 0:
                        summary.append({**base, "status": "no test",
                                        "reason": "the series is too short for this statistic"})
                        prog_tab["tests"].append(summary[-1])
                        continue
                    a, b = int(tm.min()), int(tm.max())
                    L = b - a + 1
                    in_win = [mm for mm in rel_months if a <= mm <= b and not math.isnan(s.at(test, mm))]
                    occ = len(in_win) / L
                    if L < Q1_MIN_WINDOW or occ > Q1_MAX_OCC:
                        why = (f"the testable window {i2m(a)}..{i2m(b)} is {L} months, fewer than {Q1_MIN_WINDOW}"
                               if L < Q1_MIN_WINDOW else
                               f"release months fill {len(in_win)} of the {L} months of the testable window "
                               f"{i2m(a)}..{i2m(b)}, more than {Q1_MAX_OCC:.0%}; a shifted schedule then covers "
                               f"almost the same months and the test has no contrast")
                        summary.append({**base, "status": "no test", "reason": why,
                                        "null_window": f"{i2m(a)}..{i2m(b)}", "release_months_in_window": len(in_win)})
                        prog_tab["tests"].append(summary[-1])
                        continue
                    vals_all = s.at_arr(test, tm)
                    lo, hi = np.percentile(vals_all, BAND)
                    for tag, date in rel:
                        v = s.at(test, m2i(date[:7]))
                        if not math.isnan(v):
                            per_release.append({"program": prog, "event_set": event_set, "test": test,
                                                "tag": tag, "released": date,
                                                "observable": obs, "corpus": corpus, "source": src,
                                                "value": r6(v), "outside_90_band": bool(v < lo or v > hi)})
                    res = shift_test(lambda ms: s.at_arr(test, ms), rel_months, a, b, rng_for(key), lo, hi)
                    far = shift_test(lambda ms: s.at_arr(test, ms), rel_months, a, b, rng_for("far|" + key),
                                     lo, hi, *STAT_SPAN[test])
                    if res is None or len(res["null_mean"]) == 0:
                        summary.append({**base, "status": "no test",
                                        "reason": f"no release month falls in the series' testable window "
                                                  f"{i2m(a)}..{i2m(b)}"})
                        prog_tab["tests"].append(summary[-1])
                        continue
                    nm, no = res["null_mean"], res["null_out"]
                    n_rel = int(sum(1 for _, d in rel if not math.isnan(s.at(test, m2i(d[:7])))))
                    p2_ = two_sided(nm, res["obs_mean"])
                    p_out = float(np.mean(no >= res["obs_out"]))
                    row = {**base, "status": "tested", "null_window": f"{i2m(a)}..{i2m(b)}",
                           "window_months": L, "release_share_of_window": r6(occ),
                           "releases_tested": n_rel, "release_months_tested": res["months_tested"],
                           "allowed_offsets": res["allowed_offsets"],
                           "nonoverlap_p_two_sided": (r6(two_sided(far["null_mean"], res["obs_mean"]))
                                                      if far and not far["no_offsets"] and len(far["null_mean"])
                                                      else None),
                           "tested_from": i2m(int(res["tested_months"].min())),
                           "tested_to": i2m(int(res["tested_months"].max())),
                           "observed_mean": r6(res["obs_mean"]), "null_draws_used": int(len(nm)),
                           "null_p5": r6(np.percentile(nm, 5)), "null_p95": r6(np.percentile(nm, 95)),
                           "percentile": r6(pct_rank(nm, res["obs_mean"])), "p_two_sided": r6(p2_),
                           "band_lo": r6(lo), "band_hi": r6(hi),
                           "share_release_months_outside_band": r6(res["obs_out"]),
                           "null_mean_share_outside": r6(no.mean()),
                           "p_share_outside_ge_observed": r6(p_out),
                           "beats_chance_mean": bool(p2_ < 0.10), "beats_chance_outside": bool(p_out < 0.10)}
                    summary.append(row)
                    prog_tab["tests"].append(row)
        tables[tab_key] = prog_tab
    agg = {}
    cal = calibration()
    for test in Q1_TESTS:
        tested = [r for r in summary if r["status"] == "tested" and r["test"] == test
                  and r["event_set"] == ALL_STABLE]
        rate = cal["q1_coverage_window_shift_rejection_rate"] if test == "step12" else None
        agg[test] = {"role": TEST_ROLE[test],
                     "tests": sum(1 for r in summary if r["test"] == test and r["event_set"] == ALL_STABLE),
                     "expected_by_calibrated_rate": r6(rate * len(tested)) if rate is not None else None,
                     "tested": len(tested),
                     "mean_outside_90pct_null": sum(1 for r in tested if r["beats_chance_mean"]),
                     "expected_by_chance_at_10pct": round(0.10 * len(tested), 2),
                     "outside_share_beats_null_p_lt_0.10": sum(1 for r in tested if r["beats_chance_outside"]),
                     "mean_p_two_sided": r6(np.mean([r["p_two_sided"] for r in tested])) if tested else None,
                     "nonoverlap_p_lt_0.10": sum(1 for r in tested if r.get("nonoverlap_p_two_sided") is not None
                                                 and r["nonoverlap_p_two_sided"] < 0.10)}
    feat = [r for r in summary if r["event_set"] == FEATURE_SET]
    agg["bind9_feature_releases"] = {
        test: {"tests": sum(1 for r in feat if r["test"] == test),
               "tested": sum(1 for r in feat if r["test"] == test and r["status"] == "tested"),
               "mean_outside_90pct_null": sum(1 for r in feat if r["test"] == test and r["status"] == "tested"
                                              and r["beats_chance_mean"])}
        for test in Q1_TESTS}
    return {"method": (f"Event = each stable, publicly shipped release, one per calendar month per program. "
                       f"Primary statistic step12: the mean over the {STEP_POST} after-months of the share minus "
                       f"a linear trend fitted to the {STEP_PRE} before-months and extrapolated; it keeps a "
                       f"lasting level shift. Secondary statistic transient3, the transient deviation: mean "
                       f"detrended share over {Q1_W} after-months minus {Q1_W} before-months, detrended by a "
                       f"centred {TREND_WIN}-month rolling median, which absorbs any lasting step. Reverse "
                       f"dating: for a release in calendar month r, before = labels <= r and after = labels "
                       f"r+1 on. Program statistic = mean over tested release months. Null: the release "
                       f"months that fall inside the series' own testable window circularly shifted by one "
                       f"uniform offset within that window, {N_DRAWS} draws; the zero offset, which would return the "
                       f"events themselves, is excluded. Sensitivity, nonoverlap_p_two_sided: offsets restricted "
                       f"so every shifted month lies outside its own event's window; it rejects far above 10% "
                       f"on no-effect series and is not used for conclusions. BIND 9 is also tested "
                       f"with its feature releases, tags vX.Y.0, as the event set. A test needs a window of at least "
                       f"{Q1_MIN_WINDOW} months with release months filling at most {Q1_MAX_OCC:.0%} of it; "
                       f"otherwise every shift covers nearly the same months. Single-release band: 5th-95th "
                       f"percentile of the statistic over every testable month of the series."),
            "per_program": tables, "aggregate": agg}, summary, per_release


# -------------------------------------------------------------------- q2 --


def discrete_p_le_prob(n: int, p0: float) -> float:
    """Under the placebo null the event is exchangeable with its n placebo months: it sits above i of
    them with probability 1/(n+1) for each i, giving the rank p = 2*min(i+1, n-i+1)/(n+1), as p_rank.
    Returns P(p_rank <= p0)."""
    i = np.arange(n + 1)
    p = np.minimum(1.0, 2 * np.minimum(i + 1, n - i + 1) / (n + 1))
    return float(np.mean(p <= p0 + 1e-6))   # p0 is rounded to 6 decimals


def discrete_outside_prob(n: int) -> float:
    """Probability that an exchangeable event falls outside the 5th-95th percentile band of n placebos."""
    vals = np.arange(n, dtype=float)
    lo, hi = np.percentile(vals, BAND)
    pos = np.arange(n + 1) - 0.5
    return float(np.mean((pos < lo) | (pos > hi)))


def bh_q(ps: list) -> list:
    """Benjamini-Hochberg adjusted p-values, same order as ps."""
    p = np.asarray(ps, dtype=float)
    n = len(p)
    if n == 0:
        return []
    order = np.argsort(p, kind="mergesort")
    ranked = p[order] * n / np.arange(1, n + 1)
    q = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty(n)
    out[order] = np.minimum(q, 1.0)
    return out.tolist()


def q2(rows, data):
    mapped, _ = mapping_table(rows)
    out = []
    series_cache = {}
    for m in mapped:
        e = m2i(m["timing_date"][:7])
        for corpus, src in corpora_for(m["observable"]):
            sk = (m["observable"], corpus, src)
            if sk not in series_cache:
                series_cache[sk] = Series(data, *sk)
            s = series_cache[sk]
            for test in Q2_TESTS:
                base = {"program": m["program"], "row_id": m["row_id"], "test": test, "role": TEST_ROLE[test],
                        "timing_tag": m["timing_tag"], "timing_date": m["timing_date"], "opt_in": m["opt_in"],
                        "applies_on_upgrade": m["applies_on_upgrade"], "observable": m["observable"],
                        "expected_direction": m["expected_direction"], "relation": m["relation"],
                        "corpus": corpus, "source": src}
                if not s.ok:
                    out.append({**base, "status": "no test", "reason": "no series"})
                    continue
                v = s.at(test, e)
                if math.isnan(v):
                    out.append({**base, "status": "no test", "reason": s.why_untestable(test, e)})
                    continue
                before, after = STAT_SPAN[test]
                k = s.idx(e)
                sh = s.share.to_numpy(dtype=float)
                win = sh[k - before:k + after]
                if np.nansum(win) == 0:
                    out.append({**base, "status": "no test",
                                "reason": f"the value is absent in every month of the window "
                                          f"{i2m(e + s.lag - before)}..{i2m(e + s.lag + after - 1)}"})
                    continue
                tm = s.testable_months(test)
                if len(tm) < Q2_MIN_PLACEBOS:
                    out.append({**base, "status": "no test", "testable_months_in_series": int(len(tm)),
                                "reason": f"only {len(tm)} testable months in this series, fewer than "
                                          f"{Q2_MIN_PLACEBOS}"})
                    continue
                elig = placebo_months(tm, e, 0, 0)          # primary: every testable month but the event's
                far = placebo_months(tm, e, before, after)   # sensitivity: outside the event's window
                rng = rng_for(f"q2|{test}|{m['row_id']}|{m['observable']}|{corpus}|{src}")
                draws = rng.choice(elig, size=N_DRAWS, replace=True)
                null = s.at_arr(test, draws)
                lo, hi = np.percentile(null, BAND)
                pv = s.at_arr(test, elig)
                n_below, n_above = int((pv <= v).sum()), int((pv >= v).sum())   # ties count against
                p_rank = min(1.0, 2 * min(n_below + 1, n_above + 1) / (len(elig) + 1))
                if len(far):
                    nf = s.at_arr(test, rng_for(f"q2far|{test}|{m['row_id']}|{m['observable']}|{corpus}|{src}")
                                  .choice(far, size=N_DRAWS, replace=True))
                    flo, fhi = np.percentile(nf, BAND)
                    far_cols = {"nonoverlap_placebo_months": int(len(far)),
                                "nonoverlap_percentile": r6(pct_rank(nf, v)),
                                "nonoverlap_outside_90_band": bool(v < flo or v > fhi)}
                else:
                    far_cols = {"nonoverlap_placebo_months": 0, "nonoverlap_percentile": None,
                                "nonoverlap_outside_90_band": None}
                out.append({**base, "status": "tested",
                            "before_labels": f"{i2m(e + s.lag - before)}..{i2m(e + s.lag - 1)}",
                            "after_labels": f"{i2m(e + s.lag)}..{i2m(e + s.lag + after - 1)}",
                            "share_last_before": r6(sh[k - 1]) if k >= 1 else None,
                            "raw_mean_before": r6(np.nanmean(sh[k - before:k])),
                            "raw_mean_after": r6(np.nanmean(sh[k:k + after])),
                            "observed": r6(v), "band_lo": r6(lo), "band_hi": r6(hi),
                            "percentile": r6(pct_rank(null, v)), "p_two_sided": r6(two_sided(null, v)),
                            "p_rank": r6(p_rank),
                            "outside_90_band": bool(v < lo or v > hi),
                            "in_expected_direction": bool(np.sign(v) == m["expected_direction"]),
                            "testable_months_in_series": int(len(tm)), "placebo_months": int(len(elig)),
                            **far_cols})
    summ = {}
    for test in Q2_TESTS:
        tested = [r for r in out if r["status"] == "tested" and r["test"] == test]
        for r, q in zip(tested, bh_q([r["p_rank"] for r in tested])):
            r["bh_q"] = r6(q)
        groups = {}
        for r in tested:
            g = f"applies_on_upgrade={r['applies_on_upgrade']}, opt_in={r['opt_in']}"
            gg = groups.setdefault(g, {"tested": 0, "outside_90_band": 0, "outside_and_expected_direction": 0})
            gg["tested"] += 1
            gg["outside_90_band"] += int(r["outside_90_band"])
            gg["outside_and_expected_direction"] += int(r["outside_90_band"] and r["in_expected_direction"])
        for g in groups.values():
            g["expected_outside_by_chance"] = round(0.10 * g["tested"], 2)
        ns = [r["placebo_months"] for r in tested]
        rows_tested = sorted({r["row_id"] for r in tested})
        allrows = sorted({r["row_id"] for r in out if r["test"] == test})
        summ[test] = {"role": TEST_ROLE[test], "n_tests": len(tested),
                      "n_no_test": sum(1 for r in out if r["test"] == test) - len(tested),
                      "n_outside_band": sum(r["outside_90_band"] for r in tested),
                      "n_outside_and_expected_direction": sum(r["outside_90_band"] and r["in_expected_direction"]
                                                              for r in tested),
                      "expected_outside_by_chance": round(0.10 * len(tested), 2),
                      "expected_outside_discrete": r6(sum(discrete_outside_prob(n) for n in ns)),
                      "n_outside_band_nonoverlap_null": sum(bool(r["nonoverlap_outside_90_band"]) for r in tested),
                      "n_bh_q_lt_0.10": sum(1 for r in tested if r["bh_q"] < 0.10),
                      "smallest_p": r6(min((r["p_two_sided"] for r in tested), default=None)),
                      "smallest_p_rank": r6(min((r["p_rank"] for r in tested), default=None)),
                      "bh_rank1_threshold_q_0.10": r6(0.10 / len(tested)) if tested else None,
                      "distinct_observable_corpus_month_tests": len({(r["observable"], r["source"],
                                                                     r["timing_date"][:7]) for r in tested}),
                      "by_upgrade_and_opt_in": groups, "rows_with_any_test": rows_tested,
                      "rows_with_no_test_in_any_corpus": sorted(set(allrows) - set(rows_tested))}
    # the two events the verifier singled out, judged by counts under the discrete placebo null
    step = [r for r in out if r["status"] == "tested" and r["test"] == "step12"]
    ranked = sorted(step, key=lambda x: (x["p_rank"], x["p_two_sided"], -abs(x["percentile"] - 50),
                                         x["row_id"], x["source"]))
    rank_of = {(x["row_id"], x["source"]): i + 1 for i, x in enumerate(ranked)}
    focus = []
    for rid in ("d21-signzone-nsec3-iterations-0", "knot[14]@3.2.0"):
        r = next((x for x in step if x["row_id"] == rid and x["source"] == "se"), None)
        if r is None:
            continue
        p0 = r["p_rank"]
        n_as_extreme = sum(1 for x in step if x["p_rank"] <= p0 + 1e-6)
        probs = [discrete_p_le_prob(x["placebo_months"], p0) for x in step]
        focus.append({"row_id": rid, "source": "se", "observed": r["observed"], "percentile": r["percentile"],
                      "p_two_sided": r["p_two_sided"], "p_rank": p0, "bh_q": r["bh_q"],
                      "tests_in_family": len(step),
                      "rank_by_p": rank_of[(rid, "se")],
                      "tests_at_least_as_extreme": n_as_extreme,
                      "expected_at_least_as_extreme_by_chance": r6(sum(probs)),
                      "expected_at_least_as_extreme_continuous": r6(len(step) * p0),
                      "p_count_at_least_observed": r6(poisson_binomial_tail(probs, n_as_extreme))})
    top = [{"rank": i + 1, "row_id": x["row_id"], "source": x["source"], "observable": x["observable"],
            "percentile": x["percentile"], "p_two_sided": x["p_two_sided"], "p_rank": x["p_rank"],
            "in_expected_direction": x["in_expected_direction"]} for i, x in enumerate(ranked[:8])]
    return {"method": (f"For each mapped default row and corpus. Primary, step12: mean over the {STEP_POST} "
                       f"after-months of the share minus a linear trend fitted to the {STEP_PRE} before-months "
                       f"and extrapolated. Secondary, transient12, the transient deviation: detrended mean of "
                       f"{Q2_W} after-months minus {Q2_W} before-months, blind to a lasting step. Event month m = "
                       f"calendar month of the row's timing_date; forward after-months start at m, reverse "
                       f"after-labels start at m+1 because a reverse label is the state on the 1st. Null: "
                       f"{N_DRAWS} placebo event months drawn with replacement from every testable month of the "
                       f"same series except the event month; at least {Q2_MIN_PLACEBOS} testable months are needed. "
                       f"Sensitivity, columns nonoverlap_*: placebos only from months outside the event's own "
                       f"window, {STEP_PRE} before and {STEP_POST} after for step12 and {Q2_W} either side for "
                       f"transient12. The calibration in notes.calibration shows the sensitivity null rejects "
                       f"far above its nominal 10% on no-effect series, so it is not used for conclusions. "
                       f"Band = 5th-95th percentile. Counts are compared with their expectation under the "
                       f"discrete placebo null. 'no test' where the series lacks the before- or after-period."),
            "forward_note": FORWARD_NOTE, "summary": summ, "verifier_focus_events": focus,
            "most_extreme_step_tests": top,
            "multiple_testing_note": ("p_rank is the exact two-sided rank p against the finite set of placebo "
                                      "months, 2*min(below+1, above+1)/(n+1). With at most 148 placebo months its "
                                      "floor is 2/149 = 0.013, above the rank-1 Benjamini-Hochberg threshold of "
                                      "0.10/n, so no test can reach q < 0.10 and bh_q carries no evidence. The "
                                      "family is judged by counts against their expectation under the discrete "
                                      "placebo null."),
            "events": out}, out


# ------------------------------------------------------ detection power --

POWER_CASES = [("alg13", "forward", "se", "2019-01"), ("alg13", "reverse_panel", PANEL, "2018-06"),
               ("digest1", "forward", "nu", "2019-03")]
POWER_STEPS = (0, 1, 2, 5, 10)


def _step_test_at(st: np.ndarray, k: int, rng, nonoverlap: bool) -> tuple | None:
    """step12 value at index k against its placebo null: (value, percentile, band lo, band hi).
    Primary null: every testable month but k. Sensitivity: only months outside k-24..k+12."""
    tm = np.flatnonzero(~np.isnan(st))
    elig = placebo_months(tm, k, STEP_PRE, STEP_POST) if nonoverlap else placebo_months(tm, k, 0, 0)
    if len(tm) < Q2_MIN_PLACEBOS or len(elig) == 0 or math.isnan(st[k]):
        return None
    null = st[rng.choice(elig, size=N_DRAWS, replace=True)]
    lo, hi = np.percentile(null, BAND)
    return float(st[k]), pct_rank(null, st[k]), float(lo), float(hi)


def detection_power(data) -> dict:
    """Inject a lasting step of h pp into a real series from the event on and recompute the whole
    step12 test, null included. Reported at one named event month, and as the share of all eligible
    event months of the series at which the injected step lands above the 90% band."""
    rows, smallest = [], {}
    for obs, corpus, src, month in POWER_CASES:
        s = Series(data, obs, corpus, src)
        x = s.share.to_numpy(dtype=float)
        base_tm = np.flatnonzero(~np.isnan(s.stat["step12"]))
        name = f"{obs} {src_label(src)}"
        for h in POWER_STEPS:
            k = s.idx(m2i(month))
            y = x.copy()
            y[k:] += h
            st = step_stat(y)
            row = {"series": name, "observable": obs, "corpus": corpus, "source": src,
                   "event_month": month, "step_pp": h}
            for null_name, nonov in (("", False), ("nonoverlap_", True)):
                one = _step_test_at(st, k, rng_for(f"power|{null_name}{name}|{month}|{h}"), nonov)
                hits = n_ev = 0
                for k0 in base_tm:
                    y2 = x.copy()
                    y2[k0:] += h
                    res = _step_test_at(step_stat(y2), int(k0),
                                        rng_for(f"power|{null_name}{name}|all|{int(k0)}|{h}"), nonov)
                    if res is None:
                        continue
                    n_ev += 1
                    hits += int(res[0] > res[3])
                row.update({f"{null_name}statistic": r6(one[0]) if one else None,
                            f"{null_name}percentile": r6(one[1]) if one else None,
                            f"{null_name}above_band": bool(one and one[0] > one[3]),
                            f"{null_name}event_months_tested": n_ev,
                            f"{null_name}share_of_event_months_above_band": r6(hits / n_ev) if n_ev else None})
            rows.append(row)
        det = [r for r in rows if r["series"] == name and r["step_pp"] > 0
               and (r["share_of_event_months_above_band"] or 0) >= 0.5]  # primary null
        smallest[name] = (min(r["step_pp"] for r in det) if det else None)
    return {"method": ("A lasting step of h pp is added to every month from the event on, and step12 and its "
                       "placebo null, placebos outside the event's -24..+12 window, are recomputed on the "
                       "modified series. Columns without prefix use the primary null, every testable month but the "
                       "event's; nonoverlap_* use only months outside the event's window, which is liberal: with no "
                       "step at all it already puts many event months above the band. 'percentile' is at the named "
                       "event month; the share is over every "
                       "eligible event month of the series. The smallest detectable step is the smallest h "
                       "that lands above the 90% band at half or more of the event months; None means not "
                       "even 10 pp."),
            "rows": rows, "smallest_detectable_step_pp": smallest,
            "false_positive_share_at_0pp": {r["series"]: r["share_of_event_months_above_band"]
                                            for r in rows if r["step_pp"] == 0},
            "false_positive_share_at_0pp_nonoverlap": {r["series"]: r["nonoverlap_share_of_event_months_above_band"]
                                                       for r in rows if r["step_pp"] == 0}}


def src_label(src: str) -> str:
    return "panel" if src == PANEL else f".{src}"


# --------------------------------------------------------- calibration --


def _synthetic_series(rng, n: int) -> np.ndarray:
    """A share-like series with trend, random-walk drift and noise, and no event effect."""
    walk = np.cumsum(rng.normal(0, 0.3, n))
    return 20 + 0.05 * np.arange(n) + walk + rng.normal(0, 0.5, n)


@functools.lru_cache(maxsize=None)
def calibration(n_rep: int = CALIB_REPS) -> dict:
    """Rejection rates at the 90% band on synthetic series with no effect.

    q2: one event month per series, band from N_DRAWS placebo months of the same series: every
    testable month but the event's (the primary null), and only months outside the event's -24..+12
    window (the sensitivity null).
    q1: a 25-month release schedule whose frequency rises over a 240-month span, against a series
    covering only the last 96 months, tested with the coverage-window shift used here and with the
    whole-span shift used before the revision."""
    rng = np.random.default_rng([SEED, zlib.crc32(b"calibration")])
    rej2 = rej2_far = 0
    rej1_win = rej1_span = rej1_far = 0
    n1 = 0
    for _ in range(n_rep):
        x = _synthetic_series(rng, 96)
        st = step_stat(x)
        tm = np.flatnonzero(~np.isnan(st))
        e = int(rng.choice(tm))
        null = st[rng.choice(placebo_months(tm, e, 0, 0), size=N_DRAWS, replace=True)]
        lo, hi = np.percentile(null, BAND)
        rej2 += int(st[e] < lo or st[e] > hi)
        far = placebo_months(tm, e, STEP_PRE, STEP_POST)
        null = st[rng.choice(far, size=N_DRAWS, replace=True)]
        lo, hi = np.percentile(null, BAND)
        rej2_far += int(st[e] < lo or st[e] > hi)
        # q1: releases on a 240-month span, rate rising linearly; series = months 144..239
        w = np.arange(240, dtype=float) + 1
        rel = np.sort(rng.choice(240, size=25, replace=False, p=w / w.sum()))
        full = np.full(240, np.nan)
        full[144:] = st

        def at(ms):
            ms = np.asarray(ms, dtype=int)
            return full[ms]
        valid = np.flatnonzero(~np.isnan(full))
        blo, bhi = np.percentile(full[valid], BAND)
        r_win = shift_test(at, rel, int(valid.min()), int(valid.max()), rng, blo, bhi)
        r_far = shift_test(at, rel, int(valid.min()), int(valid.max()), rng, blo, bhi, STEP_PRE, STEP_POST)
        r_span = shift_test(at, rel, int(rel.min()), int(rel.max()), rng, blo, bhi)
        if (r_win is None or r_span is None or r_far is None or r_far["no_offsets"]
                or len(r_win["null_mean"]) == 0 or len(r_span["null_mean"]) == 0 or len(r_far["null_mean"]) == 0):
            continue
        n1 += 1
        rej1_win += int(two_sided(r_win["null_mean"], r_win["obs_mean"]) < 0.10)
        rej1_span += int(two_sided(r_span["null_mean"], r_span["obs_mean"]) < 0.10)
        rej1_far += int(two_sided(r_far["null_mean"], r_far["obs_mean"]) < 0.10)
    return {"reps": n_rep, "q2_step12_rejection_rate": r6(rej2 / n_rep),
            "q2_step12_nonoverlap_null_rejection_rate": r6(rej2_far / n_rep),
            "q1_nonoverlap_shift_rejection_rate": r6(rej1_far / max(1, n1)),
            "q1_reps_with_a_test": n1,
            "q1_coverage_window_shift_rejection_rate": r6(rej1_win / max(1, n1)),
            "q1_whole_span_shift_rejection_rate": r6(rej1_span / max(1, n1)),
            "nominal": 0.10}


# -------------------------------------------------------------------- q3 --


def size_bin(n: int) -> str:
    for lo, hi, lab in SIZE_BINS:
        if lo <= n <= hi:
            return lab
    raise ValueError(n)


LEVELS = ["single delegation", "one block", "concentrated", "diffuse"]


def level_short(s: str) -> str:
    for L in LEVELS:
        if s.startswith(L):
            return L
    return s


def q3(rows):
    cl = pd.read_parquet(OUT / "delegation_change_clusters.parquet")
    lv = pd.read_parquet(OUT / "delegation_change_levels.parquet")
    lv = lv.assign(level=lv.level.map(level_short))
    universe = list(range(m2i(cl.month.min()), m2i(cl.month.max()) + 1))
    src_span = {s: (m2i(g.month.min()), m2i(g.month.max())) for s, g in cl.groupby("source")}
    cl = cl.assign(mi=cl.month.map(m2i))
    lv = lv.assign(mi=lv.month.map(m2i))
    rmap = rows.set_index("row_id")
    events = []
    for rid, alg in Q3_ALG_ROWS.items():
        r = rmap.loc[rid]
        m = m2i(r.timing_date[:7])
        events.append({"program": r.program, "row_id": rid, "to_alg": alg, "timing_date": r.timing_date,
                       "window": [i2m(m + 1), i2m(m + WINDOW + 1)],
                       "months": list(range(m + 1, m + WINDOW + 2))})
    groups = [(e["row_id"], [e]) for e in events]
    for alg in sorted({e["to_alg"] for e in events}, key=int):
        ev = [e for e in events if e["to_alg"] == alg]
        if len(ev) > 1:
            groups.append((f"all default changes to algorithm {alg}", ev))
    results = []

    def monthly(match_cl, match_lv, uni):
        """Per-month totals on the universe: all, large-action and one-block/concentrated delegations."""
        u0 = uni[0]
        n = len(uni)
        T, Lg, LT, B = (np.zeros(n) for _ in range(4))
        for mi_, nd in zip(match_cl.mi, match_cl.n_delegations):
            if 0 <= mi_ - u0 < n:
                T[mi_ - u0] += nd
                if nd >= LARGE_ACTION:
                    Lg[mi_ - u0] += nd
        for mi_, nd, lev in zip(match_lv.mi, match_lv.n_delegations, match_lv.level):
            if 0 <= mi_ - u0 < n:
                LT[mi_ - u0] += nd
                if lev in ("one block", "concentrated"):
                    B[mi_ - u0] += nd
        return T, Lg, LT, B

    def diff(mask, num, den):
        a, b = den[mask].sum(), den[~mask].sum()
        if a == 0 or b == 0:
            return float("nan")
        return float(num[mask].sum() / a - num[~mask].sum() / b)

    for gname, ev in groups:
        alg = ev[0]["to_alg"]
        win = sorted({mm for e in ev for mm in e["months"]})
        for scope in ["all RIRs"] + RIRS:
            mcl = cl[(cl.kind.isin(["sign", "rollover"])) & (cl.to_alg == alg)]
            mlv = lv[(lv.kind.isin(["sign", "rollover"])) & (lv.to_alg == alg)]
            uni = universe
            if scope != "all RIRs":
                mcl, mlv = mcl[mcl.source == scope], mlv[mlv.source == scope]
                a, b = src_span.get(scope, (None, None))
                if a is None:
                    continue
                uni = list(range(a, b + 1))
            win_s = [x for x in win if x in set(uni)]
            base = {"group": gname, "rows": ";".join(e["row_id"] for e in ev),
                    "programs": ";".join(sorted({e["program"] for e in ev})), "to_alg": alg,
                    "windows": ";".join(f"{e['window'][0]}..{e['window'][1]}" for e in ev),
                    "scope": scope, "transitions": f"sign or rollover to algorithm {alg}"}
            if not win_s:
                results.append({**base, "status": "no test",
                                "reason": f"ledger for {scope} does not cover the window"})
                continue
            T, Lg, LT, B = monthly(mcl, mlv, uni)
            mask = np.zeros(len(uni), dtype=bool)
            mask[np.array(win_s) - uni[0]] = True
            d_large, d_block, n_in = diff(mask, Lg, T), diff(mask, B, LT), int(T[mask].sum())
            n_out = int(mcl[~mcl.mi.isin(win_s)].n_delegations.sum())
            dist = {}
            wa = mcl[mcl.mi.isin(win_s)].sort_values(["n_delegations", "month", "source", "block"],
                                                     ascending=[False, True, True, True])
            largest = ({"largest_window_action": f"{wa.iloc[0].source} {wa.iloc[0].block} label {wa.iloc[0].month} "
                                                 f"{wa.iloc[0].kind}",
                        "largest_window_action_delegations": int(wa.iloc[0].n_delegations)}
                       if len(wa) else {"largest_window_action": None, "largest_window_action_delegations": 0})
            for part, sub in (("window", mcl[mcl.mi.isin(win_s)]), ("other", mcl[~mcl.mi.isin(win_s)])):
                sub = sub.assign(bin=sub.n_delegations.map(size_bin))
                dist[part + "_actions_by_size"] = {lab: int((sub.bin == lab).sum()) for *_, lab in SIZE_BINS}
                dist[part + "_delegations_by_size"] = {lab: int(sub[sub.bin == lab].n_delegations.sum())
                                                       for *_, lab in SIZE_BINS}
            for part, sub in (("window", mlv[mlv.mi.isin(win_s)]), ("other", mlv[~mlv.mi.isin(win_s)])):
                dist[part + "_delegations_by_level"] = {L: int(sub[sub.level == L].n_delegations.sum()) for L in LEVELS}
            if n_in < 5:
                results.append({**base, "status": "no test", "window_matching_delegations": n_in,
                                "other_matching_delegations": n_out,
                                "reason": "fewer than 5 matching delegations in the window", **_flat(dist)})
                continue
            rng = rng_for(f"q3|{gname}|{scope}")
            null_l, null_b = [], []
            for _ in range(N_DRAWS):
                pk = np.zeros(len(uni), dtype=bool)
                pk[rng.choice(len(uni), size=len(win_s), replace=False)] = True
                dl, db = diff(pk, Lg, T), diff(pk, B, LT)
                if not math.isnan(dl):
                    null_l.append(dl)
                if not math.isnan(db):
                    null_b.append(db)
            null_l, null_b = np.array(null_l), np.array(null_b)
            # era-matched sensitivity: permute only within +-ERA months of the window
            era_idx = np.array([i for i, x in enumerate(uni) if min(win_s) - ERA <= x <= max(win_s) + ERA])
            rng2 = rng_for(f"q3era|{gname}|{scope}")
            era_l, era_b = [], []
            for _ in range(N_DRAWS):
                pk = np.zeros(len(uni), dtype=bool)
                pk[rng2.choice(era_idx, size=len(win_s), replace=False)] = True
                dl, db = diff(pk, Lg, T), diff(pk, B, LT)
                if not math.isnan(dl):
                    era_l.append(dl)
                if not math.isnan(db):
                    era_b.append(db)
            era_l, era_b = np.array(era_l), np.array(era_b)
            results.append({**base, "status": "tested", "window_months": len(win_s),
                            "window_matching_delegations": n_in, "other_matching_delegations": n_out,
                            "diff_share_in_actions_ge_10": r6(d_large),
                            "p_large_ge_observed": r6(np.mean(null_l >= d_large)) if len(null_l) and not math.isnan(d_large) else None,
                            "diff_share_one_block_or_concentrated": r6(d_block),
                            "p_block_ge_observed": r6(np.mean(null_b >= d_block)) if len(null_b) and not math.isnan(d_block) else None,
                            "null_draws_large": int(len(null_l)), "null_draws_block": int(len(null_b)),
                            "p_large_era_matched": r6(np.mean(era_l >= d_large)) if len(era_l) and not math.isnan(d_large) else None,
                            "p_block_era_matched": r6(np.mean(era_b >= d_block)) if len(era_b) and not math.isnan(d_block) else None,
                            **largest, **_flat(dist)})
    # every-month baseline for context
    base_all = cl[cl.kind.isin(["sign", "rollover"])].assign(bin=lambda x: x.n_delegations.map(size_bin))
    baseline = {lab: int(base_all[base_all.bin == lab].n_delegations.sum()) for *_, lab in SIZE_BINS}
    return {"method": (f"Actions from delegation_change_clusters (month x source x block x transition). "
                       f"Matching transitions: sign or rollover to the algorithm the default names. Window: "
                       f"ledger labels r+1..r+{WINDOW + 1} for a release in calendar month r, i.e. the changes "
                       f"made in the release month and the {WINDOW} months after. Statistics: difference, window "
                       f"minus other months, in the share of matching delegations moved in actions of "
                       f">= {LARGE_ACTION} delegations, and in the share at level one block or concentrated "
                       f"(delegation_change_levels). Null: the same number of months drawn without "
                       f"replacement from the ledger span, {N_DRAWS} draws; p = share of draws at or above "
                       f"the observed difference. Sensitivity: the same permutation restricted to months within "
                       f"+-{ERA} months of the window (era-matched), because ledger activity rises about "
                       f"25-fold from 2009 to 2019."),
            "proxy_caveat": ("Action size is a proxy. One operator automating one delegation is "
                             "indistinguishable from a manual edit, and one operator hand-editing a block "
                             "is indistinguishable from an upgrade."),
            "ledger_dating": ("Ledger label M = the change between the snapshots of 00:00 UTC on the 1st of M-1 "
                              "and of M, so it happened in calendar month M-1. The window for a release in "
                              "calendar month r is labels r+1..r+4, the changes of calendar months r..r+3."),
            "all_sign_or_rollover_delegations_by_size": baseline,
            "events": events and [{k: v for k, v in e.items() if k != "months"} for e in events],
            "tests": results}, results


def _flat(d):
    out = {}
    for k, v in d.items():
        for kk, vv in v.items():
            out[f"{k}:{kk}"] = vv
    return out


# -------------------------------------------------------------------- q4 --


def reverse_count_series(data: Data, rir: str, dim: str, values) -> pd.Series:
    """Per-RIR count. Since the relabelling of the server run (scripts/fix_server_run_month_labels.py)
    it shares the panel's and the ledger's convention: label M = state at 00:00 UTC on the 1st of M.
    No shift is applied here."""
    pv = data.pivot("srv", rir, dim)
    months = data.months("srv", rir)
    return _num(pv, values).reindex(months, fill_value=0.0)


def check_reverse_dating(data: Data) -> dict:
    out = {}
    for rir in ("afrinic", "arin"):
        a = reverse_count_series(data, rir, "algorithm_ds", ["_total"])
        pv = data.pivot("pan", rir, "algorithm_ds")
        b = pv["_total"] if "_total" in pv.columns else pd.Series(dtype=float)
        common = sorted(set(a.index) & set(b.index))
        same = sum(1 for m in common if a[m] == b[m])
        shifted = {i2m(m2i(m) + 1): v for m, v in a.items()}
        common1 = sorted(set(shifted) & set(b.index))
        same1 = sum(1 for m in common1 if shifted[m] == b[m])
        out[rir] = {"months_compared": len(common), "equal_without_shift": same,
                    "months_compared_with_plus_one_shift": len(common1), "equal_with_plus_one_shift": same1}
    return out


def poisson_binomial_tail(ps, k):
    dist = np.zeros(len(ps) + 1)
    dist[0] = 1.0
    for p in ps:
        dist[1:] = dist[1:] * (1 - p) + dist[:-1] * p
        dist[0] *= (1 - p)
    return float(dist[k:].sum())


def q4(rows, releases, data):
    mapped, _ = mapping_table(rows)
    ledger = pd.read_parquet(OUT / "delegation_changes.parquet")
    obs_rows = {}
    for m in mapped:
        obs_rows.setdefault(m["observable"], []).append(m)
    rel_idx = {p: [(t, d, m2i(d[:7])) for t, d in r] for p, r in releases.items()}
    spikes_out, chance_out = [], []
    n = 0
    for obs in sorted(obs_rows):
        o = OBSERVABLES[obs]
        sets = []
        if o["fwd"] is not None:
            (nd, nv), _ = o["fwd"]
            for t in FORWARD_TLDS:
                if not data.months("srv", t):
                    continue
                pv = data.pivot("srv", t, nd)
                y = _num(pv, nv).reindex(data.months("srv", t), fill_value=0.0)
                den = data.pivot("srv", t, "algorithm_dnskey").get("_total")
                sets.append(("forward", t, y, FORWARD_FLOOR, den))
        if o["rev"] is not None:
            (nd, nv), _ = o["rev"]
            for rir in RIRS:
                sets.append(("reverse", rir, reverse_count_series(data, rir, nd, nv), REVERSE_FLOOR, None))
        for corpus, src, y, floor, den in sets:
            if y.max() < floor:
                continue
            months = list(y.index)
            # calendar month in which the change into each label happened: reverse label M = M-1
            cal_shift = 1 if corpus == "reverse" else 0
            mi = [m2i(x) - cal_shift for x in months]
            for direction in (+1, -1):
                rel_rows = [r for r in obs_rows[obs] if r["expected_direction"] == direction]
                rel_months = [m2i(r["timing_date"][:7]) for r in rel_rows]
                # chance: share of series months (after the first) with a relevant default 0..3 months before
                inside = sum(1 for x in mi[1:] if any(0 <= x - d <= WINDOW for d in rel_months))
                chance = inside / max(1, len(mi) - 1)
                chance_out.append({"observable": obs, "direction": direction, "corpus": corpus, "source": src,
                                   "months": len(mi) - 1, "relevant_rows": ";".join(r["row_id"] for r in rel_rows),
                                   "chance_relevant_default_within_3m": r6(chance)})
                for ep in _spikes(y.astype(int), floor, direction):
                    n += 1
                    s0 = m2i(ep["start"]) - cal_shift   # calendar month of the change
                    near = None
                    for r in rel_rows:
                        d = m2i(r["timing_date"][:7])
                        if d <= s0 and (near is None or s0 - d < near[1]):
                            near = (r, s0 - d)
                    any_dir = None
                    for r in obs_rows[obs]:
                        d = m2i(r["timing_date"][:7])
                        if d <= s0 and (any_dir is None or s0 - d < any_dir[1]):
                            any_dir = (r, s0 - d)
                    nearest_rel = {}
                    for p, rl in rel_idx.items():
                        prev = [x for x in rl if x[2] <= s0]
                        if prev:
                            t, dd, mm = prev[-1]
                            nearest_rel[p] = f"{t} {dd} lag {s0 - mm}"
                    comp = _composition(corpus, src, obs, direction, ep, ledger, den, y)
                    spikes_out.append({
                        "n": n, "observable": obs, "direction": direction, "corpus": corpus, "source": src,
                        "start": ep["start"], "end": ep["end"], "change_calendar_month_start": i2m(s0),
                        "delta": ep["delta"],
                        "level_before": ep["level_before"], "level_after": ep["level_after"],
                        "nearest_relevant_default": (f"{near[0]['program']} {near[0]['row_id']} "
                                                     f"{near[0]['timing_date']}") if near else None,
                        "lag_months": near[1] if near else None,
                        "relevant_default_within_3m": bool(near and near[1] <= WINDOW),
                        "nearest_default_any_direction": (f"{any_dir[0]['program']} {any_dir[0]['row_id']} "
                                                          f"{any_dir[0]['timing_date']} lag {any_dir[1]}")
                        if any_dir else None,
                        "chance_relevant_default_within_3m": r6(chance),
                        **{f"nearest_release_{p}": v for p, v in sorted(nearest_rel.items())},
                        **comp})
    # per observable and corpus: does alignment beat chance?
    agg = []
    df = pd.DataFrame(spikes_out)
    if len(df):
        for (obs, corpus, direction), g in df.groupby(["observable", "corpus", "direction"]):
            k = int(g.relevant_default_within_3m.sum())
            ps = g.chance_relevant_default_within_3m.astype(float).tolist()
            agg.append({"observable": obs, "corpus": corpus, "direction": int(direction), "spikes": len(g),
                        "aligned_within_3m": k, "expected_aligned": r6(sum(ps)),
                        "p_at_least_observed": r6(poisson_binomial_tail(ps, k)),
                        "beats_chance": bool(poisson_binomial_tail(ps, k) < 0.05 and k > 0)})
    return {"method": ("Spikes by program_rfc_cases.spikes() (imported, not re-implemented) on numerator "
                       "counts: forward per TLD (floor 300), reverse per RIR (floor 30, counts only). A reverse "
                       "spike labelled M is a change between the states of the 1st of M-1 and the 1st of M, so "
                       "it happened in calendar month M-1; lags and chance rates use that calendar month. "
                       "Both directions are scanned. A relevant "
                       "default change maps to the same observable with the same expected direction; "
                       "'aligned' = one at 0..3 months before the spike start. Chance = share of the "
                       "series' months that have a relevant default change 0..3 months before them. "
                       "Beating chance is judged per observable, corpus and direction by the "
                       "Poisson-binomial tail of the aligned count."),
            "forward_note": FORWARD_NOTE,
            "reverse_dating_check": check_reverse_dating(data),
            "spikes": spikes_out, "chance": chance_out, "alignment_vs_chance": agg}, spikes_out


def _composition(corpus, src, obs, direction, ep, ledger, den, y):
    algs = OBSERVABLES[obs].get("algs")
    months = [i2m(i) for i in range(m2i(ep["start"]), m2i(ep["end"]) + 1)]
    if corpus == "reverse":
        if not algs:
            return {"composition": "not determinable: the ledger records DS algorithms only",
                    "new_signings": None, "rollovers": None, "unsignings": None}
        L = ledger[(ledger.source == src) & (ledger.month.isin(months))]
        if direction > 0:
            ns = int(((L.kind == "sign") & L.to_alg.isin(algs)).sum())
            ro = int(((L.kind == "rollover") & L.to_alg.isin(algs)).sum())
            un = 0
        else:
            ns = 0
            ro = int(((L.kind == "rollover") & L.from_alg.isin(algs)).sum())
            un = int(((L.kind == "unsign") & L.from_alg.isin(algs)).sum())
        tot = ns + ro + un
        if tot == 0:
            lab = "no matching ledger events"
        elif direction > 0:
            lab = "mostly new signings" if ns >= ro else "mostly rollovers"
        else:
            lab = "mostly unsignings" if un >= ro else "mostly rollovers away"
        return {"composition": lab, "new_signings": ns, "rollovers": ro, "unsignings": un}
    # forward: bound from the growth in signed zones (per-zone records are not in the repository)
    if obs.startswith("alg") and direction > 0 and den is not None:
        prev = i2m(m2i(ep["start"]) - 1)
        dsigned = int(den.get(ep["end"], 0) - den.get(prev, 0))
        new_max = max(0, min(ep["delta"], dsigned))
        return {"composition": ("mostly rollovers (bound)" if ep["delta"] - new_max > new_max
                                else "could be mostly new signings (bound)"),
                "new_signings": f"at most {new_max}", "rollovers": f"at least {max(0, ep['delta'] - new_max)}",
                "unsignings": None}
    return {"composition": "not determinable: forward per-zone records are not in the repository",
            "new_signings": None, "rollovers": None, "unsignings": None}


# -------------------------------------------------------------------- q5 --

Q5_PAIRS = [
    dict(predecessor="RFC 5155", successor="RFC 9276", relation="related_rfc_ids of RFC 9276",
         observable="iter_gt0", what="NSEC3 owner names with more than 0 iterations (RFC 5155 practice "
                                     "that RFC 9276 retires)"),
    dict(predecessor="RFC 3110 / RFC 4034 RSASHA1 signing", successor="RFC 8624", relation="brief example; "
         "RFC 8624 makes RSASHA1 signing NOT RECOMMENDED", observable="alg5_7",
         what="RSASHA1 family (5, 7) share"),
    dict(predecessor="SHA-1 DS (RFC 4034 digest 1)", successor="RFC 8624", relation="brief example; RFC 8624 "
         "makes SHA-1 DS generation MUST NOT", observable="digest1", what="SHA-1 DS share"),
    dict(predecessor="SHA-1 DS (RFC 4034 digest 1)", successor="RFC 4509", relation="brief example: SHA-1 DS "
         "and SHA-256", observable="digest1", what="SHA-1 DS share"),
    dict(predecessor="RFC 8624", successor="RFC 9904", relation="obsoleted_by of RFC 8624",
         observable="alg8_13", what="share of RFC 8624 MUST algorithms 8 and 13"),
    dict(predecessor="RFC 3110 (RSA/SHA-1)", successor="RFC 9905", relation="related_rfc_ids of RFC 9905",
         observable="alg5_7", what="RSASHA1 family (5, 7) share"),
    dict(predecessor="RFC 5933 (GOST)", successor="RFC 9906", relation="related_rfc_ids of RFC 9906",
         observable="alg12", what="ECC-GOST (12) share"),
]


def q5(data):
    ck = json.loads((ROOT / "data/rfc_checklists/dnssec_rfc_checklists.json").read_text("utf-8"))
    pub = {r["rfc_id"]: r["publication_date"][:7] for r in ck["rfcs"]}
    out = []
    for p in Q5_PAIRS:
        sm = pub[p["successor"]]
        si = m2i(sm)
        for corpus, src in corpora_for(p["observable"]):
            s = Series(data, p["observable"], corpus, src)
            base = {"predecessor": p["predecessor"], "successor": p["successor"], "successor_published": sm,
                    "relation": p["relation"], "observable": p["observable"], "what": p["what"],
                    "corpus": corpus, "source": src}
            if not s.ok or s.first_valid is None:
                out.append({**base, "status": "not covered", "reason": "no valid series"})
                continue
            sh = s.share.dropna()
            if not s.ever_nonzero:
                out.append({**base, "status": "value never observed", "series": f"{s.first_valid}..{s.last_valid}"})
                continue
            # the peak is taken only over months with at least PEAK_MIN_DEN in the denominator: MIN_DEN
            # alone admits the panel's first signed month, 32 delegations at 103% for RSASHA1
            den = s.den.reindex(sh.index)
            shp = sh[den >= PEAK_MIN_DEN]
            peak_any_m, peak_any = sh.idxmax(), float(sh.max())
            if len(shp):
                peak_m, peak = shp.idxmax(), float(shp.max())
                below = sh[(sh.index > peak_m) & (sh < 0.5 * peak) & (den >= PEAK_MIN_DEN)]
                half_m = below.index[0] if len(below) else None
            else:
                peak_m = peak = half_m = None
            row = {**base, "series": f"{s.first_valid}..{s.last_valid}",
                   "peak_min_den": PEAK_MIN_DEN, "peak": r6(peak), "peak_month": peak_m,
                   "peak_denominator": int(den[peak_m]) if peak_m else None,
                   "first_below_half_peak_after_peak": half_m,
                   "months_from_successor_to_below_half": (m2i(half_m) - si) if half_m else None,
                   "peak_over_min_den_months": r6(peak_any), "peak_over_min_den_month": peak_any_m,
                   "peak_over_min_den_denominator": int(den[peak_any_m]),
                   # the floor's first month is not a peak when the share was already falling
                   "peak_is_first_month_over_floor": bool(peak_m is not None and len(shp)
                                                          and peak_m == shp.index[0]),
                   "first_month_over_floor": shp.index[0] if len(shp) else None}
            if sm not in sh.index:
                row.update({"status": "not covered at successor publication",
                            "first_covered_month": s.first_valid, "share_first_covered": r6(sh.iloc[0])
                            if sm < s.first_valid else None,
                            "reason": (f"series starts {s.first_valid}" if sm < s.first_valid
                                       else f"series ends {s.last_valid}")})
                out.append(row)
                continue
            s0 = float(sh[sm])
            later = sh[sh.index > sm]
            h = min(12, len(later))
            s12 = float(later.iloc[h - 1]) if h else None
            if s12 is None:
                traj = "no months after"
            elif s0 == 0 and s12 == 0:
                traj = "flat at zero"
            else:
                rel = (s12 - s0) / s0 if s0 else float("inf")
                traj = "kept rising" if rel > 0.10 else ("fell" if rel < -0.10 else "flat")
            row.update({"status": "covered", "share_at_successor": r6(s0),
                        "months_after_observed": len(later), "compare_month": later.index[h - 1] if h else None,
                        "share_after_up_to_12m": r6(s12), "trajectory": traj,
                        "share_last_month": r6(float(sh.iloc[-1])),
                        "fell_below_half_peak_before_successor": bool(half_m is not None and m2i(half_m) < si)})
            out.append(row)
    return {"method": ("Predecessor share in the successor's publication month (checklist publication_date), "
                       "then the share up to 12 months later (fewer where the corpus ends): 'kept rising' "
                       "above +10% relative, 'fell' below -10%, else 'flat'. A reverse share 'at' month M is "
                       "the state on the 1st of M. Peak = maximum over covered months with at least "
                       f"{PEAK_MIN_DEN} in the denominator; months counted from the successor's publication to the first month "
                       "after the peak below half of it. Descriptive only."),
            "forward_note": FORWARD_NOTE, "pairs": out}, out


# ------------------------------------------------------------------- main --


def coverage_facts(data: Data) -> dict:
    f = {}
    for t in FORWARD_TLDS:
        ms = data.months("srv", t)
        s = Series(data, "alg13", "forward", t)
        f[t] = {"months": f"{ms[0]}..{ms[-1]}", "signed_zone_share_valid": (f"{s.first_valid}..{s.last_valid}"
                                                                            if s.first_valid else "never")}
    s = Series(data, "alg13", "reverse_panel", PANEL)
    pm = data.months("pan", PANEL)
    f[PANEL] = {"months": f"{pm[0]}..{pm[-1]}", "signed_delegation_share_valid": f"{s.first_valid}..{s.last_valid}"}
    return f


def save(doc: dict):
    JSON_OUT.write_text(json.dumps(doc, indent=1, sort_keys=False, default=r6) + "\n", "utf-8")


def write_csv(name: str, recs: list):
    df = pd.DataFrame(recs)
    df.to_csv(OUT / f"software_vs_adoption_{name}.csv", index=False, float_format="%.6g")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--only", choices=["q1", "q2", "q3", "q4", "q5"], action="append")
    a = ap.parse_args(argv)
    todo = a.only or ["q1", "q2", "q3", "q4", "q5"]
    rows = load_rows()
    releases = load_releases()
    data = Data()
    global FORWARD_TLDS
    present = set(data.srv.loc[data.srv.basis == "zonefile", "source"].unique())
    FORWARD_TLDS = [t for t in FORWARD_TLDS if t in present] + sorted(present - set(FORWARD_TLDS))
    print(f"reading {_run_paths.describe()}; forward sources: {', '.join(FORWARD_TLDS)}")
    doc = json.loads(JSON_OUT.read_text("utf-8")) if (a.only and JSON_OUT.exists()) else {}
    mapped, unmapped = mapping_table(rows)
    doc["observable_mapping"] = {"by_mechanism": MECH_TABLE, "rows": mapped,
                                 "observables": {k: {"label": v["label"], "forward": _spec_text(v["fwd"]),
                                                     "reverse": _spec_text(v["rev"], panel=True)}
                                                 for k, v in OBSERVABLES.items()}}
    doc["excluded"] = {"rows_not_observable": unmapped, "rows_excluded_upstream": EXCLUDED_UPSTREAM,
                       "releases_excluded": ["pdns-rec aliases (alias_of)",
                                             "tags never released publicly: pdns-rec rec-4.5.0, rec-4.5.3, rec-5.0.0"]}
    doc["inputs"] = _run_paths.inputs_record()
    doc["notes"] = {
        "seed": SEED, "draws": N_DRAWS, "min_denominator": MIN_DEN,
        "detrend": f"centred {TREND_WIN}-month rolling median, min_periods {TREND_MIN}",
        "share_measure": ("shares are percentages built from domain_days (the month's mean daily share); "
                          "the MIN_DEN floor applies to the peak-day denominator. domains_peak is not "
                          "additive across values: se 2019-06 NSEC3 per-value peaks sum to 115% of the "
                          "_total peak while zones moved from 1 to 5 iterations. Sums over several "
                          "algorithm values still count a zone or delegation carrying two of them twice "
                          "(rollovers), which can push a summed share slightly above 100."),
        "coverage": coverage_facts(data),
        "step_test": (f"primary Q1/Q2 statistic: mean of actual minus a linear trend fitted to the {STEP_PRE} "
                      f"months before the event and extrapolated over the {STEP_POST} months after. The "
                      f"centred rolling-median detrend absorbs a lasting level step, so the old statistic is "
                      f"kept only as a secondary transient-deviation test."),
        "calibration": calibration(),
        "strict_panel": f"every reverse share uses {PANEL} from out/panel_run; per-RIR server-run series "
                        f"are used only for counts (q4 spikes)",
        "reverse_dating": ("Every reverse source, the server run, the panel run and the ledger, uses one "
                           "convention since the server run was relabelled: label M is the state at 00:00 UTC "
                           "on the 1st of M. A reverse state difference or ledger change labelled M therefore "
                           "happened during calendar month M-1. For a release in calendar month r, states up "
                           "to label r are before it, after-states start at label r+1, and ledger changes after "
                           "it are labels r+1 on. Forward labels are calendar months of measurement. No shift "
                           "is applied to any series; the event index is moved instead (checked in "
                           "q4.reverse_dating_check)."),
        "forward_note": FORWARD_NOTE,
        "release_dates": "stable release row's `released` from data/software/timelines; default rows use "
                         "Phase 4 timing_* columns, which already apply first_public_tag",
    }
    save(doc)
    write_csv("mapping", mapped)
    write_csv("excluded", unmapped)
    if "q1" in todo:
        res, summ, per = q1(rows, releases, data)
        doc["q1_per_program_releases"] = res
        save(doc)
        write_csv("q1", summ)
        write_csv("q1_releases", per)
        print("q1 saved", res["aggregate"])
    if "q2" in todo:
        res, recs = q2(rows, data)
        res["detection_power"] = detection_power(data)
        doc["q2_default_change_events"] = res
        save(doc)
        write_csv("q2", recs)
        write_csv("power", res["detection_power"]["rows"])
        print("q2 saved", {k: (v["n_tests"], v["n_outside_band"]) for k, v in res["summary"].items()})
    if "q3" in todo:
        res, recs = q3(rows)
        doc["q3_manual_vs_automatic"] = res
        save(doc)
        write_csv("q3", recs)
        print("q3 saved", len(recs))
    if "q4" in todo:
        res, recs = q4(rows, releases, data)
        doc["q4_spikes"] = res
        save(doc)
        write_csv("q4", recs)
        write_csv("q4_alignment", res["alignment_vs_chance"])
        print("q4 saved", len(recs), "spikes")
    if "q5" in todo:
        res, recs = q5(data)
        doc["q5_successor_rfc"] = res
        save(doc)
        write_csv("q5", recs)
        print("q5 saved", len(recs))
    # fixed key order
    order = ["inputs", "observable_mapping", "excluded", "notes", "q1_per_program_releases", "q2_default_change_events",
             "q3_manual_vs_automatic", "q4_spikes", "q5_successor_rfc"]
    save({k: doc[k] for k in order if k in doc})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
