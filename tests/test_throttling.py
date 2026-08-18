"""Behaviour of the client under OpenINTEL's rate limiter.

The limiter was measured directly against ``object.openintel.nl`` rather than
guessed at. nginx sits in front of the object store and enforces ``limit_req``:

===========  ==========  ==============  ==========
concurrency  throughput  successes       rejected
===========  ==========  ==============  ==========
1            1.10 req/s  8/8             0
4            1.02 req/s  32/32           0
5            1.02 req/s  40/40           0
6            3.63 req/s  14/48           34 x HTTP 503
===========  ==========  ==============  ==========

Concurrency one through five is *queued and delayed* to exactly one request per
second and never fails; the sixth overflows the burst queue and is rejected
outright. So the budget is ~1 request/second with a burst of ~5, and the useful
client behaviour is to stay under it rather than to retry harder -- retrying at
N times the budget is what turns a pause into an outage.

These tests pin the two failures that made a throttle fatal: a 403 that aborted
the partition instead of backing off, and a pace that never responded to being
throttled at all.
"""
from __future__ import annotations

import pytest

from openintel_rfc import scale_runner
from openintel_rfc.utils import PipelineError


# --------------------------------------------------------------------------- #
# Classifying the store's rejections
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "message",
    [
        "HTTP Error: HTTP GET error on 'https://object.openintel.nl/...' (HTTP 403)",
        "HTTP 403 Forbidden",
        "HTTP Error: 429 Too Many Requests",
        "HTTP Error: HTTP GET error (HTTP 503)",
        "<html><head><title>503 Service Temporarily Unavailable</title></head>",
    ],
)
def test_throttle_shaped_rejections_are_transient(message: str) -> None:
    """A rejection under load is a pause, not a verdict.

    nginx answers an overflowing burst queue with 503, and an address it has
    decided to block with 403. Neither says the request was wrong, so both are
    worth waiting out.
    """
    assert scale_runner._is_transient(RuntimeError(message)) is True


@pytest.mark.parametrize(
    "message",
    [
        "<Error><Code>AccessDenied</Code><Message>Access Denied</Message></Error>",
        "HTTP 403: SignatureDoesNotMatch",
        "InvalidAccessKeyId: the access key does not exist",
        "ExpiredToken: the security token included in the request is expired",
    ],
)
def test_credential_shaped_rejections_are_permanent(message: str) -> None:
    """A signed request rejected by the store is a misconfiguration.

    The bucket is public and the client is meant to send no credentials at all.
    When one leaks in -- ``AWS_ACCESS_KEY_ID`` in the environment, an instance
    profile on the server, a stale ``~/.aws/credentials`` -- every request is
    signed and every request is refused. That fails on the first partition and
    stays failed, so spending the 7.5-minute retry budget on it only buries the
    one line that explains the run.
    """
    assert scale_runner._is_transient(RuntimeError(message)) is False


def test_credential_failure_explains_itself() -> None:
    """The permanent case must name its own fix, not just re-raise."""
    with pytest.raises(PipelineError) as excinfo:
        scale_runner._process_with_retry(
            object(),
            attempts=3,
            base_wait=0.0,
            warnings=[],
            _process=_always_raise("<Error><Code>AccessDenied</Code></Error>"),
        )
    text = str(excinfo.value).lower()
    assert "credential" in text
    assert "anonymous" in text
    # The operator needs to know where to look, not merely that it broke.
    assert "aws_access_key_id" in text


# --------------------------------------------------------------------------- #
# Retry behaviour
# --------------------------------------------------------------------------- #


def _always_raise(message: str):
    def _raise(*_args, **_kwargs):
        raise RuntimeError(message)

    return _raise


def test_transient_failure_is_retried_then_gives_up() -> None:
    calls: list[int] = []

    def _raise(*_args, **_kwargs):
        calls.append(1)
        raise RuntimeError("HTTP 403")

    with pytest.raises(Exception):
        scale_runner._process_with_retry(
            object(), attempts=4, base_wait=0.0, warnings=[], _process=_raise
        )
    assert len(calls) == 4, "every attempt in the budget should be spent"


def test_retry_waits_are_jittered() -> None:
    """Identical backoff across shards re-collides on the same second.

    A sharded run is several processes hitting one 1 r/s bucket. If they all
    fail at the same moment and all sleep exactly 30s, they all return at the
    same moment and knock each other over again. Jitter is what breaks the
    lockstep.
    """
    waits = _collect_waits(attempts=5, base_wait=10.0)
    assert len(waits) == 4
    # Monotonic growth in expectation, but never the same number twice.
    assert len(set(waits)) == len(waits), f"waits are deterministic: {waits}"
    assert waits[-1] > waits[0], f"backoff should still grow: {waits}"


def _collect_waits(*, attempts: int, base_wait: float) -> list[float]:
    slept: list[float] = []
    original = scale_runner.time.sleep
    scale_runner.time.sleep = slept.append  # type: ignore[assignment]
    try:
        with pytest.raises(Exception):
            scale_runner._process_with_retry(
                object(),
                attempts=attempts,
                base_wait=base_wait,
                warnings=[],
                _process=_always_raise("HTTP 503"),
            )
    finally:
        scale_runner.time.sleep = original  # type: ignore[assignment]
    return slept


# --------------------------------------------------------------------------- #
# Staying under the budget in the first place
# --------------------------------------------------------------------------- #


def test_governor_starts_at_the_configured_floor() -> None:
    governor = scale_runner.ThrottleGovernor(floor_seconds=0.25)
    assert governor.delay == pytest.approx(0.25)


def test_governor_backs_off_when_throttled() -> None:
    """Being throttled must change behaviour, or it will happen again."""
    governor = scale_runner.ThrottleGovernor(floor_seconds=0.5, ceiling_seconds=60.0)
    governor.on_throttled()
    first = governor.delay
    governor.on_throttled()
    second = governor.delay
    assert first > 0.5, "a throttle must widen the gap"
    assert second > first, "a second throttle must widen it further"
    assert governor.throttle_events == 2


def test_governor_backoff_is_capped() -> None:
    governor = scale_runner.ThrottleGovernor(floor_seconds=0.5, ceiling_seconds=8.0)
    for _ in range(20):
        governor.on_throttled()
    assert governor.delay == pytest.approx(8.0)


def test_governor_recovers_but_never_below_the_floor() -> None:
    """A run that never recovers pays the worst moment's price for hours."""
    governor = scale_runner.ThrottleGovernor(floor_seconds=0.5, ceiling_seconds=60.0)
    governor.on_throttled()
    peak = governor.delay
    for _ in range(200):
        governor.on_success()
    assert governor.delay < peak, "clean partitions should relax the pace"
    assert governor.delay >= 0.5, "but never below the configured floor"


def test_governor_divides_the_budget_across_shards() -> None:
    """N shards share one bucket, so each may spend only 1/N of it.

    This is the failure the overnight run actually hit: each shard was polite on
    its own and the aggregate was still N times the budget.
    """
    single = scale_runner.ThrottleGovernor(floor_seconds=1.0, shards=1)
    sharded = scale_runner.ThrottleGovernor(floor_seconds=1.0, shards=4)
    assert sharded.delay == pytest.approx(4.0 * single.delay)


# --------------------------------------------------------------------------- #
# Wiring: the retry path must actually teach the governor
# --------------------------------------------------------------------------- #


def test_retry_reports_throttling_to_the_governor() -> None:
    """A governor that is never told about a throttle cannot adapt to one."""
    governor = scale_runner.ThrottleGovernor(floor_seconds=0.0, ceiling_seconds=30.0)
    with pytest.raises(Exception):
        scale_runner._process_with_retry(
            object(),
            attempts=3,
            base_wait=0.0,
            warnings=[],
            governor=governor,
            _process=_always_raise("HTTP 503"),
        )
    assert governor.throttle_events == 3
    assert governor.delay > 0.0, "being throttled must leave a wider gap behind"


def test_clean_partition_relaxes_the_governor() -> None:
    governor = scale_runner.ThrottleGovernor(floor_seconds=0.0, ceiling_seconds=30.0)
    governor.on_throttled()
    widened = governor.delay
    scale_runner._process_with_retry(
        object(),
        attempts=3,
        base_wait=0.0,
        warnings=[],
        governor=governor,
        _process=lambda *a, **k: "ok",
    )
    assert governor.delay < widened


def test_credential_failure_is_not_retried() -> None:
    """The expensive mistake: burning the retry budget on a wrong credential."""
    calls: list[int] = []

    def _raise(*_args, **_kwargs):
        calls.append(1)
        raise RuntimeError("HTTP 403 <Error><Code>AccessDenied</Code></Error>")

    with pytest.raises(PipelineError):
        scale_runner._process_with_retry(
            object(), attempts=5, base_wait=99.0, warnings=[], _process=_raise
        )
    assert calls == [1], "a permission failure must fail on the first attempt"
