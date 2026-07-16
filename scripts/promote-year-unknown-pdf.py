#!/usr/bin/env python3
"""Promote identified regulations whose promulgation day/month is unknown."""

from __future__ import annotations

import csv
import hashlib
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    review = ROOT / "pdf-local/manifests/identity-review.csv"
    promoted = skipped = 0
    with review.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            source = ROOT / row["source_path"]
            if row["tanggal_diundangkan_candidate"] or not (row["id_candidate"] and row["tahun_candidate"] and row["judul_candidate"]) or not source.exists():
                skipped += 1; continue
            slug = re.sub(r"[^a-z0-9]+", "-", row["judul_candidate"].lower()).strip("-")[:100] or "judul"
            target = ROOT / "pdf-local/by-regulation" / row["id_candidate"] / f"{row['tahun_candidate']}0000__{row['id_candidate']}__{slug}.pdf"
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            if sha(source) != sha(target) or sha(source) != row["sha256"]:
                target.unlink(); skipped += 1; continue
            source.unlink(); promoted += 1
    print(f"Promoted YYYY0000 and deleted: {promoted}; skipped: {skipped}")


if __name__ == "__main__":
    main()
