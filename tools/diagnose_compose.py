"""Instrument the Phone Link compose flow and report WHERE keystrokes land.

Run it with Phone Link open and your phone connected:

    python tools/diagnose_compose.py

It walks the same steps the sender does, and after each one prints:

  * which window is FOREGROUND (i.e. where the keyboard actually goes)
  * every Edit control in the Phone Link tree: name, rectangle, enabled,
    visible, whether it holds keyboard focus, and its value

Nothing is ever sent — the script stops before the final ENTER and closes the
compose pane with ESC. The recipient used is a dummy number.

Why this exists: two fixes were attempted from reasoning alone and the second
made things worse. The open questions this answers are:

  1. Is Phone Link actually foreground when Ctrl+V is pressed? If not, the
     paste goes to whatever app is, which would explain a message body that
     stays empty while the recipient lands fine.
  2. How many Edit controls match "Send a message"? If more than one, the
     verification may be reading a different box than the one being typed into.
  3. Does pasting via the element (msg_field.type_keys) behave differently from
     pasting via the window (main_window.type_keys)?
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# The Windows console defaults to cp1252, which cannot encode the Polish
# characters this script reads back out of the UI — printing them would kill
# the run mid-dump. Never let the diagnostic fail on its own output.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import win32gui

from pywinauto import Desktop

from automation.phone_link import (
    _MESSAGES_TAB_RE,
    _MSG_FIELD_RE,
    _TO_FIELD_RE,
    _read_value,
)

# A number with no existing conversation takes a different path through Phone
# Link than a known contact does — pass a real one as argv[1] to reproduce what
# the sender actually hits. Nothing is ever sent either way.
DUMMY_NUMBER = sys.argv[1] if len(sys.argv) > 1 else "+48000000000"
PROBE_TEXT = "PROBE-CTX-123"


def foreground_window() -> str:
    try:
        handle = win32gui.GetForegroundWindow()
        return f"{win32gui.GetWindowText(handle)!r} (hwnd={handle})"
    except Exception as e:
        return f"<nie moge odczytac: {e}>"


def dump(label: str, win) -> None:
    print(f"\n=== {label} ===")
    print(f"  FOREGROUND: {foreground_window()}")

    try:
        edits = win.descendants(control_type="Edit")
    except Exception as e:
        print(f"  <descendants() padlo: {e}>")
        return

    if not edits:
        print("  (brak zadnych pol Edit w drzewie)")
        return

    for i, elem in enumerate(edits):
        try:
            name = elem.element_info.name or ""
        except Exception:
            name = "<?>"

        tags = []
        if _matches(_TO_FIELD_RE, name):
            tags.append("MATCH:TO")
        if _matches(_MSG_FIELD_RE, name):
            tags.append("MATCH:MSG")

        print(f"  [{i}] name={name!r} {' '.join(tags)}")
        print(f"      rect={_safe(lambda: elem.rectangle())}"
              f" enabled={_safe(lambda: elem.is_enabled())}"
              f" visible={_safe(lambda: elem.is_visible())}"
              f" focused={_safe(lambda: elem.has_keyboard_focus())}")
        print(f"      value={_read_value(elem)!r}"
              f" auto_id={_safe(lambda: elem.element_info.automation_id)}")


def _matches(pattern: str, name: str) -> bool:
    import re
    return bool(re.search(pattern, name or ""))


def _safe(fn):
    try:
        return fn()
    except Exception as e:
        return f"<{type(e).__name__}>"


def main() -> None:
    desktop = Desktop(backend="uia")
    spec = desktop.window(title_re=".*Phone Link.*")
    spec.wait("visible", timeout=10)
    spec.set_focus()
    time.sleep(0.5)

    win = spec.wrapper_object()
    dump("0. Po set_focus na glownym oknie", win)

    spec.child_window(title_re=_MESSAGES_TAB_RE, control_type="TabItem").click_input()
    time.sleep(0.8)
    dump("1. Po kliknieciu zakladki Wiadomosci", win)

    spec.set_focus()
    spec.type_keys("^n")
    time.sleep(2.5)
    win = desktop.window(title_re=".*Phone Link.*").wrapper_object()
    dump("2. Po Ctrl+N (panel nowej wiadomosci)", win)

    to_field = _find(win, _TO_FIELD_RE)
    if to_field is None:
        print("\nBRAK pola 'Do' — dalej nie ma sensu. Wklej caly output.")
        return

    to_field.click_input()
    time.sleep(0.4)
    to_field.type_keys(DUMMY_NUMBER.replace("+", "{+}"), with_spaces=True)
    time.sleep(0.8)
    dump("3. Po wpisaniu numeru w pole 'Do'", win)

    to_field.type_keys("{ENTER}")
    time.sleep(2.0)
    dump("4. Po ENTER (numer zatwierdzony)", win)

    # --- the actual question: window-level vs element-level paste ---
    _put_clipboard(PROBE_TEXT + "-WINDOW")

    win.type_keys("{TAB}")
    time.sleep(0.3)
    win.type_keys("{TAB}")
    time.sleep(0.4)
    dump("5. Po {TAB}{TAB} (tak robi obecny kod)", win)

    win.type_keys("^v")
    time.sleep(1.0)
    dump("6. Po Ctrl+V PRZEZ OKNO (win.type_keys)", win)

    msg_field = _find(win, _MSG_FIELD_RE)
    if msg_field is not None:
        _put_clipboard(PROBE_TEXT + "-ELEMENT")
        msg_field.click_input()
        time.sleep(0.4)
        dump("7. Po kliknieciu pola tresci", win)

        msg_field.type_keys("^v")
        time.sleep(1.0)
        dump("8. Po Ctrl+V PRZEZ ELEMENT (msg_field.type_keys)", win)
    else:
        print("\n(nie znalazlem pola tresci — krok 7-8 pominiety)")

    # Empty the box before leaving. ESC alone closes the pane but leaves the
    # probe text sitting in the conversation's input box, where a later send
    # would paste on top of it.
    print("\n--- sprzatam: czyszcze pole tresci i ESC, nic nie wyslano ---")
    leftover = _find(win, _MSG_FIELD_RE)
    if leftover is not None:
        try:
            leftover.click_input()
            time.sleep(0.3)
            leftover.type_keys("^a")
            time.sleep(0.2)
            leftover.type_keys("{DELETE}")
            time.sleep(0.3)
            print(f"  pole tresci po czyszczeniu: {_read_value(leftover)!r}")
        except Exception as e:
            print(f"  nie udalo sie wyczyscic pola: {e}")

    for _ in range(3):
        try:
            win.type_keys("{ESC}")
        except Exception:
            pass
        time.sleep(0.4)

    print("\nGOTOWE. Wklej caly powyzszy output.")
    print("Kluczowe: czy w krokach 6 i 8 wartosc pola MATCH:MSG zawiera PROBE-CTX-123,")
    print("i co bylo FOREGROUND w momencie wklejania.")


def _find(win, pattern: str):
    try:
        for elem in win.descendants(control_type="Edit"):
            if _matches(pattern, elem.element_info.name or ""):
                return elem
    except Exception:
        pass
    return None


def _put_clipboard(text: str) -> None:
    from automation.phone_link import _set_clipboard
    _set_clipboard(text)
    time.sleep(0.2)


if __name__ == "__main__":
    main()
