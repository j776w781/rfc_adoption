"""Pins for scripts/cross_program.py (Phase 4 cross-program comparison).

Run:  python3 -m pytest tests/test_cross_program.py -q
The tests read the real timeline files; outputs are redirected to a temporary directory.
"""
from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("cross_program", ROOT / "scripts" / "cross_program.py")
cp = importlib.util.module_from_spec(spec)
sys.modules["cross_program"] = cp
spec.loader.exec_module(cp)


@pytest.fixture(scope="module")
def ctx():
    data = {p: cp.load_program(p) for p in cp.PROGRAMS}
    rel = cp.build_release_index(data)
    suspects = []
    defaults, failures = cp.norm_defaults(data, rel, suspects)
    cves = cp.norm_cves(data, rel)
    return {"data": data, "rel": rel, "defaults": defaults, "failures": failures, "suspects": suspects, "cves": cves}


@pytest.fixture()
def tmp_out(tmp_path, monkeypatch):
    monkeypatch.setattr(cp, "OUT", tmp_path)
    monkeypatch.setattr(cp, "OUT_JSON", tmp_path / "cross_program.json")
    return tmp_path


# ---------------------------------------------------------------- normalisation counts
EXPECTED_COUNTS = {
    # program: (default rows normalised, of which default changes, CVE included, CVE excluded, CVE disputed, stable releases)
    "bind9": (28, 26, 149, 58, 0, 444),
    "knot": (21, 21, 4, 9, 0, 174),
    "kresd": (18, 18, 14, 2, 0, 89),
    "nsd": (7, 7, 13, 1, 0, 130),
    "opendnssec": (15, 15, 0, 1, 0, 65),
    "pdns-auth": (12, 12, 15, 0, 0, 132),
    "pdns-rec": (22, 18, 52, 0, 0, 174),
    "unbound": (30, 30, 65, 2, 12, 120),
}


@pytest.mark.parametrize("program", cp.PROGRAMS)
def test_row_counts_after_normalisation(ctx, program):
    d, c = ctx["defaults"], ctx["cves"]
    got = (
        sum(1 for r in d if r["program"] == program),
        sum(1 for r in d if r["program"] == program and r["is_default_change"]),
        sum(1 for r in c if r["program"] == program and r["include"]),
        sum(1 for r in c if r["program"] == program and r["group"] == "excluded"),
        sum(1 for r in c if r["program"] == program and r["group"] == "disputed"),
        len(cp.stable_releases(ctx["data"][program])),
    )
    assert got == EXPECTED_COUNTS[program]


def test_every_default_row_has_a_stable_tag(ctx):
    assert ctx["failures"] == []
    for r in ctx["defaults"]:
        R = ctx["rel"][r["program"]][r["stable_tag"]]
        assert R["stable"] is True


def test_row_dates_agree_with_release_rows(ctx):
    # no normalisation-level date disagreement between a row and its release row
    assert ctx["suspects"] == []


def test_pdns_auth_uses_stable_tag_not_prerelease_date(ctx):
    r = next(x for x in ctx["defaults"] if x["row_id"] == "pdns-auth[11]@4.6.0")
    assert r["stable_tag"] == "auth-4.6.0" and r["stable_date"] == "2022-01-24"


def test_pdns_rec_never_public_tags_use_public_release(ctx):
    r = next(x for x in ctx["defaults"] if x["row_id"] == "nsec3-max-iterations-50")
    assert (r["stable_tag"], r["stable_date"]) == ("rec-5.0.0", "2023-12-18")
    assert (r["timing_tag"], r["timing_date"]) == ("rec-5.0.1", "2024-01-09")


def test_nsd_230_uses_release_commit(ctx):
    r = next(x for x in ctx["defaults"] if x["row_id"] == "nsd[2]@2.3.0")
    assert r["stable_date"] == "2005-05-02" and r["timing_instant"] == "2005-05-02T11:49:23Z"


# ---------------------------------------------------------------- topic dates checked against the clones
# Each instant below was read with: git -C out/software_repos/<repo>.git log -1 --format=%cI '<tag>^{commit}'
CLONE_CHECKED = [
    # (row id, program, repo, tag, UTC instant from the clone)
    ("knot[2]@2.1.0", "knot", "knot", "v2.1.0", "2016-01-14T09:15:02Z"),               # ECDSA P-256 default
    ("unbound[19]@1.13.2", "unbound", "unbound", "release-1.13.2", "2021-08-05T15:10:56Z"),  # NSEC3 cap 150
    ("nsec3-max-iterations-150", "pdns-rec", "pdns", "rec-4.5.2", "2021-06-07T11:54:06Z"),    # NSEC3 cap 150
    ("l01-nsec3-max-iterations-150", "bind9", "bind9", "v9.16.16", "2021-05-12T09:53:16Z"),   # NSEC3 cap 150
    ("kresd[14]@5.7.4", "kresd", "kresd", "v5.7.4", "2024-07-23T17:39:18Z"),            # KSK-2024 added
]


@pytest.mark.parametrize("row_id,program,repo,tag,instant", CLONE_CHECKED)
def test_topic_dates_match_clone(ctx, row_id, program, repo, tag, instant):
    r = next(x for x in ctx["defaults"] if x["program"] == program and x["row_id"] == row_id)
    assert r["stable_tag"] == tag
    assert r["timing_instant"] == instant
    mem = cp.topic_memberships(ctx["defaults"])
    assert any(m["row_id"] == row_id for m in mem)
    git = ROOT / "out" / "software_repos" / f"{repo}.git"
    if git.exists() and shutil.which("git"):
        out = subprocess.run(["git", "-C", str(git), "log", "-1", "--format=%cI", f"{tag}^{{commit}}"],
                             capture_output=True, text=True)
        if out.returncode == 0:
            assert cp.iso(cp.utc(out.stdout.strip())) == instant


# ---------------------------------------------------------------- topics, leaders, baseline
def test_topic_assignment_is_checked(ctx):
    mem = cp.topic_memberships(ctx["defaults"])
    assert len({m["topic"] for m in mem}) == 6
    # rows that are not default changes never enter a topic
    assert not {"d22-cdns-cdnskey-options", "d23-bindkeys-revoked-key-removed"} & {m["row_id"] for m in mem}


def test_poisson_binomial():
    assert cp.poisson_binomial_sf([0.5, 0.5], 2) == pytest.approx(0.25)
    assert cp.poisson_binomial_sf([1 / 3] * 3, 0) == pytest.approx(1.0)


def test_no_program_called_leader(ctx):
    q = cp.q4(ctx["defaults"])
    assert q["programs_called_leader"] == []
    assert set(q["tied_sub_milestones_left_out_of_baseline"]) == {
        "nsec3-iterations-rfc9276/signer-default-iterations-0", "nsec3-iterations-rfc9276/signer-default-salt-empty"}


# ---------------------------------------------------------------- question 8 null
def test_null_seed_and_draws():
    assert cp.SEED == 20260929
    assert cp.N_DRAWS == 1000
    assert cp.WINDOW_DAYS == 3


def test_q8_observed_and_deterministic(ctx, tmp_out):
    a = cp.q8(ctx["defaults"], ctx["cves"], ctx["data"])
    b = cp.q8(ctx["defaults"], ctx["cves"], ctx["data"])
    assert a["seed"] == 20260929
    assert a["headline"] == b["headline"]
    assert a["headline"]["observed"] == 4
    assert a["variants"]["tag_dates"]["tests"]["label_pairs_topic"]["observed"] == 1
    assert a["variants"]["tag_dates"]["tests"]["label_pairs_topic"]["distinguishable_from_null"] is False
    assert (tmp_out / "cross_program_q8_null.csv").exists()


def test_cve_latency_medians(ctx, tmp_out):
    q = {r["program"]: r for r in cp.q6(ctx["cves"])["per_program"]}
    assert q["bind9"]["latency_days_median"] == -13
    assert q["unbound"]["latency_days_median"] == 0
    assert q["bind9"]["dnssec_subset"].startswith("not classified")
