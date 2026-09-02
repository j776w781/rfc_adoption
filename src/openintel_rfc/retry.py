"""Shared failure classification and backoff for every call that hits the store.

Two paths talk to the object store and both can be throttled: ``scale_runner``
fetches and scans partition objects, and ``openintel_source.list_partition_keys``
lists them. They were retried independently and inconsistently -- the scan path
knew a 403 from nginx is throttling rather than a permission failure, the list
path did not, so a throttled LIST aborted a run that the scan path would have
ridden out.

Classification lives here rather than in either module because ``scale_runner``
imports ``openintel_source`` lazily to keep the import graph acyclic; a shared
constant in either one would reintroduce the cycle.

The retry shape is equal jitter: ``wait/2 + uniform(0, wait/2)``. Plain doubling
puts every shard back on the endpoint at the same instant, so a fleet that was
throttled together retries together and stays throttled; jitter is what breaks
the lockstep, and halving the deterministic part keeps the mean delay the same.
"""
from __future__ import annotations

import random
import time
from collections.abc import Callable
from typing import TypeVar

from .utils import get_logger

__all__ = [
    "ANONYMOUS_ACCESS_HELP",
    "PERMANENT_AUTH_MARKERS",
    "TRANSIENT_MARKERS",
    "is_auth_failure",
    "is_transient",
    "jittered",
    "retry_transient",
]

LOGGER = get_logger(__name__)

#: ``403`` is here because of what the endpoint actually does. nginx fronts the
#: object store and rejects an overflowing ``limit_req`` queue with 503, but an
#: address it has decided to block gets 403 -- with nginx's own HTML body, not
#: the store's XML. Neither says the request was malformed, so both are worth
#: waiting out. Distinguishing them from a genuine permission failure is
#: :data:`PERMANENT_AUTH_MARKERS`' job, and it is consulted first.
TRANSIENT_MARKERS: tuple[str, ...] = (
    "403",
    "429",
    "500",
    "502",
    "503",
    "504",
    "forbidden",
    "service unavailable",
    "slow down",
    "slowdown",
    "too many requests",
    "timeout",
    "timed out",
    "connection reset",
    "connection closed",
    "temporarily unavailable",
    "could not establish connection",
)

#: Substrings identifying a *permission* failure rather than load. The bucket is
#: public and this client is meant to send no credentials at all; when one leaks
#: in -- ``AWS_ACCESS_KEY_ID`` in the environment, an instance profile on the
#: server, a stale ``~/.aws/credentials`` -- botocore and DuckDB sign every
#: request and the store refuses every one of them with a 403 carrying an
#: ``AccessDenied`` XML body.
#:
#: That failure is immediate, total and permanent, so it must not be retried:
#: spending the full retry budget on it turns a one-line misconfiguration into an
#: overnight run that produces nothing and explains nothing. Checked before
#: :data:`TRANSIENT_MARKERS` because these messages carry "403" too.
PERMANENT_AUTH_MARKERS: tuple[str, ...] = (
    "accessdenied",
    "access denied",
    "signaturedoesnotmatch",
    "invalidaccesskeyid",
    "invalid access key",
    "expiredtoken",
    "tokenrefreshrequired",
)

#: What to tell an operator who hit the permanent case. It names the thing to
#: look at, because "AccessDenied" on a public bucket is otherwise baffling.
ANONYMOUS_ACCESS_HELP = (
    "The object store refused the request as unauthorised. This bucket is public "
    "and the pipeline reads it anonymously, so this almost always means stray AWS "
    "credentials were picked up and used to sign the request. Check "
    "AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / AWS_SESSION_TOKEN in the "
    "environment, ~/.aws/credentials, and any instance profile on this host; "
    "unset them for this run. Retrying cannot help: the credential is wrong on "
    "every request, not just this one."
)


def is_auth_failure(exc: BaseException) -> bool:
    """True when the store rejected the *identity*, not the load."""
    text = f"{type(exc).__name__}: {exc}".lower()
    return any(marker in text for marker in PERMANENT_AUTH_MARKERS)


def is_transient(exc: BaseException) -> bool:
    """True when waiting is likely to help. Auth failures are never transient."""
    if is_auth_failure(exc):
        return False
    text = f"{type(exc).__name__}: {exc}".lower()
    return any(marker in text for marker in TRANSIENT_MARKERS)


def jittered(wait: float) -> float:
    """Equal jitter: half the wait is fixed, half is random."""
    return wait / 2 + random.uniform(0, wait / 2)


T = TypeVar("T")


def retry_transient(
    operation: Callable[[], T],
    *,
    what: str,
    attempts: int = 6,
    initial_wait: float = 2.0,
    max_wait: float = 120.0,
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Call ``operation``, retrying only failures that waiting can fix.

    Raises the original exception on the last attempt, on a permanent auth
    failure, or on anything not recognised as transient -- retrying a malformed
    request just delays the error report.
    """
    wait = initial_wait
    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except Exception as exc:
            if is_auth_failure(exc):
                raise
            if not is_transient(exc) or attempt == attempts:
                raise
            delay = jittered(min(wait, max_wait))
            LOGGER.warning(
                "%s failed (attempt %d/%d), retrying in %.1fs: %s",
                what, attempt, attempts, delay, exc,
            )
            sleep(delay)
            wait = min(wait * 2, max_wait)
    raise AssertionError("unreachable")  # pragma: no cover
