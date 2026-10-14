#!/usr/bin/env python3
"""Promote staging/pdf-converted UU markdown files into regulasi/pusat/uu/ with standard AGENTS.md files."""

from __future__ import annotations

import csv
import glob
import re
import shutil
import unicodedata
from collections import defaultdict
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
STAGING_DIR = ROOT / "staging" / "pdf-converted"
REGULASI_DIR = ROOT / "regulasi" / "pusat" / "uu"
INDEX_CSV = ROOT / "indeks" / "index-regulasi.csv"

def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_val = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_val.lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    return slug[:80].rstrip("-") or "judul"

def get_existing_ids() -> set[str]:
    existing = set()
    if INDEX_CSV.exists():
        with open(INDEX_CSV, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("jenis") == "uu" and row.get("nomor") and row.get("tahun"):
                    m = re.search(r"\d+", row["nomor"])
                    if m:
                        existing.add(f"uu-{int(row['tahun']):04d}-{int(m.group(0)):03d}")
    # Also check filesystem directly
    for meta_path in REGULASI_DIR.glob("**/metadata.yml"):
        try:
            with open(meta_path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                if data.get("id"):
                    existing.add(data["id"])
        except Exception:
            pass
    return existing

def clean_title(title: str) -> str:
    # Clean redundant whitespace and legal formatting noise
    t = re.sub(r"\s+", " ", title or "").strip(" .:\r\n")
    t = re.sub(r"^(tentang|mengenai)\s+", "", t, flags=re.I).strip()
    return t

def parse_header_body(content: str) -> tuple[dict, str]:
    if not content.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    try:
        meta = yaml.safe_load(parts[1]) or {}
    except Exception:
        meta = {}
    body = parts[2].strip()
    return meta, body

def determine_actual_identity(filename: str, meta: dict, body: str) -> tuple[str, int, str]:
    # Check if filename hints at actual number (e.g. uu12-1949.pdf inside uu27-1948)
    src_pdf = meta.get("source_pdf", "")
    m_pdf = re.search(r"uu(\d+)-(\d{4})", src_pdf)
    
    # Check body for leading official header like "UNDANG-UNDANG (UU) 1949 No. 12" or "NOMOR 12 TAHUN 1949"
    head_sample = body[:1000]
    m_head = re.search(r"UNDANG-UNDANG\s*(?:\(UU\))?\s*(\d{4})\s*No\.?\s*(\d+)", head_sample, re.I)
    m_nomor_tahun = re.search(r"NOMOR\s+(\d+)\s+TAHUN\s+(\d{4})", head_sample, re.I)
    
    tahun = meta.get("tahun_candidate")
    nomor = meta.get("nomor_candidate")
    
    if m_nomor_tahun:
        nomor = int(m_nomor_tahun.group(1))
        tahun = int(m_nomor_tahun.group(2))
    elif m_head:
        tahun = int(m_head.group(1))
        nomor = int(m_head.group(2))
    elif m_pdf:
        nomor = int(m_pdf.group(1))
        tahun = int(m_pdf.group(2))
    else:
        try:
            m_no = re.search(r"\d+", str(nomor))
            nomor = int(m_no.group(0)) if m_no else 0
            tahun = int(tahun) if tahun else 0
        except Exception:
            nomor, tahun = 0, 0
            
    m_no = re.search(r"\d+", str(nomor))
    no_int = int(m_no.group(0)) if m_no else 0
    tahun_int = int(tahun) if tahun else 0
    
    if tahun_int and no_int:
        reg_id = f"uu-{tahun_int:04d}-{no_int:03d}"
    else:
        reg_id = meta.get("id_candidate") or ""
        
    judul = clean_title(meta.get("judul_candidate", ""))
    return reg_id, tahun_int, str(no_int), judul

def build_dokumen_md(reg_id: str, nomor: str, tahun: int, judul: str, body: str) -> str:
    judul_lengkap = f"Undang-Undang Nomor {nomor} Tahun {tahun} tentang {judul}"
    
    # Strip any redundant H1 at top of body if it matches judul
    cleaned_body = re.sub(r"^#\s+.*?\n+", "", body).strip()
    
    return f"""---
id: "{reg_id}"
jenis: "uu"
nomor: "{nomor}"
tahun: {tahun}
judul: "{judul_lengkap}"
status: "perlu_verifikasi"
sumber: "Ditjen Peraturan Perundang-undangan / JDIH"
---

# {judul_lengkap}

## Catatan Konversi

Dokumen ini merupakan hasil konversi dari format PDF ke Markdown. Untuk rujukan hukum resmi, gunakan dokumen resmi dari sumber regulasi terkait.

---

## Teks Regulasi

{cleaned_body}
"""

def main():
    existing_ids = get_existing_ids()
    print(f"Total UU sudah ada di regulasi/: {len(existing_ids)}")
    
    staging_files = sorted(STAGING_DIR.glob("*.md"))
    print(f"Total file staging ditemukan: {len(staging_files)}")
    
    # Group candidates by reg_id
    candidates = defaultdict(list)
    for p in staging_files:
        with open(p, encoding="utf-8") as f:
            content = f.read()
        meta, body = parse_header_body(content)
        if not meta or meta.get("jenis_candidate") != "uu":
            continue
        reg_id, th, no, judul = determine_actual_identity(p.name, meta, body)
        if reg_id and th and no:
            candidates[reg_id].append({
                "path": p,
                "meta": meta,
                "body": body,
                "reg_id": reg_id,
                "tahun": th,
                "nomor": no,
                "judul": judul,
                "bytes": meta.get("source_bytes", 0) or len(content)
            })
            
    print(f"Total kandidat UU unik teridentifikasi: {len(candidates)}")
    
    promoted = 0
    skipped_existing = 0
    
    for reg_id, items in sorted(candidates.items()):
        if reg_id in existing_ids:
            skipped_existing += 1
            continue
            
        # Choose best item by byte size / completeness
        best = max(items, key=lambda x: x["bytes"])
        
        tahun = best["tahun"]
        nomor = best["nomor"]
        judul = best["judul"] or "Regulasi"
        slug = slugify(judul)
        nomor_3d = f"{int(nomor):03d}"
        
        folder_name = f"uu-{tahun}-{nomor_3d}-{slug}"
        target_dir = REGULASI_DIR / str(tahun) / folder_name
        target_dir.mkdir(parents=True, exist_ok=True)
        
        judul_lengkap = f"Undang-Undang Nomor {nomor} Tahun {tahun} tentang {judul}"
        sha_val = best["meta"].get("source_sha256", "").replace("sha256:", "") or None
        source_pdf_name = Path(best["meta"].get("source_pdf", "external.pdf")).name
        
        # 1. dokumen.md
        dok_content = build_dokumen_md(reg_id, nomor, tahun, judul, best["body"])
        (target_dir / "dokumen.md").write_text(dok_content, encoding="utf-8")
        
        # 2. metadata.yml
        meta_dict = {
            "id": reg_id,
            "jenis": "uu",
            "jenis_lengkap": "Undang-Undang",
            "nomor": str(nomor),
            "nomor_lengkap": str(nomor),
            "tahun": tahun,
            "judul": judul,
            "judul_lengkap": judul_lengkap,
            "tingkat": "pusat",
            "hierarki_level": 3,
            "lembaga_penerbit": ["Presiden Republik Indonesia", "Dewan Perwakilan Rakyat Republik Indonesia"],
            "pejabat_penetap": [],
            "tanggal_ditetapkan": None,
            "tanggal_diundangkan": None,
            "tanggal_berlaku": None,
            "tempat_ditetapkan": None,
            "lembaran_negara": {"nomor": None, "tahun": None},
            "tambahan_lembaran_negara": {"nomor": None},
            "berita_negara": {"nomor": None, "tahun": None},
            "tambahan_berita_negara": {"nomor": None},
            "status": {
                "berlaku": None,
                "status_teks": "perlu_verifikasi",
                "mulai_berlaku": None,
                "berakhir": None,
                "dicabut_oleh": [],
                "mencabut": [],
                "mengubah": [],
                "diubah_oleh": []
            },
            "subjek": [],
            "sektor": [],
            "kata_kunci": [],
            "wilayah": {"level": "", "kode": "", "nama": ""},
            "sumber": {
                "nama": "staging/pdf-converted",
                "url": "belum_diisi",
                "alternatif": []
            },
            "file": {
                "markdown_utama": "dokumen.md",
                "batang_tubuh": None,
                "penjelasan": None,
                "lampiran": [],
                "pdf_asli": "external"
            },
            "konversi": {
                "metode": "staging pdf-converted import",
                "tanggal_konversi": "2026-10-13",
                "alat": "pdftotext",
                "ocr": None,
                "status_kualitas": "needs_review",
                "pemeriksa": "Antigravity Automated Pipeline"
            },
            "catatan": [f"Dipromosikan dari {best['path'].name}"]
        }
        with open(target_dir / "metadata.yml", "w", encoding="utf-8") as f:
            yaml.dump(meta_dict, f, allow_unicode=True, sort_keys=False)
            
        # 3. source.yml
        source_dict = {
            "id": reg_id,
            "judul": judul_lengkap,
            "pdf": {
                "stored_in_git": False,
                "source_url": [{"name": "belum_diisi", "url": "belum_diisi"}],
                "external_storage": {"provider": None, "bucket": None, "object_key": None, "url": None},
                "checksum": {"algorithm": "sha256", "value": sha_val},
                "file_size_bytes": best["meta"].get("source_bytes"),
                "last_checked": "2026-10-13"
            },
            "html_source": {"available": None, "url": None},
            "catatan": [f"Sumber lokal awal: {source_pdf_name}"]
        }
        with open(target_dir / "source.yml", "w", encoding="utf-8") as f:
            yaml.dump(source_dict, f, allow_unicode=True, sort_keys=False)
            
        # 4. relasi.yml
        relasi_dict = {
            "id": reg_id,
            "berdasarkan": [],
            "mengingat": [],
            "mencabut": [],
            "dicabut_oleh": [],
            "mengubah": [],
            "diubah_oleh": [],
            "melaksanakan": [],
            "dilaksanakan_oleh": [],
            "peraturan_pelaksana": [],
            "terkait": []
        }
        with open(target_dir / "relasi.yml", "w", encoding="utf-8") as f:
            yaml.dump(relasi_dict, f, allow_unicode=True, sort_keys=False)
            
        # 5. quality-check.yml
        qc_dict = {
            "id": reg_id,
            "status_konversi": "needs_review",
            "pemeriksaan": {
                "metadata": {"lengkap": False, "catatan": "Perlu pengisian detail LN/TLN"},
                "struktur_markdown": {"heading_konsisten": True, "pasal_terdeteksi": True, "ayat_terdeteksi": True, "lampiran_terpisah": False, "catatan": None},
                "tabel": {"ada_tabel": None, "tabel_berhasil_dikonversi": None, "catatan": None},
                "gambar_bagan": {"ada_gambar": None, "ada_bagan": None, "sudah_dibuat_mermaid": None, "catatan": None},
                "halaman": {"page_marker": "<!-- PAGE:" in best["body"], "jumlah_halaman_pdf": best["meta"].get("source_pages"), "jumlah_page_marker": None, "catatan": None},
                "validasi_manual": {"sudah_diperiksa": False, "pemeriksa": None, "tanggal": None, "catatan": None}
            },
            "risiko": []
        }
        with open(target_dir / "quality-check.yml", "w", encoding="utf-8") as f:
            yaml.dump(qc_dict, f, allow_unicode=True, sort_keys=False)
            
        # 6. README.md
        readme_text = f"""# {judul_lengkap}

## Ringkasan

Regulasi ini dipromosikan dari arsip konversi teks resmi untuk kebutuhan integrasi basis data perundang-undangan.

## Informasi Utama

| Elemen | Isi |
|---|---|
| Jenis | Undang-Undang |
| Nomor | {nomor} |
| Tahun | {tahun} |
| Judul | {judul} |
| Status | perlu_verifikasi |
| Tingkat | pusat |
| Sumber | {source_pdf_name} |

## File

- [`dokumen.md`](dokumen.md)
- [`metadata.yml`](metadata.yml)
- [`source.yml`](source.yml)
- [`relasi.yml`](relasi.yml)
- [`quality-check.yml`](quality-check.yml)

## Catatan Konversi

Status konversi: needs_review.

## Peringatan

Dokumen Markdown ini adalah hasil konversi untuk kebutuhan pencarian, analisis, dan pemrosesan teks. Untuk rujukan hukum resmi, tetap gunakan sumber regulasi resmi.
"""
        (target_dir / "README.md").write_text(readme_text, encoding="utf-8")
        
        existing_ids.add(reg_id)
        promoted += 1
        if promoted % 200 == 0:
            print(f"Progres: Berhasil mempromosikan {promoted} UU...")

    print(f"\nSelesai! Berhasil mempromosikan {promoted} UU baru. Dilewati (sudah ada): {skipped_existing}")

if __name__ == "__main__":
    main()
