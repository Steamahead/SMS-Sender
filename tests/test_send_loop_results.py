"""Tests for how the send panel records outcomes and what "Wznów" retries.

A recipient the automation failed to reach used to be filed under "sent"
alongside the other 19 numbers in its batch, so it was invisible in the report
and skipped on the next run. These tests pin the corrected behaviour without
needing a Qt event loop: the result-recording and resume logic is exercised on
an unbound instance.
"""
import pytest

from core.batch_manager import BatchManager


class TestNextPendingIndexSkip:
    def test_skip_prevents_re_serving_an_errored_batch(self):
        bm = BatchManager(["1", "2", "3"], batch_size=1)
        bm.mark_error(0, "nie poszlo")

        assert bm.next_pending_index() == 0  # unchanged without skip
        assert bm.next_pending_index(skip={0}) == 1

    def test_skip_returns_none_when_everything_was_attempted(self):
        bm = BatchManager(["1", "2"], batch_size=1)
        bm.mark_error(0, "nie poszlo")
        bm.mark_sent(1)

        assert bm.next_pending_index(skip={0, 1}) is None


class FakePanel:
    """Just enough of SendPanel to exercise _owed_numbers/_on_resume."""

    def __init__(self, results, batch_manager):
        self._results = results
        self._batch_manager = batch_manager
        self._logs = []
        self._started = False

    def _log(self, message):
        self._logs.append(message)

    def _start_sending(self):
        self._started = True


def _panel(results, batch_manager):
    from gui.widgets.send_panel import SendPanel

    panel = FakePanel(results, batch_manager)
    panel._owed_numbers = SendPanel._owed_numbers.__get__(panel, FakePanel)
    panel._on_resume = SendPanel._on_resume.__get__(panel, FakePanel)
    return panel


pytest.importorskip("PySide6")


class TestOwedNumbers:
    def test_failed_recipient_is_owed_an_sms(self):
        bm = BatchManager(["1", "2"], batch_size=2)
        bm.mark_error(0, "czesciowo")
        results = [
            {"number": "1", "status": "error"},
            {"number": "2", "status": "sent"},
        ]

        assert _panel(results, bm)._owed_numbers() == ["1"]

    def test_untouched_batches_are_owed_too(self):
        bm = BatchManager(["1", "2", "3", "4"], batch_size=2)
        bm.mark_sent(0)  # batch ["1", "2"] delivered; batch ["3", "4"] never ran
        results = [
            {"number": "1", "status": "sent"},
            {"number": "2", "status": "sent"},
        ]

        assert _panel(results, bm)._owed_numbers() == ["3", "4"]

    def test_nothing_owed_when_all_delivered(self):
        bm = BatchManager(["1", "2"], batch_size=2)
        bm.mark_sent(0)
        results = [
            {"number": "1", "status": "sent"},
            {"number": "2", "status": "sent"},
        ]

        assert _panel(results, bm)._owed_numbers() == []

    def test_a_number_is_owed_once_even_if_listed_twice(self):
        bm = BatchManager(["1", "1"], batch_size=1)
        bm.mark_error(0, "nie poszlo")
        results = [{"number": "1", "status": "error"}]

        assert _panel(results, bm)._owed_numbers() == ["1"]


class TestResume:
    def test_resume_retries_only_the_failed_number(self):
        bm = BatchManager(["1", "2", "3"], batch_size=3)
        bm.mark_error(0, "czesciowo")
        results = [
            {"number": "1", "status": "error"},
            {"number": "2", "status": "sent"},
            {"number": "3", "status": "sent"},
        ]
        panel = _panel(results, bm)

        panel._on_resume()

        assert panel._batch_manager.get_batch(0) == ["1"]
        assert panel._batch_manager.total_batches == 1
        assert panel._started is True

    def test_resume_drops_the_stale_error_row_so_it_is_not_double_counted(self):
        bm = BatchManager(["1", "2"], batch_size=2)
        bm.mark_error(0, "czesciowo")
        results = [
            {"number": "1", "status": "error"},
            {"number": "2", "status": "sent"},
        ]
        panel = _panel(results, bm)

        panel._on_resume()

        assert panel._results == [{"number": "2", "status": "sent"}]

    def test_resume_does_nothing_when_all_delivered(self):
        bm = BatchManager(["1"], batch_size=1)
        bm.mark_sent(0)
        panel = _panel([{"number": "1", "status": "sent"}], bm)

        panel._on_resume()

        assert panel._started is False
