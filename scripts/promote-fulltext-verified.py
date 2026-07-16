#!/usr/bin/env python3
"""Promote full-text date matches whose date year matches the regulation year."""

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
    review = ROOT / "pdf-local/manifests/identity-verification.csv"
    promoted = deleted = skipped = 0
    log = ROOT / "pdf-local/manifests/fulltext-promotion.log"
    with review.open(encoding="utf-8", newline="") as handle, log.open("a", encoding="utf-8") as audit:
        for row in csv.DictReader(handle):
            if not (row["fulltext_date_candidate"] and row["date_year_matches_regulation_year"] == "True" and row["id_candidate"] and row["judul_candidate"]):
                skipped += 1; continue
            source = ROOT / row["source_path"]
            slug = re.sub(r"[^a-z0-9]+", "-", row["judul_candidate"].lower()).strip("-")[:100] or "judul"
            target = ROOT / "pdf-local/by-regulation" / row["id_candidate"] / f"{row['fulltext_date_candidate']}__{row['id_candidate']}__{slug}.pdf"
            if not source.exists():
                skipped += 1; continue
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            verified = sha(source) == sha(target) == row["sha256"]
            if verified:
                source.unlink(); promoted += 1; deleted += 1
                audit.write(f"{row['source_path']} -> {target.relative_to(ROOT)} sha256={row['sha256']}\n")
            else:
                target.unlink(); skipped += 1
    print(f"Promoted and deleted: {deleted}; skipped: {skipped}")


if __name__ == "__main__":
    main()
