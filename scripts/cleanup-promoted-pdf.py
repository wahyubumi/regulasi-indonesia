#!/usr/bin/env python3
"""Remove download copies only after an identical structured copy is verified."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review", type=Path, default=ROOT / "pdf-local/manifests/identity-review.csv")
    parser.add_argument("--log", type=Path, default=ROOT / "pdf-local/manifests/cleanup-log.ndjson")
    parser.add_argument("--delete", action="store_true", help="actually delete verified source PDFs")
    args = parser.parse_args()
    rows = list(csv.DictReader(args.review.open(encoding="utf-8", newline="")))
    checked = removed = skipped = 0
    args.log.parent.mkdir(parents=True, exist_ok=True)
    with args.log.open("a", encoding="utf-8") as log:
        for row in rows:
            if row.get("status") != "candidate_ready_for_manual_confirmation":
                skipped += 1
                continue
            source = ROOT / row["source_path"]
            target = ROOT / "pdf-local" / "by-regulation" / row["id_candidate"] / row["proposed_filename"]
            if not source.exists() or not target.exists():
                skipped += 1
                continue
            checked += 1
            source_hash = digest(source)
            target_hash = digest(target)
            verified = source_hash == target_hash == row["sha256"]
            event = {
                "source": row["source_path"], "target": target.relative_to(ROOT).as_posix(),
                "sha256": source_hash, "verified": verified,
                "deleted": False, "at": datetime.now().astimezone().isoformat(timespec="seconds"),
            }
            if verified and args.delete:
                source.unlink()
                event["deleted"] = True
                removed += 1
            log.write(json.dumps(event, ensure_ascii=False) + "\n")
    mode = "deleted" if args.delete else "eligible"
    print(f"Checked: {checked}; {mode}: {removed if args.delete else checked}; skipped: {skipped}")
    if not args.delete:
        print("Dry run only. Re-run with --delete to remove verified source PDFs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
