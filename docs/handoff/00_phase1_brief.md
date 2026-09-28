# Phase 1 brief: one program's full DNSSEC timeline

You are building the timeline for ONE DNS program. Work only from primary
sources: the bare git clone under `out/software_repos/`, the NVD-derived CVE
inventory in `data/software/cve_inventory.json`, and `out/analysis/cve_crossref.json`.
Do not copy claims from `data/software/software_support.json`; you may use it
to know what to look for, but every row you emit must carry its own evidence.

## Inputs

| program | clone | tag pattern | notes |
|---|---|---|---|
| bind9 | out/software_repos/bind9.git | `v9.x.y` | odd minors >= 9.13 are development branches; mark `stable: false` |
| unbound | out/software_repos/unbound.git | `release-x.y.z` | |
| nsd | out/software_repos/nsd.git | `NSD_x_y_z_REL` | authoritative, does not sign; still record validation/DNSSEC-serving changes |
| knot | out/software_repos/knot.git | `vx.y.z` | Knot DNS (authoritative + signer) |
| kresd | out/software_repos/kresd.git | `vx.y.z` | Knot Resolver |
| opendnssec | out/software_repos/opendnssec.git | `x.y.z` / `release/x.y.z` | signer only |
| pdns-auth | out/software_repos/pdns.git | `auth-x.y.z` (older: `rec-`/`auth-` mixed, `pdns-x.y.z`) | shares the repo with pdns-rec |
| pdns-rec | out/software_repos/pdns.git | `rec-x.y.z` | |

Release date = the commit date of the tag's dereferenced commit
(`git -C <clone> log -1 --format=%cI <tag>^{commit}`), not the tagger date.

Changelog files (read at each tag with `git show <tag>:<path>`): BIND `CHANGES`
and `doc/notes/*` / `doc/arm/notes*.rst`; Unbound `doc/Changelog`; NSD
`doc/ChangeLog`; Knot `NEWS`; Knot Resolver `NEWS`; OpenDNSSEC `NEWS`;
PowerDNS `docs/changelog/*.rst` (older `pdns/docs/changelog.md`,
`ChangeLog`). If a file moved, find it; say in the output which path served
which version range.

## What to extract, per release

1. `version`, `tag`, `released` (ISO date), `stable` (bool), `commit`.
2. `changelog_entries`: every entry new in that release (diff the changelog
   against the previous tag; do not re-attribute old entries). Keep the raw
   text. Cap at the entries that mention any of: DNSSEC, DS, DNSKEY, RRSIG,
   NSEC, NSEC3, NSEC3PARAM, CDS, CDNSKEY, RSASHA, SHA-256, SHA256, SHA-512,
   ECDSA, Ed25519, Ed448, EdDSA, GOST, algorithm 8/10/12/13/14/15/16, trust
   anchor, RFC 5011, managed-keys, revoke, KSK, ZSK, CSK, rollover,
   dnssec-policy, signing, validation, validator, "RFC <number>", CVE-.
   Also record the total entry count for the release so density is known.
3. For each kept entry: `mechanism` (one of nsec3, nsec3-iterations, alg-rsa-sha2,
   alg-gost, alg-ecdsa, alg-eddsa, ds-digest, cds-cdnskey, trust-anchor-5011,
   validation, rrsig, dnskey, other), `rfcs` (any RFC numbers named or
   implied), `cves` (any CVE ids named), `kind` (one of `support-added`,
   `default-changed`, `limit-changed`, `cve-fix`, `deprecation`, `removal`,
   `other`), `is_default_change` (bool), and `evidence`: the changelog line
   verbatim plus, for `support-added` and `default-changed`, the commit hash
   that made the change (find it with `git log -S`/`--grep` between the two
   tags) and confirmation that `git tag --contains <commit>` includes the tag.
4. `cve_fixes`: for every CVE id in `cve_inventory.json` attributed to this
   product, the first tag that contains the fix (from the `fixes` field, or by
   searching the log), its date, the NVD publication date, and the latency in
   days (negative = fixed before publication).

## Default changes get the most care

A default change is a release after which a user who changed no configuration
gets different DNSSEC behaviour: default signing algorithm, default NSEC3
iterations/salt, default key sizes, validation on by default, trust anchor
handling, iteration caps, CDS publication on by default. For each, record the
before value, the after value, whether it applies on upgrade or only to new
configurations (`applies_on_upgrade`, `opt_in`), the commit, and the
documentation or changelog line. If you cannot find the commit, say
`attribution: "approximate"` and why.

## Output

* `data/software/timelines/<program>.json` — schema above, plus a top-level
  `sources` block listing every file path and command used, and a `gaps`
  list for anything you could not determine.
* `data/software/timelines/<program>.md` — a human summary: release count and
  span, table of every `support-added` / `default-changed` / `limit-changed`
  row, table of CVE fixes with latency, and the gaps.
* Do not edit any other file. Do not commit.

## Standards

* Every date from a command you ran, never from memory.
* Never infer a capability from a version number.
* Prefer "not found" to a guess. A wrong date is worse than a missing one.
* Write the .md so an agent with no other context can verify any row from
  the clone in under a minute.
