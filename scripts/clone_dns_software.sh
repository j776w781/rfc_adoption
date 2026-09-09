#!/usr/bin/env bash
#
# Bare, blobless clones of the DNS implementations the CVE and release
# cross-references read. Blobless keeps this to a few hundred MB and still
# carries every commit message and tag, which is all these analyses need.
#
#   ./scripts/clone_dns_software.sh [DEST]        # default out/software_repos
set -euo pipefail

DEST="${1:-out/software_repos}"
mkdir -p "$DEST"

REPOS="
https://github.com/NLnetLabs/unbound.git|unbound.git
https://github.com/NLnetLabs/nsd.git|nsd.git
https://gitlab.isc.org/isc-projects/bind9.git|bind9.git
https://github.com/CZ-NIC/knot.git|knot.git
https://github.com/CZ-NIC/knot-resolver.git|kresd.git
https://github.com/opendnssec/opendnssec.git|opendnssec.git
https://github.com/PowerDNS/pdns.git|pdns.git
"

for entry in $REPOS; do
    url="${entry%%|*}"; dir="${entry##*|}"
    if [ -d "$DEST/$dir" ]; then
        echo "  have $dir"
    else
        echo "  cloning $dir"
        git clone --bare --filter=blob:none -q "$url" "$DEST/$dir"
    fi
done

echo "done: $DEST"
