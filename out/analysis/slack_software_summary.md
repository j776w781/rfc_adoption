Hi, an update on the software side: I cross-referenced the DNS programs (BIND 9, Unbound, NSD, Knot DNS/Resolver, PowerDNS Auth/Recursor, OpenDNSSEC) with the adoption data from both corpora. Short deck attached (`dnssec_software_summary.pptx`, 9 slides); the full per-RFC and per-program decks are in `out/analysis/`.

*What I did*

• Cloned the 8 projects and took 1,083 stable release dates from git tags. For each RFC: the first release that signs/validates it, the release that changed the default, and validator caps, each backed by the commit.
• Added the first Ubuntu LTS and Debian release that shipped each version (Launchpad + sources.debian.org), since most operators get a new default through apt, not from upstream, and ran the same before/after test around each OS release.
• Pulled 441 CVEs for the 8 products from NVD; 97 are DNSSEC mechanisms, classified by what the description names.
• For 5 RFCs (ECDSA, RSA/SHA-256, EdDSA, NSEC3, NSEC3 iterations) I put everything on one time axis with the OpenINTEL per-TLD series and the reverse per-RIR series, found every spike, and for each spike recorded the nearest preceding release, default, cap and CVE, against the chance rate (97% of months contain some DNS release, so "a release came just before" is always true).
• Split every forward spike into new signings vs existing zones rolling over. An update can change what a newly signed zone gets; it can never re-sign an existing zone.
• Auto-update test: in the reverse ledger, the share of newly signed delegations choosing each algorithm in the 12 months before and after every default change.

*What came out*

• *Code is never the wait.* Signers ship an RFC within −0.4 to +1.8 years of publication (negative = from the draft). The first zone then takes 0.1 to 3.8 years. No event study or release scan finds a release month that moves the curve (smallest p 0.11 after detrending).
• *ECDSA (RFC 6605):* Knot and PowerDNS made it default in 2016. The first .se move is 3 months later but was mostly rollovers. The moves that made it the majority (.se 2019, +119k and +217k) were 100% rollovers, 30+ months after any default. The .ch 2021 wave (+591k) was new signings choosing ECDSA 96% of the time. That is where a default acts: silently, on new zones, years later. 2 of 31 spikes sit within 3 months of a default, exactly what a 9% chance rate predicts.
• *Auto-update works, but the OS release is the event.* On their upstream dates the 2016 Knot/PowerDNS ECDSA defaults left no trace in reverse DNS (new signings <1% ECDSA before and after), and neither did Ubuntu 16.04, which carried only Knot. Debian 9 (June 2017) was the first OS release shipping both ECDSA-default signers: in the year after it 57% of new reverse signings chose ECDSA (0.2% the year before), from 55 blocks (3 before). A second step (23% → 39%) came with BIND 9.16 via Ubuntu 20.04 / Debian 11. So defaults do reach zones, one OS release at a time and only on newly signed zones, which is exactly why they never show up as a spike in the adoption curve.
• *NSEC3 iterations (RFC 9276) is the one vendor-triggered case.* Names with ≥100 iterations collapsed in Oct–Nov 2021 in every TLD that had them (.nu 12,145 → 110), 10 months BEFORE the RFC, 2–3 months after the PowerDNS 4.5.0 and Unbound 1.13.2 caps and CVE-2021-40083 (Knot Resolver assertion failure on too many iterations). All 3 spikes are within 3 months of a cap vs a 14% chance rate. The RFC codified what validators had already forced.
• *EdDSA (RFC 8080):* never a default anywhere. Two .se/.nu episodes, both rollovers, both withdrawn within a year. No default, no adoption.
• *CVEs did not lead any push.* Every CVE nearest to a spike is a validator bug (memory leak, assertion failure). 69 of the 97 DNSSEC CVEs sit in the 4033/4034/4035 core. For NSEC3 the order is code (BIND 9.6.0, Dec 2008) → deployment (RIPE reverse, Jul 2009) → first CVE (Oct 2009).

*Caveats*

• Which software signs a zone is never visible; "nearest release" is timing evidence, and registry/registrar platforms are closed. The Debian 9 step is 55 blocks in one corpus, APNIC-heavy, with one block a third of it.
• The OpenINTEL data we have is monthly aggregates for 7 TLDs from mid-2016 (2020 for .ch/.li) to end-2023, so RSA/SHA-256 and NSEC3 adoption are only visible in reverse DNS, and forward spikes cannot be attributed to an operator.
• 3 to 31 spikes per RFC: "beats chance" is a reading, not a p-value.

Files: `dnssec_software_summary.pptx` (short), `dnssec_program_rfc_cases.pptx` (per program, 24 slides), `dnssec_rfc_why.pptx` (per RFC), CSVs `dns_program_rfc_spikes.csv`, `dns_cve_list.csv`, `dns_software_*.csv`. Happy to walk through any of it.
