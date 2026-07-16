#!/usr/bin/env python3
"""Convert inventoried PDFs to reviewable Markdown using local pdftotext.

This is intentionally a loss-aware staging step: it preserves page boundaries,
does not claim metadata is verified, and never edits or moves the source PDF.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def yaml_quote(value):
    if value is None:
        return "null"
    if isinstance(value, int):
        return str(value)
    return '"' + str(value).replace('"', '\\"') + '"'


def convert(path: Path) -> list[str]:
    result = subprocess.run(
        ["pdftotext", "-layout", "-enc", "UTF-8", str(path), "-"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    )
    pages = re.split("\f", result.stdout)
    return [page.rstrip() for page in pages if page.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=ROOT / "pdf-local/manifests/pdf-manifest.ndjson")
    parser.add_argument("--output", type=Path, default=ROOT / "staging/pdf-converted")
    parser.add_argument("--limit", type=int, default=0, help="process at most N records (0 means all)")
    args = parser.parse_args()
    records = [json.loads(line) for line in args.manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.limit:
        records = records[: args.limit]
    args.output.mkdir(parents=True, exist_ok=True)
    for index, record in enumerate(records, 1):
        source = ROOT / record["source_path"]
        identity = record["identity"]
        source_slug = re.sub(r"[^a-z0-9]+", "-", source.stem.lower()).strip("-")[:80] or "source"
        output_name = f"{record['sha256'][:12]}__{source_slug}__{Path(identity['proposed_filename']).with_suffix('.md').name}"
        output_path = args.output / output_name
        if output_path.exists():
            continue
        pages = convert(source)
        frontmatter = [
            "---",
            "type: regulation",
            f"source_pdf: {yaml_quote(record['source_path'])}",
            f"source_sha256: {yaml_quote('sha256:' + record['sha256'])}",
            f"source_bytes: {record['bytes']}",
            f"source_pages: {record['pages']}",
            f"id_candidate: {yaml_quote(identity['id_candidate'])}",
            f"jenis_candidate: {yaml_quote(identity['jenis'])}",
            f"nomor_candidate: {yaml_quote(identity['nomor'])}",
            f"tahun_candidate: {identity['tahun'] if identity['tahun'] is not None else 'null'}",
            f"judul_candidate: {yaml_quote(identity['judul_candidate'])}",
            f"tanggal_diundangkan_candidate: {yaml_quote(identity['tanggal_candidate'])}",
            f"filename_date_status: {yaml_quote((identity['tanggal_candidate'] or (str(identity['tahun']) + '0000' if identity['tahun'] else 'undated')))}",
            "status: needs_identity_review",
            "---",
            "",
            f"# {identity['judul_candidate'] or 'Regulasi (identitas belum terverifikasi)'}",
            "",
            "<!-- Konversi lokal pdftotext; verifikasi struktur dan substansi sebelum dipromosikan. -->",
            "",
        ]
        for page_number, page in enumerate(pages, 1):
            frontmatter.extend([f"<!-- PAGE: {page_number} -->", "", page, ""])
        output_path.write_text("\n".join(frontmatter), encoding="utf-8")
        if index % 100 == 0 or index == len(records):
            print(f"{index}/{len(records)} Markdown staged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
