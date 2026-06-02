"""Regression tests for the Phone Link clipboard helpers.

The original raw-ctypes implementation truncated 64-bit clipboard handles and
crashed the whole process (SIGSEGV) the moment "Wyślij" was clicked, because
_save_clipboard() runs first in send_batch(). These tests verify the
win32clipboard-based implementation round-trips without crashing.
"""
import pytest

pytest.importorskip("win32clipboard")

from automation.phone_link import _save_clipboard, _set_clipboard, _restore_clipboard


class TestClipboardHelpers:
    def test_set_and_save_roundtrip(self):
        _set_clipboard("hello world")
        assert _save_clipboard() == "hello world"

    def test_unicode_and_newlines(self):
        text = "Dzień dobry\nDruga linia ąęśćźżół"
        _set_clipboard(text)
        assert _save_clipboard() == text

    def test_restore_brings_back_original(self):
        _set_clipboard("original")
        saved = _save_clipboard()
        _set_clipboard("temporary")
        _restore_clipboard(saved)
        assert _save_clipboard() == "original"

    def test_empty_does_not_crash(self):
        _set_clipboard("")
        _save_clipboard()  # must not raise or crash the process
