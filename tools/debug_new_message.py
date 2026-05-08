"""Debug: open New Message and dump all Edit elements.

Run with Phone Link open.
Usage: python tools/debug_new_message.py
"""
import sys
import time
from pywinauto import Desktop


def main():
    desktop = Desktop(backend="uia")
    try:
        win = desktop.window(title_re=".*Phone Link.*")
        win.wait("visible", timeout=5)
    except Exception:
        print("BLAD: Nie znaleziono okna Phone Link.")
        sys.exit(1)

    print(f"Okno: {win.window_text()}")

    # Send Ctrl+N
    print("\nWysylam Ctrl+N...")
    win.set_focus()
    win.type_keys("^n")
    print("Czekam 3s na zaladowanie widoku...")
    time.sleep(3)

    # Dump ALL Edit elements
    print("\n=== Wszystkie Edit elementy ===")
    try:
        edits = win.descendants(control_type="Edit")
        for i, edit in enumerate(edits):
            try:
                name = edit.element_info.name or "(brak nazwy)"
                rect = edit.rectangle()
                print(f"  [{i}] Edit: \"{name}\"  pos=({rect.left},{rect.top},{rect.right},{rect.bottom})")
            except Exception as ex:
                print(f"  [{i}] Edit: (blad: {ex})")
    except Exception as ex:
        print(f"Blad: {ex}")

    # Dump ALL Button elements (to find Send)
    print("\n=== Wszystkie Button elementy ===")
    try:
        buttons = win.descendants(control_type="Button")
        for i, btn in enumerate(buttons):
            try:
                name = btn.element_info.name or "(brak nazwy)"
                print(f"  [{i}] Button: \"{name}\"")
            except Exception:
                pass
    except Exception as ex:
        print(f"Blad: {ex}")


if __name__ == "__main__":
    main()
