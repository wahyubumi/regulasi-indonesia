#!/usr/bin/env python3
"""
Deep search scraper untuk sisa PP dan Perpres yang bolong:
Target:
1. PP 2001 (gap besar 59 nomor)
2. Perpres 2004 (gap 15 nomor)
3. PP 2003-2026 sisa
4. Perpres 2018-2025 sisa
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

class TargetedGapScraper:
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
            pass
        return False

    def search_peraturan_go_id(self, jenis: str, nomor: int, tahun: int) -> bool:
        jenis_lengkap = "Peraturan Pemerintah" if jenis == "pp" else "Peraturan Presiden"
        term = f"{jenis_lengkap} Nomor {nomor} Tahun {tahun}"
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
                # Match strict nomor & tahun
                pattern = rf"(?:Nomor|No\.?)\s*{nomor}\s+Tahun\s*{tahun}\b"
                if re.search(pattern, title, re.I):
                    print(f"  ✨ MATCH di peraturan.go.id: {title}")
                    for a in item.find_all("a", href=True):
                        if a["href"].endswith(".pdf"):
                            pdf_url = urljoin("https://peraturan.go.id", a["href"])
                            if self.download_pdf(pdf_url, f"{jenis}{nomor}-{tahun}.pdf"):
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
                                    if self.download_pdf(pdf_url, f"{jenis}{nomor}-{tahun}.pdf"):
                                        return True
        except Exception as e:
            pass
        return False

    def search_bpk(self, jenis: str, nomor: int, tahun: int) -> bool:
        # jenisperaturan: 3 = PP, 4 = Perpres
        jp = "3" if jenis == "pp" else "4"
        search_url = f"https://peraturan.bpk.go.id/Home/Search?namaprodukhukum=&nomor={nomor}&tahun={tahun}&kategori=&jenisperaturan={jp}"
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
                                            if self.download_pdf(pdf_url, f"{jenis}{nomor}-{tahun}.pdf"):
                                                return True
        except Exception as e:
            pass
        return False

    def run(self, max_batch: int = 50):
        targets = []
        processed_dir = ROOT / "pdf-local" / "processed"
        with open(ROOT / "indeks" / "clean-gaps-pusat.csv") as f:
            for row in csv.DictReader(f):
                th = int(row["tahun"])
                j = row["jenis"].lower()
                if j in ("pp", "perpres") and th >= 2000:
                    for n in row["nomor_list"].split(";"):
                        if n:
                            num = int(n)
                            # Cek apakah file sudah ada di downloads atau processed
                            fname = f"{j}{num}-{th}.pdf"
                            if (PDF_DIR / fname).exists() or (processed_dir / fname).exists():
                                continue
                            targets.append((j, num, th))

        # Sort: utamakan PP 2001 dan Perpres 2004, lalu yang teranyar
        def priority_key(item):
            j, n, th = item
            if j == "pp" and th == 2001:
                return (0, n)
            if j == "perpres" and th == 2004:
                return (1, n)
            return (2, -th, n)

        targets.sort(key=priority_key)
        batch = targets[:max_batch]
        print(f"🎯 Target regulasi yang dicari ({len(batch)} regulasi):")
        for j, no, th in batch:
            print(f" - {j.upper()} {no}/{th}")

        for j, no, th in batch:
            print(f"\n🔍 Mencari {j.upper()} No. {no} Tahun {th}...")
            if self.search_peraturan_go_id(j, no, th):
                continue
            if self.search_bpk(j, no, th):
                continue
            print(f"  ❌ Belum ditemukan.")
            time.sleep(0.2)

        print(f"\nSelesai! Total regulasi berhasil diunduh: {self.downloaded}")

if __name__ == "__main__":
    scraper = TargetedGapScraper()
    max_b = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    scraper.run(max_batch=max_b)
