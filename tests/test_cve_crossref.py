"""Pin docs/cve_crossref.md to the analysis output.

Two classes of error already occurred while building this and neither looks
wrong on the page: product attribution that came from a substring match
("Knot DNS" matches every "Knot Resolver" advisory), and treating PowerDNS
Authoritative and Recursor as separate codebases when they ship from one
repository. Both inflated the multi-vendor coordination count, from 4 to 14.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "cve_crossref.md"
OUT = ROOT / "out" / "analysis" / "cve_crossref.json"
INV = ROOT / "data" / "software" / "cve_inventory.json"

pytestmark = pytest.mark.skipif(
    not OUT.exists(), reason="run scripts/cve_crossref.py first")


@pytest.fixture(scope="module")
def a() -> dict:
    return json.loads(OUT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_scopes_partition_the_inventory(a):
    assert sum(a["totals"]["by_scope"].values()) == a["totals"]["distinct_cves"]


def test_mechanism_counts_sum_to_dnssec_total(a):
    """Every DNSSEC CVE carries a mechanism, so the two totals must agree."""
    assert sum(a["totals"]["by_mechanism"].values()) == a["totals"]["by_scope"]["dnssec"]


def test_doc_totals_match(doc, a):
    t = a["totals"]
    assert str(t["distinct_cves"]) in doc
    for scope in ("dnssec", "dns", "dependency"):
        assert str(t["by_scope"][scope]) in doc


def test_keyword_sourced_products_never_decide_attribution(a):
    """Knot, Knot Resolver and OpenDNSSEC have no CPE; their lists overlap by
    substring, so they must not appear as evidence of who a CVE affected."""
    keyword = {p for p, m in a["query_method"].items() if m == "keyword"}
    for c in a["coordinated"]:
        for proj, how in c["affected_evidence"].items():
            assert how == "git-fix" or proj not in keyword, (c["cve"], proj)


def test_powerdns_alone_is_not_coordination(a):
    """auth and rec are one repository; alone they are one codebase, not two."""
    for c in a["coordinated"]:
        assert len(c["codebases"]) >= 2, c["cve"]
        assert c["codebases"] != ["powerdns"], c["cve"]


def test_keytrap_and_nsec3_are_the_multi_vendor_events(a):
    ids = {c["cve"] for c in a["coordinated"]}
    assert {"CVE-2023-50387", "CVE-2023-50868"} <= ids
    for cve in ("CVE-2023-50387", "CVE-2023-50868"):
        row = next(c for c in a["coordinated"] if c["cve"] == cve)
        assert len(row["vendors"]) >= 3, cve
        assert row["spread_days"] > 100, cve


def test_signers_and_authoritative_only_servers_carry_no_dnssec_cves(a):
    """The finding the measurement rests on: the DNSSEC CVE surface is on the
    validating side, which authoritative-side measurement cannot see."""
    assert a["per_project"]["nsd"].get("dnssec", 0) == 0
    assert a["per_project"]["opendnssec"].get("dnssec", 0) == 0


def test_embargo_fixes_are_not_counted_as_late(a):
    """A fix released before publication is coordinated disclosure. If the median
    latency ever goes strongly positive, check that these were not dropped."""
    assert a["fix_latency_days"]["all"]["median"] <= 7
    assert "negative_are_embargo" in a["fix_latency_days"]


def test_nsec3_deployment_moved_before_both_rfc_and_cve(a):
    """The chronology the document turns on."""
    cve = next(c for c in a["cves"] if c["cve"] == "CVE-2023-50868")
    assert cve["published"] > "2022-08"          # RFC 9276 precedes the CVE
    assert cve["mechanism"] == "nsec3"
    assert "2021-10" in DOC.read_text(encoding="utf-8")


def test_every_cve_records_the_rule_that_classified_it(a):
    for c in a["cves"]:
        assert c.get("rule"), c["cve"]


def test_doc_cve_ids_all_exist_in_the_inventory(doc, a):
    known = {c["cve"] for c in a["cves"]}
    for cve in set(re.findall(r"CVE-\d{4}-\d{4,7}", doc)):
        assert cve in known, cve


ADOPT = ROOT / "out" / "analysis" / "cve_adoption_crossref.json"


@pytest.fixture(scope="module")
def adopt() -> dict:
    if not ADOPT.exists():
        pytest.skip("run scripts/cve_adoption_crossref.py first")
    return json.loads(ADOPT.read_text(encoding="utf-8"))


def test_adoption_join_only_attaches_named_mechanisms(adopt):
    """A bug in the shared validation path is not evidence against one algorithm."""
    t = adopt["totals"]
    assert t["attached_to_a_named_mechanism"] + t["not_attachable"] == t["dnssec_cves"]
    assert t["attached_to_a_named_mechanism"] < t["not_attachable"]


def test_shared_core_carries_most_dnssec_cves(adopt):
    """The finding: the attack surface is the machinery common to all deployments."""
    assert adopt["shared_core"]["n_cves"] > adopt["totals"]["attached_to_a_named_mechanism"]


def test_no_cve_predates_first_use_of_what_it_attacks(adopt):
    stages = [c["stage_when_published"]
              for r in adopt["changes"] for c in r["cves"]]
    assert stages, "expected at least one mechanism-named CVE"
    assert "before first use" not in stages


def test_nsec3_is_measured_by_nsec3param_not_algorithm_7(adopt):
    """Algorithm 7 peaks near 29%; NSEC3 itself sits far higher, and the CVEs
    matched on /NSEC3/ are about the mechanism."""
    n3 = adopt["nsec3_mechanism"]
    alg7 = next(r for r in adopt["changes"] if r["change"] == "RSASHA1-NSEC3")
    assert n3["peak_share_pct"] > 2 * alg7["peak_share_pct"]
    assert "NSEC3PARAM" in n3["basis"]


def test_correlation_is_reported_with_its_caveat(adopt):
    assert adopt["correlation_peak_share_vs_cve_count"] is not None
    assert "establish" in adopt["correlation_caveat"]
