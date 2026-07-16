#!/usr/bin/env python3
"""Search full staged Markdown for publication-date evidence missed by page probes."""

from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MONTHS = "januari februari maret april mei juni juli agustus september oktober november desember"
DATE_RE = re.compile(
    r"\b(?:ditetapkan|diundangkan|disahkan)\s+(?:di\s+[^\n]{0,100}?)?(?:,\s*)?(?:pada\s+)?tanggal\s+(\d{1,2})\s+(" + MONTHS.replace(" ", "|") + r")\s+((?:19|20)\d{2})",
    re.I | re.S,
)


def main() -> int:
    source = ROOT / "pdf-local/manifests/identity-review.csv"
    output = ROOT / "pdf-local/manifests/identity-verification.csv"
    rows = []
    for row in csv.DictReader(source.open(encoding="utf-8")):
        if row["status"] != "needs_review":
            continue
        paths = list((ROOT / "staging/pdf-converted").glob(row["sha256"][:12] + "__*.md"))
        matches = []
        if paths:
            text = paths[0].read_text(encoding="utf-8", errors="replace")
            matches = list(DATE_RE.finditer(text))
        date = ""
        if matches:
            day, month, year = matches[-1].groups()
            month_number = MONTHS.split().index(month.lower()) + 1
            date = f"{year}{month_number:02d}{int(day):02d}"
        row["fulltext_date_candidate"] = date
        row["date_year_matches_regulation_year"] = bool(date and date[:4] == row["tahun_candidate"])
        row["verification_status"] = "date_found_check_title_number" if date else "no_date_found"
        rows.append(row)
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else ["source_path"]
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)
    print(f"Verified ambiguous queue: {len(rows)}")
    print(f"Full-text dates found: {sum(bool(r['fulltext_date_candidate']) for r in rows)}")
    print(f"Date/year matches: {sum(r['date_year_matches_regulation_year'] == 'True' for r in rows)}")


if __name__ == "__main__":
    main()
