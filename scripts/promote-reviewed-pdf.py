#!/usr/bin/env python3
"""Copy explicitly approved/high-confidence PDFs into structured local storage."""

from __future__ import annotations

import argparse
import csv
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review", type=Path, default=ROOT / "pdf-local/manifests/identity-review.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "pdf-local/by-regulation")
    parser.add_argument("--auto-candidates", action="store_true", help="promote candidate_ready_for_manual_confirmation rows")
    args = parser.parse_args()
    copied = 0
    skipped = 0
    with args.review.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            approved = row.get("approved", "").lower() == "true"
            candidate = row.get("status") == "candidate_ready_for_manual_confirmation"
            if not (approved or (args.auto_candidates and candidate)):
                skipped += 1
                continue
            regulation_id = row.get("id_candidate") or "unknown"
            source = ROOT / row["source_path"]
            target_dir = args.output / regulation_id
            target_dir.mkdir(parents=True, exist_ok=True)
            target = target_dir / (row.get("proposed_filename") or (source.stem + ".pdf"))
            if target.exists() and target.stat().st_size == source.stat().st_size:
                continue
            if target.exists():
                target = target_dir / f"{source.stem}__sha256-{row['sha256'][:12]}.pdf"
            shutil.copy2(source, target)
            copied += 1
    print(f"Copied: {copied}; skipped: {skipped}; output: {args.output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
