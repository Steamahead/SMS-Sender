"""Run the real send flow against live Phone Link WITHOUT sending anything.

    python tools/dryrun_send.py +48576473677 [ile_powtorzen]

Everything the sender does is executed for real — opening the compose pane,
typing the recipient, clearing and pasting the body, verifying both — except
the final ENTER, which is skipped. The compose pane is then closed with ESC.

This exists because two fixes were shipped on unit tests alone and neither
survived contact with the live app. A dry run is the cheapest way to find out
whether a change works before any SMS goes out.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# The Windows console defaults to cp1252 and this script prints back the Polish
# characters it read out of the UI — without this the run dies on its own output.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from automation.phone_link import (  # noqa: E402
    PhoneLinkAutomationError,
    PhoneLinkSender,
    _read_value,
)

MESSAGE = "Dry run 2.2.2 — polskie znaki: zazolc gesla jazn ĄĆĘŁŃÓŚŹŻ"


class DryRunSender(PhoneLinkSender):
    """The real sender with the final ENTER removed."""

    def __init__(self):
        super().__init__(on_log=print)
        self.sends_suppressed = 0

    def _press_send(self, msg_field) -> None:
        self.sends_suppressed += 1
        value = _read_value(msg_field)
        print(f"    [DRY RUN] pominieto wyslanie. Pole tresci zawiera: {value!r}")


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    number = sys.argv[1]
    rounds = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    sender = DryRunSender()
    sender.connect()

    failures = []
    for i in range(1, rounds + 1):
        print(f"\n===== przebieg {i}/{rounds} =====")
        started = time.monotonic()
        try:
            sender._send_single(number, MESSAGE)
            print(f"  OK w {time.monotonic() - started:.1f}s")
        except PhoneLinkAutomationError as e:
            print(f"  BLAD po {time.monotonic() - started:.1f}s: {e}")
            failures.append(str(e))

        sender._reset_compose()
        time.sleep(1.0)

    print(f"\n===== WYNIK: {rounds - len(failures)}/{rounds} przebiegow OK =====")
    print(f"wyslania pominiete (dry run): {sender.sends_suppressed}")
    if failures:
        print("bledy:")
        for f in failures:
            print(f"  - {f}")


if __name__ == "__main__":
    main()
