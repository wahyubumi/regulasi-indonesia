#!/usr/bin/env python3
"""Scraper for regulations from peraturan.go.id with clean HTML parsing, multi-PDF merging, and deduplication."""

from __future__ import annotations

import os
import sys
import re
import math
import time
import io
import shutil
import subprocess
import importlib.util
from pathlib import Path
from urllib.parse import urljoin, unquote
import requests
from bs4 import BeautifulSoup
import pypdf

ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "pdf-local" / "downloads"
PROCESSED_DIR = ROOT / "pdf-local" / "processed"
REGULASI_DIR = ROOT / "regulasi"

# Import process-incoming dynamically to access existing_regulation_ids
spec = importlib.util.spec_from_file_location("process_incoming", str(ROOT / "scripts" / "process-incoming.py"))
process_incoming = importlib.util.module_from_spec(spec)
sys.modules["process_incoming"] = process_incoming
spec.loader.exec_module(process_incoming)


class PeraturanScraper:
    def __init__(self):
        self.base_url = "https://peraturan.go.id"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        PDF_DIR.mkdir(parents=True, exist_ok=True)
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        self.existing_ids = process_incoming.existing_regulation_ids()
        self.downloaded_count = 0
        self.merged_count = 0
        self.skipped_count = 0

    def get_html(self, url: str) -> str | None:
        try:
            resp = self.session.get(url, timeout=20)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            print(f"❌ Error accessing {url}: {e}")
            return None

    def get_total_pages(self, html: str) -> int:
        soup = BeautifulSoup(html, "html.parser")
        h4 = soup.find("h4")
        if h4:
            text = h4.get_text(strip=True)
            match = re.search(r"([\d\.]+)\s*Peraturan", text)
            if match:
                total_regulations = float(match.group(1).replace(".", ""))
                items_per_page = 20
                return math.ceil(total_regulations / items_per_page)
        
        pagination = soup.find("ul", class_="pagination")
        if pagination:
            pages = pagination.find_all("a")
            if pages:
                last_visible = pages[-2].get_text(strip=True) if len(pages) > 1 else "1"
                try:
                    return int(last_visible)
                except Exception:
                    pass
        return 1

    def extract_regulation_items(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        items = soup.find_all("div", class_="strip grid")
        regulations = []

        for item in items:
            title_tag = item.find("p")
            judul = title_tag.get_text(strip=True) if title_tag else "unknown"
            
            year_tag = item.find("a", class_="wish_bt")
            tahun = year_tag.get_text(strip=True) if year_tag else "unknown"

            # Detail page link: href contains /id/ and does NOT end with /#
            detail_tag = item.find("a", href=lambda h: h and "/id/" in h and not h.endswith("#"))
            detail_url = urljoin(self.base_url, detail_tag["href"]) if detail_tag else None

            # Direct PDF links from item card
            pdf_tags = item.find_all("a", href=True)
            card_pdf_urls = [urljoin(self.base_url, a["href"]) for a in pdf_tags if a["href"].endswith(".pdf")]

            regulations.append({
                "judul": judul,
                "tahun": tahun,
                "detail_url": detail_url,
                "card_pdf_urls": list(dict.fromkeys(card_pdf_urls)),
            })

        return regulations

    def get_all_pdf_urls(self, reg_item: dict) -> list[str]:
        pdf_urls = list(reg_item["card_pdf_urls"])

        if reg_item["detail_url"]:
            detail_html = self.get_html(reg_item["detail_url"])
            if detail_html:
                soup = BeautifulSoup(detail_html, "html.parser")
                
                # Clean header, footer, nav, sidebar, recommendation carousels
                for el in soup.find_all(["footer", "header", "nav", "aside"]):
                    el.decompose()

                for el in soup.find_all("div", class_=lambda c: c and any(x in str(c) for x in ["sidebar", "footer", "booking_buttons", "carousel", "recommendation", "latest", "popolar"])):
                    el.decompose()

                detail_pdf_tags = soup.find_all("a", href=True)
                for a in detail_pdf_tags:
                    href = a["href"]
                    if href.endswith(".pdf") and ("/files/" in href or "/files2/" in href):
                        full_url = urljoin(self.base_url, href)
                        if full_url not in pdf_urls:
                            pdf_urls.append(full_url)

        return list(dict.fromkeys(pdf_urls))

    def merge_and_save_pdfs(self, pdf_urls: list[str], output_filename: str) -> bool:
        output_path = PDF_DIR / output_filename
        if output_path.exists():
            print(f"⏭️ File already in downloads: {output_filename}")
            self.skipped_count += 1
            return True

        processed_path = PROCESSED_DIR / output_filename
        if processed_path.exists():
            print(f"⏭️ File already processed: {output_filename}")
            self.skipped_count += 1
            return True

        if len(pdf_urls) == 1:
            # Single PDF download
            try:
                resp = self.session.get(pdf_urls[0], stream=True, timeout=30)
                resp.raise_for_status()
                with open(output_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"✅ Downloaded (Single): {output_filename}")
                self.downloaded_count += 1
                return True
            except Exception as e:
                print(f"❌ Failed downloading {pdf_urls[0]}: {e}")
                return False
        else:
            # Multi-PDF merge requirement
            print(f"🔗 Merging {len(pdf_urls)} PDF parts for: {output_filename}")
            merger = pypdf.PdfWriter()

            for index, pdf_url in enumerate(pdf_urls, 1):
                try:
                    resp = self.session.get(pdf_url, timeout=30)
                    resp.raise_for_status()
                    pdf_data = io.BytesIO(resp.content)
                    reader = pypdf.PdfReader(pdf_data)
                    merger.append(reader)
                    print(f"   + Added part {index}/{len(pdf_urls)}: {os.path.basename(pdf_url)}")
                except Exception as e:
                    print(f"   ⚠️ Warning part {index} failed ({pdf_url}): {e}")

            try:
                with open(output_path, "wb") as f:
                    merger.write(f)
                merger.close()
                print(f"✅ Merged & Saved ({len(pdf_urls)} parts): {output_filename}")
                self.downloaded_count += 1
                self.merged_count += 1
                return True
            except Exception as e:
                print(f"❌ Failed saving merged PDF {output_filename}: {e}")
                return False

    def process_category(self, category: str):
        print(f"\n==========================================")
        print(f"🌐 Category: /{category}")
        print(f"==========================================")

        first_url = f"{self.base_url}/{category}?page=1"
        first_html = self.get_html(first_url)
        if not first_html:
            print(f"⚠️ Skipping category {category} due to page 1 fetch failure.")
            return

        total_pages = self.get_total_pages(first_html)
        print(f"📄 Found {total_pages} total pages in /{category}")

        for page in range(1, total_pages + 1):
            url = f"{self.base_url}/{category}?page={page}"
            html = first_html if page == 1 else self.get_html(url)
            if not html:
                continue

            items = self.extract_regulation_items(html)
            print(f"\n--- Page {page}/{total_pages} (found {len(items)} regulations) ---")

            for item in items:
                pdf_urls = self.get_all_pdf_urls(item)
                if not pdf_urls:
                    continue

                primary_filename = os.path.basename(pdf_urls[0])
                if not primary_filename.endswith(".pdf"):
                    primary_filename += ".pdf"

                self.merge_and_save_pdfs(pdf_urls, primary_filename)
                time.sleep(0.2)

            time.sleep(0.3)

    def run(self, categories: list[str]):
        print(f"🚀 Starting scraper for categories: {categories}")
        for cat in categories:
            self.process_category(cat)

        print(f"\n==========================================")
        print(f"✨ Scraping & Merging Completed ✨")
        print(f"Total Downloaded/Merged: {self.downloaded_count}")
        print(f"Total Multi-PDFs Merged: {self.merged_count}")
        print(f"Total Skipped (already exists): {self.skipped_count}")
        print(f"Target Directory: {PDF_DIR}")
        print(f"==========================================")


if __name__ == "__main__":
    target_categories = ["tapmpr", "perppu", "pp", "perpres", "permen", "permenkumham", "permenkum", "perban", "perda"]
    if len(sys.argv) > 1:
        target_categories = sys.argv[1:]

    scraper = PeraturanScraper()
    scraper.run(target_categories)
