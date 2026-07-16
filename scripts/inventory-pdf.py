#!/usr/bin/env python3
"""Inventory downloaded regulation PDFs without modifying the source files.

The manifest is deliberately written below pdf-local/, which is ignored by Git.
It is the input for later identity review, renaming, and Markdown conversion.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MONTHS = {
    "januari": 1, "februari": 2, "maret": 3, "april": 4,
    "mei": 5, "juni": 6, "juli": 7, "agustus": 8, "september": 9,
    "oktober": 10, "november": 11, "desember": 12,
}


def pdf_info(path: Path) -> tuple[int | None, str]:
    try:
        result = subprocess.run(["pdfinfo", str(path)], capture_output=True, text=True, check=False)
    except OSError:
        return None, ""
    pages = None
    title = ""
    for line in result.stdout.splitlines():
        key, _, value = line.partition(":")
        if key.strip() == "Pages":
            try:
                pages = int(value.strip())
            except ValueError:
                pass
        elif key.strip() == "Title":
            title = value.strip()
    return pages, title


def page_text(path: Path, page: int) -> str:
    try:
        result = subprocess.run(
            ["pdftotext", "-layout", "-f", str(page), "-l", str(page), str(path), "-"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
        )
        return result.stdout[:12000]
    except OSError:
        return ""


def detect_identity(text: str, source_name: str) -> dict:
    compact = re.sub(r"\s+", " ", text).strip()
    match = re.search(
        r"\b(UNDANG[- ]UNDANG|PERATURAN\s+(?:PEMERINTAH|PRESIDEN|MENTERI|BADAN|OTORITAS)|KEPUTUSAN|SURAT\s+EDARAN)"
        r"[^\n]{0,100}?\bNOMOR\s+([0-9A-Za-z./-]+)\s+TAHUN\s+((?:19|20)\d{2})",
        compact, re.I,
    )
    nomor = match.group(2) if match else None
    tahun = int(match.group(3)) if match else None
    title_match = re.search(r"\bTENTANG\s+(.+?)(?=\s+(?:DENGAN RAHMAT|PRESIDEN REPUBLIK|MENIMBANG|MENGINGAT)\b)", compact, re.I)
    judul = title_match.group(1).strip(" .:-") if title_match else None
    date_match = re.search(
        r"\b(?:Ditetapkan|Diundangkan)\s+(?:di\s+[^\n,]+,?\s+)?(?:pada\s+)?tanggal\s+(\d{1,2})\s+([A-Za-z]+)\s+((?:19|20)\d{2})",
        text, re.I,
    )
    issued = None
    if date_match and date_match.group(2).lower() in MONTHS:
        issued = f"{int(date_match.group(3)):04d}{MONTHS[date_match.group(2).lower()]:02d}{int(date_match.group(1)):02d}"
    kind = "uu" if re.search(r"UNDANG[- ]UNDANG", compact, re.I) else "unknown"
    safe_title = re.sub(r"[^a-z0-9]+", "-", (judul or "unknown").lower()).strip("-")[:100] or "unknown"
    id_value = f"{kind}-{tahun}-{int(nomor):03d}" if kind == "uu" and tahun and nomor and nomor.isdigit() else None
    # YYYY0000 means the regulation year is known but the promulgation day/month
    # still requires verification. It is deliberately distinct from `undated`.
    prefix = issued or (f"{tahun:04d}0000" if tahun else "undated")
    proposed = f"{prefix}__{id_value or kind}__{safe_title}.pdf"
    return {"jenis": kind, "nomor": nomor, "tahun": tahun, "judul_candidate": judul, "tanggal_candidate": issued,
            "id_candidate": id_value, "proposed_filename": proposed}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf-dir", type=Path, default=ROOT / "pdf-local" / "downloads")
    parser.add_argument("--manifest", type=Path, default=ROOT / "pdf-local" / "manifests" / "pdf-manifest.ndjson")
    parser.add_argument("--resume", action="store_true", help="append only PDFs not already present in the manifest")
    args = parser.parse_args()
    paths = sorted(p for p in args.pdf_dir.rglob("*") if p.is_file() and p.suffix.lower() == ".pdf")
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    existing = set()
    if args.resume and args.manifest.exists():
        for line in args.manifest.read_text(encoding="utf-8").splitlines():
            try:
                existing.add(json.loads(line)["source_path"])
            except (ValueError, KeyError):
                continue
        paths = [p for p in paths if p.relative_to(ROOT).as_posix() not in existing]
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    mode = "a" if args.resume else "w"
    with args.manifest.open(mode, encoding="utf-8") as output:
        for index, path in enumerate(paths, 1):
            pages, pdf_title = pdf_info(path)
            first = page_text(path, 1)
            last = page_text(path, pages) if pages and pages > 1 else ""
            record = {
                "source_path": path.relative_to(ROOT).as_posix(),
                "source_name": path.name,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
                "pages": pages,
                "pdf_title": pdf_title or None,
                "identity": detect_identity(first + "\n" + last, path.name),
                "inventoried_at": now,
                "review_status": "needs_identity_review",
            }
            output.write(json.dumps(record, ensure_ascii=False) + "\n")
            if index % 100 == 0 or index == len(paths):
                print(f"{index}/{len(paths)} PDFs inventoried")
    print(f"Manifest: {args.manifest.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
