import re
import random
import time
import ctypes
import ctypes.wintypes

from pywinauto import Desktop

# Regex patterns for UI elements (partial match, locale-resilient)
_MESSAGES_TAB_RE = r"(?i)^(Messages|Wiadomo)"
_NEW_MESSAGE_RE = r"(?i)^(New message|Nowa wiadomo)"
_SEND_BUTTON_RE = r"(?i)^Send$"
_TO_FIELD_RE = r"(?i)^(To|Do)$"
_MSG_FIELD_RE = r"(?i)^(Send a message|Napisz wiadomo)"


def _save_clipboard() -> str | None:
    """Save current clipboard text content."""
    try:
        ctypes.windll.user32.OpenClipboard(0)
        handle = ctypes.windll.user32.GetClipboardData(13)  # CF_UNICODETEXT
        if handle:
            data = ctypes.c_wchar_p(handle).value
            ctypes.windll.user32.CloseClipboard()
            return data
        ctypes.windll.user32.CloseClipboard()
        return None
    except Exception:
        try:
            ctypes.windll.user32.CloseClipboard()
        except Exception:
            pass
        return None


def _restore_clipboard(text: str | None) -> None:
    """Restore clipboard text content."""
    if text is None:
        return
    try:
        ctypes.windll.user32.OpenClipboard(0)
        ctypes.windll.user32.EmptyClipboard()
        h_mem = ctypes.windll.kernel32.GlobalAlloc(0x0042, (len(text) + 1) * 2)
        p_mem = ctypes.windll.kernel32.GlobalLock(h_mem)
        ctypes.cdll.msvcrt.wcscpy(ctypes.c_wchar_p(p_mem), text)
        ctypes.windll.kernel32.GlobalUnlock(h_mem)
        ctypes.windll.user32.SetClipboardData(13, h_mem)
        ctypes.windll.user32.CloseClipboard()
    except Exception:
        try:
            ctypes.windll.user32.CloseClipboard()
        except Exception:
            pass


def _set_clipboard(text: str) -> None:
    """Set clipboard text content."""
    try:
        ctypes.windll.user32.OpenClipboard(0)
        ctypes.windll.user32.EmptyClipboard()
        h_mem = ctypes.windll.kernel32.GlobalAlloc(0x0042, (len(text) + 1) * 2)
        if not h_mem:
            ctypes.windll.user32.CloseClipboard()
            return
        p_mem = ctypes.windll.kernel32.GlobalLock(h_mem)
        ctypes.cdll.msvcrt.wcscpy(ctypes.c_wchar_p(p_mem), text)
        ctypes.windll.kernel32.GlobalUnlock(h_mem)
        ctypes.windll.user32.SetClipboardData(13, h_mem)
        ctypes.windll.user32.CloseClipboard()
    except Exception:
        try:
            ctypes.windll.user32.CloseClipboard()
        except Exception:
            pass


def _escape_for_type_keys(text: str) -> str:
    """Escape special characters for pywinauto type_keys."""
    result = []
    for ch in text:
        if ch in "+^%~{}()":
            result.append("{" + ch + "}")
        else:
            result.append(ch)
    return "".join(result)


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
        escaped_msg = _escape_for_type_keys(message)

        for i, number in enumerate(numbers):
            self._log(f"  SMS {i+1}/{len(numbers)}: {number}")
            self._send_single(number, escaped_msg)
            if i < len(numbers) - 1:
                time.sleep(1.0)

        self._log("Paczka wyslana!")

    def _send_single(self, number: str, escaped_msg: str) -> None:
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
        time.sleep(2.0)

        # Re-acquire as wrapper object for descendants search
        win = desktop.window(title_re=".*Phone Link.*").wrapper_object()
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

        # Step 5: Type message
        self._main_window.type_keys(escaped_msg, with_spaces=True)

        # Step 6: Send
        time.sleep(0.5)
        self._main_window.type_keys("{ENTER}")
        time.sleep(1.0)

    def _wait_for_descendant(self, win, title: str, control_type: str, timeout: int = None):
        """Find a descendant element by exact title, polling until found."""
        timeout = timeout or self.WAIT_TIMEOUT
        end_time = time.time() + timeout
        while time.time() < end_time:
            for elem in win.descendants(control_type=control_type):
                try:
                    if elem.element_info.name == title:
                        return elem
                except Exception:
                    continue
            time.sleep(0.5)
        raise PhoneLinkAutomationError(
            f"Nie moge znalezc elementu: {title} ({control_type}). "
            f"Uruchom: python tools/inspect_phone_link.py"
        )

    def _wait_for_descendant_re(self, win, pattern: str, control_type: str, timeout: int = None):
        """Find a descendant element by regex on title, polling until found."""
        timeout = timeout or self.WAIT_TIMEOUT
        end_time = time.time() + timeout
        while time.time() < end_time:
            for elem in win.descendants(control_type=control_type):
                try:
                    name = elem.element_info.name or ""
                    if re.search(pattern, name):
                        return elem
                except Exception:
                    continue
            time.sleep(0.5)
        raise PhoneLinkAutomationError(
            f"Nie moge znalezc elementu: regex={pattern} ({control_type}). "
            f"Uruchom: python tools/inspect_phone_link.py"
        )

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
