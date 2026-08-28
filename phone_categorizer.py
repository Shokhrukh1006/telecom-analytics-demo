#!/usr/bin/env python3
"""Разбор списка номеров на категории «красоты».

Вход:  CSV с колонкой `msisdn`; значимы последние 7 цифр (абонентская часть).
       В примере используется несуществующий код страны 999 — данные фиктивные.
Выход: та же таблица + колонка `category` и краткая сводка в stdout.

Данные для примера — синтетические (data/sample_numbers.csv).
"""
from __future__ import annotations

import csv
import re
import sys
from collections import Counter

# Национальный префикс + код оператора отбрасываем, работаем с абонентской частью.
SUBSCRIBER_LEN = 7


def subscriber_part(msisdn: str) -> str:
    digits = re.sub(r"\D", "", msisdn)
    return digits[-SUBSCRIBER_LEN:]


def has_run(s: str, length: int) -> bool:
    """Есть ли `length` одинаковых цифр подряд."""
    return re.search(r"(\d)\1{%d}" % (length - 1), s) is not None


def is_periodic_pair(s: str) -> bool:
    """Узор вида ABABAB (двухсимвольный период, ≥3 повтора, A != B)."""
    if len(s) < 6 or s[0] == s[1]:
        return False
    return s == (s[:2] * (len(s) // 2 + 1))[: len(s)]


def triple_pairs(s: str) -> bool:
    """Две непересекающиеся тройки одинаковых цифр: AAABBB..."""
    return len(re.findall(r"(\d)\1\1", s)) >= 2


def count_pairs(s: str) -> int:
    return len(re.findall(r"(\d)\1", s))


def categorize(msisdn: str) -> str:
    s = subscriber_part(msisdn)
    if len(s) != SUBSCRIBER_LEN or not s.isdigit():
        return "invalid"

    if has_run(s, 6):
        return "AAAAAA"
    if is_periodic_pair(s):
        return "ABABAB"
    if triple_pairs(s):
        return "AAABBB"
    if s.endswith("000"):
        return "+1000"
    if s.endswith("00"):
        return "+100"
    if has_run(s, 3):
        return "AAA"
    if count_pairs(s) >= 3:
        return "pair-rich"
    return "standard"


def run(src_path: str) -> None:
    rows = []
    with open(src_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["category"] = categorize(row["msisdn"])
            rows.append(row)

    out_path = src_path.rsplit(".", 1)[0] + "_categorized.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    summary = Counter(r["category"] for r in rows)
    total = len(rows)
    print(f"Обработано номеров: {total}")
    for cat, n in summary.most_common():
        print(f"  {cat:<10} {n:>5}  ({n / total:.1%})")
    print(f"Результат: {out_path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python3 phone_categorizer.py <numbers.csv>")
    run(sys.argv[1])
