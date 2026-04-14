# SMS Sender v2

## Quick Context
Desktopowa aplikacja do masowej wysylki SMS przez Windows Phone Link.
Python + PySide6 + pywinauto UIA.

- **Design spec v2**: `docs/superpowers/specs/2026-04-13-sms-sender-v2-design.md`
- **Status**: `docs/STATUS.md`

## Stan projektu
- Branch: `master`
- **85 testow PASS**: `pytest tests/ -v`
- **Wszystkie funkcjonalnosci zaimplementowane**
- **GUI poprawione** — kompaktowy layout, polskie znaki, ikona aplikacji
- **Exe zbudowane**: `dist/SMSSender/SMSSender.exe`
- Build: `python installer/build.py` (PyInstaller)
- Installer Windows: `installer/sms_sender.iss` (wymaga Inno Setup)

## Struktura
```
core/           — excel_importer, batch_manager, sender, personalizer,
                  template_manager, history, report, settings, clipboard_import
automation/     — phone_link.py (pywinauto UIA)
gui/app.py      — glowne okno, taby, sygnaly
gui/styles.py   — QSS, COLORS dict
gui/widgets/    — import_panel, message_panel, preview_table, send_panel, history_view
gui/resources/  — icon.png
installer/      — build.py, sms_sender.iss, icon.ico
tools/          — generate_icon.py, inspect_phone_link.py, debug_new_message.py
```

## Zasady pracy
- Jezyk UI: polski z polskimi znakami (ą, ę, ś, ć, ź, ż, ó, ł, ń)
- Testy: `pytest tests/ -v`
- Commity: po angielsku, conventional commits
- Phone Link akceptuje numery z +48 — nie stripowac prefiksu
