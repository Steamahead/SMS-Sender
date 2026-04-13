import csv
import os

from openpyxl import Workbook


_HEADERS = ["Numer", "Status", "Tresc", "Czas", "Blad"]


def export_report_xlsx(path: str, recipients: list[dict]) -> None:
    """Export sending report to Excel file."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Raport SMS"

    for col_idx, header in enumerate(_HEADERS, start=1):
        ws.cell(row=1, column=col_idx, value=header)

    for row_idx, r in enumerate(recipients, start=2):
        ws.cell(row=row_idx, column=1, value=r.get("number", ""))
        ws.cell(row=row_idx, column=2, value=r.get("status", ""))
        ws.cell(row=row_idx, column=3, value=r.get("message", ""))
        ws.cell(row=row_idx, column=4, value=r.get("time", ""))
        ws.cell(row=row_idx, column=5, value=r.get("error", ""))

    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    wb.save(path)


def export_report_csv(path: str, recipients: list[dict]) -> None:
    """Export sending report to CSV file."""
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None

    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(_HEADERS)
        for r in recipients:
            writer.writerow([
                r.get("number", ""),
                r.get("status", ""),
                r.get("message", ""),
                r.get("time", ""),
                r.get("error", ""),
            ])
