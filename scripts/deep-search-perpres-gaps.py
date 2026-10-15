#!/usr/bin/env python3
"""
Deep search scraper fokus pada Peraturan Presiden (Perpres) era 2015-2024 yang masih bolong.
Mencari di peraturan.go.id dan peraturan.bpk.go.id.
"""

from __future__ import annotations

import csv
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, quote

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "pdf-local" / "downloads"
PDF_DIR.mkdir(parents=True, exist_ok=True)

class PerpresGapSearcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        })
        self.downloaded = 0

    def download_pdf(self, url: str, filename: str) -> bool:
        dest = PDF_DIR / filename
        if dest.exists() and dest.stat().st_size > 1000:
            return True
        try:
            r = self.session.get(url, stream=True, timeout=30)
            if r.status_code == 200:
                content = r.content
                if len(content) > 500 and content.startswith(b"%PDF"):
                    with open(dest, "wb") as f:
                        f.write(content)
                    print(f"  📥 Sukses download {filename} ({len(content)} bytes)")
                    self.downloaded += 1
                    return True
        except Exception as e:
            print(f"  ❌ Gagal download {url}: {e}")
        return False

    def search_peraturan_go_id(self, nomor: int, tahun: int) -> bool:
        term = f"Peraturan Presiden Nomor {nomor} Tahun {tahun}"
        search_url = f"https://peraturan.go.id/search?q={quote(term)}"
        try:
            resp = self.session.get(search_url, timeout=20)
            if resp.status_code != 200:
                return False
            soup = BeautifulSoup(resp.text, "html.parser")
            items = soup.find_all("div", class_="strip grid")
            for item in items:
                p = item.find("p")
                title = p.get_text(strip=True) if p else ""
                pattern = rf"(?:Nomor|No\.?)\s*{nomor}\s+Tahun\s*{tahun}\b"
                if re.search(pattern, title, re.I):
                    print(f"  ✨ MATCH di peraturan.go.id: {title}")
                    for a in item.find_all("a", href=True):
                        if a["href"].endswith(".pdf"):
                            pdf_url = urljoin("https://peraturan.go.id", a["href"])
                            if self.download_pdf(pdf_url, f"perpres{nomor}-{tahun}.pdf"):
                                return True
                    link = item.find("a", href=True)
                    if link and "/dokumen/" in link["href"]:
                        det_url = urljoin("https://peraturan.go.id", link["href"])
                        det_resp = self.session.get(det_url, timeout=15)
                        if det_resp.status_code == 200:
                            det_soup = BeautifulSoup(det_resp.text, "html.parser")
                            for pdf_a in det_soup.find_all("a", href=True):
                                if pdf_a["href"].endswith(".pdf"):
                                    pdf_url = urljoin("https://peraturan.go.id", pdf_a["href"])
                                    if self.download_pdf(pdf_url, f"perpres{nomor}-{tahun}.pdf"):
                                        return True
        except Exception as e:
            pass
        return False

    def search_bpk(self, nomor: int, tahun: int) -> bool:
        search_url = f"https://peraturan.bpk.go.id/Home/Search?namaprodukhukum=&nomor={nomor}&tahun={tahun}&kategori=&jenisperaturan=4"
        try:
            r = self.session.get(search_url, timeout=20)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                rows = soup.find_all("div", class_="card-body") or soup.find_all("tr")
                for row in rows:
                    text = row.get_text()
                    if f"Nomor {nomor}" in text and str(tahun) in text:
                        for a in row.find_all("a", href=True):
                            if "/Details/" in a["href"]:
                                det_url = urljoin("https://peraturan.bpk.go.id", a["href"])
                                det_r = self.session.get(det_url, timeout=20)
                                if det_r.status_code == 200:
                                    det_soup = BeautifulSoup(det_r.text, "html.parser")
                                    for dl_a in det_soup.find_all("a", href=True):
                                        if "/Download/" in dl_a["href"] or dl_a["href"].endswith(".pdf"):
                                            pdf_url = urljoin("https://peraturan.bpk.go.id", dl_a["href"])
                                            if self.download_pdf(pdf_url, f"perpres{nomor}-{tahun}.pdf"):
                                                return True
        except Exception as e:
            pass
        return False

    def run(self):
        targets = []
        with open(ROOT / "indeks" / "clean-gaps-pusat.csv") as f:
            for row in csv.DictReader(f):
                th = int(row["tahun"])
                if row["jenis"] == "PERPRES" and 2015 <= th <= 2024:
                    for n in row["nomor_list"].split(";"):
                        if n:
                            targets.append((int(n), th))

        # Urutkan dari tahun terbaru
        targets.sort(key=lambda x: (-x[1], x[0]))
        print(f"🎯 Menemukan {len(targets)} target celah Perpres 2015-2024: {targets}")
        
        for no, th in targets:
            print(f"\n🔍 Mencari Perpres No. {no} Tahun {th}...")
            if self.search_peraturan_go_id(no, th):
                continue
            if self.search_bpk(no, th):
                continue
            print(f"  ❌ Belum ditemukan.")
            time.sleep(0.3)

        print(f"\nSelesai! Total Perpres berhasil diunduh: {self.downloaded}")

if __name__ == "__main__":
    searcher = PerpresGapSearcher()
    searcher.run()
