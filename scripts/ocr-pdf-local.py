#!/usr/bin/env python3
"""Run temporary forced OCR on local PDFs without modifying the originals."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=ROOT / "pdf-local/downloads")
    parser.add_argument("--output", type=Path, default=ROOT / "pdf-local/ocr-staging")
    parser.add_argument("--language", default="eng")
    args = parser.parse_args()
    files = sorted(args.input.rglob("*.pdf"))
    args.output.mkdir(parents=True, exist_ok=True)
    for index, source in enumerate(files, 1):
        target = args.output / f"{source.stem}.ocr.pdf"
        if target.exists():
            print(f"{index}/{len(files)} skip {source.name}")
            continue
        command = ["ocrmypdf", "--force-ocr", "--deskew", "--rotate-pages", "-l", args.language, str(source), str(target)]
        result = subprocess.run(command, check=False)
        if result.returncode:
            print(f"{index}/{len(files)} ERROR {source.name} ({result.returncode})")
            if target.exists(): target.unlink()
        else:
            print(f"{index}/{len(files)} done {source.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
