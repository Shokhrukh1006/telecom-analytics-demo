#!/usr/bin/env python3
"""Сборка Excel-отчёта по продуктам из помесячного CSV.

Вход:  CSV с колонками month,product,mrr_index,active_clients,churn_pct,arpu_index
Выход: .xlsx с листом «Данные» и листом «Сводка», с цветовой заливкой и
       условным форматированием оттока.

Данные для примера — синтетические (data/sample_kpi.csv).
"""
from __future__ import annotations

import csv
import sys
from collections import defaultdict

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
HEADER_FONT = Font(color="FFFFFF", bold=True)
GOOD_FILL = PatternFill("solid", fgColor="E7F4EC")
WARN_FILL = PatternFill("solid", fgColor="FBF0E2")
BAD_FILL = PatternFill("solid", fgColor="F7D7D7")

COLUMNS = ["month", "product", "mrr_index", "active_clients", "churn_pct", "arpu_index"]


def load(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def churn_fill(value: float) -> PatternFill | None:
    if value <= 2.5:
        return GOOD_FILL
    if value <= 3.5:
        return WARN_FILL
    return BAD_FILL


def style_header(ws) -> None:
    for cell in ws[1]:
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center")


def autosize(ws) -> None:
    for col in ws.columns:
        width = max(len(str(c.value)) for c in col if c.value is not None) + 2
        ws.column_dimensions[get_column_letter(col[0].column)].width = width


def build_data_sheet(wb: Workbook, rows: list[dict]) -> None:
    ws = wb.active
    ws.title = "Данные"
    ws.append(COLUMNS)
    for r in rows:
        ws.append([
            r["month"], r["product"],
            float(r["mrr_index"]), int(r["active_clients"]),
            float(r["churn_pct"]), float(r["arpu_index"]),
        ])
        fill = churn_fill(float(r["churn_pct"]))
        if fill:
            ws.cell(row=ws.max_row, column=5).fill = fill
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws)


def build_summary_sheet(wb: Workbook, rows: list[dict]) -> None:
    ws = wb.create_sheet("Сводка")
    ws.append(["product", "months", "mrr_index_last", "avg_churn_pct", "arpu_index_last"])

    by_product: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_product[r["product"]].append(r)

    for product, items in sorted(by_product.items()):
        items.sort(key=lambda x: x["month"])
        avg_churn = sum(float(i["churn_pct"]) for i in items) / len(items)
        ws.append([
            product, len(items),
            float(items[-1]["mrr_index"]),
            round(avg_churn, 2),
            float(items[-1]["arpu_index"]),
        ])
        fill = churn_fill(avg_churn)
        if fill:
            ws.cell(row=ws.max_row, column=4).fill = fill

    style_header(ws)
    autosize(ws)


def run(src: str, dst: str) -> None:
    rows = load(src)
    wb = Workbook()
    build_data_sheet(wb, rows)
    build_summary_sheet(wb, rows)

    import os
    os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
    wb.save(dst)
    print(f"Строк обработано: {len(rows)}")
    print(f"Отчёт сохранён:   {dst}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: python3 report_builder.py <kpi.csv> <out.xlsx>")
    run(sys.argv[1], sys.argv[2])
