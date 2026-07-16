#!/usr/bin/env python3
"""Extract review candidates from OCR-derived Markdown."""

from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MONTHS = "januari februari maret april mei juni juli agustus september oktober november desember"
DATE_RE = re.compile(r"\b(?:ditetapkan|diundangkan|disahkan)\s+(?:di\s+[^\n]{0,100}?)?(?:,\s*)?(?:pada\s+)?tanggal\s+(\d{1,2})\s+(" + MONTHS.replace(" ", "|") + r")\s+((?:19|20)\d{2})", re.I | re.S)
ID_RE = re.compile(r"\bUNDANG[-.]?UNDANG\s+REPUBLIK\s+INDONESIA[\s\S]{0,180}?NOMOR\s+(\d+)\s+TAHUN\s+((?:19|20)\d{2})", re.I)


def main() -> int:
    out = ROOT / "pdf-local/manifests/ocr-review.csv"
    rows = []
    for path in sorted((ROOT / "staging/ocr-converted").glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        identity = ID_RE.search(text[:12000])
        dates = list(DATE_RE.finditer(text))
        date = ""
        if dates:
            day, month, year = dates[-1].groups()
            date = f"{year}{MONTHS.split().index(month.lower()) + 1:02d}{int(day):02d}"
        title = ""
        m = re.search(r"\bTENTANG\s+(.+?)(?=\s+(?:DENGAN RAHMAT|PRESIDEN REPUBLIK|MENIMBANG|MENGINGAT)\b)", re.sub(r"\s+", " ", text[:12000]), re.I)
        if m: title = m.group(1).strip(" .:-")
        rows.append({"ocr_markdown": path.relative_to(ROOT).as_posix(), "id_candidate": f"uu-{identity.group(2)}-{int(identity.group(1)):03d}" if identity else "", "judul_candidate": title, "tanggal_candidate": date, "status": "candidate" if identity and title and date else "needs_review"})
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    print(f"OCR review queue: {len(rows)}; candidates: {sum(r['status']=='candidate' for r in rows)}")


if __name__ == "__main__":
    main()
