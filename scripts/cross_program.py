#!/usr/bin/env python3
"""Phase 4: cross-program comparison of the eight verified DNS software timelines.

Reads only:
  data/software/timelines/<program>.json
  data/rfc_checklists/dnssec_rfc_checklists.json
  data/software/software_support.json            (cross-check only)

Writes:
  out/analysis/cross_program.json                one key per question + normalisation,
                                                 excluded_rows, suspect_rows
  out/analysis/cross_program_<question>.csv      one long-form CSV per question

Deterministic: the only randomness is the question 8 circular-shift null, drawn from
random.Random(SEED) with SEED = 20260929 and N_DRAWS = 1000.

Usage:  python3 scripts/cross_program.py [--only q1,q2,...]
Every output row carries the program and row id it came from, so each number can be
recomputed from the timeline files.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import re
import statistics
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TL = ROOT / "data" / "software" / "timelines"
CHECKLIST = ROOT / "data" / "rfc_checklists" / "dnssec_rfc_checklists.json"
SUPPORT = ROOT / "data" / "software" / "software_support.json"
OUT = ROOT / "out" / "analysis"
OUT_JSON = OUT / "cross_program.json"

SEED = 20260929
N_DRAWS = 1000
WINDOW_DAYS = 3
DAYS_PER_MONTH = 365.2425 / 12

PROGRAMS = ["bind9", "knot", "kresd", "nsd", "opendnssec", "pdns-auth", "pdns-rec", "unbound"]
CODEBASE = {p: p for p in PROGRAMS}
CODEBASE["pdns-auth"] = CODEBASE["pdns-rec"] = "pdns"
ROLES = {
    "signer/authoritative": ["bind9", "knot", "nsd", "opendnssec", "pdns-auth"],
    "validating resolver": ["bind9", "unbound", "kresd", "pdns-rec"],
}
KIND_COLUMNS = ["support-added", "default-changed", "limit-changed", "removal", "other", "not-recorded"]


# --------------------------------------------------------------------------- helpers
def utc(s: str) -> datetime:
    """ISO timestamp -> aware UTC datetime. A bare date is taken as 00:00 UTC."""
    if len(s) == 10:
        return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
    d = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc)


def iso(d: datetime | None) -> str | None:
    return None if d is None else d.strftime("%Y-%m-%dT%H:%M:%SZ")


def days_between(a: str, b: str) -> int:
    return (date.fromisoformat(b) - date.fromisoformat(a)).days


def median(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None


def iqr(xs):
    xs = sorted(x for x in xs if x is not None)
    if len(xs) < 2:
        return (xs[0], xs[0]) if xs else (None, None)
    q = statistics.quantiles(xs, n=4, method="inclusive")
    return (q[0], q[2])


def rfc_norm(x) -> str:
    return f"RFC {int(str(x).replace('RFC', '').strip())}"


def load_program(p: str) -> dict:
    return json.loads((TL / f"{p}.json").read_text())


def write_csv(name: str, rows: list[dict], fields: list[str] | None = None) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"cross_program_{name}.csv"
    if fields is None:
        fields = []
        for r in rows:
            for k in r:
                if k not in fields:
                    fields.append(k)
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: (json.dumps(v) if isinstance(v, (list, dict)) else v) for k, v in r.items()})


def save(result: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(result, indent=1, sort_keys=False, default=str) + "\n")


# --------------------------------------------------------------------------- normalisation
NORMALISATION = {
    "release_dates": "stable releases only (releases[].stable is true); calendar date = releases[].released; "
    "ordering and windows use releases[].released_full converted to a UTC instant",
    "default_changes": {
        "bind9": "row id = id; stable tag = first_stable_tag; date = releases[first_stable_tag].released (asserted equal to first_stable_date); "
        "is_default_change = value_changed; kind as recorded",
        "knot": "row id = knot[<index>]@<version>; stable tag = releases row whose version equals the row version; date = that release's released "
        "(asserted equal to row released); kind not recorded",
        "kresd": "as knot",
        "nsd": "row id = nsd[<index>]@<version>; stable tag = tag; date = releases[tag].released, except NSD_2_3_0_REL where the row's own "
        "released date and the release-commit instant in released_note are used (the tag is manufactured on a pre-release commit); kind not recorded",
        "opendnssec": "row id = opendnssec[<index>]@<version>; stable tag = first_stable_tag, or the row version when that field is absent "
        "(the version is itself a stable release); date = first_stable_released (asserted equal to the release row); kind not recorded",
        "pdns-auth": "row id = pdns-auth[<index>]@<version>; stable tag = stable_tag; date = releases[stable_tag].released, NOT the row released "
        "(which is the first pre-release date); is_default_change and kind as recorded",
        "pdns-rec": "row id = key; stable tag = tag; date = releases[tag].released (asserted equal to row released); where first_public_tag is "
        "present the public tag and first_public_released are reported beside and used for every timing comparison; "
        "is_default_change and kind as recorded",
        "unbound": "row id = unbound[<index>]@<version>; stable tag = tag; date = releases[tag].released (asserted equal to row released); "
        "is_default_change as recorded; kind not recorded",
    },
    "kind": "kind is recorded only for bind9, pdns-auth and pdns-rec; rows of the other five programs are reported under kind "
    "'not-recorded' rather than classified by keyword",
    "cve_fixes": {
        "bind9": "tag = first_stable_tag; date = fix_release_date; included when the tag is not null; rows with a null tag are excluded "
        "and counted by status",
        "pdns-auth": "tag = fix_tag; date = fix_released; always included; latency_days_public reported beside latency_days",
        "pdns-rec": "tag = fix_tag; date = fix_released; included when applicable is True; fix_changelog_released_text and "
        "latency_days_public reported beside",
        "others": "tag = fix_tag; date = fix_released; included when applicable is True and the tag is not null; "
        "applicable == 'disputed' reported as a separate group; latency_days used as recorded",
        "pre_release_fix_tags": "where fix_tag is not a stable release (five unbound rows and the twelve disputed rows) the recorded "
        "latency_days is kept as the headline figure, as the brief requires, and latency_days_stable (first_stable_tag date minus "
        "nvd_published) is reported beside it; question 8 timing always uses the stable release",
    },
    "dnssec_related": "used as recorded; bind9 rows carry no dnssec_related field and are reported as 'not classified'. "
    "knot rows DO carry dnssec_related (the brief said they did not); the recorded values are used, not keyword inference",
    "codebases": "pdns-auth and pdns-rec share pdns.git and are one codebase 'pdns' in question 8",
}


def build_release_index(data: dict[str, dict]):
    rel = {}
    for p, d in data.items():
        idx = {}
        for r in d["releases"]:
            idx[r["tag"]] = r
        rel[p] = idx
    return rel


def stable_releases(d: dict) -> list[dict]:
    """Stable releases, aliases (same commit, alias_of set) removed, sorted by UTC instant."""
    out = []
    for r in d["releases"]:
        if not r.get("stable"):
            continue
        if r.get("alias_of"):
            continue
        out.append(r)
    out.sort(key=lambda r: utc(r["released_full"]))
    return out


def norm_defaults(data, rel, suspects):
    rows, failures = [], []
    for p in PROGRAMS:
        d = data[p]
        by_version = {}
        for r in d["releases"]:
            by_version.setdefault(r["version"], []).append(r)
        for i, r in enumerate(d["default_changes"]):
            rec_date = None  # the date the row itself asserts for its stable release
            instant_override = None
            date_note = ""
            public_tag = public_date = None
            if p == "bind9":
                rid, tag, rec_date = r["id"], r.get("first_stable_tag"), r.get("first_stable_date")
                is_dc = bool(r.get("value_changed"))
                kind = r.get("kind")
            elif p in ("knot", "kresd"):
                rid = f"{p}[{i}]@{r['version']}"
                cands = [x for x in by_version.get(r["version"], []) if x["stable"]]
                tag = cands[0]["tag"] if len(cands) == 1 else None
                rec_date, is_dc, kind = r.get("released"), True, None
            elif p == "nsd":
                rid, tag, rec_date, is_dc, kind = f"nsd[{i}]@{r['version']}", r.get("tag"), r.get("released"), True, None
                if tag == "NSD_2_3_0_REL":
                    m = re.search(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)", r.get("released_note") or "")
                    instant_override = utc(m.group(1)) if m else utc(r["released"])
                    date_note = "row released (release commit dc1c5047) used; tag NSD_2_3_0_REL is manufactured on a 2005-01-10 commit"
            elif p == "opendnssec":
                rid = f"opendnssec[{i}]@{r['version']}"
                tag = r.get("first_stable_tag") or r["version"]
                rec_date = r.get("first_stable_released") or r.get("released")
                is_dc, kind = True, None
            elif p == "pdns-auth":
                rid, tag = f"pdns-auth[{i}]@{r['version']}", r.get("stable_tag")
                rec_date = None  # row released is the pre-release date by design
                is_dc, kind = bool(r.get("is_default_change")), r.get("kind")
                date_note = f"row released {r.get('released')} is the first pre-release ({r.get('tag')}); stable_tag date used"
            elif p == "pdns-rec":
                rid, tag, rec_date = r["key"], r.get("tag"), r.get("released")
                is_dc, kind = bool(r.get("is_default_change")), r.get("kind")
                public_tag, public_date = r.get("first_public_tag"), r.get("first_public_released")
            elif p == "unbound":
                rid, tag, rec_date = f"unbound[{i}]@{r['version']}", r.get("tag"), r.get("released")
                is_dc, kind = bool(r.get("is_default_change")), None
            R = rel[p].get(tag) if tag else None
            ok = R is not None and R.get("stable") is True
            if not ok:
                failures.append({"program": p, "row_id": rid, "tag": tag,
                                 "reason": "tag missing from releases[]" if R is None else "release is not stable"})
                continue
            sdate = R["released"]
            sinst = utc(R["released_full"])
            if instant_override is not None:
                sdate, sinst = r["released"], instant_override
            if rec_date and rec_date != sdate:
                suspects.append({"program": p, "row_id": rid, "field": "released/first_stable_date",
                                 "reason": f"row date {rec_date} differs from releases[{tag}].released {sdate}",
                                 "command": f"python3 -c \"import json;d=json.load(open('data/software/timelines/{p}.json'));"
                                            f"print([x['released'] for x in d['releases'] if x['tag']=='{tag}'])\""})
            pinst = None
            if public_tag:
                PR = rel[p].get(public_tag)
                assert PR is not None and PR["stable"], (p, rid, public_tag)
                assert PR["released"] == public_date, (p, rid, public_tag, public_date)
                pinst = utc(PR["released_full"])
            rows.append({
                "program": p, "codebase": CODEBASE[p], "row_index": i, "row_id": rid,
                "version": r.get("version") or (tag or ""), "mechanism": r.get("mechanism"),
                "kind": kind, "kind_col": kind if kind else "not-recorded",
                "is_default_change": is_dc,
                "stable_tag": tag, "stable_date": sdate, "stable_instant": iso(sinst),
                "public_tag": public_tag, "public_date": public_date, "public_instant": iso(pinst),
                "timing_tag": public_tag or tag, "timing_date": public_date or sdate,
                "timing_instant": iso(pinst or sinst),
                "opt_in": r.get("opt_in"), "applies_on_upgrade": r.get("applies_on_upgrade"),
                "rfcs": [rfc_norm(x) for x in (r.get("rfcs") or [])],
                "title": r.get("title") or r.get("description") or "",
                "before": r.get("before") or "", "after": r.get("after") or "",
                "date_note": date_note,
            })
    return rows, failures


def norm_cves(data, rel):
    rows = []
    for p in PROGRAMS:
        for i, r in enumerate(data[p]["cve_fixes"]):
            if p == "bind9":
                tag, fdate = r.get("first_stable_tag"), r.get("fix_release_date")
                applicable = None
                include = tag is not None
                reason = None if include else (r.get("status") or "no-fix-tag")
                group = "included" if include else "excluded"
            elif p == "pdns-auth":
                tag, fdate, applicable = r.get("fix_tag"), r.get("fix_released"), None
                include, reason, group = True, None, "included"
                assert tag is not None
            else:
                tag, fdate, applicable = r.get("fix_tag"), r.get("fix_released"), r.get("applicable")
                if applicable is True and tag is not None:
                    include, reason, group = True, None, "included"
                elif applicable == "disputed":
                    include, reason, group = False, "disputed", "disputed"
                elif applicable is True:
                    include, reason, group = False, "applicable-but-no-fix-tag", "excluded"
                else:
                    include, reason, group = False, "not-applicable", "excluded"
            R = rel[p].get(tag) if tag else None
            tag_stable = bool(R and R["stable"])
            stag = tag if tag_stable else r.get("first_stable_tag") if p != "bind9" else tag
            SR = rel[p].get(stag) if stag else None
            if SR is not None and not SR["stable"]:
                SR = None
            nvd = r.get("nvd_published")
            # latency_days_stable differs from the recorded latency only where the recorded fix tag is a
            # pre-release; rows whose latency was deliberately left null (tag artifacts) or that carry a
            # vendor release date stay as recorded
            if tag_stable or r.get("vendor_release") or r.get("latency_days") is None:
                lat_stable = r.get("latency_days")
            else:
                lat_stable = days_between(nvd, SR["released"]) if (SR and nvd) else None
            rows.append({
                "program": p, "codebase": CODEBASE[p], "row_index": i, "cve": r["cve"],
                "group": group, "include": include, "exclusion_reason": reason,
                "applicable": applicable, "status": r.get("status"),
                "fix_tag": tag, "fix_tag_is_stable": tag_stable if tag else None, "fix_date": fdate,
                "stable_tag": SR["tag"] if SR else None, "stable_date": SR["released"] if SR else None,
                "stable_instant": iso(utc(SR["released_full"])) if SR else None,
                "nvd_published": nvd, "latency_days": r.get("latency_days"),
                "latency_days_stable": lat_stable,
                "latency_days_public": r.get("latency_days_public"),
                "public_release_date": r.get("public_release_date"),
                "changelog_public_text": r.get("fix_changelog_released_text"),
                "vendor_release": (r.get("vendor_release") or {}).get("version") if r.get("vendor_release") else None,
                "dnssec_related": ("not classified" if p == "bind9" else r.get("dnssec_related")),
            })
    return rows


# --------------------------------------------------------------------------- question 1
MECH_SIGNING_ONLY = {"alg-ecdsa", "alg-rsa-sha2", "alg-gost", "ds-digest", "dnskey", "rrsig", "nsec3",
                     "nsec3-iterations", "cds-cdnskey", "other", "alg-eddsa"}


def q1(defaults):
    mechs = sorted({r["mechanism"] for r in defaults})
    cells = []
    for m in mechs:
        for p in PROGRAMS:
            for k in KIND_COLUMNS:
                rs = [r for r in defaults if r["mechanism"] == m and r["program"] == p and r["kind_col"] == k]
                if not rs:
                    continue
                rs.sort(key=lambda r: r["timing_instant"])
                f = rs[0]
                cells.append({"mechanism": m, "program": p, "kind": k, "first_stable_tag": f["stable_tag"],
                              "first_stable_date": f["stable_date"], "public_tag": f["public_tag"],
                              "public_date": f["public_date"], "row_id": f["row_id"],
                              "is_default_change": f["is_default_change"], "n_rows": len(rs),
                              "all_row_ids": [r["row_id"] for r in rs]})
    blanks = []
    for m in mechs:
        for p in PROGRAMS:
            if not any(c["mechanism"] == m and c["program"] == p for c in cells):
                blanks.append({"mechanism": m, "program": p,
                               "meaning": "no default_changes row for this mechanism in this program's timeline; "
                                          "this is not evidence that the program never supported it (support "
                                          "additions are recorded only where they came with a default change)"})
    kinds_present = {p: sorted({r["kind_col"] for r in defaults if r["program"] == p}) for p in PROGRAMS}
    write_csv("q1_mechanism_matrix", cells)
    return {
        "description": "Per mechanism x program x kind: the earliest stable release among that program's default_changes rows "
                       "with that mechanism and kind. kind is 'not-recorded' for knot, kresd, nsd, opendnssec and unbound "
                       "because their rows carry no kind field.",
        "cells": cells,
        "blank_cells": blanks,
        "blank_meaning": "blank = no row, not 'never supported'",
        "kinds_present_per_program": kinds_present,
        "mechanisms": mechs,
        "rows_used": sorted({rid for c in cells for rid in c["all_row_ids"]}),
    }


# --------------------------------------------------------------------------- chance baseline
def poisson_binomial_sf(ps: list[float], k: int) -> float:
    """P(X >= k) for X = sum of independent Bernoulli(p_i)."""
    dist = [1.0]
    for p in ps:
        nxt = [0.0] * (len(dist) + 1)
        for j, v in enumerate(dist):
            nxt[j] += v * (1 - p)
            nxt[j + 1] += v * p
        dist = nxt
    return float(sum(dist[k:])) if k < len(dist) else 0.0


def lead_baseline(contests: list[dict]) -> list[dict]:
    """contests: [{'label', 'programs': [...], 'leader': p}] with len(programs) >= 2.
    Returns per-program observed leads vs the 1/k chance expectation and P(leads >= observed)."""
    out = []
    progs = sorted({p for c in contests for p in c["programs"]})
    for p in progs:
        ps = [1 / len(c["programs"]) for c in contests if p in c["programs"]]
        obs = sum(1 for c in contests if c["leader"] == p)
        out.append({"program": p, "contests_entered": len(ps), "observed_leads": obs,
                    "expected_leads_by_chance": round(sum(ps), 3),
                    "p_at_least_observed": round(poisson_binomial_sf(ps, obs), 4),
                    "led": [c["label"] for c in contests if c["leader"] == p],
                    "called_leader": obs >= 3 and poisson_binomial_sf(ps, obs) < 0.05})
    return out


# --------------------------------------------------------------------------- question 2
def q2(defaults, checklist):
    pub = {r["rfc_id"]: r["publication_date"] for r in checklist["rfcs"]}
    rows = []
    not_in_checklist = []
    for r in defaults:
        for rfc in r["rfcs"]:
            if rfc not in pub:
                not_in_checklist.append({"program": r["program"], "row_id": r["row_id"], "rfc": rfc})
                continue
            lag_days = days_between(pub[rfc], r["timing_date"])
            rows.append({"rfc": rfc, "publication_date": pub[rfc], "program": r["program"], "row_id": r["row_id"],
                         "mechanism": r["mechanism"], "kind": r["kind_col"], "is_default_change": r["is_default_change"],
                         "stable_tag": r["stable_tag"], "stable_date": r["stable_date"],
                         "public_tag": r["public_tag"], "public_date": r["public_date"],
                         "timing_date": r["timing_date"], "lag_days": lag_days,
                         "lag_months": round(lag_days / DAYS_PER_MONTH, 1),
                         "lag_months_stable_tag": round(days_between(pub[rfc], r["stable_date"]) / DAYS_PER_MONTH, 1),
                         "negative_lag": lag_days < 0})
    rows.sort(key=lambda x: (int(x["rfc"].split()[1]), x["timing_date"], x["program"]))
    per_rfc = []
    contests = []
    for rfc in sorted({x["rfc"] for x in rows}, key=lambda s: int(s.split()[1])):
        rs = [x for x in rows if x["rfc"] == rfc]
        first = {}
        for x in sorted(rs, key=lambda x: (x["timing_date"], x["row_id"])):
            first.setdefault(x["program"], x)
        order = sorted(first.values(), key=lambda x: x["timing_date"])
        spread = (days_between(order[0]["timing_date"], order[-1]["timing_date"]) / DAYS_PER_MONTH) if len(order) > 1 else None
        per_rfc.append({"rfc": rfc, "publication_date": pub[rfc], "n_programs": len(order),
                        "order": [{"program": x["program"], "row_id": x["row_id"], "date": x["timing_date"],
                                   "lag_months": x["lag_months"],
                                   "role": "+".join(k for k, v in ROLES.items() if x["program"] in v)} for x in order],
                        "spread_months_first_to_last": round(spread, 1) if spread is not None else None,
                        "all_row_ids": [x["row_id"] for x in rs]})
        if len(order) >= 2:
            # ties on the same calendar day would share the lead; none occur, asserted
            assert order[0]["timing_date"] != order[1]["timing_date"], rfc
            contests.append({"label": rfc, "programs": [x["program"] for x in order], "leader": order[0]["program"],
                             "leader_row": order[0]["row_id"]})
    # contests won by the same row are one event, not several (nsd[2] cites RFC 4033, 4034 and 4035)
    merged = {}
    for c in contests:
        m = merged.setdefault(c["leader_row"], {"label": [], "programs": set(), "leader": c["leader"],
                                                "leader_row": c["leader_row"]})
        m["label"].append(c["label"])
        m["programs"] |= set(c["programs"])
    merged_contests = [{"label": "+".join(m["label"]), "programs": sorted(m["programs"]), "leader": m["leader"],
                        "leader_row": m["leader_row"]} for m in merged.values()]
    write_csv("q2_code_lag", rows)
    return {
        "description": "For each default_changes row naming a checklist RFC in rfcs: timing date (public release for pdns-rec rows "
                       "citing never-public tags; otherwise the first stable release) minus the RFC publication_date, in months "
                       "of 30.44 days. Per RFC, each program's earliest such row, in order, and the spread from first to last program.",
        "caveat": "Rows cite an RFC when the default change relates to it; the earliest row per program is the first DEFAULT change "
                  "citing the RFC, not necessarily first support. bind9 rows carry no rfcs field, so bind9 is absent from this "
                  "question; that is a gap in the timeline schema, not a finding.",
        "programs_without_rfcs_field": [p for p in PROGRAMS if not any(r["program"] == p and r["rfcs"] for r in defaults)],
        "rows": rows,
        "per_rfc": per_rfc,
        "rows_citing_rfcs_not_in_checklist": not_in_checklist,
        "first_to_ship_chance_baseline": {
            "method": "each RFC with k >= 2 programs is one contest; a program leads by chance with probability 1/k; "
                      "p = P(leads >= observed) under independent contests (Poisson-binomial). No program is called a "
                      "leader on fewer than three leads or p >= 0.05.",
            "per_program": lead_baseline(contests), "contests": contests,
            "per_program_same_row_merged": lead_baseline(merged_contests), "contests_same_row_merged": merged_contests,
            "note": "RFCs whose first program is decided by the same row are merged into one contest in the *_merged "
                    "variant; the merged variant is the one to quote. Programs of different roles are compared here because "
                    "the question is about the RFC, not the role; each order entry carries the program's role."},
    }


# --------------------------------------------------------------------------- question 3
# Topic assignment. A row enters a topic only by its mechanism and its before/after text:
# every assignment below is checked by the script (mechanism in the topic's set, evidence
# regex found in title+before+after). A sub-milestone is one comparable event; rows listed
# under "context" belong to the topic but are not a like-for-like milestone.
TOPICS = {
    "ecdsa-p256-default": {
        "title": "ECDSA P-256 as default signing algorithm",
        "mechanisms": {"alg-ecdsa"},
        "role": "signer/authoritative",
        "subs": {
            "default-signing-alg-ecdsap256": {
                "regex": r"ECDSAP256|ecdsa256|algorithm=13",
                "rows": {"bind9": ["d15-dnssec-policy-default-ecdsap256"], "knot": ["knot[2]@2.1.0"],
                         "pdns-auth": ["pdns-auth[7]@4.0.0", "pdns-auth[8]@4.0.0"]}},
        },
        "not_assigned": {
            "pdns-auth[5]@4.0.0": "alg-ecdsa, but its after text names no ECDSA algorithm (default-ksk-algorithms emptied, intermediate state)",
            "pdns-auth[6]@4.0.0": "after text calls it an intermediate pre-release state, replaced by pdns-auth[8] before auth-4.0.0 (same stable date, so no timing effect)",
            "unbound[9]@1.4.17": "alg-ecdsa, but it enables ECDSA validation, not a signing default",
        },
        "no_row": {"opendnssec": "no row; opendnssec[5] after text says the example policy stays RSASHA256 through 2.1.14",
                   "nsd": "does not sign"},
    },
    "nsec3-iterations-rfc9276": {
        "title": "NSEC3 iterations capped / default 0 (RFC 9276)",
        "mechanisms": {"nsec3-iterations", "nsec3"},
        "role": "both",
        "subs": {
            "signer-default-iterations-0": {
                "regex": r"iterations 0|nsec3iter = 0U|schema default 0|1 0 0 -",
                "rows": {"bind9": ["d18-nsec3param-default-0-0", "d21-signzone-nsec3-iterations-0"],
                         "knot": ["knot[14]@3.2.0"], "pdns-auth": ["pdns-auth[11]@4.6.0"]}},
            "signer-default-salt-empty": {
                "regex": r"salt-length 0|schema default 0; empty salt|1 0 0 -",
                "rows": {"bind9": ["d18-nsec3param-default-0-0"], "knot": ["knot[18]@3.5.0"],
                         "pdns-auth": ["pdns-auth[11]@4.6.0"]}},
            "iteration-cap-at-or-below-150": {
                "regex": r"\b150\b|=100\b",
                "rows": {"bind9": ["l01-nsec3-max-iterations-150"], "kresd": ["kresd[9]@5.3.1"],
                         "pdns-auth": ["pdns-auth[10]@4.5.0"], "pdns-rec": ["nsec3-max-iterations-150"],
                         "unbound": ["unbound[19]@1.13.2"]}},
            "iteration-cap-at-or-below-50": {
                "regex": r"\b50\b",
                "rows": {"bind9": ["l02-nsec3-max-iterations-50"], "kresd": ["kresd[12]@5.7.1", "kresd[15]@6.0.6"],
                         "pdns-rec": ["nsec3-max-iterations-50"]}},
            "context": {
                "regex": r"iteration|nsec3param",
                "rows": {"bind9": ["d03-signzone-nsec3-iterations-100-to-10", "d17-nsec3param-default-in-policy"],
                         "knot": ["knot[19]@3.6.0"], "pdns-auth": ["pdns-auth[3]@3.4.0", "pdns-auth[4]@3.4.7"],
                         "pdns-rec": ["nsec3-max-iterations-2500"], "unbound": ["unbound[1]@0.5"]}},
        },
        "not_assigned": {
            "unbound[23]@1.19.1": "nsec3-iterations, but it caps NSEC3 hash computations per message, not the iteration count",
            "pdns-auth[1]@3.3": "nsec3, but the change is the opt-out flag of set-nsec3 defaults (iterations stay 1)",
            "knot[4]@2.3.0": "nsec3, re-salting schedule; iterations default 10 is the pre-existing schema value",
        },
        "no_row": {"opendnssec": "no row; opendnssec gaps say the shipped policy kept Iterations 5 from 1.0a1 to 2.1.14",
                   "nsd": "no iteration cap in the serving code (nsd gaps)"},
    },
    "validation-default-on": {
        "title": "Validation on by default",
        "mechanisms": {"validation", "trust-anchor-5011"},
        "role": "validating resolver",
        "subs": {
            "validator-enabled-needs-configured-anchor": {
                "regex": r"dnssec-validation yes|validator iterator",
                "rows": {"bind9": ["d01-validation-default-yes"], "unbound": ["unbound[0]@0.5"]}},
            "validates-out-of-the-box": {
                "regex": r"dnssec-validation auto|keyfile_default=root.keys|dnssec=process:",
                "rows": {"bind9": ["d07-validation-auto-default"], "kresd": ["kresd[6]@4.0.0"],
                         "pdns-rec": ["dnssec-default-process"]},
                "note": "pdns-rec 'process' validates only when the client sets AD or DO; it is the closest the Recursor "
                        "comes to validation by default"},
        },
        "not_assigned": {
            "dnssec-default-process-no-validate": "validation, but process-no-validate never validates",
            "dnssec-setting-introduced": "is_default_change false (support-added)",
        },
        "no_row": {"unbound": "no row making validation work without a configured anchor; unbound[0] needs a trust anchor"},
    },
    "root-trust-anchor": {
        "title": "Built-in root trust anchor and RFC 5011 rollover",
        "mechanisms": {"trust-anchor-5011", "trust-anchor", "validation"},
        "role": "validating resolver",
        "subs": {
            "builtin-root-anchor-available": {
                "regex": r"built-in root|root.keys",
                "rows": {"bind9": ["d04-root-trust-anchor-builtin"], "kresd": ["kresd[6]@4.0.0"]}},
            "ksk2017-20326-added": {
                "regex": r"20326|upcoming root KSK",
                "rows": {"bind9": ["d05-builtin-root-ksk-2017"], "unbound": ["unbound[12]@1.6.1"],
                         "pdns-rec": ["root-ds-2017-added"]}},
            "ksk2010-19036-removed": {
                "regex": r"19036",
                "rows": {"unbound": ["unbound[18]@1.11.0"], "pdns-rec": ["root-ds-19036-removed"]}},
            "ksk2024-38696-added": {
                "regex": r"38696",
                "rows": {"bind9": ["d24-bindkeys-root-2025-ds"], "kresd": ["kresd[14]@5.7.4", "kresd[17]@6.0.8"],
                         "unbound": ["unbound[24]@1.21.0"], "pdns-rec": ["root-ds-38696"]}},
            "rfc8145-key-tag-signalling-on": {
                "regex": r"_ta-",
                "rows": {"kresd": ["kresd[1]@1.5.0"], "unbound": ["unbound[14]@1.6.7"]}},
            "rfc8509-root-key-sentinel-on": {
                "regex": r"sentinel",
                "rows": {"kresd": ["kresd[3]@2.0.0"], "unbound": ["unbound[15]@1.7.1"]}},
            "context": {
                "regex": r"RFC 5011|5011",
                "rows": {"bind9": ["d07-validation-auto-default"], "kresd": ["kresd[4]@2.0.0"]}},
        },
        "not_assigned": {
            "d23-bindkeys-revoked-key-removed": "value_changed false: not a default change",
            "trust-anchor-ta-nta-management": "is_default_change false (support-added)",
        },
        "no_row": {"pdns-rec": "no RFC 5011 rollover at any tag (pdns-rec gaps); only static built-in DS changes",
                   "kresd": "no row for KSK-2017 being added or KSK-2010 removed"},
    },
    "sha1-deprecation": {
        "title": "SHA-1 / RSASHA1 deprecation",
        "mechanisms": {"ds-digest", "alg-rsa-sha2", "dnskey", "validation", "other"},
        "role": "both",
        "subs": {
            "signer-default-alg-moves-off-sha1": {
                "regex": r"RSASHA1|algorithm=5",
                "rows": {"opendnssec": ["opendnssec[5]@1.2.0b1"], "pdns-auth": ["pdns-auth[0]@3.2"],
                         "bind9": ["d06-keygen-no-default-alg"]},
                "note": "bind9 d06 removes the RSASHA1 default instead of replacing it"},
            "sha1-ds-no-longer-generated": {
                "regex": r"SHA-1",
                "rows": {"opendnssec": ["opendnssec[13]@2.1.0"], "knot": ["knot[11]@2.8.0"],
                         "bind9": ["d13-ds-cds-sha1-dropped", "d20-dnssec-cds-sha2-only"]}},
            "crypto-policy-sha1-refusal-handled": {
                "regex": r"SHA-1|crypto|policy",
                "rows": {"knot": ["knot[12]@3.0.2"], "unbound": ["unbound[21]@1.16.1"],
                         "pdns-rec": ["dnssec-disabled-algorithms-auto"]}},
            "context": {
                "regex": r"SHA-1",
                "rows": {"kresd": ["kresd[10]@5.5.0"]}},
        },
        "not_assigned": {
            "unbound[13]@1.6.2": "ds-digest, but it tolerates DS digest downgrade: the opposite direction",
            "d10-dsa-removed": "DSA removal, not RSASHA1 or SHA-1 DS",
            "knot[7]@2.6.0": "DSA removal", "unbound[17]@1.10.0": "DSA removal",
        },
        "no_row": {},
    },
    "cds-cdnskey-publication": {
        "title": "CDS/CDNSKEY publication",
        "mechanisms": {"cds-cdnskey"},
        "role": "signer/authoritative",
        "subs": {
            "cds-publication-default": {
                "regex": r"CDS/CDNSKEY",
                "rows": {"knot": ["knot[10]@2.8.0"]}},
        },
        "not_assigned": {"d22-cdns-cdnskey-options": "value_changed false: defaults equal the prior behaviour"},
        "no_row": {"bind9": "publication start (9.16.0 keymgr) not located (bind9 gaps); only d22 exists",
                   "pdns-auth": "no default_changes row; Arc A records publish support in 4.0.0",
                   "opendnssec": "no row"},
    },
}


def topic_memberships(defaults):
    by_id = {(r["program"], r["row_id"]): r for r in defaults}
    out = []
    for t, T in TOPICS.items():
        for sub, S in T["subs"].items():
            for p, ids in S["rows"].items():
                for rid in ids:
                    r = by_id.get((p, rid))
                    assert r is not None, (t, sub, p, rid)
                    assert r["is_default_change"], (t, sub, p, rid, "not a default change")
                    mech_ok = r["mechanism"] in T["mechanisms"]
                    text = " ".join([r["title"], r["before"], r["after"]])
                    m = re.search(S["regex"], text)
                    assert mech_ok, (t, sub, p, rid, r["mechanism"])
                    assert m, (t, sub, p, rid, S["regex"])
                    out.append({"topic": t, "sub": sub, "program": p, "codebase": r["codebase"], "row_id": rid,
                                "mechanism": r["mechanism"], "evidence": m.group(0),
                                "stable_tag": r["stable_tag"], "stable_date": r["stable_date"],
                                "public_tag": r["public_tag"], "public_date": r["public_date"],
                                "timing_date": r["timing_date"], "timing_instant": r["timing_instant"],
                                "opt_in": r["opt_in"], "applies_on_upgrade": r["applies_on_upgrade"],
                                "before": r["before"][:160], "after": r["after"][:160]})
        for rid in T["not_assigned"]:
            assert any(k[1] == rid for k in by_id), (t, rid)
    return out


def q3(defaults):
    mem = topic_memberships(defaults)
    tables = []
    for t, T in TOPICS.items():
        per_prog = []
        for p in PROGRAMS:
            rs = sorted([m for m in mem if m["topic"] == t and m["program"] == p], key=lambda m: m["timing_instant"])
            if not rs and p not in T["no_row"]:
                continue
            per_prog.append({"program": p,
                             "first_date": rs[0]["timing_date"] if rs else None,
                             "first_row": rs[0]["row_id"] if rs else None,
                             "rows": [{"sub": m["sub"], "row_id": m["row_id"], "date": m["timing_date"],
                                       "stable_tag": m["stable_tag"], "stable_date": m["stable_date"],
                                       "public_tag": m["public_tag"], "public_date": m["public_date"],
                                       "opt_in": m["opt_in"]} for m in rs],
                             "no_row_note": T["no_row"].get(p)})
        subs = []
        for sub, S in T["subs"].items():
            first = {}
            for m in sorted([m for m in mem if m["topic"] == t and m["sub"] == sub], key=lambda m: m["timing_instant"]):
                first.setdefault(m["program"], m)
            subs.append({"sub": sub, "is_milestone": sub != "context", "note": S.get("note"),
                         "per_program": [{"program": p, "date": m["timing_date"], "row_id": m["row_id"],
                                          "stable_tag": m["stable_tag"], "public_tag": m["public_tag"]}
                                         for p, m in sorted(first.items(), key=lambda kv: kv[1]["timing_instant"])]})
        tables.append({"topic": t, "title": T["title"], "role": T["role"], "per_program": per_prog, "sub_milestones": subs,
                       "rows_considered_not_assigned": T["not_assigned"]})
    write_csv("q3_topics", mem)
    return {"description": "Default changes grouped into six topics. Assignment is by mechanism plus an evidence regex over the "
                           "row's title/before/after text; both are asserted by the script and listed per row "
                           "(cross_program_q3_topics.csv, field 'evidence'). Timing uses the first stable release, or the "
                           "public release for pdns-rec rows citing never-public tags.",
            "assignment": {t: {"mechanisms": sorted(T["mechanisms"]),
                               "subs": {s: {"regex": S["regex"], "rows": S["rows"]} for s, S in T["subs"].items()},
                               "not_assigned": T["not_assigned"]} for t, T in TOPICS.items()},
            "tables": tables, "memberships": mem}


# --------------------------------------------------------------------------- question 4
def q4(defaults):
    mem = topic_memberships(defaults)
    subs_out, contests_sub, contests_topic, topics_out, ties_sub = [], [], [], [], []
    for t, T in TOPICS.items():
        for sub in T["subs"]:
            if sub == "context":
                continue
            first = {}
            for m in sorted([m for m in mem if m["topic"] == t and m["sub"] == sub], key=lambda m: m["timing_instant"]):
                first.setdefault(m["program"], m)
            order = sorted(first.values(), key=lambda m: m["timing_instant"])
            rec = {"topic": t, "sub": sub, "k": len(order),
                   "order": [{"program": m["program"], "row_id": m["row_id"], "date": m["timing_date"]} for m in order]}
            if len(order) >= 2:
                lead = order[0]
                gaps = [days_between(lead["timing_date"], m["timing_date"]) for m in order[1:]]
                rec.update({"leader": lead["program"], "leader_row": lead["row_id"], "leader_date": lead["timing_date"],
                            "gaps_days_to_rest": {m["program"]: g for m, g in zip(order[1:], gaps)},
                            "median_gap_days": median(gaps), "median_gap_months": round(median(gaps) / DAYS_PER_MONTH, 1),
                            "same_day_tie": days_between(order[0]["timing_date"], order[1]["timing_date"]) == 0})
                if rec["same_day_tie"]:
                    tied = [m["program"] for m in order if m["timing_date"] == lead["timing_date"]]
                    rec["leader"] = "tie: " + "+".join(tied)
                    rec["tie_note"] = ("first programs shipped on the same calendar day; the UTC order within the day is "
                                       "not a lead, so this contest is left out of the chance baseline")
                    ties_sub.append(f"{t}/{sub}")
                else:
                    contests_sub.append({"label": f"{t}/{sub}", "programs": [m["program"] for m in order],
                                         "leader": lead["program"]})
            else:
                rec["leader"] = None
                rec["why_no_leader"] = "fewer than two programs have a row"
            subs_out.append(rec)
        # topic level: each program's earliest assigned row in the topic, context rows included
        first = {}
        for m in sorted([m for m in mem if m["topic"] == t], key=lambda m: m["timing_instant"]):
            first.setdefault(m["program"], m)
        order = sorted(first.values(), key=lambda m: m["timing_instant"])
        rec = {"topic": t, "k": len(order),
               "order": [{"program": m["program"], "row_id": m["row_id"], "sub": m["sub"], "date": m["timing_date"]}
                         for m in order]}
        if len(order) >= 2:
            gaps = [days_between(order[0]["timing_date"], m["timing_date"]) for m in order[1:]]
            rec.update({"leader": order[0]["program"], "leader_row": order[0]["row_id"],
                        "median_gap_days": median(gaps), "median_gap_months": round(median(gaps) / DAYS_PER_MONTH, 1)})
            contests_topic.append({"label": t, "programs": [m["program"] for m in order], "leader": order[0]["program"]})
        topics_out.append(rec)
    base_sub = lead_baseline(contests_sub)
    base_topic = lead_baseline(contests_topic)
    csv_rows = []
    for r in subs_out:
        for i, o in enumerate(r["order"]):
            csv_rows.append({"level": "sub-milestone", "topic": r["topic"], "sub": r["sub"], "rank": i + 1,
                             "program": o["program"], "row_id": o["row_id"], "date": o["date"],
                             "gap_days_from_leader": days_between(r["order"][0]["date"], o["date"]),
                             "median_gap_days": r.get("median_gap_days")})
    for r in topics_out:
        for i, o in enumerate(r["order"]):
            csv_rows.append({"level": "topic", "topic": r["topic"], "sub": o["sub"], "rank": i + 1,
                             "program": o["program"], "row_id": o["row_id"], "date": o["date"],
                             "gap_days_from_leader": days_between(r["order"][0]["date"], o["date"]),
                             "median_gap_days": r.get("median_gap_days")})
    write_csv("q4_leader_follower", csv_rows)
    leaders = [b["program"] for b in base_sub if b["called_leader"]]
    return {"description": "Leader = program whose first row in the sub-milestone (or topic) has the earliest timing instant; "
                           "median gap = median over the other programs of (their date - leader date) in days. Chance baseline: "
                           "a program in a contest of k programs leads with probability 1/k; p = P(leads >= observed), "
                           "Poisson-binomial over independent contests. A program is called a leader only with >= 3 leads "
                           "and p < 0.05.",
            "sub_milestones": subs_out, "topics": topics_out,
            "baseline_sub_milestones": base_sub, "baseline_topics": base_topic,
            "programs_called_leader": leaders,
            "tied_sub_milestones_left_out_of_baseline": ties_sub,
            "caveat": "Contests mix programs of different roles only where the sub-milestone is role-independent in "
                      "substance (NSEC3 caps apply to validators and pdns-auth serving); sub-milestones are not independent "
                      "(bind9 d18 wins two), so the p-values are optimistic."}





# --------------------------------------------------------------------------- question 5
BROAD_MECHANISMS = {"other", "validation"}  # too broad for a later row of the same label to mean supersession

def q5(defaults, checklist, data):
    pub = {r["rfc_id"]: r["publication_date"] for r in checklist["rfcs"]}
    pairs = [(r["rfc_id"], s) for r in checklist["rfcs"] for s in (r.get("obsoleted_by") or [])]
    out_pairs, csv_rows = [], []
    for pred, succ in pairs:
        succ_pub = pub.get(succ)
        pred_rows = [r for r in defaults if pred in r["rfcs"]]
        succ_rows = [r for r in defaults if succ in r["rfcs"]]
        progs = sorted({r["program"] for r in pred_rows + succ_rows})
        per_prog = []
        for p in progs:
            pr = sorted([r for r in pred_rows if r["program"] == p], key=lambda r: r["timing_instant"])
            sr = sorted([r for r in succ_rows if r["program"] == p], key=lambda r: r["timing_instant"])
            stable = stable_releases(data[p])
            after_succ = [x for x in stable if succ_pub and x["released"] >= succ_pub]
            items = []
            for r in pr:
                later = [x for x in defaults if x["program"] == p and x["mechanism"] == r["mechanism"]
                         and x["mechanism"] not in BROAD_MECHANISMS and x["timing_instant"] > r["timing_instant"]]
                intermediate = bool(re.search(r"intermediate", r["after"]))
                still = not later and not intermediate
                items.append({"row_id": r["row_id"], "mechanism": r["mechanism"], "date": r["timing_date"],
                              "stable_tag": r["stable_tag"], "after": r["after"][:140],
                              "later_rows_same_mechanism": [x["row_id"] for x in later],
                              "still_current_default": still,
                              "intermediate_pre_release_state": intermediate,
                              "shipped_after_successor_publication": bool(still and after_succ),
                              "releases_after_successor": len(after_succ),
                              "latest_stable_release": (stable[-1]["tag"], stable[-1]["released"])})
                csv_rows.append({"predecessor": pred, "successor": succ, "successor_published": succ_pub, "program": p,
                                 **{k: v for k, v in items[-1].items() if k != "after"}})
            per_prog.append({"program": p, "first_predecessor_row": pr[0]["row_id"] if pr else None,
                             "first_predecessor_date": pr[0]["timing_date"] if pr else None,
                             "first_successor_row": sr[0]["row_id"] if sr else None,
                             "first_successor_date": sr[0]["timing_date"] if sr else None,
                             "successor_minus_predecessor_months": (round(days_between(pr[0]["timing_date"], sr[0]["timing_date"]) / DAYS_PER_MONTH, 1)
                                                                    if pr and sr else None),
                             "predecessor_rows": items})
        out_pairs.append({"predecessor": pred, "predecessor_published": pub.get(pred), "successor": succ,
                          "successor_published": succ_pub, "n_rows_predecessor": len(pred_rows),
                          "n_rows_successor": len(succ_rows), "per_program": per_prog,
                          "successor_shipping": ("not determinable: no timeline row cites " + succ) if not succ_rows else None})
    write_csv("q5_obsolescence", csv_rows)
    return {"description": "Pairs from the checklist obsoleted_by field. For each program with rows citing the predecessor: its "
                           "first predecessor row, its first successor row, and for each predecessor row whether a later row of "
                           "the same mechanism exists (mechanisms 'other' and 'validation' are too broad to count as supersession; for those the "
                           "rows were read and none names the same setting). A row with no later "
                           "same-mechanism row is taken as still the current default; 'shipped_after_successor_publication' is true "
                           "when such a row's program has stable releases dated on or after the successor's publication.",
            "obsolescence_pairs_in_checklist": [{"predecessor": a, "successor": b} for a, b in pairs],
            "pairs": out_pairs,
            "scope_note": "Only one obsoleted_by pair exists in the checklist (RFC 8624 -> RFC 9904, 2025-11-01). RFC 9904 moves "
                          "the algorithm requirements to IANA registries; a program still shipping an RFC 8624-motivated default is "
                          "not in conflict with RFC 9904 by that fact alone. RFC 9905 and RFC 9906 update, not obsolete, "
                          "and are out of this question's scope. Deployment is Phase 7."}


# --------------------------------------------------------------------------- question 6
def q6(cves):
    per_prog, csv_rows = [], []
    for p in PROGRAMS:
        rs = [r for r in cves if r["program"] == p]
        inc = [r for r in rs if r["include"]]
        lat = [r["latency_days"] for r in inc if r["latency_days"] is not None]
        lat_pub = [r["latency_days_public"] for r in inc if r["latency_days_public"] is not None]
        lat_st = [r["latency_days_stable"] for r in inc if r["latency_days_stable"] is not None]
        excl = Counter(r["exclusion_reason"] for r in rs if r["group"] == "excluded")
        disp = [r for r in rs if r["group"] == "disputed"]
        rec = {"program": p, "n_rows": len(rs), "n_included": len(inc),
               "n_included_without_latency": sum(1 for r in inc if r["latency_days"] is None),
               "included_without_latency": [r["cve"] for r in inc if r["latency_days"] is None],
               "n_excluded_by_reason": dict(excl), "n_disputed": len(disp),
               "latency_days_median": median(lat), "latency_days_iqr": iqr(lat), "n_latency": len(lat),
               "n_negative_latency": sum(1 for x in lat if x < 0),
               "latency_days_stable_median": median(lat_st), "latency_days_stable_iqr": iqr(lat_st),
               "n_pre_release_fix_tags": sum(1 for r in inc if r["fix_tag_is_stable"] is False),
               "pre_release_fix_tag_rows": [f"{r['cve']} {r['fix_tag']} -> {r['stable_tag']}" for r in inc if r["fix_tag_is_stable"] is False],
               "latency_days_public_median": median(lat_pub), "latency_days_public_iqr": iqr(lat_pub),
               "n_latency_public": len(lat_pub)}
        if p == "bind9":
            rec["dnssec_subset"] = "not classified (bind9 rows carry no dnssec_related field)"
        else:
            sub = [r for r in inc if r["dnssec_related"] is True]
            sl = [r["latency_days"] for r in sub if r["latency_days"] is not None]
            unc = [r for r in inc if r["dnssec_related"] not in (True, False)]
            rec["dnssec_subset"] = {"n": len(sub), "median": median(sl), "iqr": iqr(sl), "cves": [r["cve"] for r in sub],
                                    "n_unclassified": len(unc)}
        if disp:
            dl = [r["latency_days"] for r in disp if r["latency_days"] is not None]
            rec["disputed_group"] = {"n": len(disp), "median": median(dl), "iqr": iqr(dl), "cves": [r["cve"] for r in disp]}
        if p == "pdns-rec":
            rec["changelog_public_text_present"] = sum(1 for r in inc if r["changelog_public_text"])
        rec["rows_used"] = [r["cve"] for r in inc]
        per_prog.append(rec)
    for r in cves:
        csv_rows.append({k: r[k] for k in ["program", "cve", "group", "exclusion_reason", "fix_tag", "fix_tag_is_stable",
                                           "fix_date", "stable_tag", "stable_date", "nvd_published", "latency_days",
                                           "latency_days_stable", "latency_days_public", "public_release_date",
                                           "changelog_public_text", "dnssec_related"]})
    write_csv("q6_cve_latency", csv_rows)
    pooled = [r["latency_days"] for r in cves if r["include"] and r["latency_days"] is not None]
    return {"description": "Per program: rows included under the brief's rules, excluded rows by reason, median and IQR "
                           "(inclusive quartiles) of latency_days as recorded (fix tag date minus nvd_published; negative = "
                           "fixed before NVD publication), of latency_days_stable (first stable release, differs only where "
                           "the recorded fix tag is a pre-release) and of latency_days_public where present.",
            "per_program": per_prog,
            "pooled_all_programs": {"n": len(pooled), "median": median(pooled), "iqr": iqr(pooled)},
            "caveat": "NVD publication is often long after the vendor advisory for old CVEs (knot CVE-2014-0486 was published "
                      "3.5 years after the fix), so latency medians describe NVD lag as much as vendor speed."}


# --------------------------------------------------------------------------- question 7
def q7(data):
    per_year, per_prog, csv_rows = {}, [], []
    for p in PROGRAMS:
        st = stable_releases(data[p])
        years = Counter(r["released"][:4] for r in st)
        per_year[p] = dict(sorted(years.items()))
        inst = [utc(r["released_full"]) for r in st]
        gaps = [(b - a).total_seconds() / 86400 for a, b in zip(inst, inst[1:])]
        dec = defaultdict(list)
        for r, g in zip(st[1:], gaps):
            dec[r["released"][:3] + "0s"].append(g)
        per_prog.append({"program": p, "n_stable": len(st), "first": st[0]["tag"] + " " + st[0]["released"],
                         "last": st[-1]["tag"] + " " + st[-1]["released"],
                         "median_days_between": round(median(gaps), 2),
                         "n_same_day_pairs": sum(1 for g in gaps if g < 1),
                         "per_decade_median_days": {k: round(median(v), 2) for k, v in sorted(dec.items())},
                         "per_decade_n_intervals": {k: len(v) for k, v in sorted(dec.items())},
                         "aliases_dropped": [r["tag"] for r in data[p]["releases"] if r.get("stable") and r.get("alias_of")]})
        for y, n in sorted(years.items()):
            csv_rows.append({"program": p, "year": y, "stable_releases": n})
    write_csv("q7_release_cadence", csv_rows)
    return {"description": "Stable releases (stable true, alias tags of the same commit dropped) per calendar year of "
                           "releases[].released, and the median interval between consecutive stable releases ordered by UTC "
                           "instant, overall and by the decade of the later release. Parallel maintenance branches make "
                           "same-day releases common (bind9 ships several branches at once), which pulls the medians down.",
            "per_year": per_year, "per_program": per_prog,
            "pdns_rec_never_public": "rec-4.5.0, rec-4.5.3 and rec-5.0.0 are stable tags that were never released publicly; "
                                     "they are counted here as tags (the timeline marks them stable), which adds three to "
                                     "pdns-rec's 2021 and 2023 counts",
            "not_compared": "total_entries is not compared across programs (bind9 de-duplicates across branches, pdns-auth "
                            "counts prose paragraphs)."}








# --------------------------------------------------------------------------- question 8
MONTHS = {m: i + 1 for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august",
                                          "september", "october", "november", "december"])}


def parse_changelog_date(text: str | None) -> datetime | None:
    """'the 13th of February 2024.' -> 2024-02-13 00:00 UTC; None when the text has no such date."""
    if not text:
        return None
    m = re.search(r"(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?([A-Za-z]+),?\s+(\d{4})", text)
    if not m or m.group(2).lower() not in MONTHS:
        return None
    return datetime(int(m.group(3)), MONTHS[m.group(2).lower()], int(m.group(1)), tzinfo=timezone.utc)


def q8_events(defaults, cves, pdns_rec_public=False):
    ev = set()
    src = defaultdict(set)
    for r in cves:
        if not r["include"]:
            continue
        t = None
        if pdns_rec_public and r["program"] == "pdns-rec":
            t = parse_changelog_date(r["changelog_public_text"])
        if t is None and r["vendor_release"] and r["fix_date"]:
            t = utc(r["fix_date"])  # vendor point release whose clone tag is a bare re-tag (unbound CVE-2017-15105)
        if t is None and r["stable_instant"]:
            t = utc(r["stable_instant"])
        if t is None:
            continue
        key = (r["codebase"], "cve:" + r["cve"], t)
        ev.add(key)
        src[key].add(f"{r['program']}:{r['cve']}@{r['stable_tag']}")
    for m in topic_memberships(defaults):
        key = (m["codebase"], "topic:" + m["topic"], utc(m["timing_instant"]))
        ev.add(key)
        src[key].add(f"{m['program']}:{m['row_id']}@{m['public_tag'] or m['stable_tag']}")
    return sorted(ev), {k: sorted(v) for k, v in src.items()}


def coordinated_pairs(events, window=WINDOW_DAYS):
    """events: iterable of (codebase, label, instant). Returns {(label, cb_a, cb_b): (t_a, t_b)} for pairs of
    DIFFERENT codebases with the same label within the window (closest pair kept)."""
    by_label = defaultdict(list)
    for cb, lab, t in events:
        by_label[lab].append((cb, t))
    out = {}
    lim = window * 86400
    for lab, xs in by_label.items():
        if len({cb for cb, _ in xs}) < 2:
            continue
        for i in range(len(xs)):
            for j in range(i + 1, len(xs)):
                (ca, ta), (cb_, tb) = xs[i], xs[j]
                if ca == cb_:
                    continue
                dt = abs((ta - tb).total_seconds())
                if dt <= lim:
                    a, b = sorted([(ca, ta), (cb_, tb)])
                    k = (lab, a[0], b[0])
                    if k not in out or dt < abs((out[k][0] - out[k][1]).total_seconds()):
                        out[k] = (a[1], b[1])
    return out


def pair_stats(pairs) -> dict:
    """Four statistics of one set of coordinated pairs."""
    rel_pairs = {(a, pairs[k][0], b, pairs[k][1]) for k in pairs for a, b in [(k[1], k[2])]}
    return {"label_pairs": len(pairs),
            "label_pairs_cve": sum(1 for k in pairs if k[0].startswith("cve:")),
            "label_pairs_topic": sum(1 for k in pairs if k[0].startswith("topic:")),
            "distinct_release_pairs": len(rel_pairs)}


def circular_null(events, spans):
    rng = random.Random(SEED)
    cbs = sorted(spans)
    draws = []
    for _ in range(N_DRAWS):
        off = {cb: rng.uniform(0, (spans[cb][1] - spans[cb][0]).total_seconds()) for cb in cbs}
        shifted = []
        for cb, lab, t in events:
            lo, hi = spans[cb]
            L = (hi - lo).total_seconds()
            x = ((t - lo).total_seconds() + off[cb]) % L if L > 0 else 0.0
            shifted.append((cb, lab, lo + timedelta(seconds=x)))
        draws.append(pair_stats(coordinated_pairs(shifted)))
    return draws


def summarise_null(o, null):
    lt = sum(1 for x in null if x < o)
    eq = sum(1 for x in null if x == o)
    ge = sum(1 for x in null if x >= o)
    p = (ge + 1) / (len(null) + 1)
    return {"observed": o, "null_mean": round(statistics.fmean(null), 3), "null_median": median(null),
            "null_p95": sorted(null)[int(0.95 * len(null)) - 1], "null_max": max(null),
            "percentile_midrank": round(100 * (lt + 0.5 * eq) / len(null), 1),
            "p_value_ge": round(p, 4), "distinguishable_from_null": p < 0.05}


def codebase_spans(data):
    spans = {}
    for p in PROGRAMS:
        st = stable_releases(data[p])
        lo, hi = utc(st[0]["released_full"]), utc(st[-1]["released_full"])
        cb = CODEBASE[p]
        spans[cb] = (min(spans[cb][0], lo), max(spans[cb][1], hi)) if cb in spans else (lo, hi)
    return spans


def q8(defaults, cves, data):
    spans = codebase_spans(data)
    variants = {}
    listing_main = None
    for name, pub in [("tag_dates", False), ("pdns_rec_changelog_public_dates", True)]:
        events, src = q8_events(defaults, cves, pdns_rec_public=pub)
        obs = coordinated_pairs(events)
        ostats = pair_stats(obs)
        null = circular_null(events, spans)
        listing = []
        for (lab, a, b), (ta, tb) in sorted(obs.items(), key=lambda kv: (kv[1][0], kv[0])):
            listing.append({"variant": name, "label": lab, "codebase_a": a, "date_a": iso(ta), "codebase_b": b,
                            "date_b": iso(tb), "gap_days": round(abs((ta - tb).total_seconds()) / 86400, 2),
                            "rows_a": src[(a, lab, ta)], "rows_b": src[(b, lab, tb)]})
        multi = defaultdict(set)
        for cb, lab, t in events:
            multi[lab].add(cb)
        variants[name] = {
            "n_events": len(events),
            "labels_shared_by_2plus_codebases": {lab: sorted(v) for lab, v in sorted(multi.items()) if len(v) > 1},
            "observed_pairs": listing,
            "tests": {k: summarise_null(ostats[k], [d[k] for d in null]) for k in ostats},
        }
        if name == "tag_dates":
            listing_main = listing
            write_csv("q8_null", [{"draw": i, **d} for i, d in enumerate(null)])
    write_csv("q8_coordinated", [r for v in variants.values() for r in v["observed_pairs"]])
    return {"description": f"A coordinated pair = two different codebases shipping a stable release that carries the same label "
                           f"within {WINDOW_DAYS} days (|UTC instant difference| <= {WINDOW_DAYS} x 86400 s). Labels: "
                           f"'cve:<id>' for included CVE fix rows (first stable fix release; the vendor release date for "
                           f"unbound CVE-2017-15105) and 'topic:<topic>' for question 3 memberships (timing release). "
                           f"pdns-auth and pdns-rec are one codebase. Statistics: label_pairs = distinct (label, codebase "
                           f"pair); distinct_release_pairs counts each pair of releases once however many labels they share "
                           f"(the headline, since KeyTrap's two CVEs ship in the same releases). Null: each codebase's events "
                           f"are circularly shifted by one uniform offset within that codebase's own stable-release span, "
                           f"preserving internal spacing; {N_DRAWS} draws, random.Random({SEED}). Variant "
                           f"'pdns_rec_changelog_public_dates' replaces pdns-rec CVE tag dates with the changelog's public "
                           f"date where parseable (sensitivity check).",
            "seed": SEED, "n_draws": N_DRAWS, "window_days": WINDOW_DAYS,
            "codebase_spans": {cb: [iso(a), iso(b)] for cb, (a, b) in spans.items()},
            "variants": variants,
            "headline": variants["tag_dates"]["tests"]["distinct_release_pairs"],
            "near_misses": {
                "CVE-2020-28935": "nsd NSD_4_3_4_REL (2020-11-24) and unbound: the fix is first in release-1.13.0rc1 on the "
                                  "same day, but the first stable unbound release is release-1.13.0 on 2020-12-03, 9 days "
                                  "later, so it is not counted (only stable releases count)."},
            "caveat": "Few labels are shared by two or more codebases at all. The CVE component is one coordinated embargo "
                      "(KeyTrap, February 2024), which the shift destroys by design; the topic component is a single "
                      "same-day pair and is not distinguishable from the null."}


# --------------------------------------------------------------------------- Arc A cross-check
def cross_check_support(defaults, support, data):
    vmap = {}
    for p in PROGRAMS:
        m = {}
        for r in data[p]["releases"]:
            if r["stable"]:
                m.setdefault(r["version"], r)
        vmap[p] = m
    out_support, out_defaults = [], []
    for s in support["support"]:
        p = s["implementation"]
        R = vmap.get(p, {}).get(s["first_release"])
        issues = []
        if R is None:
            issues.append(f"version {s['first_release']} not a stable release in the {p} timeline")
        elif R["released"] != s["released"]:
            issues.append(f"Arc A date {s['released']} vs timeline releases[{R['tag']}].released {R['released']}")
        earlier = [r for r in defaults if r["program"] == p and s["rfc"] in r["rfcs"] and r["timing_date"] < s["released"]]
        for r in earlier:
            issues.append(f"timeline row {r['row_id']} cites {s['rfc']} with date {r['timing_date']}, before Arc A's first "
                          f"{s['capability']} {s['observable']} release {s['first_release']} ({s['released']})")
        out_support.append({"program": p, "capability": s["capability"], "observable": s["observable"], "rfc": s["rfc"],
                            "arc_a_first_release": s["first_release"], "arc_a_released": s["released"],
                            "agrees": not issues, "issues": issues})
    for kind in ("default_changes", "validator_limits"):
        for s in support[kind]:
            p = s["implementation"]
            R = vmap.get(p, {}).get(s["first_release"])
            rows = [r for r in defaults if r["program"] == p and R is not None and r["stable_tag"] == R["tag"]]
            issues = []
            if R is None:
                issues.append(f"version {s['first_release']} not a stable release in the {p} timeline")
            else:
                if R["released"] != s["released"]:
                    issues.append(f"Arc A date {s['released']} vs timeline releases[{R['tag']}].released {R['released']}")
                if not rows:
                    issues.append(f"no timeline default_changes row has stable tag {R['tag']}")
            out_defaults.append({"arc_a_table": kind, "program": p, "what": s.get("what"),
                                 "arc_a_first_release": s["first_release"], "arc_a_released": s["released"],
                                 "timeline_rows_at_that_release": [r["row_id"] for r in rows],
                                 "agrees": not issues, "issues": issues})
    write_csv("xcheck_software_support", [{**r, "issues": "; ".join(r["issues"])} for r in out_support + out_defaults])
    return {"description": "software_support.json (Arc A) checked against the timelines: release dates of the named first "
                           "release, timeline rows citing the same RFC dated before Arc A's first support release, and whether "
                           "Arc A default/limit rows have a timeline default row at the same stable release. Disagreements are "
                           "reported, not resolved.",
            "support_rows": out_support, "default_and_limit_rows": out_defaults,
            "n_disagreements": sum(1 for r in out_support + out_defaults if not r["agrees"])}


def _cmd(p, expr):
    return f"python3 -c \"import json;d=json.load(open('data/software/timelines/{p}.json'));{expr}\""


MANUAL_SUSPECTS: list[dict] = [
    {"program": "bind9", "row_id": "d10-dsa-removed", "field": "mechanism",
     "reason": "mechanism is alg-rsa-sha2 but the row removes DSA (algorithms 3 and 6); knot[7] and unbound[17] label the "
               "same kind of change 'other'",
     "command": _cmd("bind9", "r=[x for x in d['default_changes'] if x['id']=='d10-dsa-removed'][0];print(r['mechanism'],'|',r['description'])")},
    {"program": "pdns-auth", "row_id": "pdns-auth[5]@4.0.0", "field": "stable_tag",
     "reason": "stable_tag auth-4.0.0 is given for an intermediate pre-release state (default-ksk-algorithms emptied) that "
               "pdns-auth[8] replaced before auth-4.0.0 shipped, so no stable release carried this after-state",
     "command": _cmd("pdns-auth", "[print(i,r['tag'],r['stable_tag'],'|',r['after'][:110]) for i,r in enumerate(d['default_changes']) if i in (5,6,8)]")},
    {"program": "pdns-auth", "row_id": "pdns-auth[6]@4.0.0", "field": "stable_tag",
     "reason": "same as pdns-auth[5]: the after text calls default-zsk-algorithms=ecdsa256 an intermediate state, "
               "superseded by pdns-auth[8] (ecdsa256 KSK as CSK, empty ZSK list) in auth-4.0.0",
     "command": _cmd("pdns-auth", "[print(i,r['tag'],r['stable_tag'],'|',r['after'][:110]) for i,r in enumerate(d['default_changes']) if i in (5,6,8)]")},
]

QUESTIONS = [
    ("q1_mechanism_matrix", lambda c: q1(c["defaults"])),
    ("q2_code_lag_vs_rfc", lambda c: q2(c["defaults"], c["checklist"])),
    ("q3_default_flip_topics", lambda c: q3(c["defaults"])),
    ("q4_leader_follower", lambda c: q4(c["defaults"])),
    ("q5_obsolescence", lambda c: q5(c["defaults"], c["checklist"], c["data"])),
    ("q6_cve_latency", lambda c: q6(c["cves"])),
    ("q7_release_cadence", lambda c: q7(c["data"])),
    ("q8_coordinated_releases", lambda c: q8(c["defaults"], c["cves"], c["data"])),
    ("xcheck_software_support", lambda c: cross_check_support(c["defaults"], c["support"], c["data"])),
]

# ===========================================================================  QUESTIONS_END
# (questions 2..8 are defined above this marker as they are added)


def main(argv=None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only", default="", help="comma-separated question keys to run (default: all)")
    args = ap.parse_args(argv)
    data = {p: load_program(p) for p in PROGRAMS}
    checklist = json.loads(CHECKLIST.read_text())
    support = json.loads(SUPPORT.read_text())
    rel = build_release_index(data)
    suspects: list[dict] = []
    defaults, failures = norm_defaults(data, rel, suspects)
    cves = norm_cves(data, rel)
    only = [x for x in args.only.split(",") if x]
    result = json.loads(OUT_JSON.read_text()) if (only and OUT_JSON.exists()) else {}
    counts = {p: {"default_changes_rows": len(data[p]["default_changes"]),
                  "default_changes_normalised": sum(1 for r in defaults if r["program"] == p),
                  "default_changes_is_default_change": sum(1 for r in defaults if r["program"] == p and r["is_default_change"]),
                  "cve_rows": len(data[p]["cve_fixes"]),
                  "cve_included": sum(1 for r in cves if r["program"] == p and r["include"]),
                  "cve_disputed": sum(1 for r in cves if r["program"] == p and r["group"] == "disputed"),
                  "cve_excluded": sum(1 for r in cves if r["program"] == p and r["group"] == "excluded"),
                  "stable_releases": len(stable_releases(data[p]))}
              for p in PROGRAMS}
    result["meta"] = {"generated_by": "scripts/cross_program.py", "seed": SEED, "n_draws": N_DRAWS,
                      "window_days": WINDOW_DAYS, "programs": PROGRAMS, "roles": ROLES,
                      "codebases": sorted(set(CODEBASE.values()))}
    result["normalisation"] = NORMALISATION
    result["row_counts"] = counts
    result["excluded_rows"] = {
        "default_changes_failing_stable_tag_assert": failures,
        "default_changes_not_default_change": [
            {"program": r["program"], "row_id": r["row_id"], "kind": r["kind"],
             "reason": "value_changed false (bind9) / is_default_change false (pdns): kept in question 1, left out of questions 3, 4 and 8"}
            for r in defaults if not r["is_default_change"]],
        "cve_fixes": [{"program": r["program"], "cve": r["cve"], "group": r["group"], "reason": r["exclusion_reason"]}
                      for r in cves if not r["include"]],
    }
    ctx = {"data": data, "checklist": checklist, "support": support, "rel": rel,
           "defaults": defaults, "cves": cves, "suspects": suspects, "result": result}
    for key, fn in QUESTIONS:
        if only and key not in only:
            continue
        result[key] = fn(ctx)
        save(result)  # incremental: a cutoff loses at most one question
    # suspect rows: normalisation-level ones plus those found by questions, de-duplicated
    seen, uniq = set(), []
    for s in suspects + MANUAL_SUSPECTS:
        k = (s["program"], s["row_id"], s["reason"])
        if k not in seen:
            seen.add(k)
            uniq.append(s)
    result["suspect_rows"] = uniq
    write_csv("defaults_normalised", defaults)
    write_csv("cves_normalised", cves)
    save(result)
    return result


if __name__ == "__main__":
    main()
