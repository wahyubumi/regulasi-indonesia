#!/usr/bin/env python3
"""
Autonomous Runner untuk mengisi celah regulasi (PP, Perpres, Permen, UU).
Mencari di beberapa sumber (peraturan.go.id, jdih bpk, dll), mengunduh PDF valid,
mengonversi ke Markdown, mengimpor ke regulasi/, dan memperbarui indeks secara otomatis berulang kali.
"""

import sys
import os
import time
import subprocess
import csv
import re
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "pdf-local" / "downloads"
PROCESSED_DIR = ROOT / "pdf-local" / "processed"
GAPS_CSV = ROOT / "indeks" / "clean-gaps-pusat.csv"

PDF_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

class AutoRegulationFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

    def run_command(self, cmd_list):
        print(f"⚙️ Menjalankan: {' '.join(cmd_list)}")
        res = subprocess.run(cmd_list, cwd=str(ROOT), capture_output=True, text=True)
        if res.returncode != 0:
            print(f"⚠️ Error {cmd_list[0]}: {res.stderr[:300]}")
        else:
            print(f"✅ Selesai: {res.stdout.strip()[:200]}")
        return res

    def search_bpk_or_peraturan(self, jenis, nomor, tahun):
        """Mencari PDF dari berbagai endpoint."""
        # 1. Search peraturan.go.id direct search query
        jenis_query = {
            "UU": "undang-undang",
            "PP": "peraturan-pemerintah",
            "PERPRES": "peraturan-presiden"
        }.get(jenis, jenis.lower())
        
        search_url = f"https://peraturan.go.id/search?q={jenis_query}+nomor+{nomor}+tahun+{tahun}"
        try:
            r = self.session.get(search_url, timeout=15)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    # Cek jika ada link detail dokumen
                    if "/dokumen/" in href or "/view/" in href:
                        detail_url = urljoin("https://peraturan.go.id", href)
                        det_resp = self.session.get(detail_url, timeout=15)
                        if det_resp.status_code == 200:
                            det_soup = BeautifulSoup(det_resp.text, "html.parser")
                            for pdf_a in det_soup.find_all("a", href=True):
                                if pdf_a["href"].endswith(".pdf") or "download" in pdf_a["href"]:
                                    pdf_url = urljoin("https://peraturan.go.id", pdf_a["href"])
                                    if self.download_and_verify(pdf_url, f"{jenis.lower()}{nomor}-{tahun}.pdf"):
                                        return True
                    elif href.endswith(".pdf"):
                        pdf_url = urljoin("https://peraturan.go.id", href)
                        if self.download_and_verify(pdf_url, f"{jenis.lower()}{nomor}-{tahun}.pdf"):
                            return True
        except Exception as e:
            pass
        return False

    def download_and_verify(self, url, filename):
        dest = PDF_DIR / filename
        if dest.exists() and dest.stat().st_size > 1000:
            return True
        try:
            resp = self.session.get(url, timeout=30, stream=True)
            if resp.status_code == 200:
                content = resp.content
                if len(content) > 500 and content.startswith(b"%PDF"):
                    with open(dest, "wb") as f:
                        f.write(content)
                    print(f"📥 Berhasil download {filename} ({len(content)} bytes)")
                    return True
        except Exception as e:
            pass
        return False

    def crawl_active_listings(self, jenis_type="pp", max_pages=30):
        """Memindai listing terbaru untuk mengisi gap."""
        url_path = "peraturan-pemerintah" if jenis_type == "pp" else "perpres"
        print(f"🔍 Crawling /{url_path}...")
        
        # Baca gap terkini
        target_gaps = set()
        if GAPS_CSV.exists():
            with open(GAPS_CSV, encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    if row["jenis"].lower() == jenis_type.lower():
                        th = int(row["tahun"])
                        for n in row["nomor_list"].split(";"):
                            if n:
                                target_gaps.add((th, int(n)))

        print(f"Target {jenis_type.upper()} gap: {len(target_gaps)} regulasi.")
        found = 0
        for page in range(1, max_pages + 1):
            url = f"https://peraturan.go.id/{url_path}?page={page}"
            try:
                r = self.session.get(url, timeout=20)
                if r.status_code != 200:
                    break
                soup = BeautifulSoup(r.text, "html.parser")
                items = soup.find_all("div", class_="strip grid")
                if not items:
                    break
                
                for item in items:
                    p = item.find("p")
                    title = p.get_text(strip=True) if p else ""
                    m = re.search(r"(?:Nomor|No\.?)\s*(\d+)\s+Tahun\s+(\d{4})", title, re.I)
                    if m:
                        no = int(m.group(1))
                        th = int(m.group(2))
                        if (th, no) in target_gaps:
                            # Ambil link PDF
                            for a in item.find_all("a", href=True):
                                if a["href"].endswith(".pdf"):
                                    pdf_url = urljoin("https://peraturan.go.id", a["href"])
                                    fn = f"{jenis_type}{no}-{th}.pdf"
                                    if self.download_and_verify(pdf_url, fn):
                                        found += 1
                                        target_gaps.discard((th, no))
                                        break
            except Exception as e:
                print(f"Error crawl halaman {page}: {e}")
            time.sleep(0.2)
        print(f"Total {jenis_type.upper()} baru diunduh: {found}")
        return found

    def cycle(self):
        print("\n🚀 Memulai 1 siklus pemenuhan regulasi otomatis...")
        # 1. Update gap analysis
        self.run_command(["python3", "scripts/analyze-clean-gaps.py"])
        
        # 2. Crawl PP & Perpres
        dl_pp = self.crawl_active_listings("pp", max_pages=40)
        dl_perpres = self.crawl_active_listings("perpres", max_pages=40)
        
        # 3. Batch convert jika ada file baru di pdf-local/downloads/
        pdfs = list(PDF_DIR.glob("*.pdf"))
        if pdfs:
            print(f"📦 Ditemukan {len(pdfs)} PDF siap dikonversi...")
            self.run_command(["python3", "scripts/batch-convert-local.py"])
            self.run_command(["python3", "scripts/process-incoming.py"])
            self.run_command(["python3", "scripts/generate-index.py"])
            self.run_command(["python3", "scripts/analyze-clean-gaps.py"])
        else:
            print("ℹ️ Tidak ada PDF baru di antrean download.")

if __name__ == "__main__":
    fetcher = AutoRegulationFetcher()
    fetcher.cycle()
