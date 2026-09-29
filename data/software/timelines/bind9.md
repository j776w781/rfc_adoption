# BIND 9 DNSSEC timeline

Generated 2026-09-29 from `out/software_repos/bind9.git` (bare, blob-less partial clone of https://gitlab.isc.org/isc-projects/bind9.git), `data/software/cve_inventory.json` and `out/analysis/cve_crossref.json`. Machine-readable twin: `data/software/timelines/bind9.json`.

**Releases:** 852 tags (444 stable = 252 x.y.z + 150 -Pn + 31 ESV + 11 -Wn; 91 development-branch x.y.z; 317 a/b/rc), 1999-09-08 .. 2026-09-11 (stable: 2000-09-15 .. 2026-09-11). Release date = commit date of `<tag>^{commit}`.

Multiple long-lived maintenance branches (v9_0 .. v9_20 in the clone as refs/heads/v9_<minor>); every stable line gets its own point releases (v9.x.y), security patch rebuilds (v9.x.y-Pn), and, 2020-2021, Windows-only rebuilds (v9.x.y-Wn). Extended-support lines are tagged v9.4-ESV[-Rn][-Pn], v9.6-ESV-Rn[-Pn] and v9.9-ESV-R10-P2 (no z component). From 9.13 on, odd minors (9.13, 9.15, 9.17, 9.19, 9.21) are development branches whose x.y.z tags are marked stable:false (kind "dev"); the next even minor (9.14/9.16/9.18/9.20) is the stable line derived from it. Pre-releases (aN/bN/rcN) are stable:false. Tags v9.0.0 .. v9.9.0rc2 era (174 tags, through 2012-02) are cvs2git-manufactured commits whose commit date is the CVS tag time; all dates here are the commit date of <tag>^{commit}, never the 2023-03-16 tagger date the git tags carry. Changelog: top-level CHANGES (numbered entries, "--- x.y.z released ---" markers) for every tag up to v9.18.3x/v9.20.3/v9.21.2; afterwards per-release doc/changelog/changelog-<ver>.rst. CHANGES is per-branch: an entry backported to 9.11 appears under a 9.11.x marker in the 9.11 branch copy with its master-allocated number, so each entry is attributed to the earliest-dated final (non-a/b/rc) tag whose changelog contains it, and first_stable_tag is recorded separately when that tag is a development release.


## How to verify a row

```
C=out/software_repos/bind9.git
git -C $C log -1 --format=%cI <tag>^{commit}                       # release date
git -C $C show <tag>:CHANGES | grep -n -F "<changelog line>"        # entry present at the tag (tags <= 9.18.3x/9.20.3/9.21.2)
git -C $C show <tag>:doc/changelog/changelog-<ver>.rst              # later tags
git -C $C show <prev_stable_tag>:CHANGES | grep -c -F "<changelog line>"   # 0 = new in this release
git -C $C log <prev>..<tag> -F -i --grep="<changelog line>"         # commit that carries the entry
git -C $C tag --contains <commit> | grep -x <tag>                   # commit is in the release
git -C $C show <commit> -- <path>                                   # default value before/after
```

## Support added / defaults changed / limits changed / removed

| version | date | kind | default change | mechanism | changelog line (first line) | commit(s) | in tag |
|---|---|---|---|---|---|---|---|
| 9.0.0 | 2000-09-15 | support-added | no | validation | Do configuration file post-load validation of zones. | - | n/a |
| 9.0.0 | 2000-09-15 | support-added | no | validation | Configuration file post-load validation of zones | - | n/a |
| 9.0.0 | 2000-09-15 | support-added | no | validation | Introduced new logging category "dnssec" and | - | n/a |
| 9.0.0 | 2000-09-15 | support-added | no | other | If the server is authoritative for both a | - | n/a |
| 9.0.0 | 2000-09-15 | support-added | no | other | Allow dnssec verifications to ignore the validity | - | n/a |
| 9.0.0 | 2000-09-15 | support-added | no | other | The dnssec tools properly use the logging subsystem. | - | n/a |
| 9.0.0 | 2000-09-15 | support-added | no | rrsig | The DNSSEC key generation and signing tools now | - | n/a |
| 9.1.0 | 2001-01-17 | support-added | no | other | Add support for update forwarding as required for | - | n/a |
| 9.1.0 | 2001-01-17 | support-added | no | validation | The DNSSEC OK bit in the EDNS extended flags | - | n/a |
| 9.1.0 | 2001-01-17 | support-added | no | validation | The DNSSEC AD bit will not be set on queries which | - | n/a |
| 9.1.0 | 2001-01-17 | support-added | no | validation | A warning is now printed if the "allow-update" | - | n/a |
| 9.1.0 | 2001-01-17 | support-added | no | rrsig | dnssec-signzone is now multithreaded. | - | n/a |
| 9.1.0 | 2001-01-17 | support-added | no | rrsig | dnssec-signzone now adds a comment to the zone | - | n/a |
| 9.1.0 | 2001-01-17 | support-added | no | rrsig | dnssec-signzone -t output now includes performance | - | n/a |
| 9.2.0 | 2001-11-25 | support-added | no | other | The server can now convert RFC1886-style recursive | - | n/a |
| 9.2.0 | 2001-11-25 | support-added | no | other | Accept (but warn about) master files beginning with | - | n/a |
| 9.2.0 | 2001-11-25 | support-added | no | other | The ability to get entropy from either the | - | n/a |
| 9.2.0 | 2001-11-25 | removal | no | other | Remove openssl from the distribution; require that | - | n/a |
| 9.2.2 | 2003-02-21 | support-added | no | validation | libbind: "DNSSEC OK" (DO) support. | - | n/a |
| 9.4.0 | 2007-02-15 | support-added | no | other | dig now supports the undocumented dig 8 feature | - | n/a |
| 9.4.0 | 2007-02-15 | support-added | no | other | The dnssec tools can now take multiple '-r randomfile' | - | n/a |
| 9.4.0 | 2007-02-15 | support-added | no | validation | Treat non-authoritative responses to queries for type | - | n/a |
| 9.4.0 | 2007-02-15 | support-added | no | other | Add support for RSA-SHA1 keys (RFC3110). | - | n/a |
| 9.4.0 | 2007-02-15 | support-added | no | dnskey | dnssec-keygen should always generate keys with | - | n/a |
| 9.4.0 | 2007-02-15 | support-added | no | rrsig | Add the "key-directory" configuration statement, | - | n/a |
| 9.4.0 | 2007-02-15 | support-added | no | other | DS (delegation signer) support. | - | n/a |
| 9.4.0 | 2007-02-15 | support-added | no | other | Generate DNSSEC wildcard proofs. | - | n/a |
| 9.4.0 | 2007-02-15 | support-added | no | rrsig | dnssec-signzone: adjust the default signing time by | - | n/a |
| 9.4.0 | 2007-02-15 | support-added | no | rrsig | dnssec-signzone, dnssec-keygen, dnssec-makekeyset | - | n/a |
| 9.4.0 | 2007-02-15 | support-added | no | other | Handle records that live in the parent zone, e.g. DS. | - | n/a |
| 9.4.0 | 2007-02-15 | support-added | no | ds-digest | Explicitly request the (re-)generation of DS records | - | n/a |
| 9.4.0 | 2007-02-15 | support-added | no | dnskey | Support for KSK flag. | - | n/a |
| 9.4.0 | 2007-02-15 | support-added | no | other | DS TTL now derived from NS ttl.  NXT TTL now derived | - | n/a |
| 9.4.0 | 2007-02-15 | support-added | no | rrsig | Roll the DNSSEC types to RRSIG, NSEC and DNSKEY. | - | n/a |
| 9.4.0 | 2007-02-15 | support-added | no | other | NSEC now uses new bitmap format. | - | n/a |
| 9.4.0 | 2007-02-15 | support-added | no | other | Implement missing DNSSEC tests for | - | n/a |
| 9.4.0 | 2007-02-15 | support-added | no | other | New DNSSEC 'disable-algorithms'.  Support entry into | - | n/a |
| 9.4.0 | 2007-02-15 | support-added | no | other | Disable DNSSEC support by default.  To enable | - | n/a |
| 9.4.0 | 2007-02-15 | support-added | no | trust-anchor-5011 | DNSSEC lookaside validation. | - | n/a |
| 9.4.0 | 2007-02-15 | support-added | no | other | Specify that certain parts of the namespace must | - | n/a |
| 9.4.0 | 2007-02-15 | support-added | no | other | New dns_db_find() option DNS_DBFIND_COVERINGNSEC. | - | n/a |
| 9.4.0 | 2007-02-15 | support-added | no | validation | dig now has support to chase DNSSEC signature chains. | - | n/a |
| 9.4.0 | 2007-02-15 | support-added | no | trust-anchor-5011 | Update dnssec-lookaside named.conf syntax to support | - | n/a |
| 9.4.0 | 2007-02-15 | support-added | no | dnskey | Update dnssec-keygen to default to KEY for HMAC-MD5 | - | n/a |
| 9.4.0 | 2007-02-15 | support-added | no | rrsig | Add support for additional zone file formats for | - | n/a |
| 9.4.0 | 2007-02-15 | support-added | no | rrsig | dnssec-signzone can now randomize signature end times | - | n/a |
| 9.4.0 | 2007-02-15 | removal | no | other | Remove last vestiges of dnssec-signkey and | - | n/a |
| 9.4.0 | 2007-02-15 | support-added | no | other | Automatic empty zone creation for D.F.IP6.ARPA and | - | n/a |
| 9.4.0 | 2007-02-15 | support-added | no | other | DS is required to accept mnemonic algorithms | - | n/a |
| 9.4.0 | 2007-02-15 | support-added | no | validation | Validate pending NS RRsets, in the authority section, | - | n/a |
| 9.4.0 | 2007-02-15 | default-changed | yes | rrsig | It is now possible to configure named to accept | - | n/a |
| 9.4.0 | 2007-02-15 | support-added | no | other | TSIG HMACSHA1, HMACSHA224, HMACSHA256, HMACSHA384 and | - | n/a |
| 9.4.0 | 2007-02-15 | support-added | no | rrsig | dnssec-signzone: output the SOA record as the | - | n/a |
| 9.4.0 | 2007-02-15 | support-added | no | ds-digest | DS/DLV SHA256 digest algorithm support. [RT #15608] | - | n/a |
| 9.4.0 | 2007-02-15 | support-added | no | dnskey | Check the KSK flag when updating a secure dynamic zone. | - | n/a |
| 9.4.0 | 2007-02-15 | default-changed | yes | validation | It is now possible to explicitly enable DNSSEC | - | n/a |
| 9.4.0 | 2007-02-15 | support-added | no | validation | It is now posssible to enable/disable DNSSEC | - | n/a |
| 9.4.0 | 2007-02-15 | support-added | no | rrsig | dnssec-signzone can now update the SOA record of | - | n/a |
| 9.4.0 | 2007-02-15 | default-changed | yes | other | dnssec-checkzone output style "default" was badly | - | n/a |
| 9.5.0 | 2008-05-22 | support-added | no | other | GSS-TSIG support (RFC 3645). | - | n/a |
| 9.5.0 | 2008-05-22 | support-added | no | dnskey | dnssec-keygen now defaults to nametype "ZONE" | - | n/a |
| 9.5.0 | 2008-05-22 | support-added | no | other | Add support for Name Server ID (RFC 5001). | - | n/a |
| 9.5.0-P2 | 2008-07-29 | default-changed | yes | validation | The default value for dnssec-validation was changed to | - | n/a |
| 9.6.0 | 2008-12-21 | support-added | no | rrsig | Use the EVP interface to OpenSSL. Add PKCS#11 support. | - | n/a |
| 9.6.0 | 2008-12-21 | support-added | no | rrsig | Provide incremental re-signing support for secure | - | n/a |
| 9.6.0 | 2008-12-21 | support-added | no | dnskey | Treat DNSKEY queries as if "minimal-response yes;" | - | n/a |
| 9.6.0 | 2008-12-21 | support-added | no | nsec3 | Add NSEC3 support. [RT #15452] | - | n/a |
| 9.6.0 | 2008-12-21 | support-added | no | ds-digest | Added a tool, dnssec-dsfromkey, to generate DS records | - | n/a |
| 9.6.1 | 2009-06-09 | default-changed | yes | rrsig | Changed default sig-signing-type to 65534, because | - | n/a |
| 9.5.2 | 2009-09-21 | support-added | no | rrsig | Rationalize dnssec-signzone's signwithkey() calling. | - | n/a |
| 9.5.2 | 2009-09-21 | support-added | no | other | Treat DS queries as if "minimal-response yes;" | - | n/a |
| 9.7.0 | 2010-02-16 | support-added | no | other | Add support for the new CERT types from RFC 4398. | - | n/a |
| 9.7.0 | 2010-02-16 | support-added | no | other | Move journalprint, nsec3hash, and genrandom | - | n/a |
| 9.7.0 | 2010-02-16 | support-added | no | trust-anchor-5011 | Simplify DLV configuration, with a new option | - | n/a |
| 9.7.0 | 2010-02-16 | support-added | no | rrsig | Perform post signing verification checks in | - | n/a |
| 9.7.0 | 2010-02-16 | support-added | no | ds-digest | Add -l option to dnssec-dsfromkey to generate | - | n/a |
| 9.7.0 | 2010-02-16 | default-changed | yes | rrsig | Add default values for the arguments to | - | n/a |
| 9.7.0 | 2010-02-16 | support-added | no | trust-anchor-5011 | Add support for RFC 5011, automatic trust anchor | - | n/a |
| 9.7.0 | 2010-02-16 | removal | no | rrsig | Simplify zone signing and key maintenance with the | - | n/a |
| 9.7.0 | 2010-02-16 | support-added | no | trust-anchor-5011 | Clarify syntax for managed-keys {} statement, add | - | n/a |
| 9.7.0 | 2010-02-16 | support-added | no | dnskey | Several improvements to dnssec-* tools, including: | - | n/a |
| 9.7.0 | 2010-02-16 | deprecation | no | rrsig | Changes to key metadata behavior: | - | n/a |
| 9.7.0 | 2010-02-16 | support-added | no | nsec3 | dnssec-signzone: retain the existing NSEC or NSEC3 | - | n/a |
| 9.7.0 | 2010-02-16 | default-changed | yes | nsec3-iterations | Reduce default NSEC3 iterations from 100 to 10. | - | n/a |
| 9.7.0 | 2010-02-16 | default-changed | yes | nsec3 | dnssec-keyfromlabel no longer require engine name | - | n/a |
| 9.7.0 | 2010-02-16 | support-added | no | nsec3 | Insecure to secure and NSEC3 parameter changes via | - | n/a |
| 9.7.0 | 2010-02-16 | support-added | no | rrsig | Added some data fields, currently unused, to the | - | n/a |
| 9.7.0 | 2010-02-16 | support-added | no | rrsig | New 'dnssec-signzone -x' flag and 'dnskey-ksk-only' | - | n/a |
| 9.7.0 | 2010-02-16 | support-added | no | rrsig | New 'auto-dnssec' zone option allows zone signing | - | n/a |
| 9.7.0 | 2010-02-16 | support-added | no | alg-rsa-sha2 | Added support for SHA-2 DNSSEC algorithms, | - | n/a |
| 9.7.0 | 2010-02-16 | support-added | no | dnskey | Have dnssec-keygen display a progress indication | - | n/a |
| 9.7.0 | 2010-02-16 | support-added | no | other | Improve the performance of NSEC signed zones with | - | n/a |
| 9.7.0 | 2010-02-16 | support-added | no | alg-rsa-sha2 | Add RSASHA256 and RSASHA512 tests to the dnssec system | - | n/a |
| 9.7.0 | 2010-02-16 | support-added | no | dnskey | Allow the dnssec-keygen progress messages to be | - | n/a |
| 9.7.0 | 2010-02-16 | support-added | no | rrsig | Detect and report records that are different according | - | n/a |
| 9.7.0 | 2010-02-16 | support-added | no | rrsig | Added "smartsign" and improved "autosign" and | - | n/a |
| 9.7.0 | 2010-02-16 | support-added | no | dnskey | Prevent dnssec-keygen and dnssec-keyfromlabel from | - | n/a |
| 9.7.2 | 2010-09-02 | support-added | no | rrsig | Add autosign-ksk and autosign-zsk virtual time tests. | - | n/a |
| 9.7.2 | 2010-09-02 | support-added | no | nsec3 | Check that named successfully skips NSEC3 records | - | n/a |
| 9.7.2 | 2010-09-02 | support-added | no | rrsig | Add support to load new keys into managed zones | - | n/a |
| 9.6.3 | 2011-01-31 | support-added | no | other | Test HMAC functions using test data from RFC 2104 and | - | n/a |
| 9.8.0 | 2011-02-21 | support-added | no | alg-gost | Add GOST support (RFC 5933). [RT #20639] | - | n/a |
| 9.8.0 | 2011-02-21 | default-changed | yes | trust-anchor-5011 | Added a default trust anchor for the root zone, which | - | n/a |
| 9.7.4 | 2011-07-24 | default-changed | yes | dnskey | Running dnssec-settime -f on an old-style key will | - | n/a |
| 9.7.4 | 2011-07-24 | removal | no | rrsig | Remove doc and parser references to the | - | n/a |
| 9.8.1 | 2011-08-24 | support-added | no | other | Add RFC 1918 reverse zones to the list of built-in | - | n/a |
| 9.9.0 | 2012-02-23 | support-added | no | rrsig | New option "dnssec-signzone -X <date>" allows | - | n/a |
| 9.9.0 | 2012-02-23 | support-added | no | rrsig | New option "dnssec-signzone -D", only write out | - | n/a |
| 9.9.0 | 2012-02-23 | support-added | no | nsec3 | Made several changes to enhance human readability | - | n/a |
| 9.9.0 | 2012-02-23 | support-added | no | rrsig | New '-L' option in dnssec-keygen, dnsset-settime, and | - | n/a |
| 9.9.0 | 2012-02-23 | removal | no | rrsig | New '-R' option in dnssec-signzone forces removal | - | n/a |
| 9.9.0 | 2012-02-23 | support-added | no | ds-digest | dnssec-dsfromkey now supports reading keys from | - | n/a |
| 9.9.0 | 2012-02-23 | support-added | no | other | New 'dnssec-loadkeys-interval' option configures | - | n/a |
| 9.9.0 | 2012-02-23 | removal | no | rrsig | dnssec-signzone: Clarified some error and | - | n/a |
| 9.9.0 | 2012-02-23 | support-added | no | rrsig | New 'dnssec-update-mode' option controls updates | - | n/a |
| 9.9.0 | 2012-02-23 | support-added | no | nsec3 | Inserting an NSEC3PARAM via dynamic update in an | - | n/a |
| 9.9.0 | 2012-02-23 | support-added | no | rrsig | Initial inline signing support.  [RT #23657] | - | n/a |
| 9.9.0 | 2012-02-23 | removal | no | rrsig | 'rndc keydone', remove the indicator record that | - | n/a |
| 9.9.0 | 2012-02-23 | support-added | no | rrsig | Inline-signing is now supported for master zones. | - | n/a |
| 9.9.0 | 2012-02-23 | removal | no | nsec3 | New 'rndc signing' option for auto-dnssec zones: | - | n/a |
| 9.9.0 | 2012-02-23 | default-changed | yes | other | Upgrade dig's defaults to better reflect modern | - | n/a |
| 9.9.0 | 2012-02-23 | support-added | no | trust-anchor-5011 | Add "dnssec-lookaside 'no'".  [RT #24858] | - | n/a |
| 9.9.0 | 2012-02-23 | support-added | no | rrsig | dnssec-signzone: "-f -" prints to stdout; "-O full" | - | n/a |
| 9.9.0 | 2012-02-23 | support-added | no | rrsig | Extended the header of raw-format master files to | - | n/a |
| 9.9.0 | 2012-02-23 | support-added | no | other | No longer require that a empty zones be explicitly | - | n/a |
| 9.8.4 | 2012-09-26 | support-added | no | alg-ecdsa | Add ECDSA support (RFC 6605). [RT #21918] | - | n/a |
| 9.9.2 | 2012-09-26 | support-added | no | nsec3 | New "dnssec-verify" command checks a signed zone | - | n/a |
| 9.9.2 | 2012-09-26 | support-added | no | ds-digest | New "dnssec-checkds" command checks a zone to | - | n/a |
| 9.9.3 | 2013-05-17 | support-added | no | other | Add RFC 6598 reverse zones to built in empty zones | - | n/a |
| 9.9.3 | 2013-05-17 | support-added | no | ds-digest | dnssec-dsfromkey now emits the hash without spaces. | - | n/a |
| 9.9.3 | 2013-05-17 | support-added | no | rrsig | New "dnssec-coverage" command scans the timing | - | n/a |
| 9.9.5 | 2014-01-27 | support-added | no | dnskey | Allow externally generated DNSKEY to be imported | - | n/a |
| 9.9.5 | 2014-01-27 | support-added | no | rrsig | "dnssec-signzone -Q" drops signatures from keys | - | n/a |
| 9.9.5 | 2014-01-27 | support-added | no | rrsig | Accept integer timestamps in RRSIG records. [RT #35185] | - | n/a |
| 9.10.0 | 2014-04-28 | support-added | no | ds-digest | DS digest can be disabled at runtime with | - | n/a |
| 9.10.0 | 2014-04-28 | support-added | no | validation | "rndc validation check" reports the current status | - | n/a |
| 9.10.0 | 2014-04-28 | default-changed | yes | rrsig | Support for additional signing algorithms in rndc: | - | n/a |
| 9.10.0 | 2014-04-28 | support-added | no | dnskey | Report DNSKEY key id's when dumping the cache. | - | n/a |
| 9.10.0 | 2014-04-28 | support-added | no | other | Allow the printing of cryptographic fields in DNSSEC | - | n/a |
| 9.10.0 | 2014-04-28 | support-added | no | dnskey | 'dnssec-coverage -l' option specifies a length | - | n/a |
| 9.10.0 | 2014-04-28 | support-added | no | dnskey | "configure --enable-native-pkcs11" enables BIND | - | n/a |
| 9.10.0 | 2014-04-28 | support-added | no | validation | "delve" (domain entity lookup and validation engine): | - | n/a |
| 9.10.0 | 2014-04-28 | support-added | no | rrsig | New "max-zone-ttl" option enforces maximum | - | n/a |
| 9.10.0 | 2014-04-28 | support-added | no | rrsig | Specifying "auto" as the salt when using | - | n/a |
| 9.10.1 | 2014-09-16 | support-added | no | cds-cdnskey | Add CDS and CDNSKEY record types. [RT #36333] | - | n/a |
| 9.10.1 | 2014-09-16 | support-added | no | other | Added support for CAA record type (RFC 6844). | - | n/a |
| 9.10.3 | 2015-09-09 | support-added | no | other | Add EMPTY.AS112.ARPA as per RFC 7534. | - | n/a |
| 9.10.3 | 2015-09-09 | support-added | no | cds-cdnskey | CDS and CDNSKEY need to be signed by the key signing | - | n/a |
| 9.10.3 | 2015-09-09 | support-added | no | other | When any RR type implementation doesn't | - | n/a |
| 9.10.3 | 2015-09-09 | support-added | no | other | Accept DNS-SD non LDH PTR records in reverse zones | - | n/a |
| 9.10.4 | 2016-04-20 | support-added | no | other | Warn about a common misconfiguration when forwarding | - | n/a |
| 9.10.4 | 2016-04-20 | support-added | no | rrsig | When loading managed signed zones detect if the | - | n/a |
| 9.11.0 | 2016-09-29 | support-added | no | rrsig | "dnssec-signzone -N date" updates serial number | - | n/a |
| 9.11.0 | 2016-09-29 | support-added | no | trust-anchor-5011 | "rndc nta" can now be used to set a temporary | - | n/a |
| 9.11.0 | 2016-09-29 | support-added | no | trust-anchor-5011 | By default, negative trust anchors will be tested | - | n/a |
| 9.11.0 | 2016-09-29 | support-added | no | trust-anchor-5011 | "rndc nta" now allows negative trust anchors to be | - | n/a |
| 9.11.0 | 2016-09-29 | default-changed | yes | validation | SERVFAIL responses can now be cached for a | - | n/a |
| 9.11.0 | 2016-09-29 | support-added | no | rrsig | Allow the zone serial of a dynamically updatable | - | n/a |
| 9.11.0 | 2016-09-29 | support-added | no | trust-anchor-5011 | When added, negative trust anchors (NTA) are now | - | n/a |
| 9.11.0 | 2016-09-29 | support-added | no | trust-anchor-5011 | "rndc managed-keys" can be used to check status | - | n/a |
| 9.11.0 | 2016-09-29 | support-added | no | cds-cdnskey | Add support for automating the generation CDS and | - | n/a |
| 9.11.0 | 2016-09-29 | support-added | no | dnskey | dnssec-keymgr: A new python-based DNSSEC key | - | n/a |
| 9.11.0 | 2016-09-29 | support-added | no | dnskey | dnssec-keymgr now takes a '-r randomfile' option. | - | n/a |
| 9.11.0 | 2016-09-29 | default-changed | yes | dnskey | dnssec-keymgr could fail to create successor keys | - | n/a |
| 9.11.0 | 2016-09-29 | support-added | no | trust-anchor-5011 | Named now sends _ta-XXXX.<trust-anchor>/NULL queries | - | n/a |
| 9.11.0 | 2016-09-29 | default-changed | yes | rrsig | The default key manager policy file is now | - | n/a |
| 9.12.0 | 2018-01-17 | support-added | no | other | Added support for the EDNS Padding option (RFC 7830). | - | n/a |
| 9.12.0 | 2018-01-17 | support-added | no | other | Added support for the EDNS TCP Keepalive option | - | n/a |
| 9.12.0 | 2018-01-17 | support-added | no | nsec3 | "host -A" returns most records for a name but | - | n/a |
| 9.12.0 | 2018-01-17 | removal | no | dnskey | dnssec-keygen will no longer generate RSA keys | - | n/a |
| 9.12.0 | 2018-01-17 | support-added | no | dnskey | Update fuzzing code to (1) reply to a DNSKEY | - | n/a |
| 9.12.0 | 2018-01-17 | support-added | no | nsec3 | "nsec3hash -r" option ("rdata order") takes arguments | - | n/a |
| 9.12.0 | 2018-01-17 | support-added | no | alg-eddsa | Added support for ED25519 and ED448 DNSSEC signing | - | n/a |
| 9.12.0 | 2018-01-17 | removal | no | trust-anchor-5011 | "dig +sigchase", and related options "+topdown" and | - | n/a |
| 9.12.0 | 2018-01-17 | support-added | no | trust-anchor-5011 | Check and display EDNS KEY TAG options (RFC 8145) in | - | n/a |
| 9.12.0 | 2018-01-17 | support-added | no | validation | Synthesis of responses from DNSSEC-verified records. | - | n/a |
| 9.12.0 | 2018-01-17 | deprecation | no | rrsig | dnssec-keygen no longer uses RSASHA1 by default; | - | n/a |
| 9.12.0 | 2018-01-17 | support-added | no | cds-cdnskey | 'dnssec-signzone -x' and 'dnssec-dnskey-kskonly' | - | n/a |
| 9.12.0 | 2018-01-17 | support-added | no | other | Synthesis of responses from DNSSEC-verified records. | - | n/a |
| 9.12.0 | 2018-01-17 | support-added | no | trust-anchor-5011 | Exclude trust-anchor-telementry queries from | - | n/a |
| 9.12.0 | 2018-01-17 | support-added | no | other | Synthesis of responses from DNSSEC-verified records. | - | n/a |
| 9.12.0 | 2018-01-17 | removal | no | trust-anchor-5011 | The ISC DLV service has been shut down, and all | - | n/a |
| 9.12.0 | 2018-01-17 | support-added | no | trust-anchor-5011 | "rndc managed-keys destroy" shuts down RFC 5011 key | - | n/a |
| 9.12.0 | 2018-01-17 | support-added | no | cds-cdnskey | "dnssec-signzone -S" can now automatically add parent | - | n/a |
| 9.12.0 | 2018-01-17 | support-added | no | cds-cdnskey | New "dnssec-cds" command creates a new parent DS | - | n/a |
| 9.12.0 | 2018-01-17 | support-added | no | trust-anchor-5011 | Add logging channel "trust-anchor-telementry" to | - | n/a |
| 9.12.0 | 2018-01-17 | support-added | no | trust-anchor-5011 | The working directory and managed-keys directory has | - | n/a |
| 9.12.0 | 2018-01-17 | deprecation | no | dnskey | The use of dnssec-keygen to generate HMAC keys is | - | n/a |
| 9.12.0 | 2018-01-17 | default-changed | yes | other | The hmac-md5 algorithm is no longer recommended for | - | n/a |
| 9.12.0 | 2018-01-17 | support-added | no | other | "dnssec-checkds -s" specifies a file from which | - | n/a |
| 9.12.0 | 2018-01-17 | support-added | no | trust-anchor-5011 | Keys specified in "managed-keys" statements | - | n/a |
| 9.12.0 | 2018-01-17 | support-added | no | trust-anchor-5011 | 'dnssec-lookaside auto;' and 'dnssec-lookaside . | - | n/a |
| 9.13.0 | 2018-05-22 | dev removal | no | dnskey | dnssec-keygen can no longer generate HMAC keys. | - | n/a |
| 9.13.0 | 2018-05-22 | dev support-added | no | rrsig | The "dnskey-sig-validity" option allows | - | n/a |
| 9.13.0 | 2018-05-22 | dev removal | no | dnskey | BIND can no longer be built without DNSSEC support. | - | n/a |
| 9.13.1 | 2018-06-09 | dev support-added | no | other | Add "HOME.ARPA" to list of built in empty zones as | - | n/a |
| 9.13.1 | 2018-06-09 | dev default-changed | yes | trust-anchor-5011 | The default setting for "dnssec-validation" is now | - | n/a |
| 9.13.1 | 2018-06-09 | dev removal | no | alg-gost | Remove support for ECC-GOST (GOST R 34.11-94). | - | n/a |
| 9.13.2 | 2018-07-03 | dev support-added | no | rrsig | verifyzone() and the functions it uses were moved to | - | n/a |
| 9.13.2 | 2018-07-03 | dev support-added | no | validation | Add a new slave zone option, "mirror", to enable | - | n/a |
| 9.13.3 | 2018-09-05 | dev support-added | no | validation | New "validate-except" option specifies a list of | - | n/a |
| 9.13.4 | 2018-11-22 | dev removal | no | nsec3 | Remove support for DNSSEC algorithms 3 (DSA) | - | n/a |
| 9.13.6 | 2019-02-06 | dev support-added | no | rrsig | Improved logging of DNSSEC key events: | - | n/a |
| 9.14.1 | 2019-04-06 | removal | no | trust-anchor-5011 | Remove revoked root DNSKEY from bind.keys. [GL #945] | - | n/a |
| 9.15.0 | 2019-05-10 | dev deprecation | no | other | The "dnssec-enable" option is deprecated and no | - | n/a |
| 9.15.0 | 2019-05-10 | dev support-added | no | trust-anchor-5011 | If trusted-keys and managed-keys were configured | - | n/a |
| 9.15.0 | 2019-05-10 | dev removal | no | cds-cdnskey | The SHA-1 hash algorithm is no longer used when | - | n/a |
| 9.15.1 | 2019-06-11 | dev deprecation | no | trust-anchor-5011 | To clarify the configuration of DNSSEC keys, | - | n/a |
| 9.14.4 | 2019-07-09 | support-added | no | rrsig | Collect metrics to report to the statistics-channel | - | n/a |
| 9.15.2 | 2019-07-10 | dev default-changed | yes | dnskey | The default size for RSA keys is now 2048 bits, | - | n/a |
| 9.15.3 | 2019-08-12 | dev support-added | no | rrsig | The normal (non-debugging) output of dnssec-signzone | - | n/a |
| 9.15.3 | 2019-08-12 | dev removal | no | trust-anchor-5011 | DNSSEC Lookaside Validation (DLV) is now obsolete; | - | n/a |
| 9.14.8 | 2019-11-06 | default-changed | yes | validation | NSEC Aggressive Cache ("synth-from-dnssec") has been | - | n/a |
| 9.15.6 | 2019-11-17 | dev support-added | no | rrsig | A new "dnssec-policy" option has been added to | - | n/a |
| 9.15.6 | 2019-11-17 | dev support-added | no | ds-digest | Trust anchors can now be configured using DS | - | n/a |
| 9.15.7 | 2019-12-13 | dev support-added | no | trust-anchor-5011 | Renamed "dnssec-keys" configuration statement | - | n/a |
| 9.15.8 | 2020-01-16 | dev support-added | no | trust-anchor-5011 | Key-style trust anchors and DS-style trust anchors | - | n/a |
| 9.16.0 | 2020-02-12 | support-added | no | alg-rsa-sha2 | Update dnssec-policy configuration statements: | - | n/a |
| 9.17.0 | 2020-03-12 | dev support-added | no | trust-anchor-5011 | "rndc nta -d" and "rndc secroots" now include | - | n/a |
| 9.16.3 | 2020-05-06 | support-added | no | alg-eddsa | Update PKCS#11 EdDSA implementation to PKCS#11 v3.0. | - | n/a |
| 9.16.3 | 2020-05-06 | support-added | no | alg-ecdsa | Add engine support to OpenSSL ECDSA implementation. | - | n/a |
| 9.16.3 | 2020-05-06 | support-added | no | alg-eddsa | Add engine support to OpenSSL EdDSA implementation. | - | n/a |
| 9.17.2 | 2020-06-10 | dev deprecation | no | trust-anchor-5011 | delv failed to parse deprecated trusted-keys-style | - | n/a |
| 9.17.2 | 2020-06-10 | dev support-added | no | ds-digest | Reject DS records at the zone apex when loading | - | n/a |
| 9.17.3 | 2020-07-03 | dev support-added | no | other | Add 'rndc dnssec -status' command. [GL #1612] | - | n/a |
| 9.17.3 | 2020-07-03 | dev support-added | no | other | Added "primaries" as a synonym for "masters" in | - | n/a |
| 9.11.22 | 2020-08-06 | support-added | no | trust-anchor-5011 | Added fallback to built-in trust-anchors, managed-keys, | - | n/a |
| 9.17.5 | 2020-09-04 | dev support-added | no | ds-digest | Add 'rndc dnssec -checkds' command, which signals to | - | n/a |
| 9.17.5 | 2020-09-04 | dev support-added | no | dnskey | Add '-P ds' and '-D ds' arguments to dnssec-settime. | - | n/a |
| 9.17.5 | 2020-09-04 | dev support-added | no | cds-cdnskey | Log CDS/CDNSKEY publication. [GL #1748] | - | n/a |
| 9.17.6 | 2020-10-12 | dev support-added | no | rrsig | Add 'rndc dnssec -rollover' command to trigger a manual | - | n/a |
| 9.17.8 | 2020-12-07 | dev support-added | no | nsec3 | Add NSEC3 support to KASP. A new option for | - | n/a |
| 9.17.9 | 2021-01-11 | dev support-added | no | rrsig | dnssec-signzone and named now log a warning when falling | - | n/a |
| 9.17.9 | 2021-01-11 | dev support-added | no | cds-cdnskey | When switching to "dnssec-policy none;", named now | - | n/a |
| 9.17.10 | 2021-02-04 | dev default-changed | yes | other | The default value of "max-stale-ttl" has been changed | - | n/a |
| 9.17.10 | 2021-02-04 | dev support-added | no | other | Make "check-names" accept A records below "_spf", | - | n/a |
| 9.17.11 | 2021-03-11 | dev removal | no | rrsig | Add a new "purge-keys" option for "dnssec-policy". This | - | n/a |
| 9.16.16 | 2021-05-12 | support-added | no | other | Implement draft-vandijk-dnsop-nsec-ttl, updating the | - | n/a |
| 9.16.16 | 2021-05-12 | support-added | no | nsec3-iterations | Reduce the maximum supported number of NSEC3 iterations | - | n/a |
| 9.16.16 | 2021-05-12 | support-added | no | nsec3-iterations | Treat DNSSEC responses containing NSEC3 records with | - | n/a |
| 9.16.16 | 2021-05-12 | support-added | no | other | Update the implementation of the ZONEMD RR type to match | - | n/a |
| 9.16.16 | 2021-05-12 | support-added | no | validation | Add a new built-in KASP, "insecure", which is used to | - | n/a |
| 9.16.19 | 2021-07-09 | support-added | no | rrsig | KASP support was extended with the "check DS" feature. | - | n/a |
| 9.16.20 | 2021-08-10 | support-added | no | cds-cdnskey | Relax the checks in the dns_zone_cdscheck() function to | - | n/a |
| 9.17.17 | 2021-08-10 | dev support-added | no | other | Previously, named accepted FORMERR responses both with | - | n/a |
| 9.16.21 | 2021-09-07 | support-added | no | rrsig | dnssec-signzone now honors Predecessor and Successor | - | n/a |
| 9.16.21 | 2021-09-07 | support-added | no | rrsig | Data structures holding DNSSEC signing statistics are | - | n/a |
| 9.17.18 | 2021-09-07 | dev deprecation | no | alg-rsa-sha2 | dnssec-cds now only generates SHA-2 DS records by | - | n/a |
| 9.17.19 | 2021-10-13 | dev support-added | no | other | Require the "dot" Application-Layer Protocol Negotiation | - | n/a |
| 9.17.20 | 2021-11-05 | dev default-changed | yes | dnskey | Change default of 'dnssec-dnskey-kskonly' to 'yes'. | - | n/a |
| 9.17.20 | 2021-11-05 | dev support-added | no | nsec3-iterations | Update "nsec3param" defaults to iterations 0, salt | - | n/a |
| 9.17.21 | 2021-12-06 | dev support-added | no | rrsig | Assign HTTP freshness lifetime to responses sent | - | n/a |
| 9.17.21 | 2021-12-06 | dev support-added | no | validation | Restore NSEC Aggressive Cache ("synth-from-dnssec") | - | n/a |
| 9.17.22 | 2022-01-12 | dev support-added | no | alg-ecdsa | Use ECDSA P-256 instead of a 4096-bit RSA when | - | n/a |
| 9.19.0 | 2022-04-11 | dev support-added | no | rrsig | New option '-J' for dnssec-signzone and dnssec-verify | - | n/a |
| 9.19.0 | 2022-04-11 | dev support-added | no | dnskey | Key timing options for `dnssec-keygen` and | - | n/a |
| 9.19.0 | 2022-04-11 | dev support-added | no | other | Add support for remote TLS certificates | - | n/a |
| 9.19.1 | 2022-05-09 | dev support-added | no | cds-cdnskey | The OID embedded at the start of a PRIVATEOID public | - | n/a |
| 9.19.1 | 2022-05-09 | dev support-added | no | rrsig | Check the algorithm name or OID embedded at the start | - | n/a |
| 9.19.2 | 2022-06-02 | dev support-added | no | dnskey | Key timing options for `dnssec-settime` and related | - | n/a |
| 9.19.2 | 2022-06-02 | dev support-added | no | rrsig | Add some more dnssec-policy checks to detect weird | - | n/a |
| 9.19.2 | 2022-06-02 | dev removal | no | other | Simplify BIND's internal DNS name compression API. As | - | n/a |
| 9.19.2 | 2022-06-02 | dev support-added | no | other | Don't try to process DNSSEC-related and ZONEMD records | - | n/a |
| 9.19.3 | 2022-07-07 | dev default-changed | yes | nsec3-iterations | Changed dnssec-signzone -H default to 0 additional | - | n/a |
| 9.19.4 | 2022-08-04 | dev deprecation | no | rrsig | The use of the "max-zone-ttl" option in "zone" and | - | n/a |
| 9.19.5 | 2022-09-08 | dev support-added | no | rrsig | Zones with dnssec-policy now require dynamic DNS or | - | n/a |
| 9.19.5 | 2022-09-08 | dev support-added | no | nsec3 | Change dnssec-policy to allow graceful transition from | - | n/a |
| 9.19.6 | 2022-10-10 | dev support-added | no | rrsig | Extend dig to allow requests to be signed using SIG(0) | - | n/a |
| 9.19.6 | 2022-10-10 | dev support-added | no | other | 'named -V' now reports the list of supported | - | n/a |
| 9.19.8 | 2022-12-12 | dev support-added | no | nsec3 | Change NSEC3PARAM TTL to match the SOA MINIMUM. | - | n/a |
| 9.19.8 | 2022-12-12 | dev removal | no | other | Remove dynamic update DNSSEC management feature. | - | n/a |
| 9.19.8 | 2022-12-12 | dev deprecation | no | rrsig | Deprecate 'auto-dnssec'. [GL #3667] | - | n/a |
| 9.19.8 | 2022-12-12 | dev support-added | no | ds-digest | Reject zones which have DS records not at delegation | - | n/a |
| 9.19.11 | 2023-03-03 | dev support-added | no | cds-cdnskey | Add 'cds-digest-types' configuration option. Also allow | - | n/a |
| 9.19.12 | 2023-04-11 | dev support-added | no | validation | The new "delv +ns" option activates name server mode, | - | n/a |
| 9.19.14 | 2023-06-09 | dev support-added | no | dnskey | Add 'cdnskey' configuration option. [GL #4050] | - | n/a |
| 9.19.14 | 2023-06-09 | dev support-added | no | rrsig | Add support for the multi-signer model 2 (RFC 8901) when | - | n/a |
| 9.19.15 | 2023-07-06 | dev support-added | no | rrsig | Change function 'find_zone_keys()' to look for signing | - | n/a |
| 9.19.16 | 2023-08-04 | dev support-added | no | other | Reduce query-response latency by making recursive | - | n/a |
| 9.19.16 | 2023-08-04 | dev removal | no | rrsig | Don't add signing records for DNSKEY added with dynamic | - | n/a |
| 9.19.16 | 2023-08-04 | dev removal | no | rrsig | Remove 'auto-dnssec'. This obsoletes the configuration | - | n/a |
| 9.19.16 | 2023-08-04 | dev support-added | no | rrsig | Add inline-signing to dnssec-policy. [GL #3677] | - | n/a |
| 9.19.17 | 2023-09-08 | dev support-added | no | alg-ecdsa | Fixes to provider/engine based ECDSA key handling. | - | n/a |
| 9.19.17 | 2023-09-08 | dev deprecation | no | other | Deprecate the 'dnssec-must-be-secure' option. | - | n/a |
| 9.19.18 | 2023-11-09 | dev support-added | no | other | Added options to the QP trie that will be needed | - | n/a |
| 9.19.18 | 2023-11-09 | dev support-added | no | rrsig | The zone option 'inline-signing' is ignored from now | - | n/a |
| 9.19.19 | 2023-12-08 | dev support-added | no | nsec3-iterations | Lower the maximum number of allowed NSEC3 iterations, | - | n/a |
| 9.19.21 | 2024-02-02 | dev support-added | no | trust-anchor-5011 | The "trust-anchor-telemetry" statement is no longer | - | n/a |
| 9.19.22 | 2024-03-12 | dev support-added | no | rrsig | Add HSM support for dnssec-policy. You can now | - | n/a |
| 9.19.22 | 2024-03-12 | dev deprecation | no | trust-anchor-5011 | The 'dnssec-validation yes' option now requires an | - | n/a |
| 9.19.24 | 2024-05-03 | dev support-added | no | rrsig | Implement signature jitter for dnssec-policy. [GL #4554] | - | n/a |
| 9.19.24 | 2024-05-03 | dev support-added | no | rrsig | Don't count expired / future RRSIGs in verification | - | n/a |
| 9.19.24 | 2024-05-03 | dev support-added | no | dnskey | Allow 'dnssec-keygen' options '-f' and '-k' to be used | - | n/a |
| 9.19.24 | 2024-05-03 | dev support-added | no | rrsig | Introduce 'dnssec-ksr', a DNSSEC tool to create | - | n/a |
| 9.21.1 | 2024-09-09 | dev support-added | no | cds-cdnskey | Support for Offline KSK implemented. ``bfa206beecc`` | - | n/a |
| 9.21.1 | 2024-09-09 | dev support-added | no | trust-anchor-5011 | Support restricted key tag range when generating new keys. ``d40b722d462`` | - | n/a |
| 9.21.1 | 2024-09-09 | dev support-added | no | alg-ecdsa | Use deterministic ecdsa for openssl >= 3.2. ``069c6c22654`` | - | n/a |
| 9.20.2 | 2024-09-09 | support-added | no | cds-cdnskey | Support for Offline KSK implemented. ``3555094a686`` | - | n/a |
| 9.20.2 | 2024-09-09 | support-added | no | trust-anchor-5011 | Support restricted key tag range when generating new keys. ``d0899632635`` | - | n/a |
| 9.21.2 | 2024-10-07 | dev removal | no | rrsig | Remove statslock from dnssec-signzone. ``f466e32fdb1`` | - | n/a |
| 9.20.3 | 2024-10-07 | removal | no | rrsig | Remove statslock from dnssec-signzone. ``12eb16186ff`` | - | n/a |
| 9.18.31 | 2024-10-07 | removal | no | rrsig | Remove statslock from dnssec-signzone. ``5c51e044c42`` | - | n/a |
| 9.21.3 | 2024-12-03 | dev support-added | no | other | Implement RFC 9567: EDNS Report-Channel option. ``e1588022c1`` | - | n/a |
| 9.21.3 | 2024-12-03 | dev support-added | no | trust-anchor-5011 | Update bind.keys with the new 2025 IANA root key. ``63ee8979a7`` | - | n/a |
| 9.21.3 | 2024-12-03 | dev removal | no | cds-cdnskey | Dnssec-ksr now supports KSK rollovers. ``675a7f0166`` | - | n/a |
| 9.20.4 | 2024-12-03 | support-added | no | trust-anchor-5011 | Update bind.keys with the new 2025 IANA root key. ``1f988e2cc7`` | - | n/a |
| 9.20.4 | 2024-12-03 | removal | no | cds-cdnskey | Dnssec-ksr now supports KSK rollovers. ``834c04fc77`` | - | n/a |
| 9.18.32 | 2024-12-03 | support-added | no | trust-anchor-5011 | Update bind.keys with the new 2025 IANA root key. ``1303fe5ea0`` | - | n/a |
| 9.18.32 | 2024-12-03 | support-added | no | nsec3 | Revert "Fix NSEC3 closest encloser lookup for names with empty non-terminals" ``56d1ccbdba`` | - | n/a |
| 9.21.4 | 2025-01-20 | dev removal | no | other | Remove dnssec-must-be-secure feature. ``f5f792f1ed2`` | - | n/a |
| 9.21.4 | 2025-01-20 | dev removal | no | trust-anchor-5011 | Remove trusted-keys and managed-keys options. ``9de6b228d41`` | - | n/a |
| 9.21.4 | 2025-01-20 | dev support-added | no | validation | Use query counters in validator code. ``63060314098`` | - | n/a |
| 9.20.5 | 2025-01-20 | support-added | no | nsec3 | Revert "Fix NSEC3 closest encloser lookup for names with empty non-terminals" ``993cb761489`` | - | n/a |
| 9.20.5 | 2025-01-20 | support-added | no | validation | Use query counters in validator code. ``d91835160a2`` | - | n/a |
| 9.18.33 | 2025-01-20 | support-added | no | validation | Use query counters in validator code. ``b1207ea9ed6`` | - | n/a |
| 9.21.5 | 2025-02-11 | dev support-added | no | validation | Adds support for EDE code 1 and 2. ``5a8fce4851b`` | - | n/a |
| 9.20.6 | 2025-02-11 | support-added | no | validation | Adds support for EDE code 1 and 2. ``b3eab79bc18`` | - | n/a |
| 9.21.6 | 2025-03-11 | dev support-added | no | rrsig | Add digest methods for SIG and RRSIG. ``fd48df20f3`` | - | n/a |
| 9.21.6 | 2025-03-11 | dev support-added | no | other | Drop malformed notify messages early instead of decompressing them. ``7fce7707db`` | - | n/a |
| 9.21.6 | 2025-03-11 | dev default-changed | yes | other | Use named Service Parameter Keys (SvcParamKeys) by default. ``3f61a87be3`` | - | n/a |
| 9.20.7 | 2025-03-11 | support-added | no | rrsig | Add digest methods for SIG and RRSIG. ``6d8c513986`` | - | n/a |
| 9.18.35 | 2025-03-11 | support-added | no | rrsig | Add digest methods for SIG and RRSIG. ``7f4023fe7d`` | - | n/a |
| 9.21.7 | 2025-04-09 | dev support-added | no | other | Add support for EDE 20 (Not Authoritative) ``45ee3715e1`` | - | n/a |
| 9.21.7 | 2025-04-09 | dev support-added | no | validation | Add support for EDE 7 and EDE 8. ``e66dc07c68`` | - | n/a |
| 9.21.7 | 2025-04-09 | dev removal | no | dnskey | Remove unnecessary options in dnssec-keygen and dnssec-keyfromlabel. ``b0f8b443c9`` | - | n/a |
| 9.21.7 | 2025-04-09 | dev support-added | no | validation | When forwarding, query with CD=0 first. ``25c91dffcc`` | - | n/a |
| 9.20.8 | 2025-04-09 | support-added | no | other | Add support for EDE 20 (Not Authoritative) ``f8a293aa11`` | - | n/a |
| 9.20.8 | 2025-04-09 | support-added | no | validation | Add support for EDE 7 and EDE 8. ``27442c3104`` | - | n/a |
| 9.21.10 | 2025-07-04 | dev default-changed | yes | alg-rsa-sha2 | "Add code paths to fully support PRIVATEDNS and PRIVATEOID keys" ``119f511a458`` | - | n/a |
| 9.21.10 | 2025-07-04 | dev support-added | no | other | Use RCU for rad name. ``32e86ed6434`` | - | n/a |
| 9.18.39 | 2025-08-13 | deprecation | no | cds-cdnskey | Add deprecation warnings for RSASHA1, RSASHA1-NSEC3SHA1 and DS digest type 1. ``1ea4164f71`` | - | n/a |
| 9.20.12 | 2025-08-13 | deprecation | no | cds-cdnskey | Add deprecation warnings for RSASHA1, RSASHA1-NSEC3SHA1 and DS digest type 1. ``5aefaa4b97`` | - | n/a |
| 9.21.11 | 2025-08-13 | dev deprecation | no | cds-cdnskey | Add deprecation warnings for RSASHA1, RSASHA1-NSEC3SHA1 and DS digest type 1. ``c407f3c12a`` | - | n/a |
| 9.21.11 | 2025-08-13 | dev support-added | no | rrsig | Extract the resigning heap into a separate struct. ``512f1d3005`` | - | n/a |
| 9.21.11 | 2025-08-13 | dev support-added | no | other | Prepend qpkey with namespace (normal vs denial of existence) ``15653c54a0`` | - | n/a |
| 9.21.12 | 2025-09-04 | dev support-added | no | rrsig | Add manual mode configuration option to dnsec-policy. ``888b5f55a8`` | - | n/a |
| 9.20.13 | 2025-09-04 | support-added | no | rrsig | Add manual mode configuration option to dnsec-policy. ``1e435b107f`` | - | n/a |
| 9.21.14 | 2025-10-18 | dev support-added | no | rrsig | Add dnssec-policy keys configuration check to named-checkconf. ``23a79b42ea4`` | - | n/a |
| 9.21.14 | 2025-10-18 | dev support-added | no | rrsig | Add a circular reference between slabtops for type and RRSIG(type) ``a20c8fe74b0`` | - | n/a |
| 9.21.14 | 2025-10-18 | dev support-added | no | cds-cdnskey | Convert slabtop and slabheader to use the cds list. ``7443ff330cc`` | - | n/a |
| 9.21.14 | 2025-10-18 | dev removal | no | other | Squash the qpcache tree and nsec tries. ``22803b93e3f`` | - | n/a |
| 9.20.15 | 2025-10-18 | support-added | no | rrsig | Add dnssec-policy keys configuration check to named-checkconf. ``1f5a0405f72`` | - | n/a |
| 9.21.15 | 2025-11-07 | dev support-added | no | other | Add support for Extended DNS Error 24 (Invalid Data) ``4941d33a8ae`` | - | n/a |
| 9.21.16 | 2025-12-09 | dev support-added | no | rrsig | Improve output of 'rndc dnssec -status' ``814f7a72cd`` | - | n/a |
| 9.21.16 | 2025-12-09 | dev support-added | no | other | Change the QNAME minimization algorithm to follow the standard. ``15494053b1`` | - | n/a |
| 9.21.16 | 2025-12-09 | dev support-added | no | rrsig | Add RRSIG if required as soon as they are found. ``2955bb90c8`` | - | n/a |
| 9.21.17 | 2026-01-09 | dev support-added | no | ds-digest | Add support for Extended DNS Error 9 (Missing DNSKEY) ``fe456b47f9`` | - | n/a |
| 9.21.17 | 2026-01-09 | dev support-added | no | cds-cdnskey | Add support for Generalized DNS Notifications. ``9696da5f24`` | - | n/a |
| 9.21.17 | 2026-01-09 | dev support-added | no | other | Add Extended DNS Error 13 (Cached Error) support. ``8055747146`` | - | n/a |
| 9.21.18 | 2026-02-04 | dev support-added | no | validation | Lowercase the NSEC next owner name when signing. ``dd8651ff36`` | - | n/a |
| 9.21.18 | 2026-02-04 | dev deprecation | no | alg-ecdsa | Initial openssl version splitting. ``fe9fee63c6`` | - | n/a |
| 9.21.19 | 2026-02-26 | dev support-added | no | nsec3 | Invalid NSEC3 can cause OOB read of the isdelegation() stack. ``d8be931c491`` | - | n/a |
| 9.20.20 | 2026-02-26 | support-added | no | nsec3 | Invalid NSEC3 can cause OOB read of the isdelegation() stack. ``e6f234169e2`` | - | n/a |
| 9.18.46 | 2026-02-26 | support-added | no | nsec3 | Invalid NSEC3 can cause OOB read of the isdelegation() stack. ``97fd0c56e48`` | - | n/a |
| 9.21.21 | 2026-03-31 | dev removal | no | dnskey | Remove -C option from dnssec-keygen and dnssec-keyfromlabel. ``864932a15ec`` | - | n/a |
| 9.21.22 | 2026-05-08 | dev removal | no | rrsig | Remove obsolete KEY record flags deprecated by RFC 3445. ``1535b32dab`` | - | n/a |
| 9.21.22 | 2026-05-08 | dev support-added | no | nsec3 | Change NSEC3 and NSEC3PARAM rdata struct fields to use isc_region_t. ``245c71dfac`` | - | n/a |
| 9.21.22 | 2026-05-08 | dev support-added | no | rrsig | Fix off by one error in dnssec-ksr sign. ``ae739daec2`` | - | n/a |
| 9.21.22 | 2026-05-08 | dev support-added | no | other | Harden GSS-API context establishment in TKEY negotiation. ``9212e1ac50`` | - | n/a |
| 9.21.22 | 2026-05-08 | dev support-added | no | other | Implement RFC 3645 Section 4.1.1 key expiry check in TKEY. ``6b6913c83b`` | - | n/a |
| 9.21.22 | 2026-05-08 | dev default-changed | yes | rrsig | Use the zone file's basename as origin in DNSSEC tools. ``08fa344014`` | - | n/a |
| 9.20.23 | 2026-05-08 | removal | no | rrsig | Remove obsolete KEY record EXTENDED flag deprecated by RFC 3445. ``99c226576a`` | - | n/a |
| 9.20.23 | 2026-05-08 | support-added | no | rrsig | Fix off by one error in dnssec-ksr sign. ``819df0d19e`` | - | n/a |
| 9.20.23 | 2026-05-08 | default-changed | yes | rrsig | Use the zone file's basename as origin in DNSSEC tools. ``097c14da45`` | - | n/a |
| 9.21.23 | 2026-06-08 | dev removal | no | rrsig | Remove legacy special handling for SIG, NXT, and KEY records. ``ac342bf652`` | - | n/a |
| 9.21.23 | 2026-06-08 | dev support-added | no | validation | Fix a resolver stall on a CNAME response to a DS query. ``ed3a16bea8`` | - | n/a |
| 9.21.23 | 2026-06-08 | dev support-added | no | ds-digest | Consolidate the validator's DS fetches into one helper. ``4ff4e1346e`` | - | n/a |
| 9.20.24 | 2026-06-08 | removal | no | other | Remove ineffective TCP fallback after repeated UDP timeouts. ``eb13adcb47`` | - | n/a |
| 9.20.24 | 2026-06-08 | support-added | no | validation | Fix a resolver stall on a CNAME response to a DS query. ``1407f48670`` | - | n/a |
| 9.18.50 | 2026-06-08 | removal | no | other | Remove ineffective TCP fallback after repeated UDP timeouts. ``9b53e4be29`` | - | n/a |
| 9.21.24 | 2026-07-13 | dev removal | no | validation | Remove the secondary validator in query.c. ``1fe179973e2`` | - | n/a |
| 9.21.24 | 2026-07-13 | dev support-added | no | cds-cdnskey | Support larger DNSSEC keys and signatures. ``eed44c38762`` | - | n/a |
| 9.20.26 | 2026-07-20 | removal | no | validation | Remove the secondary validator in query.c. ``1687a3d0b85`` | - | n/a |
| 9.21.25 | 2026-08-05 | dev support-added | no | trust-anchor-5011 | Disclose active Negative Trust Anchors with Extended DNS Error 33. ``8dae0a8cda5`` | - | n/a |
| 9.21.25 | 2026-08-05 | dev removal | no | nsec3 | Remove unused closest encloser proof caching. ``de7f34fb44b`` | - | n/a |
| 9.20.27 | 2026-08-05 | support-added | no | trust-anchor-5011 | Disclose active Negative Trust Anchors with Extended DNS Error 33. ``566e7018278`` | - | n/a |
| 9.21.26 | 2026-09-03 | dev removal | no | other | Remove the RFC 1918 reverse-lookup leakage warning. ``8f7874ed58`` | - | n/a |
| 9.21.26 | 2026-09-03 | dev support-added | no | alg-eddsa | Reject oversized and malformed DNSKEY records up front. ``68f2385175`` | - | n/a |
| 9.21.26 | 2026-09-03 | dev support-added | no | rrsig | Reject out-of-zone records in zone transfers and zone files. ``2d8fda350b`` | - | n/a |
| 9.21.26 | 2026-09-03 | dev removal | no | other | Remove nodep from the dns_db_find() API. ``2c0c3bf87c`` | - | n/a |
| 9.21.26 | 2026-09-03 | dev default-changed | yes | trust-anchor-5011 | Honor DNSSEC policy key tag ranges. ``05b463c2cc`` | - | n/a |
| 9.20.29 | 2026-09-11 | removal | no | nsec3 | Remove unused closest encloser proof caching. ``abd8b5bfd8`` | - | n/a |
| 9.20.29 | 2026-09-11 | support-added | no | alg-eddsa | Reject oversized and malformed DNSKEY records up front. ``6c22109924`` | - | n/a |
| 9.20.29 | 2026-09-11 | default-changed | yes | trust-anchor-5011 | Honor DNSSEC policy key tag ranges. ``b82e5834b7`` | - | n/a |

384 rows. `(!)` marks a commit not contained in the tag; `n/a` = no commit found by message grep (entry is still at the tag). "dev" prefix = development-branch release (stable:false); the first stable release carrying the entry is in the JSON `first_stable_tag`.

## Default changes (before / after) and limit changes

Every row is backed by the commit(s) listed; `first tag` = earliest tag of any kind containing the commit, `first stable` = earliest stable tag. Verify a row with:

```
C=out/software_repos/bind9.git
git -C $C show --stat <commit>                       # file list: the product file must not be under bin/tests/
git -C $C tag --contains <commit> | grep -x <first stable>
git -C $C show <first stable>:<file> | grep -n <value>   # value after (and <previous tag>:<file> for before)
```

Items d01-d04 predate 2012-03 (cvs2git-manufactured tags): `git tag --contains` lists tags that do not carry the change, so the first tag was established by tree content instead (see the note column). A commit that only edits `bin/tests/system/*` would be a test fixture, not a product default; none of the rows below is fixture-only (file lists in the JSON `commits[].files`, `touches_test_fixture_only` = false).

| id | kind | change | before | after | on upgrade | opt-in | commit(s) | first tag | first stable |
|---|---|---|---|---|---|---|---|---|---|
| d01-validation-default-yes | default-changed | Built-in default of the dnssec-validation option flipped from "no" (9.4.x / 9.5.0) to "yes". "yes" only validates when trusted-keys/managed-keys are configured; no built-in root key existed yet, so most unconfigured servers still did not validate. | dnssec-validation no; | dnssec-validation yes; | yes | no | 1bff2d56a0 | v9.5.0-P1 (2008-05-28) | v9.5.0-P1 (2008-05-28) |
| d02-keygen-default-alg-rsasha1 | default-changed | dnssec-keygen gained default arguments: without -a it generates a 1024-bit RSASHA1 ZSK, or a 2048-bit RSASHA1 KSK with -f KSK. | no default algorithm; -a required | RSASHA1, 1024-bit ZSK / 2048-bit KSK | yes | no | b272d38cc5 | v9.7.0a1 (2009-06-18) | v9.7.0 (2010-02-16) |
| d03-signzone-nsec3-iterations-100-to-10 | default-changed | Default number of additional NSEC3 iterations used by dnssec-signzone (-H) reduced from 100 to 10. | nsec3iter = 100U | nsec3iter = 10U | yes | no | a93a66f618 | v9.7.0b1 (2009-10-19) | v9.7.0 (2010-02-16) |
| d04-root-trust-anchor-builtin | default-changed | A built-in root-zone trust anchor (bind.keys, managed via RFC 5011) was added; it is used only when "dnssec-validation auto;" is configured. | no built-in trust anchor; validation needs trusted-keys/managed-keys | built-in root key available via "dnssec-validation auto;" | no | yes | 79bf7c874b | v9.8.0b1 (2011-01-23) | v9.8.0 (2011-02-21) |
| d05-builtin-root-ksk-2017 | default-changed | CHANGES 4564: built-in managed keys updated to include the upcoming root KSK-2017 (CHANGES 4564 says only "the upcoming root KSK", RT #44579) ahead of the later rollover. Backported to every maintained branch as separate commits. | bind.keys without the upcoming root KSK | bind.keys with the upcoming root KSK | no | yes | 00a83c64d7, b5ad091624, 3984c8da30, 9543825c15, 3d63f9d813, 4e47688455, 95f9b9a078 | v9.10.5rc1 (2017-02-06) | v9.9.9-P8 (2017-03-29) |
| d06-keygen-no-default-alg | removal | dnssec-keygen and dnssec-keyfromlabel no longer default to RSASHA1 (NSEC3RSASHA1 with -3); -a is mandatory. Scripts relying on the default fail. | RSASHA1 (1024/2048) when -a omitted | error: algorithm must be given with -a | yes | no | 45afdb2672 | v9.12.0a1 (2017-09-11) | v9.12.0 (2018-01-17) |
| d07-validation-auto-default | default-changed | Built-in default of dnssec-validation changed from "yes" to "auto": validation is on by default using the built-in IANA root trust anchor, with RFC 5011 managed-keys maintenance. | dnssec-validation yes; (validates only with explicitly configured keys) | dnssec-validation auto; (built-in root key) | yes | no | bef18ecac6 | v9.13.1 (2018-06-09) | v9.14.0 (2019-03-20) |
| d08-rsamd5-removed | removal | RSAMD5 (algorithm 1) support removed entirely (a later commit 9b78f78c69, 2025-10-16, "Restore RSAMD5 tag computation", is not a re-enablement). | RSAMD5 supported (explicit -a RSAMD5 to generate; validation accepted it) | RSAMD5 unsupported | yes | no | e69dc0dbc7 | v9.13.6 (2019-02-06) | v9.14.0 (2019-03-20) |
| d09-gost-removed | removal | ECC-GOST (algorithm 12, GOST R 34.11-94) support removed. | GOST supported (optional build) | GOST unsupported | yes | no | 27593e65dc | v9.13.1 (2018-06-09) | v9.14.0 (2019-03-20) |
| d10-dsa-removed | removal | DSA (algorithm 3) and DSA-NSEC3-SHA1 (algorithm 6) support removed; algorithm numbers kept only as name mapping. | DSA algorithms supported | DSA algorithms unsupported | yes | no | d6c50674bb | v9.13.4 (2018-11-22) | v9.14.0 (2019-03-20) |
| d11-synth-from-dnssec-off-9.14 | default-changed | NSEC aggressive cache (synth-from-dnssec) disabled by default in the 9.14 stable branch after a performance problem. | synth-from-dnssec yes; | synth-from-dnssec no; | yes | no | b97004be30 | v9.14.8 (2019-11-06) | v9.14.8 (2019-11-06) |
| d12-synth-from-dnssec-restored-9.18 | default-changed | synth-from-dnssec restored to yes as the default (9.18 line); 9.16 stayed at no. | synth-from-dnssec no; | synth-from-dnssec yes; | yes | no | 90dbdb2cb5 | v9.17.21 (2021-12-06) | v9.18.0 (2022-01-24) |
| d13-ds-cds-sha1-dropped | default-changed | SHA-1 DS/CDS digests are no longer generated by default: dnssec-dsfromkey emits SHA-256 only (was SHA-1 and SHA-256 both), dnssec-signzone dsset files and named-generated CDS records carry SHA-256 only. | DS/CDS: SHA-1 + SHA-256 | DS/CDS: SHA-256 only | yes | no | 796a6c4e4e, 8785f6fa34, d8f2eb249a | v9.15.0 (2019-05-10) | v9.16.0 (2020-02-12) |
| d14-keygen-rsa-zsk-2048 | default-changed | Default RSA ZSK size in dnssec-keygen raised from 1024 to 2048 bits (KSK was already 2048). | RSA ZSK 1024-bit / KSK 2048-bit | RSA 2048-bit for both | yes | no | 24f23e7fad | v9.15.2 (2019-07-10) | v9.16.0 (2020-02-12) |
| d15-dnssec-policy-default-ecdsap256 | support-added | Built-in dnssec-policy "default": a single CSK (KSK+ZSK roles, unlimited lifetime) with algorithm 13 ECDSAP256SHA256, no explicit key size. The built-in policy "none" is the default for zones (dnssec-policy is opt-in per zone). | no built-in policy (external dnssec-keymgr) | dnssec-policy "default": csk lifetime unlimited algorithm ECDSAP256SHA256 | no | yes | 7bfac50336, a339a6df48 | v9.15.6 (2019-11-17) | v9.16.0 (2020-02-12) |
| d16-dnssec-policy-default-key-size-2048 | default-changed | kasp default RSA key size: ZSK 1024 -> 2048 (KSK stayed 2048). Only relevant when a policy names an RSA algorithm without a size; the built-in policy uses ECDSAP256SHA256. | RSA ZSK 1024-bit / KSK 2048-bit | RSA 2048-bit for both roles | no | yes | 0f9d45a5b8 | v9.15.7 (2019-12-13) | v9.16.0 (2020-02-12) |
| d17-nsec3param-default-in-policy | support-added | dnssec-policy gained "nsec3param"; when given without parameters it defaulted to 5 iterations and an 8-byte salt. | no NSEC3 in dnssec-policy | nsec3param iterations 5 salt-length 8 | no | yes | 008e84e965 | v9.16.10 (2020-12-07) | v9.16.10 (2020-12-07) |
| d18-nsec3param-default-0-0 | default-changed | Default nsec3param parameters in dnssec-policy changed to zero additional iterations and no salt (RFC 9276 / draft-ietf-dnsop-nsec3-guidance). | iterations 5, salt-length 8 (DEFAULT_NSEC3PARAM_ITER 5, SALTLEN 8) | iterations 0, salt-length 0 | yes | yes | 8f324b4717 | v9.17.20 (2021-11-05) | v9.18.0 (2022-01-24) |
| d19-dnskey-kskonly-yes | default-changed | dnssec-dnskey-kskonly default changed from no to yes: with auto-dnssec the DNSKEY RRset is signed only by KSKs. | dnssec-dnskey-kskonly no; | dnssec-dnskey-kskonly yes; | yes | no | 2abad4d969 | v9.17.20 (2021-11-05) | v9.18.0 (2022-01-24) |
| d20-dnssec-cds-sha2-only | default-changed | dnssec-cds generates SHA-2 DS records by default, avoids copying deprecated SHA-1 records from the child, and derives SHA-2 DS from CDNSKEY when the child publishes no SHA-2 CDS. | copies SHA-1 and SHA-2 CDS digests | SHA-2 only | yes | no | eabf898b36 | v9.17.18 (2021-09-07) | v9.18.0 (2022-01-24) |
| d21-signzone-nsec3-iterations-0 | default-changed | Default additional NSEC3 iterations of dnssec-signzone reduced from 10 to 0. | nsec3iter = 10U | nsec3iter = 0U | yes | no | 47c214644b, d029d6374d | v9.19.3 (2022-07-07) | v9.18.5 (2022-07-07) |
| d22-cdns-cdnskey-options | support-added | dnssec-policy gained "cds-digest-type" (default 2 = SHA-256) and "cdnskey" (default yes). Defaults equal the prior hard-coded behaviour, so publication defaults are unchanged; only configurability is new. | CDS SHA-256 and CDNSKEY published without options (per reference.rst text added by 8be61d1845: default yes) | cds-digest-type 2; cdnskey yes; (configurable) | no | yes | 2742fe656f, 8be61d1845 | v9.19.11 (2023-03-03) | v9.20.0 (2024-07-08) |
| d23-bindkeys-revoked-key-removed | other | Revoked root DNSKEY removed from bind.keys. No behavioural change for validation (key is revoked). | bind.keys carries revoked root key | revoked key removed | no | no | 3954d4ec30, d5c57db1ae, 0e805b58e8 | v9.14.1 (2019-04-06) | v9.14.1 (2019-04-06) |
| d24-bindkeys-root-2025-ds | default-changed | New IANA root key (key tag 38696; CHANGES subject: "Update bind.keys with the new 2025 IANA root key") added to bind.keys. | bind.keys without key 38696 | bind.keys with key 38696 | no | no | 089d0eb30a, 7045da6d6a, 609bf35075, a2f8b76c5e | v9.21.3 (2024-12-03) | v9.20.4 (2024-12-03) |
| l01-nsec3-max-iterations-150 | limit-changed | Maximum NSEC3 iterations reduced to a fixed 150 (was key-size dependent: 150 for keys <=1024 bits, 500 for <=2048, 2500 for <=4096). Zone configuration above 150 is rejected and validating resolvers treat NSEC3 answers with more than 150 iterations as insecure | max iterations 150/500/2500 depending on smallest DNSKEY size | max iterations 150 fixed | yes | no | 9324d2d295, 9170275738, 91a7f94a66 | v9.16.16 (2021-05-12) | v9.16.16 (2021-05-12) |
| l02-nsec3-max-iterations-50 | limit-changed | Validator and dnssec-signzone limit on NSEC3 iterations lowered from 150 to 50 on the main line only (answers above the limit are treated as insecure); dnssec-policy additionally refuses to load any non-zero iteration count (RFC 9276). | DNS_NSEC3_MAXITERATIONS 150 | DNS_NSEC3_MAXITERATIONS 50 | yes | no | ff4201e388, 75e0d394dd | v9.19.19 (2023-12-08) | v9.20.0 (2024-07-08) |
| l03-keytrap-validation-limits-9.16-9.18 | limit-changed | CVE-2023-50387 (KeyTrap) mitigation in the maintenance branches: DNS message validation stops at the first validation failure; validation work is moved to a separate slow task queue. | validator retried all key/signature combinations | fail on first validation failure | yes | no | 0add293477, 6a65a42528, c12608ca93 | v9.18.24 (2024-02-11) | v9.18.24 (2024-02-11) |
| l04-max-validations-per-fetch | limit-changed | New options capping DNSSEC validations (default 16) and validation failures (default 1) per resolver fetch; validation made asynchronous. | unbounded (per-fetch) | max-validations-per-fetch 16; max-validation-failures-per-fetch 1 | yes | no | 15096aefdf | v9.19.21 (2024-02-02) | v9.20.0 (2024-07-08) |

16 default-changed, 4 limit-changed, 4 removal, 3 support-added, 1 other (28 rows). Rows with `value_changed=false` (d22, d23) record new options / no-op edits whose default equals prior behaviour.

Rows added in Phase 5 (found by the Phase 4 verifier):

| d29-trust-anchor-telemetry-default-yes | default-changed | Trust-anchor telemetry (RFC 8145 key-tag signalling, _ta-XXXX queries) on by default. | no trust-anchor telemetry queries | trust-anchor-telemetry yes (named sends _ta-XXXX.<anchor>/NULL) | yes | no | f20179857a, b7161f9898 | v9.11.0b3 (2016-07-28) | v9.11.0 (2016-09-29) |
| d30-root-key-sentinel-default-yes | default-changed | Root key sentinel (RFC 8509) answering on by default. | no root-key-sentinel handling | root-key-sentinel yes | yes | no | 68e9315c7d, 3890b5d7ba | v9.13.0 (2018-05-22) | v9.9.13 (2018-07-03) |

Phase 5: d10 mechanism alg-rsa-sha2 -> other; d23 value_changed false -> true (bind.keys lost 19036 at v9.14.1).

### Notes per row

* **d01-validation-default-yes** basis: tree content: git show v9.5.0-P1:bin/named/config.c has "dnssec-validation yes;" and v9.5.0:bin/named/config.c has "dnssec-validation no;" (git tag --contains lists cvs2git tags that do not contain the change). Changelog: "The default value for dnssec-validation was changed to "yes" in 9.5.0-P1 and all subsequent releases; this was inadvertently omitted from CHANGES at the time." Note: sibling commit 3634531310 is the same change on the development trunk (first appears in 9.5.1b1 / later 9.6). The 2006 CHANGES 2007 entry announced the switch ("default dnssec-validation no; to be changed to yes in 9.5.0") but the code change landed only in 9.5.0-P1 and the CHANGES line was omitted until 9.5.0-P2.
* **d02-keygen-default-alg-rsasha1** basis: tree content: v9.7.0a1:CHANGES contains entry 2612 and v9.6.1/v9.5.2/v9.4.3-P3 do not; git tag --contains wrongly lists v9.4.3-P3 and v9.6.1-P1 (cvs2git ancestry). first stable tag with DEFAULT_ALGORITHM in dnssec-keygen.c is v9.7.0.
* **d03-signzone-nsec3-iterations-100-to-10** basis: tree content: git show v9.7.0b1:bin/dnssec/dnssec-signzone.c has "nsec3iter = 10U"; v9.4.3-P4, v9.5.2-P1, v9.6.1-P2 (listed by git tag --contains) do not; no stable tag between b1 and v9.7.0 has it. Changelog: "Reduce default NSEC3 iterations from 100 to 10. [RT #19970]"
* **d04-root-trust-anchor-builtin** basis: tree content: v9.8.0b1:CHANGES and v9.8.0:CHANGES contain the entry, v9.7.3 and v9.7.2-P3 do not (git tag --contains wrongly lists v9.7.3). Changelog: "Added a default trust anchor for the root zone, which can be switched on by setting "dnssec-validation auto;" in the named.conf options. [RT #21727]" Note: opt-in: default dnssec-validation stayed "yes" until 9.13.1 (d07).
* **d05-builtin-root-ksk-2017** basis: git tag --contains. Note: takes effect only under "dnssec-validation auto;" (built-in keys); earliest stable tag is the minimum over the seven per-branch commits.
* **d06-keygen-no-default-alg** basis: git tag --contains; tree content confirmed: v9.11.0:dnssec-keygen.c has DEFAULT_ALGORITHM, v9.12.0 does not. Changelog: "dnssec-keygen no longer uses RSASHA1 by default; the signing algorithm must be specified on the command line with the "-a" option.  Signing scripts that rely on the existing default behavior will brea"
* **d07-validation-auto-default** basis: git tag --contains. Changelog: "The default setting for "dnssec-validation" is now "auto", which activates DNSSEC validation using the IANA root key. (The default can be changed back to "yes", which activates DNSSEC validation only " Note: first appears in development release 9.13.1; stable users first see it in 9.14.0 (v9.14.0:bin/named/config.c uses VALIDATION_DEFAULT; v9.13.0 does not). Applies on upgrade to any named.conf that does not set dnssec-validation.
* **d08-rsamd5-removed** basis: git tag --contains. Note: no CHANGES line kept; release-note commit abe39991be "Add release notes for RSAMD5 removal". Earlier: RSAMD5 stopped being the RSA default for dnssec-keygen in 9.4.0 (commit 431e2ab380, CHANGES 1945).
* **d09-gost-removed** basis: git tag --contains. Changelog: "Remove support for ECC-GOST (GOST R 34.11-94). [GL #295]"
* **d10-dsa-removed** basis: git tag --contains. Changelog: "Remove support for DNSSEC algorithms 3 (DSA) and 6 (DSA-NSEC3-SHA1). [GL #22]"
* **d11-synth-from-dnssec-off-9.14** basis: git tag --contains. Changelog: "NSEC Aggressive Cache ("synth-from-dnssec") has been disabled by default because it was found to have a significant performance impact on the recursive service. [GL #1265]" Note: 9.14.8 is the first tag; the same change on master (a20c42dca6) reaches the 9.16 stable line at v9.16.0. v9.16.50:bin/named/config.c still has "synth-from-dnssec no;".
* **d12-synth-from-dnssec-restored-9.18** basis: git tag --contains. Note: CHANGES/release note commit 12c64d55f2 (GL #1265).
* **d13-ds-cds-sha1-dropped** basis: git tag --contains. Note: first tag is development 9.15.0; first stable is 9.16.0.
* **d14-keygen-rsa-zsk-2048** basis: git tag --contains. Changelog: "The default size for RSA keys is now 2048 bits, for both ZSKs and KSKs. [GL #1097]" Note: first tag is development 9.15.2; first stable is 9.16.0.
* **d15-dnssec-policy-default-ecdsap256** basis: git tag --contains. Changelog: none recorded (Phase 3 removed an unrelated GL #1593 line). Note: 7bfac50336 sets key->algorithm = DNS_KEYALG_ECDSA256 for the default kasp; a339a6df48 adds dnssec-policy.default.conf documenting "csk key-directory lifetime 0 algorithm 13" and states "none" is the default. Earlier work-in-progress copies (b54aba9f10, 2019-10-18) are in no release tag. Later commit 5ff414e986 (2022-06-28) moves the built-ins into named -C output (defaultconf).
* **d16-dnssec-policy-default-key-size-2048** basis: git tag --contains. Note: touches lib/dns/kasp.c plus bin/tests/system/kasp/tests.sh; product file is kasp.c.
* **d17-nsec3param-default-in-policy** basis: git tag --contains. Note: first stable is v9.16.10 (v9.16 branch commit); main-branch twin 114af58ee2 reaches 9.18.0.
* **d18-nsec3param-default-0-0** basis: git tag --contains. Note: applies to zones whose dnssec-policy sets "nsec3param;" without values (opt-in to NSEC3 itself). Not backported to 9.16: v9.16.50:lib/isccfg/kaspconf.c still has DEFAULT_NSEC3PARAM_ITER 5. First stable 9.18.0.
* **d19-dnskey-kskonly-yes** basis: git tag --contains. Changelog: "Change default of 'dnssec-dnskey-kskonly' to 'yes'. [GL #1316]" Note: commit also edits bin/tests/system/*/named.conf.in fixtures (adapting tests); the product change is bin/named/config.c.
* **d20-dnssec-cds-sha2-only** basis: git tag --contains. Changelog: "dnssec-cds now only generates SHA-2 DS records by default and avoids copying deprecated SHA-1 records from a child zone to its delegation in the parent. If the child zone does not publish SHA-2 CDS re"
* **d21-signzone-nsec3-iterations-0** basis: git tag --contains. Changelog: "Changed dnssec-signzone -H default to 0 additional NSEC3 iterations. [GL #3395]" Note: 47c214644b is the 9.18 backport (first stable v9.18.5); d029d6374d is main (9.19.3, first stable 9.20.0).
* **d22-cdns-cdnskey-options** basis: git tag --contains. Note: Not a default change (value_changed=false). The commit that first made dnssec-policy publish CDS/CDNSKEY (9.16.0 keymgr) was not located; see gaps.
* **d23-bindkeys-revoked-key-removed** basis: git tag --contains. Changelog: "Remove revoked root DNSKEY from bind.keys. [GL #945]"
* **d24-bindkeys-root-2025-ds** basis: git tag --contains. Note: per-branch commits; a2f8b76c5e (9.16 line) is in no release tag. Phase 3 correction: opt-in is no, because the built-in key is used whenever dnssec-validation is unset (auto, default since v9.14.0, d07).
* **l01-nsec3-max-iterations-150** basis: git tag --contains. Changelog: "Reduce the maximum supported number of NSEC3 iterations that can be configured for a zone to 150. [GL #2642]" Note: 9324d2d295 (9.16 code), 9170275738 (9.16 validator) and 91a7f94a66 (9.11 ESV line, first tag 9.11.32) are the branch commits; main twin 29126500d2 reaches 9.18.0. The v9.16.16:lib/dns/include/dns/nsec3.h has MAXITERATIONS 150; v9.16.15 has no such macro.
* **l02-nsec3-max-iterations-50** basis: git tag --contains. Note: Not backported: v9.18.31 and v9.16.50 keep 150 (checked in lib/dns/include/dns/nsec3.h). ff4201e388 message: "the next major BIND release should lower the maximum allowed NSEC3 iterations to 50" (RFC 9276 guidance); it reaches stable users at 9.20.0.
* **l03-keytrap-validation-limits-9.16-9.18** basis: git tag --contains. Changelog: "Separate DNSSEC validation from the long-running tasks. ``c0022f68025`` As part of the KeyTrap \[CVE-2023-50387\] mitigation, the DNSSEC CPU- intensive operations were offloaded to a separate threadpo" Note: 0add293477 (9.18.24) and its cherry-pick 6a65a42528 (9.16.48). 9.16/9.18 have no max-validations-per-fetch option (v9.16.48 and v9.18.24 bin/named/server.c do not contain it).
* **l04-max-validations-per-fetch** basis: git tag --contains. Note: reference.rst in the commit: "The default is 16" / "The default is 1", labelled experimental. Later changes (9.20.x) not tracked here. Present in v9.19.21 and v9.20.0 (bin/named/server.c), absent from v9.16.48 / v9.18.24.

## Limit changes (subset, for quick reference)

| id | before | after | first stable | commits |
|---|---|---|---|---|
| l01-nsec3-max-iterations-150 | max iterations 150/500/2500 depending on smallest DNSKEY size | max iterations 150 fixed | v9.16.16 (2021-05-12) | 9324d2d295, 9170275738, 91a7f94a66 |
| l02-nsec3-max-iterations-50 | DNS_NSEC3_MAXITERATIONS 150 | DNS_NSEC3_MAXITERATIONS 50 | v9.20.0 (2024-07-08) | ff4201e388, 75e0d394dd |
| l03-keytrap-validation-limits-9.16-9.18 | validator retried all key/signature combinations | fail on first validation failure | v9.18.24 (2024-02-11) | 0add293477, 6a65a42528, c12608ca93 |
| l04-max-validations-per-fetch | unbounded (per-fetch) | max-validations-per-fetch 16; max-validation-failures-per-fetch 1 | v9.20.0 (2024-07-08) | 15096aefdf |

## News / changelog edits after release

| id | what | commits | first tag with edit |
|---|---|---|---|
| n01 | CHANGES entry 2405 added retroactively: dnssec-validation default was changed to "yes" in 9.5.0-P1 but the CHANGES line was omitted at the time | cf5ea2dff6, e43b095921, d406c6833f | v9.5.0-P2 |
| n02 | CHANGES entry 6322 (KeyTrap, CVE-2023-50387) edited on 2024-02-14 to also name CVE-2023-50868; commit message: "CVE-2023-50868 does not have a dedicated fix in BIND 9" | ec1afa639f, 6a40a5eada, 2fd20bbaf5 | v9.16.50 |
| n03 | Release note for CVE-2023-50868 retroactively added to the already released 9.19.21 notes | 01ac86f90b | v9.19.22 |

## CVE fixes

184 CVEs are attributed to BIND by the inventory. 127 have a first stable tag; 31 are not BIND 9 stable-release issues; 26 are not found. A further 23 CVEs come from the inventory's fixes.bind9 git scrape and have no NVD product tag: 22 have a first stable tag (basis `changelog` = CVE id in CHANGES / release notes, `commit` = commit containment only, CVE-2006-5989) and 1 (CVE-2015-3193, OpenSSL version gate in configure only) is not a BIND 9 code fix; NVD published and latency are filled only where the inventory keyword lists carry the date (`-` otherwise). `first stable tag` = earliest stable non-Windows tag (by UTC instant of the tag commit; Phase 3 corrected six rows that had been ordered by committer-local time) that (a) contains a commit naming the CVE or a cherry-pick sibling of one, (b) has the CVE id in CHANGES / release notes, or (c) carries a kept stage-2 changelog entry naming it; same-day tags on other branches are in the `same day` column. `approx` = version taken from the NVD text (tag exists, fix commit not located). Latency = tag date minus NVD published date (negative = fixed first). `inv` = the inventory `fix_release` when it differs.

```
C=out/software_repos/bind9.git
git -C $C show <tag>:CHANGES | grep -n -F <CVE-id>       # changelog basis (or the path in the JSON `verify` field)
git -C $C tag --contains <commit> | grep -x <tag>          # commit basis
```

| CVE | NVD published | first stable tag | fix date | latency d | basis | same day | inv |
|---|---|---|---|---|---|---|---|
| CVE-2002-0400 | 2002-06-18 | v9.2.1 | 2002-04-23 | -56 | approx (NVD) |  |  |
| CVE-2006-0987 | 2006-03-03 | v9.4.1-P1 | 2007-07-09 | 493 | approx (NVD) |  |  |
| CVE-2006-4095 | 2006-09-06 | v9.3.2-P1 | 2006-08-17 | -20 | approx (NVD) |  |  |
| CVE-2006-4096 | 2006-09-06 | v9.3.2-P1 | 2006-08-17 | -20 | approx (NVD) |  |  |
| CVE-2006-5989 | - | v9.16.12 | 2021-02-04 |  | commit | v9.11.28 | 9.11.29 |
| CVE-2008-0122 | 2008-01-16 | v9.3.5 | 2008-04-03 | 78 | changelog |  | 9.4.3 |
| CVE-2008-1447 | 2008-07-08 | v9.4.2-P1 | 2008-05-28 | -41 | approx (NVD) |  |  |
| CVE-2009-0696 | 2009-07-29 | v9.4.3-P3 | 2009-07-28 | -1 | approx (NVD) |  |  |
| CVE-2009-4022 | 2009-11-25 | v9.5.2-P1 | 2009-11-18 | -7 | approx (NVD) |  |  |
| CVE-2010-0097 | 2010-01-22 | v9.6.1-P3 | 2010-01-07 | -15 | approx (NVD) |  |  |
| CVE-2010-0290 | 2010-01-22 | v9.6.1-P3 | 2010-01-07 | -15 | approx (NVD) |  |  |
| CVE-2010-0382 | 2010-01-22 | v9.6.1-P3 | 2010-01-07 | -15 | approx (NVD) | v9.4.3-P5 |  |
| CVE-2010-3613 | 2010-12-06 | v9.4-ESV-R4 | 2010-11-29 | -7 | changelog | v9.6-ESV-R3, v9.6.2-P3, v9.7.2-P3 |  |
| CVE-2010-3614 | 2010-12-06 | v9.4-ESV-R4 | 2010-11-29 | -7 | changelog | v9.6-ESV-R3, v9.6.2-P3, v9.7.2-P3 |  |
| CVE-2010-3615 | 2010-12-06 | v9.6-ESV-R3 | 2010-11-29 | -7 | changelog | v9.7.2-P3 |  |
| CVE-2010-3762 | 2010-10-05 | v9.7.2-P2 | 2010-09-24 | -11 | approx (NVD) |  |  |
| CVE-2011-1907 | 2011-05-09 | v9.8.0-P1 | 2011-04-27 | -12 | approx (NVD) |  |  |
| CVE-2011-1910 | 2011-05-31 | v9.6-ESV-R4-P1 | 2011-05-27 | -4 | approx (NVD) |  |  |
| CVE-2011-2464 | 2011-07-08 | v9.6-ESV-R4-P3 | 2011-06-21 | -17 | approx (NVD) |  |  |
| CVE-2011-4313 | 2011-11-29 | v9.4-ESV-R5-P1 | 2011-11-16 | -13 | changelog (entry 3218 text) | v9.6-ESV-R5-P1, v9.7.4-P1, v9.8.1-P1 |  |
| CVE-2012-1667 | 2012-06-05 | v9.9.1-P1 | 2012-06-01 | -4 | approx (NVD) |  |  |
| CVE-2012-3817 | 2012-07-25 | v9.8.3-P2 | 2012-07-02 | -23 | approx (NVD) |  |  |
| CVE-2012-3868 | 2012-07-25 | v9.9.1-P2 | 2012-07-12 | -13 | approx (NVD) |  |  |
| CVE-2012-4244 | 2012-09-14 | v9.6-ESV-R7-P3 | 2012-08-24 | -21 | approx (NVD) |  |  |
| CVE-2012-5166 | 2012-10-10 | v9.6-ESV-R7-P4 | 2012-09-26 | -14 | approx (NVD) |  |  |
| CVE-2012-5688 | 2012-12-06 | v9.9.2-P1 | 2012-10-26 | -41 | approx (NVD) |  |  |
| CVE-2012-5689 | 2013-01-25 | v9.9.3 | 2013-05-17 | 112 | changelog | v9.8.5 |  |
| CVE-2013-2266 | 2013-03-28 | v9.9.2-P2 | 2013-03-06 | -22 | approx (NVD) |  |  |
| CVE-2013-3919 | 2013-06-06 | v9.9.3-P1 | 2013-06-04 | -2 | approx (NVD) |  |  |
| CVE-2013-4854 | 2013-07-29 | v9.8.5-P2 | 2013-07-17 | -12 | changelog | v9.9.3-P2 | 9.8.6 |
| CVE-2013-6230 | 2013-11-08 | v9.6-ESV-R10-P1 | 2013-10-16 | -23 | approx (NVD) |  |  |
| CVE-2014-0591 | 2014-01-14 | v9.9.4-P2 | 2013-12-20 | -25 | approx (NVD) |  |  |
| CVE-2014-3214 | 2014-05-09 | v9.10.0-P2 | 2014-05-27 | 18 | changelog |  |  |
| CVE-2014-3859 | 2014-06-13 | v9.10.0-P2 | 2014-05-27 | -17 | changelog |  | 9.8.8 |
| CVE-2014-8500 | 2014-12-11 | v9.10.1-P1 | 2014-11-20 | -21 | changelog | v9.9.6-P1 | 9.9.7 |
| CVE-2014-8680 | 2014-12-11 | v9.10.1-P1 | 2014-11-20 | -21 | changelog |  |  |
| CVE-2015-1349 | 2015-02-19 | v9.9.6-P2 | 2015-02-11 | -8 | changelog | v9.10.1-P2 |  |
| CVE-2015-4620 | 2015-07-08 | v9.9.7-P1 | 2015-06-17 | -21 | changelog | v9.10.2-P2 |  |
| CVE-2015-5477 | 2015-07-29 | v9.9.7-P2 | 2015-07-14 | -15 | changelog | v9.10.2-P3 |  |
| CVE-2015-5722 | 2015-09-05 | v9.10.2-P4 | 2015-08-15 | -21 | changelog | v9.9.7-P3 |  |
| CVE-2015-5986 | 2015-09-05 | v9.10.2-P4 | 2015-08-15 | -21 | changelog | v9.9.7-P3 |  |
| CVE-2015-8000 | 2015-12-16 | v9.9.8-P2 | 2015-12-06 | -10 | changelog | v9.10.3-P2 |  |
| CVE-2015-8461 | 2015-12-16 | v9.9.8-P2 | 2015-12-06 | -10 | changelog | v9.10.3-P2 |  |
| CVE-2015-8704 | 2016-01-20 | v9.9.8-P3 | 2016-01-06 | -14 | changelog | v9.10.3-P3 |  |
| CVE-2015-8705 | 2016-01-20 | v9.10.3-P3 | 2016-01-06 | -14 | changelog |  | 9.11.0 |
| CVE-2016-1285 | 2016-03-09 | v9.10.3-P4 | 2016-02-29 | -9 | changelog | v9.9.8-P4 |  |
| CVE-2016-1286 | 2016-03-09 | v9.10.3-P4 | 2016-02-29 | -9 | changelog | v9.9.8-P4 |  |
| CVE-2016-2088 | 2016-03-09 | v9.10.3-P4 | 2016-02-29 | -9 | changelog |  | 9.11.0 |
| CVE-2016-2775 | 2016-07-19 | v9.9.9-P2 | 2016-07-13 | -6 | changelog | v9.10.4-P2 | 9.9.10 |
| CVE-2016-2776 | 2016-09-28 | v9.9.9-P3 | 2016-09-09 | -19 | changelog |  |  |
| CVE-2016-6170 | 2016-07-06 | v9.9.10 | 2017-04-14 | 282 | changelog | v9.10.5, v9.11.1 | 9.10.5 |
| CVE-2016-8864 | 2016-11-02 | v9.10.4-P4 | 2016-10-21 | -12 | changelog | v9.11.0-P1, v9.9.9-P4 |  |
| CVE-2016-9131 | 2017-01-12 | v9.9.9-P5 | 2016-12-11 | -32 | changelog | v9.10.4-P5, v9.11.0-P2 |  |
| CVE-2016-9147 | 2017-01-12 | v9.9.9-P5 | 2016-12-11 | -32 | changelog | v9.10.4-P5, v9.11.0-P2 |  |
| CVE-2016-9444 | 2017-01-12 | v9.9.9-P5 | 2016-12-11 | -32 | changelog | v9.10.4-P5, v9.11.0-P2 | 9.9.10 |
| CVE-2016-9778 | 2019-01-16 | v9.9.9-P5 | 2016-12-11 | -766 | changelog | v9.10.4-P5, v9.11.0-P2 |  |
| CVE-2017-3135 | 2019-01-16 | v9.11.0-P3 | 2017-01-31 | -715 | changelog | v9.10.4-P6, v9.9.9-P6 |  |
| CVE-2017-3136 | 2019-01-16 | v9.9.9-P8 | 2017-03-29 | -658 | changelog | v9.10.4-P8, v9.11.0-P5 | 9.12.0 |
| CVE-2017-3137 | 2019-01-16 | v9.9.9-P8 | 2017-03-29 | -658 | changelog | v9.10.4-P8, v9.11.0-P5 |  |
| CVE-2017-3138 | 2019-01-16 | v9.9.9-P8 | 2017-03-29 | -658 | changelog | v9.10.4-P8, v9.11.0-P5 |  |
| CVE-2017-3140 | 2019-01-16 | v9.9.10-P1 | 2017-05-31 | -595 | changelog | v9.10.5-P1, v9.11.1-P1 |  |
| CVE-2017-3141 | 2019-01-16 | v9.9.10-P1 | 2017-05-31 | -595 | changelog | v9.10.5-P1, v9.11.1-P1 |  |
| CVE-2017-3142 | 2019-01-16 | v9.11.1-P2 | 2017-06-28 | -567 | changelog | v9.10.5-P2, v9.9.10-P2 |  |
| CVE-2017-3143 | 2019-01-16 | v9.11.1-P2 | 2017-06-28 | -567 | changelog | v9.10.5-P2, v9.9.10-P2 |  |
| CVE-2017-3145 | 2019-01-16 | v9.11.2-P1 | 2018-01-04 | -377 | changelog | v9.10.6-P1, v9.9.11-P1 |  |
| CVE-2018-5736 | 2019-01-16 | v9.12.1-P2 | 2018-05-16 | -245 | changelog |  |  |
| CVE-2018-5737 | 2019-01-16 | v9.12.1-P2 | 2018-05-16 | -245 | changelog |  | 9.13.0 |
| CVE-2018-5738 | 2019-01-16 | v9.9.13 | 2018-07-03 | -197 | changelog | v9.10.8, v9.11.4, v9.12.2 |  |
| CVE-2018-5740 | 2019-01-16 | v9.12.2-P1 | 2018-07-24 | -176 | changelog | v9.11.4-P1 | 9.11.5 |
| CVE-2018-5741 | 2019-01-16 | v9.11.5 | 2018-10-06 | -102 | approx (NVD) |  |  |
| CVE-2018-5743 | 2019-10-09 | v9.12.4-P1 | 2019-04-06 | -186 | changelog | v9.11.6-P1, v9.14.1 |  |
| CVE-2018-5744 | 2019-10-09 | v9.12.3-P4 | 2019-02-04 | -247 | changelog |  |  |
| CVE-2018-5745 | 2019-10-09 | v9.12.3-P4 | 2019-02-04 | -247 | changelog |  |  |
| CVE-2019-6465 | 2019-10-09 | v9.12.3-P4 | 2019-02-04 | -247 | changelog |  |  |
| CVE-2019-6467 | 2019-10-09 | v9.12.4-P1 | 2019-04-06 | -186 | changelog | v9.14.1 |  |
| CVE-2019-6471 | 2019-10-09 | v9.14.3 | 2019-06-04 | -127 | changelog | v9.11.8 |  |
| CVE-2019-6475 | 2019-10-17 | v9.14.7 | 2019-10-02 | -15 | changelog |  |  |
| CVE-2019-6476 | 2019-10-17 | v9.14.7 | 2019-10-02 | -15 | changelog |  |  |
| CVE-2019-6477 | 2019-11-26 | v9.14.8 | 2019-11-06 | -20 | changelog | v9.11.13 | 9.15.7 |
| CVE-2020-8616 | 2020-05-19 | v9.16.3 | 2020-05-06 | -13 | changelog | v9.11.19, v9.14.12 | 9.11.20 |
| CVE-2020-8617 | 2020-05-19 | v9.16.3 | 2020-05-06 | -13 | changelog | v9.11.19, v9.14.12 | 9.11.20 |
| CVE-2020-8618 | 2020-06-17 | v9.16.4 | 2020-06-10 | -7 | changelog |  | 9.16.5 |
| CVE-2020-8619 | 2020-06-17 | v9.11.20 | 2020-06-10 | -7 | changelog | v9.16.4 | 9.11.21 |
| CVE-2020-8620 | 2020-08-21 | v9.16.6 | 2020-08-10 | -11 | changelog |  |  |
| CVE-2020-8621 | 2020-08-21 | v9.16.6 | 2020-08-10 | -11 | changelog |  |  |
| CVE-2020-8622 | 2020-08-21 | v9.11.22 | 2020-08-06 | -15 | changelog |  |  |
| CVE-2020-8623 | 2020-08-21 | v9.11.22 | 2020-08-06 | -15 | changelog |  |  |
| CVE-2020-8624 | 2020-08-21 | v9.11.22 | 2020-08-06 | -15 | changelog |  |  |
| CVE-2020-8625 | 2021-02-17 | v9.16.12 | 2021-02-04 | -13 | changelog | v9.11.28 | 9.11.29 |
| CVE-2021-25214 | 2021-04-29 | v9.16.15 | 2021-04-19 | -10 | changelog | v9.11.31 | 9.11.32 |
| CVE-2021-25215 | 2021-04-29 | v9.16.15 | 2021-04-19 | -10 | changelog | v9.11.31 | 9.11.32 |
| CVE-2021-25216 | 2021-04-29 | v9.16.15 | 2021-04-19 | -10 | changelog | v9.11.31 | 9.11.32 |
| CVE-2021-25218 | 2021-08-18 | v9.16.20 | 2021-08-10 | -8 | changelog |  | 9.17.18 |
| CVE-2021-25219 | 2021-10-27 | v9.11.36 | 2021-10-11 | -16 | changelog |  | 9.11.37 |
| CVE-2021-25220 | 2022-03-23 | v9.18.1 | 2022-03-07 | -16 | changelog | v9.11.37, v9.16.27 | 9.16.28 |
| CVE-2022-0396 | 2022-03-23 | v9.18.1 | 2022-03-07 | -16 | changelog | v9.16.27 | 9.16.28 |
| CVE-2022-0635 | 2022-03-23 | v9.18.1 | 2022-03-07 | -16 | changelog |  | 9.18.2 |
| CVE-2022-0667 | 2022-03-22 | v9.18.1 | 2022-03-07 | -15 | changelog |  | 9.18.2 |
| CVE-2022-1183 | 2022-05-19 | v9.18.3 | 2022-05-09 | -10 | changelog |  |  |
| CVE-2022-2795 | 2022-09-21 | v9.18.7 | 2022-09-08 | -13 | changelog | v9.16.33 |  |
| CVE-2022-2881 | 2022-09-21 | v9.18.7 | 2022-09-08 | -13 | changelog |  |  |
| CVE-2022-2906 | 2022-09-21 | v9.18.7 | 2022-09-08 | -13 | changelog |  |  |
| CVE-2022-3080 | 2022-09-21 | v9.18.7 | 2022-09-08 | -13 | changelog | v9.16.33 | 9.16.33 |
| CVE-2022-3094 | 2023-01-26 | v9.18.11 | 2023-01-12 | -14 | changelog | v9.16.37 | 9.16.37 |
| CVE-2022-3736 | 2023-01-26 | v9.18.11 | 2023-01-12 | -14 | changelog | v9.16.37 | 9.16.37 |
| CVE-2022-38177 | 2022-09-21 | v9.16.33 | 2022-09-08 | -13 | changelog |  |  |
| CVE-2022-38178 | 2022-09-21 | v9.18.7 | 2022-09-08 | -13 | changelog | v9.16.33 | 9.16.33 |
| CVE-2022-3924 | 2023-01-26 | v9.18.11 | 2023-01-12 | -14 | changelog | v9.16.37 | 9.16.39 |
| CVE-2023-2828 | 2023-06-21 | v9.18.16 | 2023-06-09 | -12 | changelog | v9.16.42 |  |
| CVE-2023-2911 | 2023-06-21 | v9.18.16 | 2023-06-09 | -12 | changelog | v9.16.42 | 9.16.42 |
| CVE-2023-3341 | 2023-09-20 | v9.16.44 | 2023-09-08 | -12 | changelog |  | 9.18.20 |
| CVE-2023-4236 | 2023-09-20 | v9.18.19 | 2023-09-11 | -9 | changelog |  |  |
| CVE-2023-4408 | 2024-02-13 | v9.18.24 | 2024-02-11 | -2 | changelog | v9.16.48 | 9.16.48 |
| CVE-2023-50387 | 2024-02-14 | v9.18.24 | 2024-02-11 | -3 | changelog | v9.16.48 | 9.16.48 |
| CVE-2023-50868 | 2024-02-14 | v9.18.24 | 2024-02-11 | -3 | shared fix | v9.16.48 | 9.16.50 |
| CVE-2023-5517 | 2024-02-13 | v9.18.24 | 2024-02-11 | -2 | changelog | v9.16.48 | 9.16.48 |
| CVE-2023-5679 | 2024-02-13 | v9.18.24 | 2024-02-11 | -2 | changelog | v9.16.48 | 9.16.48 |
| CVE-2023-6516 | 2024-02-13 | v9.16.48 | 2024-02-11 | -2 | changelog |  |  |
| CVE-2024-0760 | - | v9.20.0 | 2024-07-08 |  | changelog | v9.18.28 | 9.18.28 |
| CVE-2024-1737 | - | v9.20.0 | 2024-07-08 |  | changelog | v9.18.28 | 9.18.28 |
| CVE-2024-1975 | 2024-07-23 | v9.20.0 | 2024-07-08 | -15 | changelog | v9.18.28 | 9.18.28 |
| CVE-2024-4076 | - | v9.20.0 | 2024-07-08 |  | changelog | v9.18.28 | 9.18.28 |
| CVE-2024-11187 | - | v9.20.5 | 2025-01-20 |  | changelog | v9.18.33 | 9.18.33 |
| CVE-2024-12705 | - | v9.20.5 | 2025-01-20 |  | changelog | v9.18.33 | 9.18.33 |
| CVE-2025-8677 | 2025-10-22 | v9.20.15 | 2025-10-18 | -4 | changelog | v9.18.41 | 9.18.41 |
| CVE-2025-13878 | - | v9.20.18 | 2026-01-09 |  | changelog | v9.18.44 | 9.18.44 |
| CVE-2025-40775 | - | v9.20.9 | 2025-05-08 |  | changelog |  |  |
| CVE-2025-40777 | - | v9.20.11 | 2025-07-04 |  | changelog |  |  |
| CVE-2025-40778 | - | v9.20.15 | 2025-10-18 |  | changelog | v9.18.41 | 9.18.44 |
| CVE-2025-40780 | - | v9.20.15 | 2025-10-18 |  | changelog | v9.18.41 | 9.18.41 |
| CVE-2026-1519 | 2026-03-25 | v9.20.21 | 2026-03-13 | -12 | changelog | v9.18.47 | 9.18.47 |
| CVE-2026-3039 | 2026-05-20 | v9.20.23 | 2026-05-08 | -12 | changelog | v9.18.49 |  |
| CVE-2026-3104 | 2026-03-25 | v9.20.21 | 2026-03-13 | -12 | changelog |  |  |
| CVE-2026-3119 | 2026-03-25 | v9.20.21 | 2026-03-13 | -12 | changelog |  |  |
| CVE-2026-3591 | 2026-03-25 | v9.20.21 | 2026-03-13 | -12 | changelog |  |  |
| CVE-2026-3592 | 2026-05-20 | v9.20.23 | 2026-05-08 | -12 | changelog | v9.18.49 |  |
| CVE-2026-3593 | 2026-05-20 | v9.20.23 | 2026-05-08 | -12 | changelog |  | 9.21.22 |
| CVE-2026-5946 | 2026-05-20 | v9.20.23 | 2026-05-08 | -12 | changelog | v9.18.49 | 9.20.26 |
| CVE-2026-5947 | 2026-05-20 | v9.20.23 | 2026-05-08 | -12 | changelog |  | 9.21.22 |
| CVE-2026-5950 | 2026-05-20 | v9.20.23 | 2026-05-08 | -12 | changelog | v9.18.49 |  |
| CVE-2026-10723 | 2026-07-22 | v9.20.26 | 2026-07-20 | -2 | changelog |  |  |
| CVE-2026-10822 | 2026-07-22 | v9.20.26 | 2026-07-20 | -2 | changelog |  |  |
| CVE-2026-11331 | - | v9.20.26 | 2026-07-20 |  | changelog |  |  |
| CVE-2026-11605 | 2026-07-22 | v9.20.26 | 2026-07-20 | -2 | changelog |  |  |
| CVE-2026-11622 | 2026-07-22 | v9.20.26 | 2026-07-20 | -2 | changelog |  |  |
| CVE-2026-11721 | 2026-07-22 | v9.20.26 | 2026-07-20 | -2 | changelog |  | 9.21.24 |
| CVE-2026-12617 | - | v9.20.26 | 2026-07-20 |  | changelog |  |  |
| CVE-2026-13204 | 2026-07-22 | v9.20.26 | 2026-07-20 | -2 | changelog |  |  |
| CVE-2026-13321 | - | v9.20.26 | 2026-07-20 |  | changelog |  | 9.21.24 |

### CVEs without a tag

| CVE | status | reason |
|---|---|---|
| CVE-1999-0009 | not-applicable-or-not-bind9-release | description names only BIND 4/8, other vendors/libc, Windows-only, Supported Preview (-S) or Red Hat builds; no v9.x sta |
| CVE-1999-0010 | not-applicable-or-not-bind9-release | description names only BIND 4/8, other vendors/libc, Windows-only, Supported Preview (-S) or Red Hat builds; no v9.x sta |
| CVE-1999-0011 | not-applicable-or-not-bind9-release | description names only BIND 4/8, other vendors/libc, Windows-only, Supported Preview (-S) or Red Hat builds; no v9.x sta |
| CVE-1999-0024 | not-found | no fix commit, no CVE-id mention in CHANGES/notes at any tag, and no fixed-version in NVD text |
| CVE-1999-0184 | not-found | no fix commit, no CVE-id mention in CHANGES/notes at any tag, and no fixed-version in NVD text |
| CVE-1999-0833 | not-applicable-or-not-bind9-release | description names only BIND 4/8, other vendors/libc, Windows-only, Supported Preview (-S) or Red Hat builds; no v9.x sta |
| CVE-1999-0837 | not-found | no fix commit, no CVE-id mention in CHANGES/notes at any tag, and no fixed-version in NVD text |
| CVE-1999-0848 | not-found | no fix commit, no CVE-id mention in CHANGES/notes at any tag, and no fixed-version in NVD text |
| CVE-1999-0849 | not-found | no fix commit, no CVE-id mention in CHANGES/notes at any tag, and no fixed-version in NVD text |
| CVE-1999-1499 | not-applicable-or-not-bind9-release | description names only BIND 4/8, other vendors/libc, Windows-only, Supported Preview (-S) or Red Hat builds; no v9.x sta |
| CVE-2000-0335 | not-applicable-or-not-bind9-release | description names only BIND 4/8, other vendors/libc, Windows-only, Supported Preview (-S) or Red Hat builds; no v9.x sta |
| CVE-2000-0887 | not-applicable-or-not-bind9-release | description names only BIND 4/8, other vendors/libc, Windows-only, Supported Preview (-S) or Red Hat builds; no v9.x sta |
| CVE-2000-0888 | not-applicable-or-not-bind9-release | description names only BIND 4/8, other vendors/libc, Windows-only, Supported Preview (-S) or Red Hat builds; no v9.x sta |
| CVE-2000-1029 | not-found | no fix commit, no CVE-id mention in CHANGES/notes at any tag, and no fixed-version in NVD text |
| CVE-2001-0010 | not-applicable-or-not-bind9-release | description names only BIND 4/8, other vendors/libc, Windows-only, Supported Preview (-S) or Red Hat builds; no v9.x sta |
| CVE-2001-0011 | not-applicable-or-not-bind9-release | description names only BIND 4/8, other vendors/libc, Windows-only, Supported Preview (-S) or Red Hat builds; no v9.x sta |
| CVE-2001-0012 | not-applicable-or-not-bind9-release | description names only BIND 4/8, other vendors/libc, Windows-only, Supported Preview (-S) or Red Hat builds; no v9.x sta |
| CVE-2001-0013 | not-applicable-or-not-bind9-release | description names only BIND 4/8, other vendors/libc, Windows-only, Supported Preview (-S) or Red Hat builds; no v9.x sta |
| CVE-2001-0497 | not-found | no fix commit, no CVE-id mention in CHANGES/notes at any tag, and no fixed-version in NVD text |
| CVE-2002-0029 | not-found | no fix commit, no CVE-id mention in CHANGES/notes at any tag, and no fixed-version in NVD text |
| CVE-2002-0651 | not-applicable-or-not-bind9-release | description names only BIND 4/8, other vendors/libc, Windows-only, Supported Preview (-S) or Red Hat builds; no v9.x sta |
| CVE-2002-0684 | not-found | no fix commit, no CVE-id mention in CHANGES/notes at any tag, and no fixed-version in NVD text |
| CVE-2002-1219 | not-found | no fix commit, no CVE-id mention in CHANGES/notes at any tag, and no fixed-version in NVD text |
| CVE-2002-1220 | not-applicable-or-not-bind9-release | description names only BIND 4/8, other vendors/libc, Windows-only, Supported Preview (-S) or Red Hat builds; no v9.x sta |
| CVE-2002-1221 | not-applicable-or-not-bind9-release | description names only BIND 4/8, other vendors/libc, Windows-only, Supported Preview (-S) or Red Hat builds; no v9.x sta |
| CVE-2002-2211 | not-applicable-or-not-bind9-release | description names only BIND 4/8, other vendors/libc, Windows-only, Supported Preview (-S) or Red Hat builds; no v9.x sta |
| CVE-2002-2212 | not-applicable-or-not-bind9-release | description names only BIND 4/8, other vendors/libc, Windows-only, Supported Preview (-S) or Red Hat builds; no v9.x sta |
| CVE-2002-2213 | not-applicable-or-not-bind9-release | description names only BIND 4/8, other vendors/libc, Windows-only, Supported Preview (-S) or Red Hat builds; no v9.x sta |
| CVE-2003-0914 | not-applicable-or-not-bind9-release | description names only BIND 4/8, other vendors/libc, Windows-only, Supported Preview (-S) or Red Hat builds; no v9.x sta |
| CVE-2005-0033 | not-applicable-or-not-bind9-release | description names only BIND 4/8, other vendors/libc, Windows-only, Supported Preview (-S) or Red Hat builds; no v9.x sta |
| CVE-2005-0034 | not-found | no fix commit, no CVE-id mention in CHANGES/notes at any tag, and no fixed-version in NVD text |
| CVE-2006-0527 | not-applicable-or-not-bind9-release | description names only BIND 4/8, other vendors/libc, Windows-only, Supported Preview (-S) or Red Hat builds; no v9.x sta |
| CVE-2006-2073 | not-found | no fix commit, no CVE-id mention in CHANGES/notes at any tag, and no fixed-version in NVD text |
| CVE-2007-0493 | not-found | no fix commit, no CVE-id mention in CHANGES/notes at any tag, and no fixed-version in NVD text |
| CVE-2007-0494 | not-found | no fix commit, no CVE-id mention in CHANGES/notes at any tag, and no fixed-version in NVD text |
| CVE-2007-2241 | not-found | no fix commit, no CVE-id mention in CHANGES/notes at any tag, and no fixed-version in NVD text |
| CVE-2007-2925 | not-found | no fix commit, no CVE-id mention in CHANGES/notes at any tag, and no fixed-version in NVD text |
| CVE-2007-2926 | not-found | no fix commit, no CVE-id mention in CHANGES/notes at any tag, and no fixed-version in NVD text |
| CVE-2007-2930 | not-applicable-or-not-bind9-release | description names only BIND 4/8, other vendors/libc, Windows-only, Supported Preview (-S) or Red Hat builds; no v9.x sta |
| CVE-2008-4163 | not-applicable-or-not-bind9-release | description names only BIND 4/8, other vendors/libc, Windows-only, Supported Preview (-S) or Red Hat builds; no v9.x sta |
| CVE-2009-0025 | not-found | no fix commit, no CVE-id mention in CHANGES/notes at any tag, and no fixed-version in NVD text |
| CVE-2009-0265 | not-found | no fix commit, no CVE-id mention in CHANGES/notes at any tag, and no fixed-version in NVD text |
| CVE-2010-0213 | not-found | no fix commit, no CVE-id mention in CHANGES/notes at any tag, and no fixed-version in NVD text |
| CVE-2010-0218 | not-found | no fix commit, no CVE-id mention in CHANGES/notes at any tag, and no fixed-version in NVD text |
| CVE-2011-0414 | not-found | no fix commit, no CVE-id mention in CHANGES/notes at any tag, and no fixed-version in NVD text |
| CVE-2011-2465 | not-found | no fix commit, no CVE-id mention in CHANGES/notes at any tag, and no fixed-version in NVD text |
| CVE-2012-1033 | not-found | no fix commit, no CVE-id mention in CHANGES/notes at any tag, and no fixed-version in NVD text |
| CVE-2013-5661 | not-found | no fix commit, no CVE-id mention in CHANGES/notes at any tag, and no fixed-version in NVD text |
| CVE-2015-3193 | not-applicable-or-not-bind9-release | CVE-2015-3193 is an OpenSSL bug (BN_mod_exp carry). BIND's only change (CHANGES 4270, commit 559236b5e4 and cherry-picks) edits configure / configure.in to widen the OpenSSL version check (accept >= 1.0.2e, reject 1.0.2 through 1.0.2d, and similar for 1.0.1); no BIND product source file (lib/, bin/) changed. Dependency version gate only, so not a BIND 9 code fix. Tags carrying CHANGES 4270 (earliest v9.9.8-P2) are recorded in verify for reference. |
| CVE-2016-1284 | not-applicable-or-not-bind9-release | description names only BIND 4/8, other vendors/libc, Windows-only, Supported Preview (-S) or Red Hat builds; no v9.x sta |
| CVE-2016-2848 | not-found | no fix commit, no CVE-id mention in CHANGES/notes at any tag, and no fixed-version in NVD text |
| CVE-2018-5734 | not-applicable-or-not-bind9-release | description names only BIND 4/8, other vendors/libc, Windows-only, Supported Preview (-S) or Red Hat builds; no v9.x sta |
| CVE-2018-5742 | not-applicable-or-not-bind9-release | description names only BIND 4/8, other vendors/libc, Windows-only, Supported Preview (-S) or Red Hat builds; no v9.x sta |
| CVE-2019-6468 | not-applicable-or-not-bind9-release | description names only BIND 4/8, other vendors/libc, Windows-only, Supported Preview (-S) or Red Hat builds; no v9.x sta |
| CVE-2019-6469 | not-applicable-or-not-bind9-release | description names only BIND 4/8, other vendors/libc, Windows-only, Supported Preview (-S) or Red Hat builds; no v9.x sta |
| CVE-2022-3488 | not-applicable-or-not-bind9-release | description names only BIND 4/8, other vendors/libc, Windows-only, Supported Preview (-S) or Red Hat builds; no v9.x sta |
| CVE-2023-2829 | not-applicable-or-not-bind9-release | description names only BIND 4/8, other vendors/libc, Windows-only, Supported Preview (-S) or Red Hat builds; no v9.x sta |
| CVE-2023-5680 | not-applicable-or-not-bind9-release | description names only BIND 4/8, other vendors/libc, Windows-only, Supported Preview (-S) or Red Hat builds; no v9.x sta |

## Release list

| tag | date | stable | kind | branch | commit | changelog entries (kept/total) |
|---|---|---|---|---|---|---|
| v9.0.0a2 | 1999-09-08 | no | alpha | 9.0 | c04a3d879c | 0/- |
| v9.0.0a1 | 1999-11-02 | no | alpha | 9.0 | cca310a647 | 0/- |
| v9.0.0a3 | 1999-11-06 | no | alpha | 9.0 | dd0c913e06 | 0/- |
| v9.0.0b1 | 2000-02-05 | no | beta | 9.0 | 0b4558f2cd | 0/- |
| v9.0.0b2 | 2000-02-07 | no | beta | 9.0 | ab00bdb13f | 0/- |
| v9.0.0b3 | 2000-05-23 | no | beta | 9.0 | 7457d6b1e1 | 0/- |
| v9.0.0b4 | 2000-06-14 | no | beta | 9.0 | d9cea1977d | 0/- |
| v9.0.0b5 | 2000-06-30 | no | beta | 9.0 | fe1d8658e8 | 0/- |
| v9.0.0rc1 | 2000-07-26 | no | rc | 9.0 | 5704b77baf | 0/- |
| v9.0.0rc2 | 2000-08-08 | no | rc | 9.0 | 43bd38034f | 0/- |
| v9.0.0rc3 | 2000-08-15 | no | rc | 9.0 | d9cfdf00ee | 0/- |
| v9.0.0rc4 | 2000-08-22 | no | rc | 9.0 | a20b5c6d66 | 0/- |
| v9.0.0rc5 | 2000-08-28 | no | rc | 9.0 | 1d5247bd1c | 0/- |
| v9.0.0rc6 | 2000-09-13 | no | rc | 9.0 | 3a642572db | 0/- |
| v9.0.0 | 2000-09-15 | yes | release | 9.0 | 19d6c56085 | 20/403 |
| v9.0.1rc1 | 2000-11-03 | no | rc | 9.0 | 4df2b2a65e | 0/- |
| v9.0.1rc2 | 2000-11-06 | no | rc | 9.0 | 5ad7e61731 | 0/- |
| v9.0.1 | 2000-11-09 | yes | release | 9.0 | 254504379a | 0/40 |
| v9.1.0b1 | 2000-12-05 | no | beta | 9.1 | 01fa6f1bef | 0/- |
| v9.1.0b2 | 2000-12-28 | no | beta | 9.1 | 0073346086 | 0/- |
| v9.1.0b3 | 2001-01-08 | no | beta | 9.1 | 48b7b8fb19 | 0/- |
| v9.1.0rc1 | 2001-01-13 | no | rc | 9.1 | 5a57443c63 | 0/- |
| v9.1.0 | 2001-01-17 | yes | release | 9.1 | dec7e52a8b | 14/225 |
| v9.1.1rc1 | 2001-02-07 | no | rc | 9.1 | 544b578245 | 0/- |
| v9.1.1rc2 | 2001-02-12 | no | rc | 9.1 | a3d0d44b14 | 0/- |
| v9.1.1rc3 | 2001-02-26 | no | rc | 9.1 | 06ebba2789 | 0/- |
| v9.1.1rc4 | 2001-03-06 | no | rc | 9.1 | c3f028ec2d | 0/- |
| v9.1.1rc5 | 2001-03-14 | no | rc | 9.1 | 756d5f41a2 | 0/- |
| v9.1.1rc6 | 2001-03-22 | no | rc | 9.1 | 18c9034480 | 0/- |
| v9.1.1rc7 | 2001-03-27 | no | rc | 9.1 | 3e50d328f0 | 0/- |
| v9.1.1 | 2001-03-28 | yes | release | 9.1 | 486f92981d | 3/51 |
| v9.1.2rc1 | 2001-05-02 | no | rc | 9.1 | 5ddc458b2d | 0/- |
| v9.1.2 | 2001-05-04 | yes | release | 9.1 | a094732128 | 3/16 |
| v9.1.3rc1 | 2001-05-23 | no | rc | 9.1 | 25aad710d0 | 0/- |
| v9.2.0a1 | 2001-06-01 | no | alpha | 9.2 | 05317dc51d | 0/- |
| v9.2.0a2 | 2001-06-11 | no | alpha | 9.2 | dee72c6779 | 0/- |
| v9.1.3rc2 | 2001-06-18 | no | rc | 9.1 | 34c10cbe89 | 0/- |
| v9.1.3rc3 | 2001-06-28 | no | rc | 9.1 | e64a3da280 | 0/- |
| v9.1.3 | 2001-07-03 | yes | release | 9.1 | 517c1d5daa | 3/28 |
| v9.2.0a3 | 2001-07-13 | no | alpha | 9.2 | c9041258f2 | 0/- |
| v9.2.0b1 | 2001-07-17 | no | beta | 9.2 | 7728c7dc85 | 0/- |
| v9.2.0b2 | 2001-07-31 | no | beta | 9.2 | 1f5ad4f4dd | 0/- |
| v9.2.0rc1 | 2001-08-09 | no | rc | 9.2 | 1364b6deaa | 0/- |
| v9.2.0rc2 | 2001-09-06 | no | rc | 9.2 | 8df0653f05 | 0/- |
| v9.2.0rc3 | 2001-09-12 | no | rc | 9.2 | 294d64d1cc | 0/- |
| v9.2.0rc4 | 2001-09-21 | no | rc | 9.2 | afaf9371a2 | 0/- |
| v9.2.0rc5 | 2001-10-01 | no | rc | 9.2 | 06bc7fcf03 | 0/- |
| v9.2.0rc6 | 2001-10-09 | no | rc | 9.2 | a884733321 | 0/- |
| v9.2.0rc7 | 2001-10-16 | no | rc | 9.2 | 9a9d05a155 | 0/- |
| v9.2.0rc8 | 2001-10-23 | no | rc | 9.2 | 7150d5e275 | 0/- |
| v9.2.0rc9 | 2001-11-07 | no | rc | 9.2 | 4da829561f | 0/- |
| v9.2.0rc10 | 2001-11-16 | no | rc | 9.2 | 4cbcc6e25b | 0/- |
| v9.2.0 | 2001-11-25 | yes | release | 9.2 | fd212b7095 | 10/277 |
| v9.2.1rc1 | 2002-02-28 | no | rc | 9.2 | 5d2c86eb13 | 0/- |
| v9.2.1rc2 | 2002-03-29 | no | rc | 9.2 | 9bf2541ce9 | 0/- |
| v9.2.1 | 2002-04-23 | yes | release | 9.2 | 3ed9f39f74 | 4/80 |
| v9.2.0-P1 | 2002-06-01 | yes | patch | 9.2 | fde8269185 | 0/1 |
| v9.1.1-P1 | 2002-06-01 | yes | patch | 9.1 | 1c3f932921 | 0/0 |
| v9.2.2rc1 | 2002-08-08 | no | rc | 9.2 | efb1d6b0eb | 0/- |
| v9.2.2 | 2003-02-21 | yes | release | 9.2 | 3adb30769d | 8/82 |
| v9.2.3rc1 | 2003-08-06 | no | rc | 9.2 | 1b72c5d129 | 0/- |
| v9.1.1-P2 | 2003-09-01 | yes | patch | 9.1 | b39f966a0c | 0/2 |
| v9.2.3rc2 | 2003-09-17 | no | rc | 9.2 | 95956e4929 | 0/- |
| v9.2.2-P1 | 2003-09-17 | yes | patch | 9.2 | fce660ed6a | 0/1 |
| v9.1.3-P1 | 2003-09-17 | yes | patch | 9.1 | d0d3e341d1 | 0/0 |
| v9.1.3-P2 | 2003-09-19 | yes | patch | 9.1 | 8d0005164e | 0/4 |
| v9.2.2-P2 | 2003-09-19 | yes | patch | 9.2 | a9b3f643af | 0/0 |
| v9.2.3rc3 | 2003-09-19 | no | rc | 9.2 | 21ad64a269 | 0/- |
| v9.2.2-P3 | 2003-09-22 | yes | patch | 9.2 | 2785031501 | 0/2 |
| v9.1.3-P3 | 2003-09-22 | yes | patch | 9.1 | b64048e1a6 | 0/0 |
| v9.2.3 | 2003-10-17 | yes | release | 9.2 | 6106f7b31b | 3/95 |
| v9.2.4rc1 | 2004-03-16 | no | rc | 9.2 | 59d86dbcc8 | 0/- |
| v9.2.4rc2 | 2004-04-13 | no | rc | 9.2 | 6441016da9 | 0/- |
| v9.2.4rc3 | 2004-04-29 | no | rc | 9.2 | 39d114ae1b | 0/- |
| v9.2.4rc4 | 2004-05-18 | no | rc | 9.2 | 3802d6611c | 0/- |
| v9.2.3rc4 | 2004-06-08 | no | rc | 9.2 | 7dd0b097bb | 0/- |
| v9.2.4rc5 | 2004-06-11 | no | rc | 9.2 | 37bf75b905 | 0/- |
| v9.3.0rc1 | 2004-06-17 | no | rc | 9.3 | 73f0b92805 | 0/- |
| v9.3.0rc2 | 2004-07-02 | no | rc | 9.3 | 463ad05fc4 | 0/- |
| v9.2.4rc6 | 2004-07-03 | no | rc | 9.2 | 6c6734ae3a | 0/- |
| v9.2.4rc7 | 2004-08-11 | no | rc | 9.2 | a306d3623b | 0/- |
| v9.3.0rc3 | 2004-08-11 | no | rc | 9.3 | 1dbb78e467 | 0/- |
| v9.3.0rc4 | 2004-09-01 | no | rc | 9.3 | f2c7c89f84 | 0/- |
| v9.2.4rc8 | 2004-09-02 | no | rc | 9.2 | a7d9d49f29 | 0/- |
| v9.2.4 | 2004-09-20 | yes | release | 9.2 | 5aa7cc9a56 | 0/100 |
| v9.3.0 | 2004-09-20 | yes | release | 9.3 | e8a547a3eb | 0/262 |
| v9.3.1rc1 | 2005-02-09 | no | rc | 9.3 | 84d8d9e6cb | 0/- |
| v9.2.5rc1 | 2005-02-09 | no | rc | 9.2 | dbec0f1bd9 | 0/- |
| v9.3.1 | 2005-03-03 | yes | release | 9.3 | 47aee994d3 | 0/74 |
| v9.2.5 | 2005-03-03 | yes | release | 9.2 | 91ed141205 | 4/2 |
| v9.3.2b1 | 2005-09-12 | no | beta | 9.3 | f00a50a937 | 0/- |
| v9.2.6b1 | 2005-09-12 | no | beta | 9.2 | 0ce96a53d0 | 0/- |
| v9.4.0a1 | 2005-09-20 | no | alpha | 9.4 | df61987b00 | 0/- |
| v9.3.2b2 | 2005-10-14 | no | beta | 9.3 | 8457762149 | 0/- |
| v9.2.6b2 | 2005-10-14 | no | beta | 9.2 | e4e80d69b9 | 0/- |
| v9.4.0a2 | 2005-10-21 | no | alpha | 9.4 | 9aed407b75 | 0/- |
| v9.3.2rc1 | 2005-11-04 | no | rc | 9.3 | 411e34678c | 0/- |
| v9.2.6rc1 | 2005-11-04 | no | rc | 9.2 | 1089a28926 | 0/- |
| v9.4.0a3 | 2005-12-06 | no | alpha | 9.4 | 0ba8784cb9 | 0/- |
| v9.2.6 | 2005-12-14 | yes | release | 9.2 | 39e24bfe50 | 3/60 |
| v9.3.2 | 2005-12-14 | yes | release | 9.3 | 2cdd6ef127 | 0/30 |
| v9.4.0a4 | 2006-03-10 | no | alpha | 9.4 | 806f538c21 | 0/- |
| v9.4.0a5 | 2006-05-03 | no | alpha | 9.4 | 82c943cfb2 | 0/- |
| v9.3.3b1 | 2006-05-25 | no | beta | 9.3 | 7c76c03921 | 0/- |
| v9.4.0a6 | 2006-05-26 | no | alpha | 9.4 | d0afd54b34 | 0/- |
| v9.2.7b1 | 2006-05-26 | no | beta | 9.2 | c49ca02c02 | 0/- |
| v9.4.0b1 | 2006-07-24 | no | beta | 9.4 | 6f993eb201 | 0/- |
| v9.2.7rc1 | 2006-08-10 | no | rc | 9.2 | f6221d089d | 0/- |
| v9.3.3rc1 | 2006-08-10 | no | rc | 9.3 | 26d954aa04 | 0/- |
| v9.3.2-P1 | 2006-08-17 | yes | patch | 9.3 | 26c012b906 | 0/2 |
| v9.2.6-P1 | 2006-08-17 | yes | patch | 9.2 | 6b45cf2a97 | 0/0 |
| v9.3.3rc2 | 2006-08-31 | no | rc | 9.3 | 2f53e83a64 | 0/- |
| v9.2.7rc2 | 2006-08-31 | no | rc | 9.2 | 54cba99ec9 | 0/- |
| v9.4.0b2 | 2006-08-31 | no | beta | 9.4 | 19ac081b78 | 0/- |
| v9.3.2-P2 | 2006-10-04 | yes | patch | 9.3 | f40558cd8a | 0/4 |
| v9.3.3rc3 | 2006-10-17 | no | rc | 9.3 | d357463397 | 0/- |
| v9.4.0b3 | 2006-10-19 | no | beta | 9.4 | eba23747a4 | 0/- |
| v9.2.7rc3 | 2006-10-19 | no | rc | 9.2 | c056709acd | 0/- |
| v9.2.6-P2 | 2006-10-19 | yes | patch | 9.2 | 6beb40e35f | 0/0 |
| v9.4.0b4 | 2006-11-08 | no | beta | 9.4 | f31a0a6676 | 0/- |
| v9.3.3 | 2006-12-07 | yes | release | 9.3 | fe839e0abc | 0/104 |
| v9.2.7 | 2006-12-07 | yes | release | 9.2 | d763866a41 | 0/0 |
| v9.4.0rc1 | 2006-12-07 | no | rc | 9.4 | 4bf35d8214 | 0/- |
| v9.5.0a1 | 2006-12-22 | no | alpha | 9.5 | 74d6235d13 | 0/- |
| v9.3.4 | 2007-01-12 | yes | release | 9.3 | 6db1f0140e | 0/2 |
| v9.2.8 | 2007-01-12 | yes | release | 9.2 | a8b6b203c4 | 1/0 |
| v9.4.0rc2 | 2007-01-15 | no | rc | 9.4 | be9e331d5e | 0/- |
| v9.1.1-P3 | 2007-01-23 | yes | patch | 9.1 | 249bec72af | 0/0 |
| v9.2.1-P1 | 2007-02-09 | yes | patch | 9.2 | e60c0136f0 | 0/0 |
| v9.4.0 | 2007-02-15 | yes | release | 9.4 | 600305bf9b | 79/180 |
| v9.5.0a2 | 2007-03-12 | no | alpha | 9.5 | 072eaf055b | 0/- |
| v9.5.0a3 | 2007-04-04 | no | alpha | 9.5 | 9c33579709 | 0/- |
| v9.4.1 | 2007-04-30 | yes | release | 9.4 | 9bf72603fc | 0/1 |
| v9.5.0a4 | 2007-04-30 | no | alpha | 9.5 | f6476fa522 | 0/- |
| v9.5.0a5 | 2007-05-24 | no | alpha | 9.5 | d1199d9c06 | 0/- |
| v9.2.8-P1 | 2007-06-28 | yes | patch | 9.2 | b2b832c844 | 0/3 |
| v9.3.4-P1 | 2007-06-28 | yes | patch | 9.3 | e7819a56c4 | 0/0 |
| v9.4.1-P1 | 2007-07-09 | yes | patch | 9.4 | 680662166c | 0/2 |
| v9.5.0a6 | 2007-07-09 | no | alpha | 9.5 | cd315d4cf6 | 0/- |
| v9.4.2b1 | 2007-07-24 | no | beta | 9.4 | 1382bb2a20 | 0/- |
| v9.2.9b1 | 2007-08-06 | no | beta | 9.2 | c4db1740f2 | 0/- |
| v9.1.1-P4 | 2007-08-12 | yes | patch | 9.1 | 5c362e675e | 0/0 |
| v9.2.0-P2 | 2007-08-12 | yes | patch | 9.2 | 6bb68b2cb7 | 0/0 |
| v9.2.9rc1 | 2007-08-29 | no | rc | 9.2 | 457410a26c | 0/- |
| v9.2.9 | 2007-09-20 | yes | release | 9.2 | a7637b7db7 | 1/37 |
| v9.4.2rc1 | 2007-09-26 | no | rc | 9.4 | 22aa2f0019 | 0/- |
| v9.4.2rc2 | 2007-10-31 | no | rc | 9.4 | 6436129a46 | 0/- |
| v9.5.0a7 | 2007-11-09 | no | alpha | 9.5 | d5a9cb5fdd | 0/- |
| v9.4.2 | 2007-11-21 | yes | release | 9.4 | ea71a777ce | 9/50 |
| v9.5.0b1 | 2007-11-27 | no | beta | 9.5 | d7d597a2a3 | 0/- |
| v9.3.5b1 | 2007-12-17 | no | beta | 9.3 | df47a22824 | 0/- |
| v9.5.0b2 | 2008-01-29 | no | beta | 9.5 | 5205441b98 | 0/- |
| v9.3.5rc1 | 2008-02-14 | no | rc | 9.3 | 307347da97 | 0/- |
| v9.3.5rc2 | 2008-03-05 | no | rc | 9.3 | d4b72448de | 0/- |
| v9.3.5 | 2008-04-03 | yes | release | 9.3 | 725b35e59c | 4/46 |
| v9.5.0b3 | 2008-04-11 | no | beta | 9.5 | 4203f5255b | 0/- |
| v9.4.3b1 | 2008-04-18 | no | beta | 9.4 | 4bbd4fcdae | 0/- |
| v9.5.0rc1 | 2008-05-06 | no | rc | 9.5 | 47682a39a6 | 0/- |
| v9.5.0 | 2008-05-22 | yes | release | 9.5 | 4883ba14a2 | 4/99 |
| v9.4.2-P1 | 2008-05-28 | yes | patch | 9.4 | 742a17b1ea | 0/1 |
| v9.3.5-P1 | 2008-05-28 | yes | patch | 9.3 | 99ba67d065 | 0/0 |
| v9.5.0-P1 | 2008-05-28 | yes | patch | 9.5 | 919036287e | 0/0 |
| v9.4.3b2 | 2008-07-04 | no | beta | 9.4 | e146b3f662 | 0/- |
| v9.5.1b1 | 2008-07-04 | no | beta | 9.5 | 54ec55c45e | 0/- |
| v9.3.5-P2 | 2008-07-29 | yes | patch | 9.3 | 0c4df78294 | 0/11 |
| v9.4.2-P2 | 2008-07-29 | yes | patch | 9.4 | 0541399136 | 0/0 |
| v9.5.0-P2 | 2008-07-29 | yes | patch | 9.5 | 256664f0df | 1/4 |
| v9.4.2-P2-W1 | 2008-09-04 | yes | windows-only | 9.4 | 40a96669b8 | 0/2 |
| v9.3.5-P2-W1 | 2008-09-04 | yes | windows-only | 9.3 | 8bb1cafc41 | 0/0 |
| v9.5.0-P2-W1 | 2008-09-05 | yes | windows-only | 9.5 | 3685c78c57 | 0/2 |
| v9.3.5-P2-W2 | 2008-09-11 | yes | windows-only | 9.3 | ebe2d5a7c4 | 0/1 |
| v9.4.2-P2-W2 | 2008-09-11 | yes | windows-only | 9.4 | ee0720eedc | 0/0 |
| v9.5.0-P2-W2 | 2008-09-16 | yes | windows-only | 9.5 | dba9eb9640 | 0/1 |
| v9.5.1b2 | 2008-09-16 | no | beta | 9.5 | 482c6d8212 | 0/- |
| v9.4.3b3 | 2008-09-16 | no | beta | 9.4 | 3cad2dbb22 | 0/- |
| v9.3.6b1 | 2008-09-16 | no | beta | 9.3 | 0b4812d3fd | 0/- |
| v9.6.0a1 | 2008-10-16 | no | alpha | 9.6 | d922fbf53a | 0/- |
| v9.3.6rc1 | 2008-10-24 | no | rc | 9.3 | 745ab1ef7b | 0/- |
| v9.4.3rc1 | 2008-10-24 | no | rc | 9.4 | 96d66f5042 | 0/- |
| v9.5.1b3 | 2008-10-27 | no | beta | 9.5 | 40c2b7e647 | 0/- |
| v9.6.0b1 | 2008-10-29 | no | beta | 9.6 | 4178e37726 | 0/- |
| v9.3.6 | 2008-11-12 | yes | release | 9.3 | 7b3438f4d4 | 3/45 |
| v9.4.3 | 2008-11-12 | yes | release | 9.4 | f0cc3f96cd | 1/5 |
| v9.6.0rc1 | 2008-11-20 | no | rc | 9.6 | 6f6d3c23f4 | 0/- |
| v9.5.1rc1 | 2008-11-20 | no | rc | 9.5 | 619d0e3aa0 | 0/- |
| v9.5.1rc2 | 2008-12-13 | no | rc | 9.5 | adc62dbc06 | 0/- |
| v9.6.0rc2 | 2008-12-14 | no | rc | 9.6 | b1faf7c293 | 0/- |
| v9.6.0 | 2008-12-21 | yes | release | 9.6 | 8b07cdbf50 | 14/67 |
| v9.5.1 | 2008-12-21 | yes | release | 9.5 | 1553b2e323 | 0/0 |
| v9.6.0-P1 | 2008-12-24 | yes | patch | 9.6 | f7407f97bd | 0/1 |
| v9.5.1-P1 | 2008-12-24 | yes | patch | 9.5 | 201f5fd82e | 0/0 |
| v9.4.3-P1 | 2008-12-24 | yes | patch | 9.4 | e3b07fa444 | 0/0 |
| v9.3.6-P1 | 2008-12-24 | yes | patch | 9.3 | e18e06754a | 0/0 |
| v9.6.1b1 | 2009-03-13 | no | beta | 9.6 | f43d43aa7d | 0/- |
| v9.5.1-P2 | 2009-03-17 | yes | patch | 9.5 | 1b30e547b9 | 1/1 |
| v9.4.3-P2 | 2009-03-17 | yes | patch | 9.4 | df32168c3c | 0/0 |
| v9.3.6-P2 | 2009-03-17 | yes | patch | 9.3 | 2387d20da2 | 0/0 |
| v9.6.1rc1 | 2009-05-11 | no | rc | 9.6 | b19741d515 | 0/- |
| v9.6.1 | 2009-06-09 | yes | release | 9.6 | 48f475e778 | 14/70 |
| v9.7.0a1 | 2009-06-18 | no | alpha | 9.7 | 31a6411712 | 0/- |
| v9.4.3-P3 | 2009-07-28 | yes | patch | 9.4 | 768c1b40df | 0/1 |
| v9.5.1-P3 | 2009-07-28 | yes | patch | 9.5 | 62eb72a08f | 0/0 |
| v9.6.1-P1 | 2009-07-28 | yes | patch | 9.6 | f1a7f3d680 | 0/0 |
| v9.7.0a2 | 2009-08-05 | no | alpha | 9.7 | 8c4855b8fc | 0/- |
| v9.4.4b1 | 2009-08-14 | no | beta | 9.4 | 8a497740d6 | 0/- |
| v9.5.2b1 | 2009-08-14 | no | beta | 9.5 | 8e29f7f28a | 0/- |
| v9.5.2rc1 | 2009-09-09 | no | rc | 9.5 | 989256b896 | 0/- |
| v9.7.0a3 | 2009-09-10 | no | alpha | 9.7 | 1525befad6 | 0/- |
| v9.5.2 | 2009-09-21 | yes | release | 9.5 | 77e1b4805b | 3/29 |
| v9.7.0b1 | 2009-10-19 | no | beta | 9.7 | 97745aa14d | 0/- |
| v9.7.0b2 | 2009-10-28 | no | beta | 9.7 | 6c502d455e | 0/- |
| v9.4-ESVb1 | 2009-11-05 | no | beta | 9.4-ESV | e414d1aa9a | 0/- |
| v9.5.2-P1 | 2009-11-18 | yes | patch | 9.5 | 1503d91dbf | 0/1 |
| v9.6.1-P2 | 2009-11-18 | yes | patch | 9.6 | 0ec67eaaa4 | 0/0 |
| v9.4.3-P4 | 2009-11-19 | yes | patch | 9.4 | 7d6e62e3b6 | 0/0 |
| v9.7.0b3 | 2009-11-24 | no | beta | 9.7 | 764b3fac19 | 0/- |
| v9.6.2b1 | 2009-12-03 | no | beta | 9.6 | 2f36054bb0 | 0/- |
| v9.7.0rc1 | 2009-12-08 | no | rc | 9.7 | e1e898cf25 | 0/- |
| v9.4-ESVrc1 | 2009-12-11 | no | rc | 9.4-ESV | e312c286f8 | 0/- |
| v9.6.1-P3 | 2010-01-07 | yes | patch | 9.6 | 7508907262 | 1/3 |
| v9.4.3-P5 | 2010-01-07 | yes | patch | 9.4 | 22ae16e540 | 0/0 |
| v9.5.2-P2 | 2010-01-07 | yes | patch | 9.5 | 9bc8d05a23 | 0/0 |
| v9.6.2rc1 | 2010-01-15 | no | rc | 9.6 | 905c946de0 | 0/- |
| v9.4-ESV | 2010-01-21 | yes | esv | 9.4-ESV | 4075946cf1 | 1/7 |
| v9.7.0rc2 | 2010-01-22 | no | rc | 9.7 | 285891821e | 0/- |
| v9.7.0 | 2010-02-16 | yes | release | 9.7 | e3734ed6d1 | 85/233 |
| v9.6.2 | 2010-02-18 | yes | release | 9.6 | dbd13430ce | 0/1 |
| v9.5.2-P3 | 2010-03-03 | yes | patch | 9.5 | 31bba4b1ae | 1/1 |
| v9.6-ESV | 2010-03-04 | yes | esv | 9.6-ESV | 2176cc236d | 0/0 |
| v9.6.2-P1 | 2010-03-04 | yes | patch | 9.6 | 5bb9c13ea0 | 0/0 |
| v9.7.0-P1 | 2010-03-04 | yes | patch | 9.7 | 479811a46c | 0/0 |
| v9.4-ESV-R1 | 2010-03-04 | yes | esv | 9.4-ESV | c3582936b1 | 0/0 |
| v9.4-ESV-R2 | 2010-05-10 | yes | esv | 9.4-ESV | 078580a74d | 0/1 |
| v9.5.2-P4 | 2010-05-10 | yes | patch | 9.5 | 0c9f4521b1 | 0/0 |
| v9.6.2-P2 | 2010-05-10 | yes | patch | 9.6 | 8f0fdad5d6 | 0/0 |
| v9.7.0-P2 | 2010-05-10 | yes | patch | 9.7 | 1f84b6f979 | 0/0 |
| v9.6-ESV-R1 | 2010-05-10 | yes | esv | 9.6-ESV | 1fc35fe236 | 0/0 |
| v9.7.1b1 | 2010-05-19 | no | beta | 9.7 | a116e2efec | 0/- |
| v9.7.1rc1 | 2010-06-02 | no | rc | 9.7 | 82404f5aef | 0/- |
| v9.7.1 | 2010-06-15 | yes | release | 9.7 | 0890eb695b | 15/55 |
| v9.7.1-P1 | 2010-06-29 | yes | patch | 9.7 | 476b0351b1 | 1/2 |
| v9.7.1-P2 | 2010-07-15 | yes | patch | 9.7 | edabefeb1a | 1/1 |
| v9.7.2b1 | 2010-07-20 | no | beta | 9.7 | 01d404c4ad | 0/- |
| v9.5.3b1 | 2010-08-09 | no | beta | 9.5 | 6776061a4c | 0/- |
| v9.7.2rc1 | 2010-08-17 | no | rc | 9.7 | 704e4daff8 | 0/- |
| v9.7.2 | 2010-09-02 | yes | release | 9.7 | 4cb7af6b18 | 6/31 |
| v9.4-ESV-R3 | 2010-09-02 | yes | esv | 9.4-ESV | 7245a76211 | 0/0 |
| v9.6-ESV-R2 | 2010-09-06 | yes | esv | 9.6-ESV | 46054b10cc | 0/0 |
| v9.5.3rc1 | 2010-09-09 | no | rc | 9.5 | 599f17349f | 0/- |
| v9.7.2-P1 | 2010-09-15 | yes | patch | 9.7 | 03f3107e03 | 0/5 |
| v9.7.2-P2 | 2010-09-24 | yes | patch | 9.7 | c6965f062d | 0/1 |
| v9.4-ESV-R4 | 2010-11-29 | yes | esv | 9.4-ESV | 9ef41eec67 | 2/4 |
| v9.6.2-P3 | 2010-11-29 | yes | patch | 9.6 | bec226774c | 0/2 |
| v9.6-ESV-R3 | 2010-11-29 | yes | esv | 9.6-ESV | ccf3c9495e | 0/5 |
| v9.7.2-P3 | 2010-11-29 | yes | patch | 9.7 | 509e4c4d6e | 0/1 |
| v9.6.3b1 | 2010-12-09 | no | beta | 9.6 | 57628d8c51 | 0/- |
| v9.8.0a1 | 2010-12-10 | no | alpha | 9.8 | ddad831899 | 0/- |
| v9.7.3b1 | 2010-12-10 | no | beta | 9.7 | 465d41bd1c | 0/- |
| v9.7.3rc1 | 2011-01-14 | no | rc | 9.7 | 7bc44cccc1 | 0/- |
| v9.6.3rc1 | 2011-01-14 | no | rc | 9.6 | eb7b89e4d6 | 0/- |
| v9.8.0b1 | 2011-01-23 | no | beta | 9.8 | d21bca8873 | 0/- |
| v9.6.3 | 2011-01-31 | yes | release | 9.6 | 70f21f30ce | 2/18 |
| v9.8.0rc1 | 2011-02-08 | no | rc | 9.8 | 24035989ce | 0/- |
| v9.8.0 | 2011-02-21 | yes | release | 9.8 | 89e60b8333 | 10/47 |
| v9.7.3 | 2011-02-26 | yes | release | 9.7 | eefb0cb790 | 0/0 |
| v9.6-ESV-R4 | 2011-03-28 | yes | esv | 9.6-ESV | 36b886ae36 | 0/0 |
| v9.6-ESV-R5b1 | 2011-04-08 | no | beta | 9.6-ESV | 8f926ae56d | 0/- |
| v9.7.4b1 | 2011-04-08 | no | beta | 9.7 | c802ba3785 | 0/- |
| v9.4-ESV-R5b1 | 2011-04-08 | no | beta | 9.4-ESV | d340cfafd2 | 0/- |
| v9.8.0-P1 | 2011-04-27 | yes | patch | 9.8 | a7cbf356e1 | 1/1 |
| v9.8.1b1 | 2011-05-17 | no | beta | 9.8 | e86659f1d9 | 0/- |
| v9.6-ESV-R4-P1 | 2011-05-27 | yes | esv-patch | 9.6-ESV | 9856dd776f | 1/2 |
| v9.7.3-P1 | 2011-05-27 | yes | patch | 9.7 | 3f30124cd6 | 0/0 |
| v9.8.0-P2 | 2011-05-27 | yes | patch | 9.8 | 432db2f57b | 0/0 |
| v9.4-ESV-R4-P1 | 2011-05-27 | yes | esv-patch | 9.4-ESV | 259fe7b42f | 0/0 |
| v9.6-ESV-R4-P2 | 2011-06-09 | yes | esv-patch | 9.6-ESV | 45b34964d2 | 0/1 |
| v9.7.3-P2 | 2011-06-09 | yes | patch | 9.7 | 200a19bc50 | 0/0 |
| v9.8.0-P3 | 2011-06-09 | yes | patch | 9.8 | 5745823158 | 0/3 |
| v9.8.1b2 | 2011-06-15 | no | beta | 9.8 | 49e3895104 | 0/- |
| v9.7.4rc1 | 2011-06-16 | no | rc | 9.7 | 6c80f9dc3a | 0/- |
| v9.6-ESV-R5rc1 | 2011-06-16 | no | rc | 9.6-ESV | e6254ce353 | 0/- |
| v9.4-ESV-R5rc1 | 2011-06-16 | no | rc | 9.4-ESV | b29ba963e3 | 0/- |
| v9.6-ESV-R4-P3 | 2011-06-21 | yes | esv-patch | 9.6-ESV | 52ec16a8c3 | 0/1 |
| v9.7.3-P3 | 2011-06-21 | yes | patch | 9.7 | 304fe688c0 | 0/0 |
| v9.8.0-P4 | 2011-06-21 | yes | patch | 9.8 | 0ee905d040 | 0/0 |
| v9.8.1b3 | 2011-07-09 | no | beta | 9.8 | b063d569ef | 0/- |
| v9.7.4 | 2011-07-24 | yes | release | 9.7 | 14b2ad7281 | 21/67 |
| v9.4-ESV-R5 | 2011-07-24 | yes | esv | 9.4-ESV | 3c4a5faf6f | 0/1 |
| v9.6-ESV-R5 | 2011-07-24 | yes | esv | 9.6-ESV | 18f7c6fcac | 0/0 |
| v9.8.1rc1 | 2011-08-09 | no | rc | 9.8 | 5d2e823828 | 0/- |
| v9.8.1 | 2011-08-24 | yes | release | 9.8 | af8f35aa7c | 5/20 |
| v9.9.0a1 | 2011-08-25 | no | alpha | 9.9 | a993eecb16 | 0/- |
| v9.9.0a2 | 2011-09-23 | no | alpha | 9.9 | 39c38f5156 | 0/- |
| v9.9.0a3 | 2011-10-14 | no | alpha | 9.9 | ac8984d5ae | 0/- |
| v9.9.0b1 | 2011-10-29 | no | beta | 9.9 | 8a2d9ba36c | 0/- |
| v9.4-ESV-R5-P1 | 2011-11-16 | yes | esv-patch | 9.4-ESV | 00a93b2466 | 1/1 |
| v9.8.1-P1 | 2011-11-16 | yes | patch | 9.8 | 0ad328daa5 | 0/0 |
| v9.6-ESV-R5-P1 | 2011-11-16 | yes | esv-patch | 9.6-ESV | b0a7955250 | 0/0 |
| v9.7.4-P1 | 2011-11-16 | yes | patch | 9.7 | 9f4dbf5b58 | 0/0 |
| v9.9.0b2 | 2011-11-18 | no | beta | 9.9 | 9596ff0d5d | 0/- |
| v9.6-ESV-R6b1 | 2011-11-24 | no | beta | 9.6-ESV | f49495bc4e | 0/- |
| v9.7.5b1 | 2011-12-05 | no | beta | 9.7 | db2cb7eaae | 0/- |
| v9.8.2b1 | 2011-12-05 | no | beta | 9.8 | 90d46d8ed1 | 0/- |
| v9.9.0rc1 | 2011-12-24 | no | rc | 9.9 | aec4b2442a | 0/- |
| v9.6-ESV-R6rc1 | 2012-01-04 | no | rc | 9.6-ESV | e9a5f2860c | 0/- |
| v9.7.5rc1 | 2012-01-04 | no | rc | 9.7 | 7f06b20a83 | 0/- |
| v9.8.2rc1 | 2012-01-04 | no | rc | 9.8 | a5cea6308e | 0/- |
| v9.9.0rc2 | 2012-02-14 | no | rc | 9.9 | 36cf7cff6d | 0/- |
| v9.6-ESV-R6rc2 | 2012-02-15 | no | rc | 9.6-ESV | 1d161c5ed7 | 0/- |
| v9.7.5rc2 | 2012-02-15 | no | rc | 9.7 | adbd86faa3 | 0/- |
| v9.8.2rc2 | 2012-02-15 | no | rc | 9.8 | ce9a779497 | 0/- |
| v9.9.0rc3 | 2012-02-15 | no | rc | 9.9 | afaa271287 | 0/- |
| v9.9.0rc4 | 2012-02-23 | no | rc | 9.9 | 6ef023873e | 0/- |
| v9.9.0 | 2012-02-23 | yes | release | 9.9 | 3514c49b2f | 43/165 |
| v9.7.5 | 2012-03-22 | yes | release | 9.7 | 9bf892ead1 | 0/8 |
| v9.6-ESV-R6 | 2012-03-26 | yes | esv | 9.6-ESV | 0049ddf3a6 | 0/0 |
| v9.8.2 | 2012-04-09 | yes | release | 9.8 | 81360275ec | 0/1 |
| v9.9.0-W1 | 2012-04-24 | yes | windows-only | 9.9 | 83bf3128f5 | 0/1 |
| v9.8.2-W1 | 2012-04-24 | yes | windows-only | 9.8 | 812c7ce0f0 | 0/0 |
| v9.7.5-W1 | 2012-04-24 | yes | windows-only | 9.7 | 4e29752898 | 0/0 |
| v9.9.1 | 2012-05-10 | yes | release | 9.9 | f5e44458b8 | 1/17 |
| v9.8.3 | 2012-05-10 | yes | release | 9.8 | 72c1a6b333 | 0/0 |
| v9.7.6 | 2012-05-10 | yes | release | 9.7 | 6451a2bd14 | 0/0 |
| v9.6-ESV-R7 | 2012-05-10 | yes | esv | 9.6-ESV | 1511cda8b6 | 0/0 |
| v9.9.1-P1 | 2012-06-01 | yes | patch | 9.9 | ba3ee3c56b | 0/1 |
| v9.7.6-P1 | 2012-06-01 | yes | patch | 9.7 | b0713c8193 | 0/0 |
| v9.8.3-P1 | 2012-06-01 | yes | patch | 9.8 | 0d0c12c447 | 0/0 |
| v9.6-ESV-R7-P1 | 2012-06-01 | yes | esv-patch | 9.6-ESV | 81b9842e47 | 0/0 |
| v9.8.3-P2 | 2012-07-02 | yes | patch | 9.8 | 68f2ec3e7b | 0/2 |
| v9.6-ESV-R7-P2 | 2012-07-02 | yes | esv-patch | 9.6-ESV | e7903c066b | 0/1 |
| v9.7.6-P2 | 2012-07-02 | yes | patch | 9.7 | fc0fcb8103 | 0/0 |
| v9.9.1-P2 | 2012-07-12 | yes | patch | 9.9 | 447a6514e9 | 0/2 |
| v9.9.2b1 | 2012-07-20 | no | beta | 9.9 | 53cf25c993 | 0/- |
| v9.6-ESV-R8b1 | 2012-07-24 | no | beta | 9.6-ESV | 58d4e6452a | 0/- |
| v9.7.7b1 | 2012-07-24 | no | beta | 9.7 | 6af32d4dbd | 0/- |
| v9.8.4b1 | 2012-07-24 | no | beta | 9.8 | 7e64041031 | 0/- |
| v9.7.7rc1 | 2012-08-23 | no | rc | 9.7 | 807e964f99 | 0/- |
| v9.8.4rc1 | 2012-08-23 | no | rc | 9.8 | 849758530a | 0/- |
| v9.9.2rc1 | 2012-08-23 | no | rc | 9.9 | 799c467a90 | 0/- |
| v9.6-ESV-R7-P3 | 2012-08-24 | yes | esv-patch | 9.6-ESV | c1cce13f0e | 0/1 |
| v9.7.6-P3 | 2012-08-24 | yes | patch | 9.7 | acc452ea78 | 0/0 |
| v9.8.3-P3 | 2012-08-24 | yes | patch | 9.8 | ef35a379e8 | 0/0 |
| v9.9.1-P3 | 2012-08-24 | yes | patch | 9.9 | 2cc8b1e5bb | 0/0 |
| v9.7.7 | 2012-09-26 | yes | release | 9.7 | b32a14510f | 6/23 |
| v9.6-ESV-R8 | 2012-09-26 | yes | esv | 9.6-ESV | ecc6435be0 | 0/1 |
| v9.8.4 | 2012-09-26 | yes | release | 9.8 | 5dffd984bf | 1/5 |
| v9.9.2 | 2012-09-26 | yes | release | 9.9 | 170f87bf92 | 3/8 |
| v9.6-ESV-R7-P4 | 2012-09-26 | yes | esv-patch | 9.6-ESV | 31db231b89 | 0/0 |
| v9.7.6-P4 | 2012-09-26 | yes | patch | 9.7 | 0ecd9e0c63 | 0/0 |
| v9.8.3-P4 | 2012-09-26 | yes | patch | 9.8 | 6489261b83 | 0/0 |
| v9.9.1-P4 | 2012-09-26 | yes | patch | 9.9 | 44bf36c9ab | 0/0 |
| v9.9.2-P1 | 2012-10-26 | yes | patch | 9.9 | 489c6c10f7 | 0/1 |
| v9.8.4-P1 | 2012-10-26 | yes | patch | 9.8 | 6eaf3d3bb6 | 0/0 |
| v9.9.3b1 | 2013-01-21 | no | beta | 9.9 | 1c59cea1c0 | 0/- |
| v9.8.5b1 | 2013-01-21 | no | beta | 9.8 | 862e51f42b | 0/- |
| v9.6-ESV-R9b1 | 2013-01-21 | no | beta | 9.6-ESV | 4f18cc1174 | 0/- |
| v9.9.2-P2 | 2013-03-06 | yes | patch | 9.9 | 5f7c9ab92b | 0/1 |
| v9.8.4-P2 | 2013-03-06 | yes | patch | 9.8 | 7c1ef8f05c | 0/0 |
| v9.6-ESV-R9b2 | 2013-03-07 | no | beta | 9.6-ESV | b0f3042e37 | 0/- |
| v9.8.5b2 | 2013-03-07 | no | beta | 9.8 | 8d9304dc7d | 0/- |
| v9.9.3b2 | 2013-03-07 | no | beta | 9.9 | aa7c259035 | 0/- |
| v9.9.3rc1 | 2013-04-05 | no | rc | 9.9 | 4e1de77656 | 0/- |
| v9.8.5rc1 | 2013-04-05 | no | rc | 9.8 | 640be3c898 | 0/- |
| v9.6-ESV-R9rc1 | 2013-04-05 | no | rc | 9.6-ESV | 908a5408f3 | 0/- |
| v9.6-ESV-R9rc2 | 2013-04-30 | no | rc | 9.6-ESV | a32b34e372 | 0/- |
| v9.8.5rc2 | 2013-04-30 | no | rc | 9.8 | 1c67f3be9f | 0/- |
| v9.9.3rc2 | 2013-04-30 | no | rc | 9.9 | c7fcef622d | 0/- |
| v9.9.3 | 2013-05-17 | yes | release | 9.9 | d281b39456 | 27/153 |
| v9.8.5 | 2013-05-17 | yes | release | 9.8 | bee549e53e | 0/1 |
| v9.6-ESV-R9 | 2013-05-17 | yes | esv | 9.6-ESV | 8dfe8cb671 | 0/0 |
| v9.9.3-P1 | 2013-06-04 | yes | patch | 9.9 | 58d2f2e260 | 0/1 |
| v9.8.5-P1 | 2013-06-04 | yes | patch | 9.8 | df6718246c | 0/0 |
| v9.6-ESV-R9-P1 | 2013-06-04 | yes | esv-patch | 9.6-ESV | a058f20157 | 0/0 |
| v9.6-ESV-R10b1 | 2013-07-01 | no | beta | 9.6-ESV | bfb778470a | 0/- |
| v9.9.4b1 | 2013-07-01 | no | beta | 9.9 | cd053d6805 | 0/- |
| v9.8.6b1 | 2013-07-01 | no | beta | 9.8 | 9383a01afc | 0/- |
| v9.6-ESV-R10rc1 | 2013-07-15 | no | rc | 9.6-ESV | 166b961979 | 0/- |
| v9.8.5-P2 | 2013-07-17 | yes | patch | 9.8 | de58cd1a5f | 1/1 |
| v9.9.3-P2 | 2013-07-17 | yes | patch | 9.9 | d8a6fe8b4d | 0/0 |
| v9.8.6rc1 | 2013-07-18 | no | rc | 9.8 | cb39171dd5 | 0/- |
| v9.9.4rc1 | 2013-07-19 | no | rc | 9.9 | 9d0313350a | 0/- |
| v9.8.6rc2 | 2013-08-19 | no | rc | 9.8 | 415f8d470d | 0/- |
| v9.9.4rc2 | 2013-08-19 | no | rc | 9.9 | 2d1fd70e51 | 0/- |
| v9.6-ESV-R10rc2 | 2013-08-19 | no | rc | 9.6-ESV | 78e1b0e742 | 0/- |
| v9.9.4 | 2013-09-04 | yes | release | 9.9 | 8f9657aaf6 | 4/51 |
| v9.8.6 | 2013-09-04 | yes | release | 9.8 | aa2232fc88 | 0/0 |
| v9.6-ESV-R10 | 2013-09-04 | yes | esv | 9.6-ESV | d61392dc24 | 0/0 |
| v9.6-ESV-R10-P1 | 2013-10-16 | yes | esv-patch | 9.6-ESV | e3f91ffca0 | 0/1 |
| v9.8.6-P1 | 2013-10-16 | yes | patch | 9.8 | aefa9de2cf | 0/0 |
| v9.9.4-P1 | 2013-10-16 | yes | patch | 9.9 | 07aaf1ef49 | 0/0 |
| v9.10.0a1 | 2013-11-18 | no | alpha | 9.10 | 15eb0cb8e1 | 0/- |
| v9.6-ESV-R11b1 | 2013-12-11 | no | beta | 9.6-ESV | 051a810e4b | 0/- |
| v9.9.5b1 | 2013-12-11 | no | beta | 9.9 | a51a573942 | 0/- |
| v9.8.7b1 | 2013-12-11 | no | beta | 9.8 | c9c07bb5d6 | 0/- |
| v9.9.4-P2 | 2013-12-20 | yes | patch | 9.9 | 3f00a920fa | 1/2 |
| v9.8.6-P2 | 2013-12-20 | yes | patch | 9.8 | ff76ff6888 | 0/0 |
| v9.8.9-P2 | 2013-12-20 | yes | patch | 9.8 | ff76ff6888 | 0/0 |
| v9.9-ESV-R10-P2 | 2013-12-20 | yes | esv-patch | 9.9-ESV | 887ecb10fa | 0/0 |
| v9.6-ESV-R11rc1 | 2014-01-10 | no | rc | 9.6-ESV | 624ac2af5a | 0/- |
| v9.8.7rc1 | 2014-01-10 | no | rc | 9.8 | 4785004e3e | 0/- |
| v9.9.5rc1 | 2014-01-11 | no | rc | 9.9 | f7a59390e6 | 0/- |
| v9.6-ESV-R11rc2 | 2014-01-17 | no | rc | 9.6-ESV | 5f2ecf827f | 0/- |
| v9.8.7rc2 | 2014-01-17 | no | rc | 9.8 | e7666e1bac | 0/- |
| v9.9.5rc2 | 2014-01-17 | no | rc | 9.9 | ea195f0b43 | 0/- |
| v9.9.5 | 2014-01-27 | yes | release | 9.9 | f9b8a50e30 | 7/58 |
| v9.8.7 | 2014-01-27 | yes | release | 9.8 | 231d741842 | 0/0 |
| v9.6-ESV-R11 | 2014-01-27 | yes | esv | 9.6-ESV | 5e848fe578 | 0/0 |
| v9.10.0a2 | 2014-02-04 | no | alpha | 9.10 | a8cdf2a2e7 | 0/- |
| v9.9.5-W1 | 2014-02-06 | yes | windows-only | 9.9 | ecd1b8f348 | 0/1 |
| v9.8.7-W1 | 2014-02-06 | yes | windows-only | 9.8 | 5202fd728f | 0/0 |
| v9.10.0b1 | 2014-02-24 | no | beta | 9.10 | ed70f92dd0 | 0/- |
| v9.10.0b2 | 2014-03-14 | no | beta | 9.10 | 8058292627 | 0/- |
| v9.10.0rc1 | 2014-04-07 | no | rc | 9.10 | f5df4974b7 | 0/- |
| v9.10.0rc2 | 2014-04-23 | no | rc | 9.10 | a326778a0a | 0/- |
| v9.10.0 | 2014-04-28 | yes | release | 9.10 | 63fbb3ea39 | 24/185 |
| v9.10.0-P1 | 2014-05-05 | yes | patch | 9.10 | e94d8db1ad | 0/1 |
| v9.9.5-P1 | 2014-05-23 | yes | patch | 9.9 | 2f73dd493f | 0/2 |
| v9.8.7-P1 | 2014-05-24 | yes | patch | 9.8 | eb9529a257 | 0/0 |
| v9.10.0-P2 | 2014-05-27 | yes | patch | 9.10 | d23ac0434f | 1/5 |
| v9.10.1b1 | 2014-06-23 | no | beta | 9.10 | cc152ad50f | 0/- |
| v9.9.6b1 | 2014-06-23 | no | beta | 9.9 | 27897e9d38 | 0/- |
| v9.8.8b1 | 2014-06-23 | no | beta | 9.8 | 32dccf62bb | 0/- |
| v9.9.6b2 | 2014-08-06 | no | beta | 9.9 | 4cdc56f375 | 0/- |
| v9.8.8b2 | 2014-08-06 | no | beta | 9.8 | 6af1195f7e | 0/- |
| v9.10.1b2 | 2014-08-06 | no | beta | 9.10 | bf3ebcb44c | 0/- |
| v9.10.1rc1 | 2014-08-29 | no | rc | 9.10 | 9c1a043383 | 0/- |
| v9.8.8rc1 | 2014-08-29 | no | rc | 9.8 | 6b9e465adb | 0/- |
| v9.9.6rc1 | 2014-08-29 | no | rc | 9.9 | 95ac626e8d | 0/- |
| v9.10.1rc2 | 2014-09-05 | no | rc | 9.10 | 90f5dc6f45 | 0/- |
| v9.9.6rc2 | 2014-09-05 | no | rc | 9.9 | e025ff45dc | 0/- |
| v9.8.8rc2 | 2014-09-05 | no | rc | 9.8 | 90b0210eac | 0/- |
| v9.10.1 | 2014-09-16 | yes | release | 9.10 | fe66c6b152 | 9/98 |
| v9.9.6 | 2014-09-16 | yes | release | 9.9 | ea4e9ef83b | 0/1 |
| v9.8.8 | 2014-09-16 | yes | release | 9.8 | 8fc2e36186 | 0/0 |
| v9.10.1-P1 | 2014-11-20 | yes | patch | 9.10 | 162bfa6274 | 4/4 |
| v9.9.6-P1 | 2014-11-20 | yes | patch | 9.9 | 3612d8fb12 | 0/0 |
| v9.10.2b1 | 2014-12-29 | no | beta | 9.10 | fb3b6818ad | 0/- |
| v9.9.7b1 | 2014-12-30 | no | beta | 9.9 | abbade6bd1 | 0/- |
| v9.10.2rc1 | 2015-01-26 | no | rc | 9.10 | d0c7c4694d | 0/- |
| v9.9.7rc1 | 2015-01-26 | no | rc | 9.9 | 1e590ad71b | 0/- |
| v9.10.1-P2 | 2015-02-10 | yes | patch | 9.10 | 58bfdeb650 | 1/2 |
| v9.10.2rc2 | 2015-02-10 | no | rc | 9.10 | 551bea5743 | 0/- |
| v9.9.7rc2 | 2015-02-10 | no | rc | 9.9 | d7e11eb2d3 | 0/- |
| v9.9.6-P2 | 2015-02-11 | yes | patch | 9.9 | 6e349439f0 | 0/0 |
| v9.10.2 | 2015-02-18 | yes | release | 9.10 | 53e49fb5a8 | 9/75 |
| v9.9.7 | 2015-02-18 | yes | release | 9.9 | e87fa9ae0f | 0/1 |
| v9.10.2-P1 | 2015-06-09 | yes | patch | 9.10 | e6f4c9333a | 0/9 |
| v9.9.7-P1 | 2015-06-17 | yes | patch | 9.9 | 64f383844f | 1/1 |
| v9.10.2-P2 | 2015-06-17 | yes | patch | 9.10 | 638a11d49e | 0/0 |
| v9.9.7-P2 | 2015-07-14 | yes | patch | 9.9 | 304c9a9f07 | 1/1 |
| v9.10.2-P3 | 2015-07-14 | yes | patch | 9.10 | e5e8feeccd | 0/0 |
| v9.10.3b1 | 2015-08-03 | no | beta | 9.10 | b3e2361dba | 0/- |
| v9.9.8b1 | 2015-08-03 | no | beta | 9.9 | eca0e613de | 0/- |
| v9.10.2-P4 | 2015-08-15 | yes | patch | 9.10 | 2754d37321 | 2/2 |
| v9.9.7-P3 | 2015-08-15 | yes | patch | 9.9 | 464a99d5f5 | 0/0 |
| v9.10.3rc1 | 2015-08-25 | no | rc | 9.10 | 29904d0564 | 0/- |
| v9.9.8rc1 | 2015-08-25 | no | rc | 9.9 | 73a3d1f8cf | 0/- |
| v9.10.3 | 2015-09-09 | yes | release | 9.10 | 2799933bc6 | 8/101 |
| v9.9.8 | 2015-09-09 | yes | release | 9.9 | 2d6d4babba | 0/2 |
| v9.10.3-P2 | 2015-12-06 | yes | patch | 9.10 | f9be8b2189 | 3/4 |
| v9.9.8-P2 | 2015-12-06 | yes | patch | 9.9 | 8f4dc43fe9 | 0/0 |
| v9.9.8-P3 | 2016-01-06 | yes | patch | 9.9 | c6638fb259 | 1/2 |
| v9.10.3-P3 | 2016-01-06 | yes | patch | 9.10 | bdaecad72d | 1/1 |
| v9.10.3-P4 | 2016-02-29 | yes | patch | 9.10 | ebd72b3f6a | 3/3 |
| v9.9.8-P4 | 2016-02-29 | yes | patch | 9.9 | deea0d7033 | 0/0 |
| v9.10.4b1 | 2016-03-09 | no | beta | 9.10 | 632f984881 | 0/- |
| v9.9.9b1 | 2016-03-09 | no | beta | 9.9 | 9833cd85a8 | 0/- |
| v9.10.4b2 | 2016-03-11 | no | beta | 9.10 | d36f894b88 | 0/- |
| v9.11.0a1 | 2016-03-23 | no | alpha | 9.11 | 7fa4c18451 | 0/- |
| v9.10.4b3 | 2016-03-25 | no | beta | 9.10 | 2f98c1c2a0 | 0/- |
| v9.9.9b2 | 2016-03-25 | no | beta | 9.9 | d6d860e96e | 0/- |
| v9.10.4rc1 | 2016-04-14 | no | rc | 9.10 | cea32f84f0 | 0/- |
| v9.9.9rc1 | 2016-04-15 | no | rc | 9.9 | dc7668b449 | 0/- |
| v9.10.4 | 2016-04-20 | yes | release | 9.10 | a5e4938f2d | 7/112 |
| v9.9.9 | 2016-04-20 | yes | release | 9.9 | b7843f9794 | 0/2 |
| v9.9.9-P1 | 2016-05-22 | yes | patch | 9.9 | 99ed57a343 | 0/2 |
| v9.10.4-P1 | 2016-05-24 | yes | patch | 9.10 | adfc58895a | 0/1 |
| v9.11.0a2 | 2016-05-24 | no | alpha | 9.11 | 3ba1f79ade | 0/- |
| v9.11.0a3 | 2016-06-01 | no | alpha | 9.11 | ce2dc26bc5 | 0/- |
| v9.11.0b1 | 2016-06-27 | no | beta | 9.11 | dca6957b62 | 0/- |
| v9.9.9-P2 | 2016-07-13 | yes | patch | 9.9 | e8948b831a | 2/3 |
| v9.10.4-P2 | 2016-07-13 | yes | patch | 9.10 | 7658a94c1e | 0/0 |
| v9.11.0b2 | 2016-07-14 | no | beta | 9.11 | 111ec860a8 | 0/- |
| v9.11.0b3 | 2016-07-28 | no | beta | 9.11 | a23f742c3d | 0/- |
| v9.11.0rc1 | 2016-08-30 | no | rc | 9.11 | e0815f8120 | 0/- |
| v9.9.9-P3 | 2016-09-09 | yes | patch | 9.9 | 1b68143f20 | 1/1 |
| v9.12.0a0 | 2016-09-12 | no | alpha | 9.12 | 7ad784388c | 0/- |
| v9.10.4-P3 | 2016-09-14 | yes | patch | 9.10 | 7e49f11e98 | 0/1 |
| v9.11.0rc2 | 2016-09-14 | no | rc | 9.11 | 31c7bf574e | 0/- |
| v9.11.0rc3 | 2016-09-23 | no | rc | 9.11 | c54d7ba815 | 0/- |
| v9.11.0 | 2016-09-29 | yes | release | 9.11 | 1477c19dd9 | 29/220 |
| v9.10.4-P4 | 2016-10-21 | yes | patch | 9.10 | 853aa4b2e0 | 1/1 |
| v9.9.9-P4 | 2016-10-21 | yes | patch | 9.9 | 53185941dd | 0/0 |
| v9.11.0-P1 | 2016-10-21 | yes | patch | 9.11 | 1e9bd53d5e | 0/0 |
| v9.9.9-P5 | 2016-12-11 | yes | patch | 9.9 | 1ab232a0c0 | 3/6 |
| v9.11.0-P2 | 2016-12-11 | yes | patch | 9.11 | 9713922880 | 1/1 |
| v9.10.4-P5 | 2016-12-11 | yes | patch | 9.10 | 2b12043ba0 | 0/0 |
| v9.9.10b1 | 2016-12-29 | no | beta | 9.9 | 43281eeb83 | 0/- |
| v9.11.1b1 | 2016-12-29 | no | beta | 9.11 | e7f06a8535 | 0/- |
| v9.10.5b1 | 2016-12-29 | no | beta | 9.10 | 341e64a2de | 0/- |
| v9.11.0-P3 | 2017-01-31 | yes | patch | 9.11 | 4801fbccaa | 1/2 |
| v9.10.4-P6 | 2017-01-31 | yes | patch | 9.10 | a6837d0b78 | 0/0 |
| v9.9.9-P6 | 2017-01-31 | yes | patch | 9.9 | 67d38a6313 | 0/0 |
| v9.11.1rc1 | 2017-02-06 | no | rc | 9.11 | ece26dd7d7 | 0/- |
| v9.10.5rc1 | 2017-02-06 | no | rc | 9.10 | 66d4de0075 | 0/- |
| v9.9.10rc1 | 2017-02-06 | no | rc | 9.9 | c7fb2ad160 | 0/- |
| v9.9.10rc2 | 2017-03-01 | no | rc | 9.9 | ba9be2be7e | 0/- |
| v9.10.5rc2 | 2017-03-01 | no | rc | 9.10 | 7f90852277 | 0/- |
| v9.11.1rc2 | 2017-03-01 | no | rc | 9.11 | f9ecaf8a4a | 0/- |
| v9.9.9-P8 | 2017-03-29 | yes | patch | 9.9 | af51affcff | 4/5 |
| v9.10.4-P8 | 2017-03-29 | yes | patch | 9.10 | 9f5232eb83 | 0/0 |
| v9.11.0-P5 | 2017-03-29 | yes | patch | 9.11 | ad4fb79684 | 0/0 |
| v9.11.1rc3 | 2017-03-29 | no | rc | 9.11 | f2c50d7dd2 | 0/- |
| v9.10.5rc3 | 2017-03-29 | no | rc | 9.10 | 709352017e | 0/- |
| v9.9.10rc3 | 2017-03-29 | no | rc | 9.9 | abaf4a6a5c | 0/- |
| v9.9.10 | 2017-04-14 | yes | release | 9.9 | 1a7c6f9dc8 | 5/56 |
| v9.10.5 | 2017-04-14 | yes | release | 9.10 | feb005b1b9 | 0/9 |
| v9.11.1 | 2017-04-14 | yes | release | 9.11 | e3dc2e7b99 | 1/12 |
| v9.9.10-P1 | 2017-05-31 | yes | patch | 9.9 | 40edd31a39 | 2/2 |
| v9.10.5-P1 | 2017-05-31 | yes | patch | 9.10 | 34fd9c65ed | 0/0 |
| v9.11.1-P1 | 2017-05-31 | yes | patch | 9.11 | 88773555a8 | 0/0 |
| v9.11.1-P2 | 2017-06-28 | yes | patch | 9.11 | f90acef005 | 1/2 |
| v9.9.10-P2 | 2017-06-28 | yes | patch | 9.9 | 733de85889 | 0/0 |
| v9.10.5-P2 | 2017-06-28 | yes | patch | 9.10 | a39c587731 | 0/0 |
| v9.9.11b1 | 2017-06-29 | no | beta | 9.9 | 3765187b5f | 0/- |
| v9.10.6b1 | 2017-06-29 | no | beta | 9.10 | 2c00a11db3 | 0/- |
| v9.11.2b1 | 2017-06-29 | no | beta | 9.11 | 35255451d4 | 0/- |
| v9.11.1-P3 | 2017-07-08 | yes | patch | 9.11 | 57c2abdf7d | 0/1 |
| v9.10.5-P3 | 2017-07-08 | yes | patch | 9.10 | 7d5676f286 | 0/0 |
| v9.9.10-P3 | 2017-07-08 | yes | patch | 9.9 | a89f040bd2 | 0/0 |
| v9.9.11rc1 | 2017-07-11 | no | rc | 9.9 | 4d1466b46b | 0/- |
| v9.11.2rc1 | 2017-07-11 | no | rc | 9.11 | c48fdfda7a | 0/- |
| v9.10.6rc1 | 2017-07-11 | no | rc | 9.10 | 8814bbde8d | 0/- |
| v9.9.11rc2 | 2017-07-20 | no | rc | 9.9 | 15977c6939 | 0/- |
| v9.10.6rc2 | 2017-07-20 | no | rc | 9.10 | bba308ea26 | 0/- |
| v9.11.2rc2 | 2017-07-20 | no | rc | 9.11 | 3ba8d04247 | 0/- |
| v9.9.11 | 2017-07-24 | yes | release | 9.9 | efa5130b23 | 4/34 |
| v9.10.6 | 2017-07-24 | yes | release | 9.10 | 9d1ea0b7fe | 0/9 |
| v9.11.2 | 2017-07-24 | yes | release | 9.11 | 0a2b929f15 | 0/12 |
| v9.12.0a1 | 2017-09-11 | no | alpha | 9.12 | a9dfb7ef6e | 0/- |
| v9.12.0b1 | 2017-10-12 | no | beta | 9.12 | 08a3dedda1 | 0/- |
| v9.12.0b2 | 2017-11-07 | no | beta | 9.12 | 5b1e929b8b | 0/- |
| v9.12.0rc1 | 2017-12-06 | no | rc | 9.12 | f9c3aba9b3 | 0/- |
| v9.11.2-P1 | 2018-01-04 | yes | patch | 9.11 | 2c2bc60330 | 1/1 |
| v9.10.6-P1 | 2018-01-04 | yes | patch | 9.10 | f941e3654e | 0/0 |
| v9.9.11-P1 | 2018-01-04 | yes | patch | 9.9 | 008ed2d685 | 0/0 |
| v9.12.0rc2 | 2018-01-04 | no | rc | 9.12 | 9cf13ffaab | 0/- |
| v9.12.0rc3 | 2018-01-12 | no | rc | 9.12 | 4bb22b6400 | 0/- |
| v9.12.0 | 2018-01-17 | yes | release | 9.12 | 71a40862c0 | 58/224 |
| v9.9.12b1 | 2018-01-24 | no | beta | 9.9 | 470cee7071 | 0/- |
| v9.10.7b1 | 2018-01-24 | no | beta | 9.10 | fe1302d544 | 0/- |
| v9.11.3b1 | 2018-01-24 | no | beta | 9.11 | 617639b7cc | 0/- |
| v9.12.1b1 | 2018-02-08 | no | beta | 9.12 | ed829a6ba4 | 0/- |
| v9.11.3rc1 | 2018-02-15 | no | rc | 9.11 | b1331a6b3d | 0/- |
| v9.10.7rc1 | 2018-02-15 | no | rc | 9.10 | d8c1dbcbd4 | 0/- |
| v9.9.12rc1 | 2018-02-15 | no | rc | 9.9 | 1a63a9b4b2 | 0/- |
| v9.12.1rc1 | 2018-02-17 | no | rc | 9.12 | cd8d44403b | 0/- |
| v9.11.3 | 2018-03-08 | yes | release | 9.11 | a375815431 | 3/30 |
| v9.10.7 | 2018-03-08 | yes | release | 9.10 | db65d701b9 | 0/0 |
| v9.9.12 | 2018-03-08 | yes | release | 9.9 | 4eb49c4882 | 0/0 |
| v9.12.1 | 2018-03-08 | yes | release | 9.12 | b2307b2546 | 2/13 |
| v9.12.1-P2 | 2018-05-16 | yes | patch | 9.12 | 14b0e01fee | 2/2 |
| v9.13.0 | 2018-05-22 | no | dev | 9.13 | 29b3a7d842 | 6/58 |
| v9.13.1 | 2018-06-09 | no | dev | 9.13 | 5b7102595e | 6/18 |
| v9.12.2rc1 | 2018-06-09 | no | rc | 9.12 | 146d6b6351 | 0/- |
| v9.11.4rc1 | 2018-06-09 | no | rc | 9.11 | 37f469d329 | 0/- |
| v9.10.8rc1 | 2018-06-09 | no | rc | 9.10 | 0279263e6d | 0/- |
| v9.9.13rc1 | 2018-06-13 | no | rc | 9.9 | 3ae30dc7af | 0/- |
| v9.12.2rc2 | 2018-06-28 | no | rc | 9.12 | 56cf466766 | 0/- |
| v9.11.4rc2 | 2018-06-28 | no | rc | 9.11 | 0de0733307 | 0/- |
| v9.10.8rc2 | 2018-06-28 | no | rc | 9.10 | 2b459063a1 | 0/- |
| v9.9.13rc2 | 2018-06-29 | no | rc | 9.9 | d75765e897 | 0/- |
| v9.9.13 | 2018-07-03 | yes | release | 9.9 | 3f3dd451af | 1/5 |
| v9.10.8 | 2018-07-03 | yes | release | 9.10 | 12f71327ff | 1/3 |
| v9.11.4 | 2018-07-03 | yes | release | 9.11 | 2fe4344de4 | 0/3 |
| v9.12.2 | 2018-07-03 | yes | release | 9.12 | 3631aeb070 | 0/3 |
| v9.13.2 | 2018-07-03 | no | dev | 9.13 | 4f6ef2f3e5 | 2/5 |
| v9.12.2-P1 | 2018-07-24 | yes | patch | 9.12 | 8914b8391d | 1/1 |
| v9.11.4-P1 | 2018-07-24 | yes | patch | 9.11 | 2b060b2cc3 | 0/0 |
| v9.12.2-P2 | 2018-09-04 | yes | patch | 9.12 | b2bf2789c6 | 1/5 |
| v9.11.4-P2 | 2018-09-04 | yes | patch | 9.11 | 7107deba23 | 0/0 |
| v9.13.3 | 2018-09-05 | no | dev | 9.13 | 3561018919 | 8/36 |
| v9.11.5rc1 | 2018-10-02 | no | rc | 9.11 | 426dbf0bef | 0/- |
| v9.12.3rc1 | 2018-10-02 | no | rc | 9.12 | 08a6a2d892 | 0/- |
| v9.11.5 | 2018-10-06 | yes | release | 9.11 | 3b0b2047ce | 0/5 |
| v9.12.3 | 2018-10-06 | yes | release | 9.12 | 6c8e92c06d | 0/1 |
| v9.13.4 | 2018-11-22 | no | dev | 9.13 | ac4f8a51cc | 3/63 |
| v9.13.5 | 2018-12-07 | no | dev | 9.13 | 8b17f364a9 | 2/10 |
| v9.12.3-P1 | 2018-12-07 | yes | patch | 9.12 | cfdd35f26a | 0/0 |
| v9.11.5-P1 | 2018-12-10 | yes | patch | 9.11 | 647dac6f96 | 0/0 |
| v9.13.5-W1 | 2018-12-17 | no | dev | 9.13 | 3dc18b25b9 | 0/1 |
| v9.12.3-P4 | 2019-02-04 | yes | patch | 9.12 | a3d2ae08fd | 3/3 |
| v9.11.5-P4 | 2019-02-05 | yes | patch | 9.11 | 998753c758 | 0/0 |
| v9.13.6 | 2019-02-06 | no | dev | 9.13 | acfbf1ae94 | 7/44 |
| v9.13.7 | 2019-02-21 | no | dev | 9.13 | 6491691ac4 | 3/9 |
| v9.12.4rc1 | 2019-02-21 | no | rc | 9.12 | fdb01cd050 | 0/- |
| v9.11.6rc1 | 2019-02-21 | no | rc | 9.11 | 4c3f28eb0e | 0/- |
| v9.11.6 | 2019-02-27 | yes | release | 9.11 | 4c50a8f8fb | 0/1 |
| v9.12.4 | 2019-02-27 | yes | release | 9.12 | a953e08740 | 0/0 |
| v9.14.0rc1 | 2019-02-28 | no | rc | 9.14 | c2c957735f | 0/- |
| v9.14.0rc2 | 2019-03-07 | no | rc | 9.14 | 7f614fb584 | 0/- |
| v9.14.0rc3 | 2019-03-13 | no | rc | 9.14 | b2dc88096c | 0/- |
| v9.14.0 | 2019-03-20 | yes | release | 9.14 | d1e053ed8d | 2/10 |
| v9.12.4-P1 | 2019-04-06 | yes | patch | 9.12 | 28e45cd00e | 2/3 |
| v9.11.6-P1 | 2019-04-06 | yes | patch | 9.11 | eba38b8900 | 0/0 |
| v9.14.1 | 2019-04-06 | yes | release | 9.14 | a372174145 | 2/16 |
| v9.15.0 | 2019-05-10 | no | dev | 9.15 | 031bca512d | 8/38 |
| v9.14.2 | 2019-05-10 | yes | release | 9.14 | 354cf1f66f | 0/0 |
| v9.11.7 | 2019-05-10 | yes | release | 9.11 | b8170affae | 0/0 |
| v9.14.3 | 2019-06-04 | yes | release | 9.14 | 17df4c34a9 | 2/8 |
| v9.11.8 | 2019-06-04 | yes | release | 9.11 | f10b6b330b | 0/0 |
| v9.15.1 | 2019-06-11 | no | dev | 9.15 | fea4d53c60 | 1/7 |
| v9.11.9 | 2019-07-09 | yes | release | 9.11 | c148ba880e | 1/7 |
| v9.14.4 | 2019-07-09 | yes | release | 9.14 | b8c84a7900 | 1/2 |
| v9.15.2 | 2019-07-10 | no | dev | 9.15 | 98eda76eb6 | 1/6 |
| v9.15.3 | 2019-08-12 | no | dev | 9.15 | e1792341ac | 3/14 |
| v9.14.5 | 2019-08-13 | yes | release | 9.14 | 6ec104e71c | 0/0 |
| v9.11.10 | 2019-08-13 | yes | release | 9.11 | 467afb4bc8 | 0/0 |
| v9.11.11 | 2019-09-09 | yes | release | 9.11 | 414bcc7f64 | 1/9 |
| v9.14.6 | 2019-09-09 | yes | release | 9.14 | 39057cceec | 0/2 |
| v9.15.4 | 2019-09-09 | no | dev | 9.15 | 3be71081bf | 1/3 |
| v9.15.5 | 2019-10-02 | no | dev | 9.15 | 87676a6ac0 | 3/8 |
| v9.14.7 | 2019-10-02 | yes | release | 9.14 | d410de0545 | 0/0 |
| v9.11.12 | 2019-10-02 | yes | release | 9.11 | 3b6c6c88b0 | 0/0 |
| v9.14.8 | 2019-11-06 | yes | release | 9.14 | abcf57d588 | 4/11 |
| v9.11.13 | 2019-11-06 | yes | release | 9.11 | 8f32a30e5c | 0/1 |
| v9.15.6 | 2019-11-17 | no | dev | 9.15 | fa2f16db89 | 5/8 |
| v9.11.14 | 2019-12-12 | yes | release | 9.11 | ea409239d5 | 0/7 |
| v9.14.9 | 2019-12-12 | yes | release | 9.14 | 623e23e296 | 0/0 |
| v9.15.7 | 2019-12-13 | no | dev | 9.15 | de42a7aa9f | 3/10 |
| v9.15.8 | 2020-01-16 | no | dev | 9.15 | 9c5547b118 | 2/11 |
| v9.11.15 | 2020-01-16 | yes | release | 9.11 | 808d0b07b0 | 0/0 |
| v9.14.10 | 2020-01-16 | yes | release | 9.14 | 00d5a0a865 | 0/0 |
| v9.11.16 | 2020-02-12 | yes | release | 9.11 | 6afa4a49bc | 2/5 |
| v9.16.0 | 2020-02-12 | yes | release | 9.16 | 6270e602ea | 2/4 |
| v9.14.11 | 2020-02-13 | yes | release | 9.14 | 098f68799b | 0/0 |
| v9.11.17 | 2020-03-11 | yes | release | 9.11 | 65c9496daf | 2/2 |
| v9.16.1 | 2020-03-11 | yes | release | 9.16 | d497c325e7 | 5/6 |
| v9.17.0 | 2020-03-12 | no | dev | 9.17 | 04ca7cc4b6 | 1/2 |
| v9.11.18 | 2020-04-09 | yes | release | 9.11 | bc6c00f15a | 0/6 |
| v9.16.2 | 2020-04-09 | yes | release | 9.16 | b310dc7f5e | 2/10 |
| v9.17.1 | 2020-04-09 | no | dev | 9.17 | deb57872b6 | 0/1 |
| v9.16.3 | 2020-05-06 | yes | release | 9.16 | 5ea41c14fb | 7/18 |
| v9.14.12 | 2020-05-06 | yes | release | 9.14 | f3dc26e898 | 0/0 |
| v9.11.19 | 2020-05-06 | yes | release | 9.11 | 905ec6491d | 0/0 |
| v9.17.2 | 2020-06-10 | no | dev | 9.17 | 6d46544f58 | 8/37 |
| v9.11.20 | 2020-06-10 | yes | release | 9.11 | f3d1d66bb9 | 0/0 |
| v9.16.4 | 2020-06-10 | yes | release | 9.16 | 0849b42333 | 0/0 |
| v9.17.3 | 2020-07-03 | no | dev | 9.17 | 079e9baebe | 4/20 |
| v9.16.5 | 2020-07-03 | yes | release | 9.16 | c00b4586ab | 0/0 |
| v9.11.21 | 2020-07-03 | yes | release | 9.11 | 4ce7edb580 | 0/0 |
| v9.11.22 | 2020-08-06 | yes | release | 9.11 | 6a05a966f3 | 4/8 |
| v9.16.6 | 2020-08-10 | yes | release | 9.16 | 25846cfec4 | 2/13 |
| v9.17.4 | 2020-08-10 | no | dev | 9.17 | 9a2a819817 | 0/6 |
| v9.17.5 | 2020-09-04 | no | dev | 9.17 | dd1d178379 | 5/17 |
| v9.16.7 | 2020-09-04 | yes | release | 9.16 | 6fd3eb76b0 | 0/0 |
| v9.11.23 | 2020-09-07 | yes | release | 9.11 | 4f700562e0 | 0/0 |
| v9.17.6 | 2020-10-12 | no | dev | 9.17 | 9868df8387 | 2/14 |
| v9.16.8 | 2020-10-13 | yes | release | 9.16 | 539f9f0860 | 0/0 |
| v9.11.24 | 2020-10-13 | yes | release | 9.11 | c10a19fcb9 | 0/0 |
| v9.17.7 | 2020-11-16 | no | dev | 9.17 | ed85d0660d | 1/17 |
| v9.16.9 | 2020-11-16 | yes | release | 9.16 | b3f41b79a7 | 0/0 |
| v9.11.25 | 2020-11-16 | yes | release | 9.11 | 4a7e9aaff7 | 0/0 |
| v9.17.8 | 2020-12-07 | no | dev | 9.17 | fba4f351fe | 1/12 |
| v9.16.10 | 2020-12-07 | yes | release | 9.16 | fac8def1b4 | 0/0 |
| v9.11.26 | 2020-12-08 | yes | release | 9.11 | 3ff862016c | 0/0 |
| v9.17.9 | 2021-01-11 | no | dev | 9.17 | 66fc6c5a9e | 5/15 |
| v9.16.11 | 2021-01-11 | yes | release | 9.16 | 9ff601bcca | 0/0 |
| v9.11.27 | 2021-01-11 | yes | release | 9.11 | 99ca3c536a | 0/0 |
| v9.17.10 | 2021-02-04 | no | dev | 9.17 | 5fbd5ff429 | 6/19 |
| v9.16.12 | 2021-02-04 | yes | release | 9.16 | aeb943df66 | 0/0 |
| v9.11.28 | 2021-02-04 | yes | release | 9.11 | 60f9417ce4 | 0/0 |
| v9.11.29 | 2021-03-09 | yes | release | 9.11 | a35739f6ad | 0/1 |
| v9.17.11 | 2021-03-11 | no | dev | 9.17 | 72c690df30 | 2/18 |
| v9.16.13 | 2021-03-11 | yes | release | 9.16 | 072e758d32 | 0/0 |
| v9.17.12 | 2021-04-12 | no | dev | 9.17 | 50d43fc590 | 5/20 |
| v9.16.15 | 2021-04-19 | yes | release | 9.16 | 4469e3e626 | 0/2 |
| v9.11.31 | 2021-04-19 | yes | release | 9.11 | ac3f4eb88b | 0/0 |
| v9.16.16 | 2021-05-12 | yes | release | 9.16 | 0c314d81f1 | 10/15 |
| v9.11.32 | 2021-05-12 | yes | release | 9.11 | 27e3f0188e | 0/0 |
| v9.17.13 | 2021-05-12 | no | dev | 9.17 | ce3c5674cf | 0/4 |
| v9.17.14 | 2021-06-08 | no | dev | 9.17 | 1530bf8b55 | 1/14 |
| v9.16.17 | 2021-06-08 | yes | release | 9.16 | fe79347146 | 0/0 |
| v9.11.33 | 2021-06-08 | yes | release | 9.11 | 1823b436ea | 0/0 |
| v9.17.15 | 2021-06-18 | no | dev | 9.17 | 13c129d961 | 0/2 |
| v9.16.18 | 2021-06-18 | yes | release | 9.16 | 1c027c4382 | 0/0 |
| v9.16.19 | 2021-07-09 | yes | release | 9.16 | df0e7519ee | 5/13 |
| v9.17.16 | 2021-07-09 | no | dev | 9.17 | b33f621318 | 0/4 |
| v9.11.34 | 2021-07-09 | yes | release | 9.11 | b2b8f2e6ab | 0/0 |
| v9.16.20 | 2021-08-10 | yes | release | 9.16 | 26db37f5ec | 3/10 |
| v9.17.17 | 2021-08-10 | no | dev | 9.17 | 73d28b368d | 1/8 |
| v9.11.35 | 2021-08-10 | yes | release | 9.11 | 8aead5f87a | 0/0 |
| v9.16.21 | 2021-09-07 | yes | release | 9.16 | a8aa4502f4 | 3/14 |
| v9.17.18 | 2021-09-07 | no | dev | 9.17 | 019a476e04 | 1/8 |
| v9.11.36 | 2021-10-11 | yes | release | 9.11 | 68dbd5b966 | 1/2 |
| v9.16.22 | 2021-10-13 | yes | release | 9.16 | 59bfaba325 | 0/8 |
| v9.17.19 | 2021-10-13 | no | dev | 9.17 | b63de6b586 | 2/15 |
| v9.17.20 | 2021-11-05 | no | dev | 9.17 | a666cba383 | 3/19 |
| v9.16.23 | 2021-11-05 | yes | release | 9.16 | fde3b1f005 | 0/0 |
| v9.17.21 | 2021-12-06 | no | dev | 9.17 | ffdb8569f4 | 5/20 |
| v9.16.24 | 2021-12-07 | yes | release | 9.16 | 93e3098f22 | 0/0 |
| v9.17.22 | 2022-01-12 | no | dev | 9.17 | e30f7bb19d | 4/15 |
| v9.16.25 | 2022-01-12 | yes | release | 9.16 | 3e144230f9 | 0/0 |
| v9.18.0 | 2022-01-24 | yes | release | 9.18 | 8db45afa1a | 0/6 |
| v9.16.26 | 2022-02-04 | yes | release | 9.16 | 5c0098d486 | 0/3 |
| v9.16.27 | 2022-03-07 | yes | release | 9.16 | 96094c577f | 2/8 |
| v9.18.1 | 2022-03-07 | yes | release | 9.18 | 1a4e4c2989 | 3/11 |
| v9.11.37 | 2022-03-07 | yes | release | 9.11 | 796133c72d | 0/0 |
| v9.19.0 | 2022-04-11 | no | dev | 9.19 | cab15392af | 4/38 |
| v9.16.28 | 2022-04-11 | yes | release | 9.16 | 7aea13ff14 | 0/0 |
| v9.18.2 | 2022-04-11 | yes | release | 9.18 | 3babb1557a | 0/0 |
| v9.19.1 | 2022-05-09 | no | dev | 9.19 | 8e12227580 | 5/30 |
| v9.18.3 | 2022-05-09 | yes | release | 9.18 | 16aefa34b0 | 0/0 |
| v9.16.29 | 2022-05-10 | yes | release | 9.16 | 7e23e43e14 | 0/0 |
| v9.19.2 | 2022-06-02 | no | dev | 9.19 | f7c233e8e9 | 6/13 |
| v9.16.30 | 2022-06-02 | yes | release | 9.16 | 61fdb40fb2 | 0/0 |
| v9.18.4 | 2022-06-02 | yes | release | 9.18 | 727d0d68d8 | 0/0 |
| v9.19.3 | 2022-07-07 | no | dev | 9.19 | c043bad469 | 3/20 |
| v9.18.5 | 2022-07-07 | yes | release | 9.18 | 6593103e39 | 0/0 |
| v9.16.31 | 2022-07-11 | yes | release | 9.16 | 1c4b350ca2 | 0/0 |
| v9.19.4 | 2022-08-04 | no | dev | 9.19 | 63279dc661 | 5/15 |
| v9.18.6 | 2022-08-04 | yes | release | 9.18 | 8dbd488a50 | 0/0 |
| v9.16.32 | 2022-08-05 | yes | release | 9.16 | 56f3439263 | 0/0 |
| v9.19.5 | 2022-09-08 | no | dev | 9.19 | 5b2fed25f4 | 9/28 |
| v9.18.7 | 2022-09-08 | yes | release | 9.18 | 85a6eb108e | 0/0 |
| v9.16.33 | 2022-09-08 | yes | release | 9.16 | 35e9c6e31d | 0/0 |
| v9.19.6 | 2022-10-10 | no | dev | 9.19 | cb867d2ef0 | 3/30 |
| v9.18.8 | 2022-10-10 | yes | release | 9.18 | 35f5d35d41 | 0/0 |
| v9.16.34 | 2022-10-10 | yes | release | 9.16 | 08724b7eef | 0/0 |
| v9.19.7 | 2022-11-07 | no | dev | 9.19 | 83b4004d71 | 2/21 |
| v9.16.35 | 2022-11-07 | yes | release | 9.16 | 4ce90d03a8 | 0/0 |
| v9.18.9 | 2022-11-07 | yes | release | 9.18 | e83150781b | 0/0 |
| v9.19.8 | 2022-12-12 | no | dev | 9.19 | eac4314684 | 4/30 |
| v9.18.10 | 2022-12-12 | yes | release | 9.18 | 7011eaf906 | 0/0 |
| v9.16.36 | 2022-12-12 | yes | release | 9.16 | edc1615077 | 0/0 |
| v9.19.9 | 2023-01-12 | no | dev | 9.19 | a752887dce | 6/24 |
| v9.18.11 | 2023-01-12 | yes | release | 9.18 | 1f554acee8 | 0/0 |
| v9.16.37 | 2023-01-12 | yes | release | 9.16 | 2b2afb28ab | 0/0 |
| v9.19.10 | 2023-02-03 | no | dev | 9.19 | 789be8ef62 | 2/16 |
| v9.18.12 | 2023-02-03 | yes | release | 9.18 | 99783f9a5e | 0/0 |
| v9.16.38 | 2023-02-03 | yes | release | 9.16 | af0056a44e | 0/0 |
| v9.19.11 | 2023-03-03 | no | dev | 9.19 | 5e3e7a262b | 2/37 |
| v9.18.13 | 2023-03-03 | yes | release | 9.18 | 3c85ab7f4c | 0/0 |
| v9.16.39 | 2023-03-06 | yes | release | 9.16 | 83e26c215f | 0/0 |
| v9.19.12 | 2023-04-11 | no | dev | 9.19 | 460760ee77 | 4/26 |
| v9.18.14 | 2023-04-11 | yes | release | 9.18 | 2c5e22fcbc | 0/0 |
| v9.16.40 | 2023-04-11 | yes | release | 9.16 | 113a865465 | 0/0 |
| v9.19.13 | 2023-05-08 | no | dev | 9.19 | 66a3c6b318 | 1/18 |
| v9.18.15 | 2023-05-09 | yes | release | 9.18 | f53a0765c3 | 0/0 |
| v9.16.41 | 2023-05-09 | yes | release | 9.16 | 4df4cecf05 | 0/0 |
| v9.19.14 | 2023-06-09 | no | dev | 9.19 | fce9689893 | 5/28 |
| v9.18.16 | 2023-06-09 | yes | release | 9.18 | 8193c9b862 | 0/0 |
| v9.16.42 | 2023-06-09 | yes | release | 9.16 | a62d1bd69a | 0/0 |
| v9.19.15 | 2023-07-06 | no | dev | 9.19 | 9127376fb1 | 1/15 |
| v9.18.17 | 2023-07-06 | yes | release | 9.18 | 42ca7611bd | 0/0 |
| v9.19.16 | 2023-08-04 | no | dev | 9.19 | 5c1f9951b3 | 5/14 |
| v9.18.18 | 2023-08-04 | yes | release | 9.18 | 1f8de2f0aa | 0/0 |
| v9.16.43 | 2023-08-04 | yes | release | 9.16 | de6f1a07f7 | 0/0 |
| v9.19.17 | 2023-09-08 | no | dev | 9.19 | 464cf8ce5e | 4/25 |
| v9.16.44 | 2023-09-08 | yes | release | 9.16 | cd2b4602b0 | 0/0 |
| v9.18.19 | 2023-09-11 | yes | release | 9.18 | c78cd3681c | 0/0 |
| v9.19.18 | 2023-11-09 | no | dev | 9.19 | 8dea58c390 | 4/34 |
| v9.18.20 | 2023-11-09 | yes | release | 9.18 | 396c2b43f4 | 0/0 |
| v9.16.45 | 2023-11-09 | yes | release | 9.16 | 353fb4b9d3 | 0/0 |
| v9.19.19 | 2023-12-08 | no | dev | 9.19 | 18a05caf55 | 2/17 |
| v9.18.21 | 2023-12-08 | yes | release | 9.18 | cb6cff65a9 | 0/0 |
| v9.19.21 | 2024-02-02 | no | dev | 9.19 | c030a677ae | 8/24 |
| v9.18.24 | 2024-02-11 | yes | release | 9.18 | 6d7674f8f2 | 0/2 |
| v9.16.48 | 2024-02-11 | yes | release | 9.16 | 0dab57e15f | 0/0 |
| v9.19.22 | 2024-03-12 | no | dev | 9.19 | d01a4e5fc6 | 6/35 |
| v9.18.25 | 2024-03-12 | yes | release | 9.18 | 6dc676cb72 | 0/0 |
| v9.16.49 | 2024-03-12 | yes | release | 9.16 | d5b3d64b8b | 0/0 |
| v9.19.23 | 2024-04-02 | no | dev | 9.19 | 3c0eaff4c6 | 1/11 |
| v9.18.26 | 2024-04-03 | yes | release | 9.18 | 936d80b4f4 | 0/0 |
| v9.16.50 | 2024-04-03 | yes | release | 9.16 | acf2ba4a93 | 0/0 |
| v9.19.24 | 2024-05-03 | no | dev | 9.19 | be3e3da7b2 | 5/12 |
| v9.18.27 | 2024-05-03 | yes | release | 9.18 | 663e6d969c | 0/0 |
| v9.20.0 | 2024-07-08 | yes | release | 9.20 | 14bbdfc7b9 | 6/23 |
| v9.18.28 | 2024-07-08 | yes | release | 9.18 | f77fadbf59 | 0/0 |
| v9.18.29 | 2024-08-13 | yes | release | 9.18 | a697ae6d0b | 1/22 |
| v9.21.0 | 2024-08-13 | no | dev | 9.21 | b732da695e | 1/42 |
| v9.20.1 | 2024-08-13 | yes | release | 9.20 | 478c83cde3 | 1/32 |
| v9.21.1 | 2024-09-09 | no | dev | 9.21 | 2e24083c79 | 5/28 |
| v9.20.2 | 2024-09-09 | yes | release | 9.20 | 66643d6a2a | 4/23 |
| v9.18.30 | 2024-09-09 | yes | release | 9.18 | cdc8d69148 | 2/12 |
| v9.21.2 | 2024-10-07 | no | dev | 9.21 | 05d1ca8a3b | 3/33 |
| v9.20.3 | 2024-10-07 | yes | release | 9.20 | 1e2850eb63 | 3/22 |
| v9.18.31 | 2024-10-07 | yes | release | 9.18 | 6298f90b85 | 1/10 |
| v9.21.3 | 2024-12-03 | no | dev | 9.21 | 8306005ef1 | 7/46 |
| v9.20.4 | 2024-12-03 | yes | release | 9.20 | 283ac230b9 | 6/29 |
| v9.18.32 | 2024-12-03 | yes | release | 9.18 | d1f139270c | 5/16 |
| v9.21.4 | 2025-01-20 | no | dev | 9.21 | 0f626b8cc3 | 8/37 |
| v9.20.5 | 2025-01-20 | yes | release | 9.20 | 5464a5d46a | 5/26 |
| v9.18.33 | 2025-01-20 | yes | release | 9.18 | 6fc161b582 | 4/11 |
| v9.21.5 | 2025-02-11 | no | dev | 9.21 | ee913c1370 | 4/23 |
| v9.20.6 | 2025-02-11 | yes | release | 9.20 | 72cbad0469 | 4/17 |
| v9.18.34 | 2025-02-11 | yes | release | 9.18 | d8c38c95b6 | 0/12 |
| v9.21.6 | 2025-03-11 | no | dev | 9.21 | 21ca763bca | 10/48 |
| v9.20.7 | 2025-03-11 | yes | release | 9.20 | 305df58976 | 8/31 |
| v9.18.35 | 2025-03-11 | yes | release | 9.18 | f506f80a7e | 6/15 |
| v9.21.7 | 2025-04-09 | no | dev | 9.21 | 6a06226c0f | 12/37 |
| v9.20.8 | 2025-04-09 | yes | release | 9.20 | 6400fd6c05 | 9/23 |
| v9.18.36 | 2025-04-09 | yes | release | 9.18 | 20451734dd | 2/7 |
| v9.21.8 | 2025-05-08 | no | dev | 9.21 | 0119c99206 | 4/15 |
| v9.20.9 | 2025-05-08 | yes | release | 9.20 | 98f2a5b7f4 | 3/9 |
| v9.18.37 | 2025-05-09 | yes | release | 9.18 | d8ff479b23 | 0/1 |
| v9.21.9 | 2025-06-06 | no | dev | 9.21 | 514753e09f | 0/20 |
| v9.20.10 | 2025-06-06 | yes | release | 9.20 | 6107035984 | 0/6 |
| v9.21.10 | 2025-07-04 | no | dev | 9.21 | 205da98524 | 5/18 |
| v9.20.11 | 2025-07-04 | yes | release | 9.20 | c6b2e3128e | 2/5 |
| v9.18.38 | 2025-07-04 | yes | release | 9.18 | cfcc202bf3 | 1/5 |
| v9.18.39 | 2025-08-13 | yes | release | 9.18 | 737584125e | 2/6 |
| v9.20.12 | 2025-08-13 | yes | release | 9.20 | 81f59f8283 | 3/13 |
| v9.21.11 | 2025-08-13 | no | dev | 9.21 | dc452c32d6 | 6/36 |
| v9.21.12 | 2025-09-04 | no | dev | 9.21 | 9bafc35302 | 4/35 |
| v9.20.13 | 2025-09-04 | yes | release | 9.20 | 1f79fb934e | 3/13 |
| v9.21.14 | 2025-10-18 | no | dev | 9.21 | 537824f32e | 11/36 |
| v9.20.15 | 2025-10-18 | yes | release | 9.20 | 0c0fcf7b2b | 7/10 |
| v9.18.41 | 2025-10-18 | yes | release | 9.18 | e8adafa196 | 6/12 |
| v9.21.15 | 2025-11-07 | no | dev | 9.21 | dcf6c33eae | 6/37 |
| v9.20.16 | 2025-11-07 | yes | release | 9.20 | c97aa2d267 | 4/8 |
| v9.18.42 | 2025-11-07 | yes | release | 9.18 | af1647a9bd | 1/1 |
| v9.21.16 | 2025-12-09 | no | dev | 9.21 | 3d048e0ace | 7/32 |
| v9.18.43 | 2025-12-11 | yes | release | 9.18 | 25bf6c731c | 2/4 |
| v9.20.17 | 2025-12-11 | yes | release | 9.20 | 00545e4375 | 3/13 |
| v9.21.17 | 2026-01-09 | no | dev | 9.21 | f37931a18e | 10/25 |
| v9.20.18 | 2026-01-09 | yes | release | 9.20 | 0d2e0d8fac | 5/11 |
| v9.18.44 | 2026-01-09 | yes | release | 9.18 | 2e74eea40c | 2/4 |
| v9.18.45 | 2026-02-04 | yes | release | 9.18 | bfaaa12a8e | 0/4 |
| v9.20.19 | 2026-02-04 | yes | release | 9.20 | 928dc4b252 | 0/8 |
| v9.21.18 | 2026-02-04 | no | dev | 9.21 | abb3f2a2cb | 2/15 |
| v9.21.19 | 2026-02-26 | no | dev | 9.21 | cb213255e2 | 5/18 |
| v9.20.20 | 2026-02-26 | yes | release | 9.20 | 70865706d2 | 4/14 |
| v9.18.46 | 2026-02-26 | yes | release | 9.18 | aef945ecdd | 1/2 |
| v9.21.20 | 2026-03-13 | no | dev | 9.21 | 3e7037ceef | 5/10 |
| v9.20.21 | 2026-03-13 | yes | release | 9.20 | 12f97d4162 | 4/5 |
| v9.18.47 | 2026-03-13 | yes | release | 9.18 | 84c0d37e12 | 1/1 |
| v9.21.21 | 2026-03-31 | no | dev | 9.21 | ec2e1ce35a | 4/34 |
| v9.20.22 | 2026-03-31 | yes | release | 9.20 | e6099075cd | 1/23 |
| v9.18.48 | 2026-03-31 | yes | release | 9.18 | b7f82d8c37 | 0/9 |
| v9.21.22 | 2026-05-08 | no | dev | 9.21 | 02a7b2c8a5 | 31/75 |
| v9.20.23 | 2026-05-08 | yes | release | 9.20 | 7d0b4d4d43 | 19/37 |
| v9.18.49 | 2026-05-08 | yes | release | 9.18 | cd4a53b463 | 10/22 |
| v9.21.23 | 2026-06-08 | no | dev | 9.21 | ef06030357 | 8/35 |
| v9.20.24 | 2026-06-08 | yes | release | 9.20 | e5d43f1764 | 5/20 |
| v9.18.50 | 2026-06-08 | yes | release | 9.18 | ad1a84a99f | 2/7 |
| v9.21.24 | 2026-07-13 | no | dev | 9.21 | 4b1f0f38b2 | 30/79 |
| v9.20.26 | 2026-07-20 | yes | release | 9.20 | 5a605f835e | 28/53 |
| v9.21.25 | 2026-08-05 | no | dev | 9.21 | d6bef71720 | 10/40 |
| v9.20.27 | 2026-08-05 | yes | release | 9.20 | 74d0754dbe | 5/21 |
| v9.21.26 | 2026-09-03 | no | dev | 9.21 | 7e5d38dde4 | 24/61 |
| v9.20.29 | 2026-09-11 | yes | release | 9.20 | c3d4465e57 | 23/48 |

## Gaps

* CVE fix tag NOT FOUND for 26 inventory CVEs (no fix commit in inventory, no CVE id in CHANGES/notes at any tag, no fixed version in NVD text): CVE-1999-0024, CVE-1999-0184, CVE-1999-0837, CVE-1999-0848, CVE-1999-0849, CVE-2000-1029, CVE-2001-0497, CVE-2002-0029, CVE-2002-0684, CVE-2002-1219, CVE-2005-0034, CVE-2006-2073, CVE-2007-0493, CVE-2007-0494, CVE-2007-2241, CVE-2007-2925, CVE-2007-2926, CVE-2009-0025, CVE-2009-0265, CVE-2010-0213, CVE-2010-0218, CVE-2011-0414, CVE-2011-2465, CVE-2012-1033, CVE-2013-5661, CVE-2016-2848
* 31 inventory CVEs are not BIND 9 stable-release issues (BIND 4/8, glibc/libbind or other vendors, Windows -W rebuilds, Supported Preview -S only, Red Hat builds): CVE-1999-0009, CVE-1999-0010, CVE-1999-0011, CVE-1999-0833, CVE-1999-1499, CVE-2000-0335, CVE-2000-0887, CVE-2000-0888, CVE-2001-0010, CVE-2001-0011, CVE-2001-0012, CVE-2001-0013, CVE-2002-0651, CVE-2002-1220, CVE-2002-1221, CVE-2002-2211, CVE-2002-2212, CVE-2002-2213, CVE-2003-0914, CVE-2005-0033, CVE-2006-0527, CVE-2007-2930, CVE-2008-4163, CVE-2016-1284, CVE-2018-5734, CVE-2018-5742, CVE-2019-6468, CVE-2019-6469, CVE-2022-3488, CVE-2023-2829, CVE-2023-5680 - status not-applicable-or-not-bind9-release, no tag emitted.
* 25 CVE fix tags are attribution:approximate (taken from the NVD description 'before X' / 'prior to X'; the tag exists in the clone and the top [security] entries of that tag's CHANGES are stored, but the fixing commit was not located): CVE-2002-0400, CVE-2006-0987, CVE-2006-4095, CVE-2006-4096, CVE-2008-1447, CVE-2009-0696, CVE-2009-4022, CVE-2010-0097, CVE-2010-0290, CVE-2010-0382, CVE-2010-3762, CVE-2011-1907, CVE-2011-1910, CVE-2011-2464, CVE-2012-1667, CVE-2012-3817, CVE-2012-3868, CVE-2012-4244, CVE-2012-5166, CVE-2012-5688, CVE-2013-2266, CVE-2013-3919, CVE-2013-6230, CVE-2014-0591, CVE-2018-5741
* cds/cdnskey: the commit that first made dnssec-policy publish CDS/CDNSKEY (9.16.0 keymgr code) was not located; only the later cds-digest-type / cdnskey options (d22, value_changed=false) are recorded. So no default_change row asserts a CDS/CDNSKEY default change.
* The first key-size dependent NSEC3 iteration limit (150/500/2500) is already present in lib/dns/nsec3.c at v9.6.0a1 (v9.5.2 has no nsec3.c), so it shipped with NSEC3 support itself; no default_change row is recorded for it. l01 records the change from that scheme to a fixed 150 (2021). (Located in Phase 3.)
* Stage-2 changelog_entries[].commits arrays are empty for all 1,383 kept entries (stage 2 attributed entries to tags, not commits); commit evidence exists only on default_changes rows and cve_fixes rows produced here.
* cvs2git-era tags (<= 2012-02) make git tag --contains unreliable (e.g. v9.0.1, v9.4.3-P3, v9.6.1-P1 'contain' 2009-2011 commits). Defaults d01-d04 were therefore verified by tree content at the tag; pre-2012-03 commit containment is not used for cve_fixes.
* Defaults changed after v9.20.0 (9.20.x, 9.21 development) were only sampled through the kept changelog entries (e.g. dnssec-policy key tag range handling, dnssec-keygen option removals, RSASHA1/DS-SHA1 deprecation warnings 2025); no additional default_changes rows were verified for them. 9.21 development releases are stable:false.
* max-* limit options not tied to DNSSEC validation (max-records-per-type, max-rrtypes-per-name, max-recursion-queries) are not recorded as limit_changed rows; CVE-2026-xxxx validation-limit fixes (e.g. 9.20.29 key-tag limit) appear only as cve-fix entries.
* Effect of 'dnssec-validation yes' requiring an explicit trust-anchors statement (GL #4373, 9.19.22 -> 9.20.0) and of removal of managed-keys/trusted-keys (9.21.4) is only in the kept changelog entries, not as default_changes rows.
* 43 cve_fixes rows name an earlier tag than the inventory fix_release (see differs_from_inventory); the inventory generally names the next master release, the branch/point release shipped first. CVE-2023-50868 inventory value v9.16.50 is the CVE-id mention commit, not the fix (see news_edits n02).
* Embargo effect: for several security releases the tag commit date precedes NVD/ISC public disclosure by days to weeks (negative latency); the tag commit date is used as instructed and is not the public announcement date.
* total_entries counts entries after cross-branch de-duplication: an entry already attributed to an earlier-dated tag on another branch is not counted again (v9.16.1 records 6; a raw CHANGES diff against v9.16.0 gives 8 because 5357 and 5358 shipped first in v9.11.17). v9.4.0 records 180 where the Phase 3 raw diff reproduced 156; not reconciled. (Phase 3.)
* rst era (per-release doc/changelog/changelog-<ver>.rst): 150 changelog lines appear under two or three releases (e.g. 'Update bind.keys with the new 2025 IANA root key' under v9.21.3, v9.20.4 and v9.18.32). The earliest-dated-final-tag rule stated in branch_note was not applied to rst-era entries. (Phase 3.)
* released is the committer-local calendar date of <tag>^{commit}, not the UTC date; about 60 rows differ (e.g. v9.9.1 released 2012-05-10, instant 2012-05-09T22:39:51Z). Earliest-tag choices use the UTC instant after Phase 3. (Phase 3.)
* Public announcement dates of embargoed releases (e.g. v9.4.2-P1, v9.3.5-P1, v9.5.0-P1: tag commits 2008-05-28, ISC public 2008-07-08) are outside the clone; d01's date and the CVE-2008-1447 latency of -41 days use the tag commit date. (Phase 3.)
* 23 further inventory CVEs (fixes.bind9 git-scrape rows without NVD product tags) were appended to cve_fixes after the first 184: 22 have a first stable tag (21 commit/changelog-verified via CHANGES / doc/changelog / doc/notes mention plus commit containment; CVE-2006-5989 by commit containment only, since CHANGES 5562 names CVE-2020-8625 instead) and 1 (CVE-2015-3193, an OpenSSL bug; BIND only widened the OpenSSL version gate in configure) is not-applicable-or-not-bind9-release. 13 of the 22 name an earlier tag than the inventory fix_release. nvd_published is null unless the inventory by_keyword list carries it (CVE-2024-1975, CVE-2025-8677, CVE-2026-10723, -10822, -11605, -11622, -11721, -13204); the 184-row counts in the `verification` block and in the gaps above do not include these 23. No 9.18 (>= 9.18.51), 9.16 or 9.11 tag exists after the July 2026 fixes, so the 2026 CVEs first ship in v9.20.26.
