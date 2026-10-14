#!/usr/bin/env python3
"""Calculate clean gaps across all national regulations (UU, PP, Perpres) and export to CSV/Markdown."""

import csv
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX_CSV = ROOT / "indeks" / "index-regulasi.csv"
OUTPUT_CSV = ROOT / "indeks" / "clean-gaps-pusat.csv"

data = defaultdict(lambda: defaultdict(set))

with open(INDEX_CSV, encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row.get("tingkat") == "pusat" and row.get("tahun") and row.get("nomor"):
            try:
                th = int(row["tahun"])
                m = re.search(r"^\d+", row["nomor"].strip())
                if m:
                    data[row["jenis"]][th].add(int(m.group(0)))
            except ValueError:
                pass

def to_ranges(nums):
    if not nums: return ""
    ranges = []
    start = nums[0]
    end = nums[0]
    for n in nums[1:]:
        if n == end + 1:
            end = n
        else:
            ranges.append(f"{start}" if start == end else f"{start}-{end}")
            start = end = n
    ranges.append(f"{start}" if start == end else f"{start}-{end}")
    return ", ".join(ranges)

rows_out = []
print("=== RINGKASAN GAP PASCA-PROMOSI ===")

for jenis in ["uu", "pp", "perpres"]:
    total_existing = sum(len(v) for v in data[jenis].values())
    total_missing = 0
    years = sorted(data[jenis].keys())
    
    for th in years:
        if th < 1945:
            continue
        present = data[jenis][th]
        max_no = max(present) if present else 0
        full = set(range(1, max_no + 1))
        missing = sorted(full - present)
        
        if missing:
            total_missing += len(missing)
            rows_out.append({
                "jenis": jenis.upper(),
                "tahun": th,
                "terisi": len(present),
                "nomor_tertinggi": max_no,
                "jumlah_bolong": len(missing),
                "daftar_nomor_bolong": to_ranges(missing),
                "nomor_list": ";".join(str(x) for x in missing)
            })
            
    print(f"{jenis.upper():<8}: {total_existing:>5} terindeks | {total_missing:>4} nomor bolong tersisa")

with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["jenis", "tahun", "terisi", "nomor_tertinggi", "jumlah_bolong", "daftar_nomor_bolong", "nomor_list"])
    writer.writeheader()
    writer.writerows(rows_out)

print(f"\nDetail sisa gap berhasil diekspor ke: {OUTPUT_CSV.relative_to(ROOT)}")
