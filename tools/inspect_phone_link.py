"""Diagnostic: dump Phone Link UI element tree.

Run this with Phone Link open to see actual element names/types.
Usage: python tools/inspect_phone_link.py
"""
import sys
from pywinauto import Desktop


def main():
    desktop = Desktop(backend="uia")
    try:
        win = desktop.window(title_re=".*Phone Link.*")
        win.wait("visible", timeout=5)
    except Exception:
        print("BLAD: Nie znaleziono okna Phone Link. Upewnij sie, ze jest otwarte.")
        sys.exit(1)

    print(f"Okno: {win.window_text()}")
    print(f"Control type: {win.element_info.control_type}")
    print()
    print("=== Elementy UI (depth=3) ===")
    print()

    def dump(elem, depth=0, max_depth=6):
        if depth > max_depth:
            return
        try:
            info = elem.element_info
            name = info.name or "(brak nazwy)"
            ctype = info.control_type or "?"
            indent = "  " * depth
            print(f"{indent}[{ctype}] \"{name}\"")
            for child in elem.children():
                dump(child, depth + 1, max_depth)
        except Exception:
            pass

    dump(win)


if __name__ == "__main__":
    main()
