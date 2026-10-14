#!/usr/bin/env python3
"""Targeted scraper for missing regulations using peraturan.go.id category crawler."""

from __future__ import annotations

import csv
import io
import math
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

import pypdf
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "pdf-local" / "downloads"
PROCESSED_DIR = ROOT / "pdf-local" / "processed"
REGULASI_DIR = ROOT / "regulasi"
GAPS_CSV = ROOT / "indeks" / "clean-gaps-pusat.csv"

class TargetedGapScraper:
    def __init__(self, target_years: list[int] = None):
        self.base_url = "https://peraturan.go.id"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        PDF_DIR.mkdir(parents=True, exist_ok=True)
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        
        self.missing_targets = set()
        if GAPS_CSV.exists():
            with open(GAPS_CSV, encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    if row["jenis"] == "UU":
                        th = int(row["tahun"])
                        if target_years is None or th in target_years:
                            nos = [int(x) for x in row["nomor_list"].split(";") if x]
                            for n in nos:
                                self.missing_targets.add((th, n))
                                
        print(f"🎯 Target gap UU yang dicari: {len(self.missing_targets)} regulasi")
        self.downloaded_count = 0
        self.skipped_count = 0

    def parse_regulation_number_year(self, title: str) -> tuple[int, int] | None:
        m = re.search(r"(?:Undang-Undang|UU)\s+(?:Nomor|No\.?)\s*(\d+)\s+Tahun\s+(\d{4})", title, re.I)
        if m:
            return int(m.group(2)), int(m.group(1))
        return None

    def get_html(self, url: str) -> str | None:
        try:
            resp = self.session.get(url, timeout=20)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            print(f"❌ Error akses {url}: {e}")
            return None

    def download_pdf(self, pdf_url: str, output_name: str) -> bool:
        dest = PDF_DIR / output_name
        if dest.exists():
            return True
        try:
            r = self.session.get(pdf_url, stream=True, timeout=30)
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"  ✅ Berhasil download: {output_name}")
            self.downloaded_count += 1
            return True
        except Exception as e:
            print(f"  ❌ Gagal download {pdf_url}: {e}")
            return False

    def crawl_uu_pages(self, start_page: int = 20, max_pages: int = 50):
        print(f"🔎 Memindai halaman /uu di peraturan.go.id dari halaman {start_page} hingga {max_pages}...")
        found_in_session = 0
        
        for page in range(start_page, max_pages + 1):
            url = f"{self.base_url}/uu?page={page}"
            html = self.get_html(url)
            if not html:
                break
                
            soup = BeautifulSoup(html, "html.parser")
            items = soup.find_all("div", class_="strip grid")
            if not items:
                print(f"Halaman {page} kosong, berhenti.")
                break
                
            print(f"--- Halaman {page}: mengevaluasi {len(items)} regulasi (Sisa target: {len(self.missing_targets)}) ---")
            for item in items:
                p_tag = item.find("p")
                title = p_tag.get_text(strip=True) if p_tag else ""
                parsed = self.parse_regulation_number_year(title)
                
                if parsed and parsed in self.missing_targets:
                    th, no = parsed
                    print(f"✨ MATCH DITEMUKAN: UU No. {no} Tahun {th} ({title})")
                    
                    pdf_tags = item.find_all("a", href=True)
                    card_pdfs = [urljoin(self.base_url, a["href"]) for a in pdf_tags if a["href"].endswith(".pdf")]
                    
                    if card_pdfs:
                        out_name = f"uu{no}-{th}.pdf"
                        if self.download_pdf(card_pdfs[0], out_name):
                            found_in_session += 1
                            self.missing_targets.remove(parsed)
                            
            time.sleep(0.3)
            if not self.missing_targets:
                print("🎉 Semua target gap berhasil ditemukan!")
                break
                
        print(f"\nSelesai pemindaian! Total diunduh: {self.downloaded_count}")

if __name__ == "__main__":
    years_filter = list(range(1999, 2015))
    scraper = TargetedGapScraper(target_years=years_filter)
    # Halaman 20 - 55 mencakup rentang 2014 ke belakang hingga sekitar 2000
    scraper.crawl_uu_pages(start_page=20, max_pages=60)
