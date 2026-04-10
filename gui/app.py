import os
import threading
import random
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from core.excel_importer import import_from_excel, import_from_csv
from core.batch_manager import BatchManager
from core.sender import PhoneLinkSender


class SMSSenderApp:
    MAX_SMS_CHARS = 160

    def __init__(self):
        self._root = tk.Tk()
        self._root.title("SMS Sender")
        self._root.geometry("550x650")
        self._root.resizable(False, False)

        self._numbers: list[str] = []
        self._skipped: list[dict] = []
        self._batch_manager: BatchManager | None = None
        self._sender = PhoneLinkSender(on_log=self._log)
        self._sending = False
        self._stop_requested = False

        self._build_ui()

    def run(self):
        self._root.mainloop()

    # -- UI Construction --

    def _build_ui(self):
        pad = {"padx": 10, "pady": 5}

        # Import section
        import_frame = tk.Frame(self._root)
        import_frame.pack(fill="x", **pad)

        self._btn_import = tk.Button(
            import_frame, text="Importuj Excel", command=self._on_import
        )
        self._btn_import.pack(side="left")

        self._lbl_file = tk.Label(import_frame, text="Brak pliku", fg="gray")
        self._lbl_file.pack(side="left", padx=(10, 0))

        self._lbl_summary = tk.Label(self._root, text="", anchor="w")
        self._lbl_summary.pack(fill="x", **pad)

        # Number list
        list_frame = tk.LabelFrame(self._root, text="Numery")
        list_frame.pack(fill="both", expand=True, **pad)

        self._number_list = tk.Listbox(list_frame, height=8)
        scrollbar = tk.Scrollbar(list_frame, command=self._number_list.yview)
        self._number_list.config(yscrollcommand=scrollbar.set)
        self._number_list.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Message section
        tk.Label(self._root, text="Tresc SMS:", anchor="w").pack(fill="x", **pad)

        self._txt_message = tk.Text(self._root, height=3, wrap="word")
        self._txt_message.pack(fill="x", **pad)
        self._txt_message.bind("<KeyRelease>", self._on_message_changed)

        self._lbl_chars = tk.Label(self._root, text="Znaki: 0/160", anchor="w")
        self._lbl_chars.pack(fill="x", **pad)

        # Batch info
        self._lbl_batches = tk.Label(self._root, text="", anchor="w")
        self._lbl_batches.pack(fill="x", **pad)

        # Buttons
        btn_frame = tk.Frame(self._root)
        btn_frame.pack(fill="x", **pad)

        self._btn_send = tk.Button(
            btn_frame, text="\u25b6 Wyslij", command=self._on_send, state="disabled"
        )
        self._btn_send.pack(side="left", padx=(0, 5))

        self._btn_stop = tk.Button(
            btn_frame, text="\u23f9 Stop", command=self._on_stop, state="disabled"
        )
        self._btn_stop.pack(side="left", padx=(0, 5))

        self._btn_resume = tk.Button(
            btn_frame, text="\u21bb Wznow", command=self._on_resume, state="disabled"
        )
        self._btn_resume.pack(side="left")

        # Progress bar
        self._progress = ttk.Progressbar(self._root, mode="determinate")
        self._progress.pack(fill="x", **pad)

        self._lbl_progress = tk.Label(self._root, text="", anchor="w")
        self._lbl_progress.pack(fill="x", **pad)

        # Log
        log_frame = tk.LabelFrame(self._root, text="Log")
        log_frame.pack(fill="both", expand=True, **pad)

        self._txt_log = tk.Text(log_frame, height=6, state="disabled", wrap="word")
        self._txt_log.pack(fill="both", expand=True)

    # -- Event Handlers --

    def _on_import(self):
        path = filedialog.askopenfilename(
            filetypes=[
                ("Excel files", "*.xlsx"),
                ("CSV files", "*.csv"),
                ("All files", "*.*"),
            ]
        )
        if not path:
            return

        try:
            if path.lower().endswith(".csv"):
                self._numbers, self._skipped = import_from_csv(path)
            else:
                self._numbers, self._skipped = import_from_excel(path)
        except FileNotFoundError as e:
            messagebox.showerror("Blad", str(e))
            return
        except Exception as e:
            messagebox.showerror("Blad odczytu pliku", str(e))
            return

        # Update UI
        filename = os.path.basename(path)
        self._lbl_file.config(text=f"plik: {filename}", fg="black")
        self._lbl_summary.config(
            text=f"Zaladowano: {len(self._numbers)} numerow ({len(self._skipped)} pominietych)"
        )

        self._number_list.delete(0, "end")
        for num in self._numbers:
            self._number_list.insert("end", f"{num}  \u2713")
        for entry in self._skipped:
            self._number_list.insert("end", f"{entry['value']}  \u2717 ({entry['reason']})")

        self._batch_manager = BatchManager(self._numbers, batch_size=20)
        self._update_batch_info()
        self._btn_send.config(state="normal" if self._numbers else "disabled")
        self._log(f"Zaimportowano {len(self._numbers)} numerow z {filename}")

    def _on_message_changed(self, event=None):
        text = self._txt_message.get("1.0", "end-1c")
        count = len(text)
        self._lbl_chars.config(
            text=f"Znaki: {count}/{self.MAX_SMS_CHARS}",
            fg="red" if count > self.MAX_SMS_CHARS else "black",
        )

    def _on_send(self):
        message = self._txt_message.get("1.0", "end-1c").strip()
        if not message:
            messagebox.showwarning("Brak tresci", "Wpisz tresc SMS-a")
            return
        if not self._numbers:
            messagebox.showwarning("Brak numerow", "Zaimportuj numery z Excela")
            return

        if len(self._numbers) > 40:
            if not messagebox.askyesno(
                "Ostrzezenie",
                "Wysylanie duzej liczby SMS-ow z prywatnego numeru moze "
                "triggerowac filtry anty-spam operatora. Kontynuowac?",
            ):
                return

        self._batch_manager = BatchManager(self._numbers, batch_size=20)
        self._start_sending(message)

    def _on_stop(self):
        self._stop_requested = True
        self._log("Zatrzymywanie wysylki...")

    def _on_resume(self):
        message = self._txt_message.get("1.0", "end-1c").strip()
        if not message:
            messagebox.showwarning("Brak tresci", "Wpisz tresc SMS-a")
            return
        self._start_sending(message)

    # -- Sending Logic --

    def _start_sending(self, message: str):
        self._sending = True
        self._stop_requested = False
        self._btn_send.config(state="disabled")
        self._btn_stop.config(state="normal")
        self._btn_resume.config(state="disabled")
        self._btn_import.config(state="disabled")

        messagebox.showwarning(
            "Uwaga",
            "Nie ruszaj myszka ani klawiatura podczas wysylki.\n"
            "Komputer bedzie zablokowany na czas automatyzacji.",
        )

        thread = threading.Thread(target=self._send_loop, args=(message,), daemon=True)
        thread.start()

    def _send_loop(self, message: str):
        bm = self._batch_manager
        total = bm.total_batches

        self._root.after(0, lambda: self._progress.config(maximum=total, value=0))

        try:
            self._sender._automation.connect()
        except Exception as e:
            self._log(f"BLAD: {e}")
            self._root.after(0, self._on_sending_done)
            return

        while True:
            idx = bm.next_pending_index()
            if idx is None or self._stop_requested:
                break

            batch = bm.get_batch(idx)
            self._log(f"Paczka {idx + 1}/{total} ({len(batch)} numerow)...")
            self._root.after(
                0, lambda i=idx: self._lbl_progress.config(text=f"Paczka {i + 1}/{total}")
            )

            try:
                self._sender.send(batch, message)
                bm.mark_sent(idx)
                self._log(f"Paczka {idx + 1}/{total} wyslana")
            except Exception as e:
                bm.mark_error(idx, str(e))
                self._log(f"BLAD paczka {idx + 1}/{total}: {e}")
                self._root.after(0, self._on_sending_done)
                return

            self._root.after(0, lambda i=idx: self._progress.config(value=i + 1))

            # Random delay between batches
            if bm.next_pending_index() is not None:
                delay = random.uniform(4.0, 8.0)
                self._log(f"Czekam {delay:.1f}s przed nastepna paczka...")
                time.sleep(delay)

        summary = bm.summary()
        self._log(
            f"Zakonczono: {summary['sent']} wyslanych, "
            f"{summary['error']} bledow, {summary['pending']} oczekujacych"
        )
        self._root.after(0, self._on_sending_done)

    def _on_sending_done(self):
        self._sending = False
        self._btn_send.config(state="normal")
        self._btn_stop.config(state="disabled")
        self._btn_import.config(state="normal")

        if self._batch_manager:
            summary = self._batch_manager.summary()
            if summary["error"] > 0 or summary["pending"] > 0:
                self._btn_resume.config(state="normal")

    # -- Helpers --

    def _update_batch_info(self):
        if not self._batch_manager or self._batch_manager.total_batches == 0:
            self._lbl_batches.config(text="")
            return
        bm = self._batch_manager
        sizes = [len(bm.get_batch(i)) for i in range(bm.total_batches)]
        self._lbl_batches.config(
            text=f"Paczki: {' + '.join(str(s) for s in sizes)} = {len(self._numbers)} numerow"
        )

    def _log(self, message: str):
        timestamp = time.strftime("%H:%M:%S")
        line = f"{timestamp} {message}\n"

        def _append():
            self._txt_log.config(state="normal")
            self._txt_log.insert("end", line)
            self._txt_log.see("end")
            self._txt_log.config(state="disabled")

        if threading.current_thread() is threading.main_thread():
            _append()
        else:
            self._root.after(0, _append)
