import random
import time
import ctypes
import ctypes.wintypes

from pywinauto import Desktop


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
        """Send an SMS to a batch of numbers (max 20)."""
        if not self._main_window:
            self.connect()

        self._log(f"Wysylam paczke: {len(numbers)} numerow")

        # Step 1: Click Messages tab
        self._click_element("Messages", "TabItem")

        # Step 2: Click New Message
        self._click_element("New message", "Button")

        # Step 3: Add recipients
        for i, number in enumerate(numbers):
            self._log(f"  Dodaje odbierce {i+1}/{len(numbers)}: {number}")
            to_field = self._find_element("To", "Edit")
            to_field.click_input()
            to_field.type_keys(number, with_spaces=True)
            time.sleep(0.3)
            to_field.type_keys("{ENTER}")
            time.sleep(0.5)

        # Step 4: Type message with clipboard protection
        self._log("Wklejam tresc wiadomosci...")
        saved_clipboard = _save_clipboard()
        try:
            msg_field = self._find_element_by_type("Edit", occurrence=2)
            msg_field.click_input()

            # Copy message to clipboard and paste
            ctypes.windll.user32.OpenClipboard(0)
            ctypes.windll.user32.EmptyClipboard()
            h_mem = ctypes.windll.kernel32.GlobalAlloc(0x0042, (len(message) + 1) * 2)
            p_mem = ctypes.windll.kernel32.GlobalLock(h_mem)
            ctypes.cdll.msvcrt.wcscpy(ctypes.c_wchar_p(p_mem), message)
            ctypes.windll.kernel32.GlobalUnlock(h_mem)
            ctypes.windll.user32.SetClipboardData(13, h_mem)
            ctypes.windll.user32.CloseClipboard()

            msg_field.type_keys("^v")  # Ctrl+V
        finally:
            _restore_clipboard(saved_clipboard)

        # Step 5: Click Send
        time.sleep(0.3)
        self._click_element("Send", "Button")
        self._log("Paczka wyslana!")

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
