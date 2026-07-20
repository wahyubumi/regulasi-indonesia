#!/usr/bin/env python3
"""Batch convert local PDFs to staging/incoming Markdown with deduplication and OCR fallback."""

from __future__ import annotations

import os
import sys
import re
import shutil
import subprocess
import importlib.util
from pathlib import Path
import pypdf

ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "pdf-local" / "downloads"
OCR_STAGING = ROOT / "pdf-local" / "ocr-staging"
STAGING_INCOMING = ROOT / "staging" / "incoming"
STAGING_REVIEWED = ROOT / "staging" / "reviewed"
STAGING_REJECTED = ROOT / "staging" / "rejected"
REGULASI_DIR = ROOT / "regulasi"
PROCESSED_DIR = ROOT / "pdf-local" / "processed"

# Import process-incoming dynamically to access infer_info and existing_regulation_ids
spec = importlib.util.spec_from_file_location("process_incoming", str(ROOT / "scripts" / "process-incoming.py"))
process_incoming = importlib.util.module_from_spec(spec)
sys.modules["process_incoming"] = process_incoming
spec.loader.exec_module(process_incoming)


def is_scanned_pdf(pdf_path: Path) -> bool:
    try:
        reader = pypdf.PdfReader(pdf_path)
        total_text_len = 0
        for page in reader.pages[:3]:
            text = page.extract_text() or ""
            total_text_len += len(text.strip())
        return total_text_len < 50
    except Exception as e:
        return True


def run_ocr(input_path: Path, output_path: Path) -> bool:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ocrmypdf",
        "--force-ocr",
        "--deskew",
        "--rotate-pages",
        "-l", "eng",
        str(input_path),
        str(output_path)
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Gagal OCR [{input_path.name}]: {e.stderr[:200] if e.stderr else 'error'}")
        return False


def convert_pdf_to_pages(pdf_path: Path) -> list[str]:
    try:
        result = subprocess.run(
            ["pdftotext", "-layout", "-enc", "UTF-8", str(pdf_path), "-"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", check=True
        )
        pages = re.split(r"\f", result.stdout)
        return [page.rstrip() for page in pages if page.strip()]
    except Exception as e:
        print(f"❌ Gagal pdftotext [{pdf_path.name}]: {e}")
        return []


def quick_text(pdf_path: Path) -> str:
    try:
        res = subprocess.run(
            ["pdftotext", "-layout", "-enc", "UTF-8", "-f", "1", "-l", "3", str(pdf_path), "-"],
            capture_output=True, text=True, errors="replace", check=False
        )
        return res.stdout
    except Exception:
        return ""


def main() -> int:
    STAGING_INCOMING.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    OCR_STAGING.mkdir(parents=True, exist_ok=True)

    existing_ids = process_incoming.existing_regulation_ids()
    print(f"Loaded {len(existing_ids)} existing regulation IDs from regulasi/")

    pdf_files = sorted(PDF_DIR.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files in pdf-local/downloads/\n")

    converted_count = 0
    skipped_existing_count = 0
    skipped_staged_count = 0
    ocr_count = 0
    failed_count = 0

    for index, pdf_path in enumerate(pdf_files, 1):
        target_md_name = pdf_path.stem + ".md"
        staged_incoming = STAGING_INCOMING / target_md_name
        staged_reviewed = STAGING_REVIEWED / target_md_name
        staged_rejected = STAGING_REJECTED / target_md_name

        # Check if already staged or reviewed
        if staged_incoming.exists():
            skipped_staged_count += 1
            continue

        if staged_reviewed.exists() or staged_rejected.exists():
            skipped_staged_count += 1
            # Move PDF to processed archive since it has already been processed (reviewed or rejected)
            target_archive = PROCESSED_DIR / pdf_path.name
            if not target_archive.exists():
                shutil.move(str(pdf_path), str(target_archive))
            else:
                pdf_path.unlink() # Delete duplicate if already in processed
            continue

        # Extract header text to infer regulation ID
        txt_header = quick_text(pdf_path)
        info = process_incoming.infer_info(pdf_path, txt_header)

        active_pdf_path = pdf_path
        scanned = is_scanned_pdf(pdf_path)

        if scanned and not info:
            ocr_pdf_path = OCR_STAGING / f"{pdf_path.stem}.ocr.pdf"
            if not ocr_pdf_path.exists():
                print(f"[{index}/{len(pdf_files)}] Running OCR on scanned PDF: {pdf_path.name}...")
                success = run_ocr(pdf_path, ocr_pdf_path)
                if not success:
                    failed_count += 1
                    continue
                ocr_count += 1
            active_pdf_path = ocr_pdf_path
            txt_header = quick_text(active_pdf_path)
            info = process_incoming.infer_info(pdf_path, txt_header)

        # Check if regulation ID already exists in regulasi/
        if info and info.regulation_id in existing_ids:
            skipped_existing_count += 1
            # Move PDF to processed archive since regulation already exists
            target_archive = PROCESSED_DIR / pdf_path.name
            if not target_archive.exists():
                shutil.move(str(pdf_path), str(target_archive))
            print(f"[{index}/{len(pdf_files)}] Skip {pdf_path.name}: {info.regulation_id} already exists in regulasi/")
            continue

        # Extract full text
        pages = convert_pdf_to_pages(active_pdf_path)
        total_text_len = sum(len(page.strip()) for page in pages)
        avg_chars_per_page = total_text_len / len(pages) if pages else 0
        if (total_text_len < 300 or avg_chars_per_page < 100) and active_pdf_path == pdf_path:
            ocr_pdf_path = OCR_STAGING / f"{pdf_path.stem}.ocr.pdf"
            if not ocr_pdf_path.exists():
                print(f"[{index}/{len(pdf_files)}] pdftotext returned very low text density ({avg_chars_per_page:.1f} chars/page), running fallback OCR: {pdf_path.name}...")
                success = run_ocr(pdf_path, ocr_pdf_path)
                if success:
                    active_pdf_path = ocr_pdf_path
                    pages = convert_pdf_to_pages(active_pdf_path)
            else:
                active_pdf_path = ocr_pdf_path
                pages = convert_pdf_to_pages(active_pdf_path)

        total_text_len = sum(len(page.strip()) for page in pages)
        if total_text_len < 50:
            print(f"[{index}/{len(pdf_files)}] ❌ No text extracted from {pdf_path.name}")
            failed_count += 1
            continue

        # Build Markdown content
        markdown_lines = []
        if info and info.jenis:
            markdown_lines.append("---")
            markdown_lines.append(f"bentuk_singkat: {info.jenis}")
            markdown_lines.append(f"nomor: {info.nomor}")
            markdown_lines.append(f"tahun: {info.tahun}")
            markdown_lines.append(f"tentang: {info.judul}")
            markdown_lines.append("---")
            markdown_lines.append("")

        for page_num, page_text in enumerate(pages, 1):
            markdown_lines.append(f"<!-- page: {page_num} -->")
            markdown_lines.append("")
            markdown_lines.append(page_text)
            markdown_lines.append("")

        with open(staged_incoming, "w", encoding="utf-8") as f:
            f.write("\n".join(markdown_lines))

        converted_count += 1
        print(f"[{index}/{len(pdf_files)}] ✅ Staged: {pdf_path.name} -> {target_md_name}")

    print("\n--- Summary ---")
    print(f"Total PDFs checked: {len(pdf_files)}")
    print(f"Converted & Staged: {converted_count}")
    print(f"OCR executed: {ocr_count}")
    print(f"Skipped (already in regulasi/): {skipped_existing_count}")
    print(f"Skipped (already staged): {skipped_staged_count}")
    print(f"Failed: {failed_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
