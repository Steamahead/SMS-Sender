import os
import tempfile

import pytest

from core.history import HistoryManager


class TestHistoryManager:
    def _make_manager(self) -> HistoryManager:
        path = os.path.join(tempfile.mkdtemp(), "history.db")
        return HistoryManager(path)

    def test_save_session(self):
        hm = self._make_manager()
        session_id = hm.save_session(
            message="Witaj!",
            source_file="dane.xlsx",
            recipients=[
                {"number": "+48512345678", "status": "sent", "error": None},
                {"number": "+48601234567", "status": "error", "error": "Timeout"},
            ],
        )
        assert session_id is not None

    def test_list_sessions(self):
        hm = self._make_manager()
        hm.save_session("Msg1", "f1.xlsx", [
            {"number": "+48512345678", "status": "sent", "error": None},
        ])
        hm.save_session("Msg2", "f2.xlsx", [
            {"number": "+48601234567", "status": "sent", "error": None},
        ])
        sessions = hm.list_sessions()
        assert len(sessions) == 2
        assert sessions[0]["message"] == "Msg2"  # newest first

    def test_get_session_details(self):
        hm = self._make_manager()
        sid = hm.save_session("Witaj!", "dane.xlsx", [
            {"number": "+48512345678", "status": "sent", "error": None},
            {"number": "+48601234567", "status": "error", "error": "Timeout"},
        ])
        details = hm.get_session(sid)
        assert details["message"] == "Witaj!"
        assert details["source_file"] == "dane.xlsx"
        assert len(details["recipients"]) == 2
        assert details["recipients"][0]["status"] == "sent"
        assert details["recipients"][1]["error"] == "Timeout"

    def test_summary_counts(self):
        hm = self._make_manager()
        sid = hm.save_session("Hi", "f.xlsx", [
            {"number": "+48512345678", "status": "sent", "error": None},
            {"number": "+48601234567", "status": "sent", "error": None},
            {"number": "+48701234567", "status": "error", "error": "Fail"},
        ])
        details = hm.get_session(sid)
        assert details["total"] == 3
        assert details["sent"] == 2
        assert details["errors"] == 1

    def test_max_sessions_limit(self):
        hm = self._make_manager()
        hm.MAX_SESSIONS = 3
        for i in range(5):
            hm.save_session(f"Msg{i}", f"f{i}.xlsx", [
                {"number": "+48512345678", "status": "sent", "error": None},
            ])
        sessions = hm.list_sessions()
        assert len(sessions) == 3

    def test_persistence(self):
        path = os.path.join(tempfile.mkdtemp(), "history.db")
        hm1 = HistoryManager(path)
        hm1.save_session("Witaj!", "f.xlsx", [
            {"number": "+48512345678", "status": "sent", "error": None},
        ])

        hm2 = HistoryManager(path)
        sessions = hm2.list_sessions()
        assert len(sessions) == 1
