#!/usr/bin/env python3
"""Convert temporary OCR PDFs to reviewable Markdown with page markers."""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=ROOT / "pdf-local/ocr-staging")
    parser.add_argument("--output", type=Path, default=ROOT / "staging/ocr-converted")
    args = parser.parse_args()
    files = sorted(p for p in args.input.glob("*.ocr.pdf") if p.is_file())
    args.output.mkdir(parents=True, exist_ok=True)
    for index, pdf in enumerate(files, 1):
        target = args.output / f"{pdf.stem}.md"
        if target.exists():
            continue
        result = subprocess.run(["pdftotext", "-layout", "-enc", "UTF-8", str(pdf), "-"], capture_output=True, text=True, errors="replace", check=False)
        pages = [p.rstrip() for p in re.split("\f", result.stdout) if p.strip()]
        body = ["---", "type: regulation", f"ocr_pdf: \"{pdf.relative_to(ROOT).as_posix()}\"", f"ocr_sha256: \"sha256:{sha(pdf)}\"", "status: needs_review", "---", "", "<!-- OCR staging; verifikasi substansi sebelum promosi. -->", ""]
        for n, page in enumerate(pages, 1):
            body.extend([f"<!-- PAGE: {n} -->", "", page, ""])
        target.write_text("\n".join(body), encoding="utf-8")
        if index % 10 == 0 or index == len(files):
            print(f"{index}/{len(files)} Markdown OCR staged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
