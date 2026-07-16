#!/usr/bin/env python3
"""Create a deterministic identity-review queue from the PDF manifest.

This script does not promote files. Promotion requires an explicit approved CSV
so an OCR mistake cannot silently become a legal-document identity.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def existing_ids() -> set[str]:
    ids = set()
    for path in (ROOT / "regulasi").glob("**/metadata.yml"):
        try:
            value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            if value.get("id"):
                ids.add(str(value["id"]))
        except yaml.YAMLError:
            pass
    return ids


def score(record: dict, known: set[str]) -> tuple[int, str]:
    identity = record["identity"]
    points = 0
    reasons = []
    if identity.get("id_candidate"):
        points += 3
        reasons.append("id")
    if identity.get("judul_candidate") and len(identity["judul_candidate"]) >= 8:
        points += 2
        reasons.append("judul")
    if identity.get("tanggal_candidate"):
        points += 2
        reasons.append("tanggal")
    if identity.get("id_candidate") in known:
        points += 2
        reasons.append("metadata_match")
    if identity.get("tahun") and identity.get("tanggal_candidate"):
        if str(identity["tanggal_candidate"])[:4] != str(identity["tahun"]):
            reasons.append("tanggal_tahun_berbeda")
            points -= 1
    return points, ",".join(reasons)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=ROOT / "pdf-local/manifests/pdf-manifest.ndjson")
    parser.add_argument("--output", type=Path, default=ROOT / "pdf-local/manifests/identity-review.csv")
    args = parser.parse_args()
    known = existing_ids()
    rows = []
    for line in args.manifest.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        identity = record["identity"]
        points, reasons = score(record, known)
        status = "candidate_ready_for_manual_confirmation" if points >= 7 and identity.get("tanggal_candidate") else "needs_review"
        rows.append({
            "source_path": record["source_path"], "source_name": record["source_name"],
            "sha256": record["sha256"], "bytes": record["bytes"], "pages": record["pages"],
            "id_candidate": identity.get("id_candidate") or "", "jenis_candidate": identity.get("jenis") or "",
            "nomor_candidate": identity.get("nomor") or "", "tahun_candidate": identity.get("tahun") or "",
            "judul_candidate": identity.get("judul_candidate") or "",
            "tanggal_diundangkan_candidate": identity.get("tanggal_candidate") or "",
            "proposed_filename": identity.get("proposed_filename") or "",
            "score": points, "evidence": reasons, "status": status, "approved": "false",
        })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    print(f"Review queue: {args.output.relative_to(ROOT)} ({len(rows)} rows)")
    print(f"Candidates requiring manual confirmation: {sum(row['status'].startswith('candidate') for row in rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
