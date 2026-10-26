import os
import time
import threading
import random

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QProgressBar, QTextEdit, QMessageBox, QFileDialog, QSizePolicy, QInputDialog,
)
from PySide6.QtCore import Signal, Qt

from core.batch_manager import BatchManager
from core.sender import PhoneLinkSender
from core.excel_importer import validate_phone_number
from core.personalizer import unresolved_variables
from core.sms_counter import count_sms, strip_polish, MAX_CHARS
from core.report import export_report_xlsx, export_report_csv
from gui.styles import COLORS
from gui.widgets.resize_grip import add_resize_grip


# From this many parts on, some Android messaging apps quietly send an MMS.
MMS_RISK_PARTS = 4


class SendPanel(QWidget):
    """Panel with send/stop/resume buttons, progress bar, and log."""

    sending_finished = Signal(list)
    _log_signal = Signal(str)
    _progress_init_signal = Signal(int)
    _progress_update_signal = Signal(int, int)
    _send_finished_signal = Signal()
    _connect_failed_signal = Signal(str)
    _test_done_signal = Signal()

    def __init__(self, settings=None, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._sender = PhoneLinkSender(on_log=self._log)
        self._sending = False
        self._stop_requested = False
        self._batch_manager = None
        self._results = []
        self._numbers = []
        self._message = ""
        self._texts = {}
        self._get_selected = lambda: []
        self._get_messages = lambda: {}
        self._build_ui()
        self._log_signal.connect(self._slot_log)
        self._progress_init_signal.connect(self._slot_progress_init)
        self._progress_update_signal.connect(self._slot_progress_update)
        self._send_finished_signal.connect(self._finish_sending)
        self._connect_failed_signal.connect(self._slot_connect_failed)
        self._test_done_signal.connect(self._finish_test)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(6)

        main_row = QHBoxLayout()
        main_row.setSpacing(10)

        left_col = QVBoxLayout()
        left_col.setSpacing(6)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self._btn_send = QPushButton("Rozpocznij wysyłkę")
        self._btn_send.setProperty("class", "primary")
        self._btn_send.setMinimumWidth(160)
        self._btn_send.setMinimumHeight(36)
        self._btn_send.setEnabled(False)
        self._btn_send.clicked.connect(self._on_send)
        btn_row.addWidget(self._btn_send)

        self._btn_stop = QPushButton("Zatrzymaj")
        self._btn_stop.setMinimumHeight(36)
        self._btn_stop.setEnabled(False)
        self._btn_stop.clicked.connect(self._on_stop)
        btn_row.addWidget(self._btn_stop)

        self._btn_resume = QPushButton("Wznów")
        self._btn_resume.setMinimumHeight(36)
        self._btn_resume.setEnabled(False)
        self._btn_resume.clicked.connect(self._on_resume)
        btn_row.addWidget(self._btn_resume)

        self._btn_test = QPushButton("Wyślij test do siebie")
        self._btn_test.setToolTip(
            "Wysyła jedną wiadomość na Twój numer — zobaczysz, jak SMS wygląda "
            "na telefonie, zanim pójdzie do całej listy"
        )
        self._btn_test.setMinimumHeight(36)
        self._btn_test.setEnabled(False)
        self._btn_test.clicked.connect(self._on_test)
        btn_row.addWidget(self._btn_test)

        btn_row.addStretch()

        self._btn_export = QPushButton("Eksportuj raport")
        self._btn_export.setMinimumHeight(36)
        self._btn_export.setEnabled(False)
        self._btn_export.clicked.connect(self._on_export)
        btn_row.addWidget(self._btn_export)

        left_col.addLayout(btn_row)

        progress_row = QHBoxLayout()

        self._progress = QProgressBar()
        self._progress.setTextVisible(False)
        self._progress.setMinimumHeight(8)
        self._progress.setMaximumHeight(8)
        self._progress.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        progress_row.addWidget(self._progress)

        self._lbl_progress = QLabel("0%")
        self._lbl_progress.setMinimumWidth(60)
        self._lbl_progress.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._lbl_progress.setProperty("class", "dim")
        progress_row.addWidget(self._lbl_progress)

        left_col.addLayout(progress_row)
        left_col.addStretch()
        main_row.addLayout(left_col, stretch=1)

        self._txt_log = QTextEdit()
        self._txt_log.setReadOnly(True)
        self._txt_log.setMinimumHeight(70)
        self._txt_log.setStyleSheet(
            f"background-color: {COLORS['surface']}; "
            f"color: {COLORS['text_secondary']}; "
            f"border: 1px solid {COLORS['border']}; "
            f"border-radius: 8px; "
            f"font-size: 12px; font-family: 'Consolas', monospace;"
        )
        add_resize_grip(self._txt_log)
        main_row.addWidget(self._txt_log, stretch=1)

        layout.addLayout(main_row, stretch=1)

    def set_ready(self, has_numbers: bool, has_message: bool):
        can_send = has_numbers and has_message and not self._sending
        self._btn_send.setEnabled(can_send)
        self._btn_test.setEnabled(has_message and not self._sending)

    def set_data(self, numbers, message, get_selected_fn, get_messages_fn):
        self._numbers = numbers
        self._message = message
        self._get_selected = get_selected_fn
        self._get_messages = get_messages_fn

    def _text_for(self, number: str) -> str:
        """The personalized text this number gets, frozen when sending started."""
        return self._texts.get(number, self._message)

    def _on_send(self):
        selected = self._get_selected()
        if not selected:
            QMessageBox.warning(self, "Brak odbiorców", "Zaznacz przynajmniej jednego odbiorcę.")
            return
        if not self._message:
            QMessageBox.warning(self, "Brak treści", "Wpisz treść wiadomości.")
            return

        # Freeze each recipient's text now, so editing the message mid-run (or
        # before "Wznów") cannot change what the remaining people receive.
        messages = self._get_messages()
        self._texts = {n: messages.get(n, self._message) for n in selected}

        if not self._confirm_send(list(self._texts.values())):
            return

        self._batch_manager = BatchManager(selected, batch_size=20)
        self._results = []
        self._start_sending()

    def _confirm_send(self, texts: list[str]) -> bool:
        total_parts = sum(count_sms(t).parts for t in texts)
        most_parts = max(count_sms(t).parts for t in texts)
        longest = max(len(t) for t in texts)
        with_placeholders = [t for t in texts if unresolved_variables(t)]

        lines = [
            f"Odbiorcy: {len(texts)}",
            f"Łącznie części SMS: {total_parts} (tyle policzy operator)",
        ]
        if with_placeholders:
            example = unresolved_variables(with_placeholders[0])[0]
            lines.append(
                f"\n⚠ {len(with_placeholders)} z {len(texts)} wiadomości zawiera "
                f"niepodmienioną zmienną, np. {{{example}}} — odbiorca zobaczy ją "
                f"dosłownie. Sprawdź kolumnę „Gotowa treść” w podglądzie."
            )
        if longest > MAX_CHARS:
            lines.append(
                f"\n⚠ Najdłuższa wiadomość ma {longest} znaków — więcej niż "
                f"limit {MAX_CHARS}."
            )
        if most_parts >= MMS_RISK_PARTS:
            lines.append(
                f"\n⚠ Wiadomość składa się z {most_parts} części SMS. Część telefonów "
                f"z Androidem wysyła tak długie wiadomości jako MMS (mogą być płatne). "
                f"Jeśli nie wiesz, jak zachowa się Twój — najpierw „Wyślij test do siebie”."
            )
        lines.append(
            "\nNie ruszaj myszką ani klawiaturą podczas wysyłki — "
            "komputer będzie zajęty automatyzacją."
        )

        reply = QMessageBox.question(
            self, "Potwierdź wysyłkę", "\n".join(lines),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        return reply == QMessageBox.StandardButton.Yes

    def _test_text(self) -> tuple[str, str]:
        """(text, whose) — the first selected recipient's personalized text, so
        the test shows real substitutions; the bare template without a list."""
        selected = self._get_selected()
        if selected:
            first = selected[0]
            return self._get_messages().get(first, self._message), f"treść dla {first}"
        text = self._message
        if self._settings and self._settings.strip_polish:
            text = strip_polish(text)
        return text, "treść szablonu"

    def _on_test(self):
        if self._sending:
            return
        text, whose = self._test_text()
        if not text:
            QMessageBox.warning(self, "Brak treści", "Wpisz treść wiadomości.")
            return

        last = self._settings.test_number if self._settings else ""
        raw, ok = QInputDialog.getText(
            self, "Wyślij test do siebie",
            f"Na jaki numer wysłać test? ({whose}, {count_sms(text).parts} SMS)\n"
            f"Nie ruszaj myszką ani klawiaturą, dopóki test się nie wyśle.",
            text=last,
        )
        if not ok or not raw.strip():
            return
        is_valid, number, reason = validate_phone_number(raw)
        if not is_valid:
            QMessageBox.warning(self, "Zły numer", reason or "Nieprawidłowy numer.")
            return
        if self._settings:
            self._settings.test_number = number

        self._sending = True
        self._btn_send.setEnabled(False)
        self._btn_test.setEnabled(False)
        self._log(f"Test: wysyłam na {number}...")
        threading.Thread(target=self._test_worker, args=(number, text), daemon=True).start()

    def _test_worker(self, number: str, text: str):
        try:
            self._sender._automation.connect()
            outcome = []
            self._sender.send(
                [number], text,
                on_result=lambda n, ok, err: outcome.append((ok, err)),
            )
            ok, err = outcome[0] if outcome else (False, "brak wyniku")
            self._log("Test wysłany — sprawdź telefon." if ok else f"Test nieudany: {err}")
        except Exception as e:
            self._log(f"Test nieudany: {e}")
        self._test_done_signal.emit()

    def _finish_test(self):
        # A test is not a mailing: no results, no history, the list stays.
        self._sending = False
        self._btn_test.setEnabled(bool(self._message))
        self._btn_send.setEnabled(bool(self._numbers) and bool(self._message))

    def _on_stop(self):
        self._stop_requested = True
        self._log("Zatrzymywanie wysyłki...")

    def _on_resume(self):
        owed = self._owed_numbers()
        if not owed:
            self._log("Nie ma czego wznawiać — wszystkie SMS-y wysłane.")
            return

        # Retry exactly the numbers still owed an SMS — the failed recipients
        # plus whatever a stop left untouched. Resending a whole batch would
        # duplicate the SMS-es that did go out.
        self._results = [r for r in self._results if r["number"] not in set(owed)]
        self._batch_manager = BatchManager(owed, batch_size=20)
        self._log(f"Wznawiam: {len(owed)} numerów")
        self._start_sending()

    def _owed_numbers(self) -> list:
        """Numbers that still need an SMS: failed recipients first, then any
        batch this run never got to."""
        owed = [r["number"] for r in self._results if r["status"] == "error"]

        bm = self._batch_manager
        if bm:
            for idx in range(bm.total_batches):
                if bm.get_status(idx) == "pending":
                    owed.extend(bm.get_batch(idx))

        seen = set()
        return [n for n in owed if not (n in seen or seen.add(n))]

    def _start_sending(self):
        self._sending = True
        self._stop_requested = False
        self._btn_send.setEnabled(False)
        self._btn_test.setEnabled(False)
        self._btn_stop.setEnabled(True)
        self._btn_resume.setEnabled(False)
        self._btn_export.setEnabled(False)

        thread = threading.Thread(target=self._send_loop, daemon=True)
        thread.start()

    def _send_loop(self):
        bm = self._batch_manager
        total = bm.total_batches
        attempted = set()

        self._progress_init_signal.emit(total)

        try:
            self._sender._automation.connect()
        except Exception as e:
            self._connect_failed_signal.emit(str(e))
            return

        while True:
            idx = bm.next_pending_index(skip=attempted)
            if idx is None or self._stop_requested:
                break
            attempted.add(idx)

            batch = bm.get_batch(idx)
            self._log(f"Paczka {idx + 1}/{total} ({len(batch)} numerów)...")

            # Record each recipient as the automation reports it. A recipient
            # that silently failed must never be filed under "sent" — that is
            # what made a dropped SMS invisible and unretryable.
            failed = []

            def on_result(number, ok, error, _failed=failed):
                self._results.append({
                    "number": number,
                    "status": "sent" if ok else "error",
                    "message": self._text_for(number),
                    "time": time.strftime("%H:%M:%S"),
                    "error": "" if ok else error,
                })
                if not ok:
                    _failed.append(number)

            try:
                self._sender.send(batch, self._text_for, on_result=on_result)
            except Exception as e:
                # The automation could not run at all (e.g. Phone Link vanished);
                # nothing after this batch can work either, so stop.
                bm.mark_error(idx, str(e))
                self._log(f"BLAD paczka {idx + 1}/{total}: {e}")

                reported = {r["number"] for r in self._results}
                for num in batch:
                    if num not in reported:
                        self._results.append({
                            "number": num,
                            "status": "error",
                            "message": self._text_for(num),
                            "time": time.strftime("%H:%M:%S"),
                            "error": str(e),
                        })

                self._send_finished_signal.emit()
                return

            if failed:
                bm.mark_error(idx, f"nie wysłano {len(failed)} z {len(batch)}")
                self._log(
                    f"Paczka {idx + 1}/{total}: wysłano {len(batch) - len(failed)}"
                    f"/{len(batch)}, nieudane: {', '.join(failed)}"
                )
            else:
                bm.mark_sent(idx)
                self._log(f"Paczka {idx + 1}/{total} wysłana poprawnie")

            self._progress_update_signal.emit(idx + 1, total)

            if bm.next_pending_index(skip=attempted) is not None and not self._stop_requested:
                delay = random.uniform(4.0, 8.0)
                self._log(f"Czekam {delay:.1f}s...")
                time.sleep(delay)

        summary = bm.summary()
        self._log(
            f"Koniec: {summary['sent']} wysłanych, "
            f"{summary['error']} błędów, {summary['pending']} pominiętych"
        )
        self._send_finished_signal.emit()

    def _finish_sending(self):
        self._sending = False
        self._btn_send.setEnabled(True)
        self._btn_test.setEnabled(bool(self._message))
        self._btn_stop.setEnabled(False)
        self._btn_export.setEnabled(bool(self._results))

        self._btn_resume.setEnabled(bool(self._owed_numbers()))

        self.sending_finished.emit(self._results)

    def _on_export(self):
        if not self._results:
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Eksportuj raport",
            f"raport_SMS_{time.strftime('%Y-%m-%d_%H%M%S')}.xlsx",
            "Excel (*.xlsx);;CSV (*.csv)",
        )
        if not path:
            return

        if path.lower().endswith(".csv"):
            export_report_csv(path, self._results)
        else:
            export_report_xlsx(path, self._results)

        self._log(f"Zapisano raport: {os.path.basename(path)}")

    def _log(self, message: str):
        self._log_signal.emit(message)

    def _slot_log(self, message: str):
        timestamp = time.strftime("%H:%M:%S")
        line = f"[{timestamp}] {message}"
        self._txt_log.append(line)
        scrollbar = self._txt_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _slot_progress_init(self, total: int):
        self._progress.setMaximum(total)
        self._progress.setValue(0)
        self._lbl_progress.setText(f"0 / {total}")

    def _slot_progress_update(self, current: int, total: int):
        self._progress.setValue(current)
        self._lbl_progress.setText(f"{current} / {total}")

    def _slot_connect_failed(self, error: str):
        self._slot_log(f"BLAD: {error}")
        self._finish_sending()
