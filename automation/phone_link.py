import re
import random
import time

import win32clipboard

from pywinauto import Desktop

_CF_UNICODETEXT = win32clipboard.CF_UNICODETEXT

# Regex patterns for UI elements (partial match, locale-resilient)
_MESSAGES_TAB_RE = r"(?i)^(Messages|Wiadomo)"
_NEW_MESSAGE_RE = r"(?i)^(New message|Nowa wiadomo)"
_SEND_BUTTON_RE = r"(?i)^Send$"
_TO_FIELD_RE = r"(?i)^(To|Do)$"
_MSG_FIELD_RE = r"(?i)^(Send a message|Napisz wiadomo)"


def _open_clipboard(attempts: int = 10, delay: float = 0.05) -> bool:
    """Open the clipboard, retrying briefly if another app holds it.

    The Windows clipboard is a single global resource; a clipboard manager or
    Phone Link itself may hold it for a few milliseconds. Retrying avoids
    silently skipping a copy/paste during a bulk send (which would otherwise
    paste stale text). Bounded attempts — never blocks indefinitely.
    """
    for _ in range(attempts):
        try:
            win32clipboard.OpenClipboard()
            return True
        except Exception:
            time.sleep(delay)
    return False


def _save_clipboard() -> str | None:
    """Save current clipboard text content (Unicode), or None if not text.

    Uses pywin32's win32clipboard, which handles 64-bit handles correctly.
    The previous raw-ctypes implementation truncated handles to 32 bits and
    crashed the process with an access violation.
    """
    if not _open_clipboard():
        return None
    try:
        if win32clipboard.IsClipboardFormatAvailable(_CF_UNICODETEXT):
            return win32clipboard.GetClipboardData(_CF_UNICODETEXT)
        return None
    except Exception:
        return None
    finally:
        try:
            win32clipboard.CloseClipboard()
        except Exception:
            pass


def _set_clipboard(text: str) -> None:
    """Set clipboard to the given Unicode text."""
    if not _open_clipboard():
        return
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(_CF_UNICODETEXT, text)
    except Exception:
        pass
    finally:
        try:
            win32clipboard.CloseClipboard()
        except Exception:
            pass


def _restore_clipboard(text: str | None) -> None:
    """Restore previously saved clipboard text content."""
    if text is None:
        return
    _set_clipboard(text)


def _wait_until(predicate, timeout: float, poll_interval: float = 0.2):
    """Poll ``predicate`` until it returns a truthy value or ``timeout`` elapses.

    Returns the truthy value (e.g. a found UI element) or ``None`` on timeout.
    Exceptions raised by ``predicate`` are treated as "not ready yet" and
    retried — UIA queries often raise transiently while the UI is still
    loading. This is the condition-based-waiting pattern: it proceeds the
    instant the UI is ready (faster than a fixed sleep) and never proceeds
    before it is ready (safer than a fixed sleep).
    """
    end = time.monotonic() + timeout
    while True:
        try:
            result = predicate()
        except Exception:
            result = None
        if result:
            return result
        if time.monotonic() >= end:
            return None
        time.sleep(poll_interval)


class PhoneLinkAutomationError(Exception):
    """Raised when Phone Link automation fails."""
    pass


class PhoneLinkSender:
    WAIT_TIMEOUT = 10  # seconds

    def __init__(self, on_log=None):
        self._main_window = None
        self._on_log = on_log or (lambda msg: None)

    def _log(self, message: str) -> None:
        self._on_log(message)

    def connect(self) -> None:
        """Connect to the Phone Link application window."""
        self._log("Szukam okna Phone Link...")
        try:
            desktop = Desktop(backend="uia")
            self._main_window = desktop.window(title_re=".*Phone Link.*")
            self._main_window.wait("visible", timeout=self.WAIT_TIMEOUT)
            self._main_window.set_focus()
            self._log("Polaczono z Phone Link")
        except Exception as e:
            raise PhoneLinkAutomationError(
                "Nie znaleziono okna Phone Link. Upewnij sie, ze Phone Link jest otwarty i telefon polaczony."
            ) from e

    def is_available(self) -> bool:
        """Check if Phone Link window is visible."""
        try:
            desktop = Desktop(backend="uia")
            win = desktop.window(title_re=".*Phone Link.*")
            win.wait("visible", timeout=3)
            return True
        except Exception:
            return False

    def send_batch(self, numbers: list[str], message: str) -> None:
        """Send individual SMS to each number in the batch."""
        if not self._main_window:
            self.connect()

        self._log(f"Wysylam paczke: {len(numbers)} numerow")

        # Save the user's clipboard once and restore it after the whole batch —
        # we use the clipboard to paste the message body (see _send_single).
        saved_clipboard = _save_clipboard()
        try:
            for i, number in enumerate(numbers):
                self._log(f"  SMS {i+1}/{len(numbers)}: {number}")
                self._send_single(number, message)
                if i < len(numbers) - 1:
                    time.sleep(1.0)
        finally:
            _restore_clipboard(saved_clipboard)

        self._log("Paczka wyslana!")

    def _send_single(self, number: str, message: str) -> None:
        """Send a single SMS to one recipient."""
        # Re-acquire window fresh each time
        desktop = Desktop(backend="uia")
        self._main_window = desktop.window(title_re=".*Phone Link.*")
        self._main_window.wait("visible", timeout=self.WAIT_TIMEOUT)
        self._main_window.set_focus()
        time.sleep(0.5)

        # Step 1: Click Messages tab
        self._click_element_re(_MESSAGES_TAB_RE, "TabItem")
        time.sleep(0.5)

        # Step 2: Open New Message via Ctrl+N
        self._main_window.set_focus()
        self._main_window.type_keys("^n")

        # Re-acquire the compose window and wait for it to be ready, instead of a
        # blind 2s pause. _wait_for_descendant below then polls until the "To"
        # field actually exists — so we proceed the moment the UI is ready.
        win = self._reacquire_window()
        self._main_window = win

        # Step 3: Enter single recipient
        to_field = self._wait_for_descendant(win, "To", "Edit")
        to_field.click_input()
        time.sleep(0.3)

        escaped_num = number.replace("+", "{+}")
        to_field.type_keys(escaped_num, with_spaces=True)
        time.sleep(0.5)
        to_field.type_keys("{ENTER}")
        time.sleep(1.5)

        # Step 4: Tab to message field (1 recipient = 2 tabs)
        self._main_window.type_keys("{TAB}")
        time.sleep(0.2)
        self._main_window.type_keys("{TAB}")
        time.sleep(0.3)

        # Step 5: Paste message via clipboard.
        # Pasting (instead of type_keys) safely handles newlines, Polish
        # characters and any character that type_keys would treat as a control
        # sequence. A raw "\n" sent through type_keys would press ENTER and send
        # the SMS prematurely, truncating multi-line messages.
        _set_clipboard(message)
        time.sleep(0.2)
        self._main_window.type_keys("^v")
        time.sleep(0.3)

        # Step 6: Send
        time.sleep(0.5)
        self._main_window.type_keys("{ENTER}")
        time.sleep(1.0)

    def _wait_for_descendant(self, win, title: str, control_type: str, timeout: int = None):
        """Find a descendant element by exact title, polling until found."""
        def find():
            for elem in win.descendants(control_type=control_type):
                try:
                    if elem.element_info.name == title:
                        return elem
                except Exception:
                    continue
            return None

        elem = _wait_until(find, timeout or self.WAIT_TIMEOUT)
        if elem is None:
            raise PhoneLinkAutomationError(
                f"Nie moge znalezc elementu: {title} ({control_type}). "
                f"Uruchom: python tools/inspect_phone_link.py"
            )
        return elem

    def _wait_for_descendant_re(self, win, pattern: str, control_type: str, timeout: int = None):
        """Find a descendant element by regex on title, polling until found."""
        def find():
            for elem in win.descendants(control_type=control_type):
                try:
                    name = elem.element_info.name or ""
                    if re.search(pattern, name):
                        return elem
                except Exception:
                    continue
            return None

        elem = _wait_until(find, timeout or self.WAIT_TIMEOUT)
        if elem is None:
            raise PhoneLinkAutomationError(
                f"Nie moge znalezc elementu: regex={pattern} ({control_type}). "
                f"Uruchom: python tools/inspect_phone_link.py"
            )
        return elem

    def _reacquire_window(self):
        """Re-acquire the Phone Link window as a live wrapper, polling until ready.

        Replaces a blind ``time.sleep(2.0)`` after Ctrl+N: returns as soon as the
        window responds, and raises only if it never appears within the timeout.
        """
        desktop = Desktop(backend="uia")
        win = _wait_until(
            lambda: desktop.window(title_re=".*Phone Link.*").wrapper_object(),
            timeout=self.WAIT_TIMEOUT,
        )
        if win is None:
            raise PhoneLinkAutomationError(
                "Nie moge odzyskac okna Phone Link po otwarciu nowej wiadomosci."
            )
        return win

    def _find_element(self, title: str, control_type: str):
        """Find a UI element by title and control type."""
        try:
            elem = self._main_window.child_window(
                title=title, control_type=control_type
            )
            elem.wait("visible", timeout=self.WAIT_TIMEOUT)
            return elem
        except Exception as e:
            raise PhoneLinkAutomationError(
                f"Nie moge znalezc elementu: {title} ({control_type}). "
                f"Sprawdz czy Phone Link jest otwarty i widoczny."
            ) from e

    def _find_element_re(self, title_re: str, control_type: str):
        """Find a UI element by regex pattern on title (locale-resilient)."""
        try:
            elem = self._main_window.child_window(
                title_re=title_re, control_type=control_type
            )
            elem.wait("visible", timeout=self.WAIT_TIMEOUT)
            return elem
        except Exception as e:
            raise PhoneLinkAutomationError(
                f"Nie moge znalezc elementu: regex={title_re} ({control_type}). "
                f"Sprawdz czy Phone Link jest otwarty i widoczny. "
                f"Uruchom: python tools/inspect_phone_link.py aby zobaczyc dostepne elementy."
            ) from e

    def _find_element_by_type(self, control_type: str, occurrence: int = 1):
        """Find a UI element by control type and occurrence number."""
        try:
            elem = self._main_window.child_window(
                control_type=control_type, found_index=occurrence - 1
            )
            elem.wait("visible", timeout=self.WAIT_TIMEOUT)
            return elem
        except Exception as e:
            raise PhoneLinkAutomationError(
                f"Nie moge znalezc elementu typu {control_type} (#{occurrence})."
            ) from e

    def _click_element(self, title: str, control_type: str) -> None:
        """Find and click a UI element."""
        elem = self._find_element(title, control_type)
        elem.click_input()
        time.sleep(0.3)

    def _click_element_re(self, title_re: str, control_type: str) -> None:
        """Find and click a UI element by regex pattern."""
        elem = self._find_element_re(title_re, control_type)
        elem.click_input()
        time.sleep(0.3)
