import os
import time
import threading
import random

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QProgressBar, QTextEdit, QMessageBox, QFileDialog, QSizePolicy,
)
from PySide6.QtCore import Signal, Qt

from core.batch_manager import BatchManager
from core.sender import PhoneLinkSender
from core.report import export_report_xlsx, export_report_csv
from gui.styles import COLORS


class SendPanel(QWidget):
    """Panel with send/stop/resume buttons, progress bar, and log."""

    sending_finished = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._sender = PhoneLinkSender(on_log=self._log)
        self._sending = False
        self._stop_requested = False
        self._batch_manager = None
        self._results = []
        self._numbers = []
        self._message = ""
        self._get_selected = lambda: []
        self._build_ui()

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
        main_row.addLayout(left_col, stretch=1)

        self._txt_log = QTextEdit()
        self._txt_log.setReadOnly(True)
        self._txt_log.setMinimumHeight(70)
        self._txt_log.setMaximumHeight(90)
        self._txt_log.setStyleSheet(
            f"background-color: {COLORS['surface']}; "
            f"color: {COLORS['text_secondary']}; "
            f"border: 1px solid {COLORS['border']}; "
            f"border-radius: 8px; "
            f"font-size: 12px; font-family: 'Consolas', monospace;"
        )
        main_row.addWidget(self._txt_log, stretch=1)

        layout.addLayout(main_row)

    def set_ready(self, has_numbers: bool, has_message: bool):
        can_send = has_numbers and has_message and not self._sending
        self._btn_send.setEnabled(can_send)

    def set_data(self, numbers, message, get_selected_fn):
        self._numbers = numbers
        self._message = message
        self._get_selected = get_selected_fn

    def _on_send(self):
        selected = self._get_selected()
        if not selected:
            QMessageBox.warning(self, "Brak odbiorców", "Zaznacz przynajmniej jednego odbiorcę.")
            return
        if not self._message:
            QMessageBox.warning(self, "Brak treści", "Wpisz treść wiadomości.")
            return

        QMessageBox.warning(
            self, "Uwaga",
            "Nie ruszaj myszką ani klawiaturą podczas wysyłki.\n"
            "Komputer będzie zablokowany na czas automatyzacji.",
        )

        self._batch_manager = BatchManager(selected, batch_size=20)
        self._results = []
        self._start_sending()

    def _on_stop(self):
        self._stop_requested = True
        self._log("Zatrzymywanie wysyłki...")

    def _on_resume(self):
        self._start_sending()

    def _start_sending(self):
        self._sending = True
        self._stop_requested = False
        self._btn_send.setEnabled(False)
        self._btn_stop.setEnabled(True)
        self._btn_resume.setEnabled(False)
        self._btn_export.setEnabled(False)

        thread = threading.Thread(target=self._send_loop, daemon=True)
        thread.start()

    def _send_loop(self):
        bm = self._batch_manager
        total = bm.total_batches

        self._progress.setMaximum(total)
        self._progress.setValue(0)
        self._lbl_progress.setText(f"0 / {total}")

        try:
            self._sender._automation.connect()
        except Exception as e:
            self._log(f"BLAD: {e}")
            self._finish_sending()
            return

        while True:
            idx = bm.next_pending_index()
            if idx is None or self._stop_requested:
                break

            batch = bm.get_batch(idx)
            self._log(f"Paczka {idx + 1}/{total} ({len(batch)} numerów)...")

            try:
                self._sender.send(batch, self._message)
                bm.mark_sent(idx)
                self._log(f"Paczka {idx + 1}/{total} wysłana poprawnie")

                for num in batch:
                    self._results.append({
                        "number": num,
                        "status": "sent",
                        "message": self._message,
                        "time": time.strftime("%H:%M:%S"),
                        "error": "",
                    })
            except Exception as e:
                bm.mark_error(idx, str(e))
                self._log(f"BLAD paczka {idx + 1}/{total}: {e}")

                for num in batch:
                    self._results.append({
                        "number": num,
                        "status": "error",
                        "message": self._message,
                        "time": time.strftime("%H:%M:%S"),
                        "error": str(e),
                    })

                self._finish_sending()
                return

            self._progress.setValue(idx + 1)
            self._lbl_progress.setText(f"{idx + 1} / {total}")

            if bm.next_pending_index() is not None:
                delay = random.uniform(4.0, 8.0)
                self._log(f"Czekam {delay:.1f}s...")
                time.sleep(delay)

        summary = bm.summary()
        self._log(
            f"Koniec: {summary['sent']} wysłanych, "
            f"{summary['error']} błędów, {summary['pending']} pominiętych"
        )
        self._finish_sending()

    def _finish_sending(self):
        self._sending = False
        self._btn_send.setEnabled(True)
        self._btn_stop.setEnabled(False)
        self._btn_export.setEnabled(bool(self._results))

        if self._batch_manager:
            summary = self._batch_manager.summary()
            if summary["error"] > 0 or summary["pending"] > 0:
                self._btn_resume.setEnabled(True)

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
        timestamp = time.strftime("%H:%M:%S")
        line = f"[{timestamp}] {message}"
        self._txt_log.append(line)
        scrollbar = self._txt_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
