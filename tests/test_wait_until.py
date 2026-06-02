"""Tests for the condition-based-waiting helper used by Phone Link automation.

_wait_until replaces fixed time.sleep() calls in the send flow: it returns as
soon as a condition is met (faster) and never proceeds before it is met (safer).
"""
import time

import pytest

pytest.importorskip("win32clipboard")  # automation.phone_link imports it

from automation.phone_link import _wait_until


class TestWaitUntil:
    def test_returns_value_as_soon_as_truthy(self):
        calls = {"n": 0}

        def pred():
            calls["n"] += 1
            return "ready" if calls["n"] >= 3 else None

        assert _wait_until(pred, timeout=5, poll_interval=0.01) == "ready"
        assert calls["n"] == 3  # stopped polling immediately once ready

    def test_returns_none_on_timeout(self):
        assert _wait_until(lambda: None, timeout=0.1, poll_interval=0.01) is None

    def test_returns_immediately_when_already_true(self):
        start = time.monotonic()
        result = _wait_until(lambda: True, timeout=5, poll_interval=1.0)
        elapsed = time.monotonic() - start
        assert result is True
        assert elapsed < 0.5  # did not wait a full poll interval

    def test_predicate_exceptions_are_retried_not_fatal(self):
        calls = {"n": 0}

        def pred():
            calls["n"] += 1
            if calls["n"] < 2:
                raise RuntimeError("UIA not ready yet")
            return "ok"

        assert _wait_until(pred, timeout=5, poll_interval=0.01) == "ok"

    def test_persistent_exception_times_out_to_none(self):
        def pred():
            raise RuntimeError("never ready")

        assert _wait_until(pred, timeout=0.1, poll_interval=0.01) is None
