#!/usr/bin/env python3
"""Create a regulation folder with repository-standard template files."""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path


JENIS_LENGKAP = {
    "uud": "Undang-Undang Dasar",
    "tap-mpr": "Ketetapan MPR",
    "uu": "Undang-Undang",
    "perppu": "Peraturan Pemerintah Pengganti Undang-Undang",
    "pp": "Peraturan Pemerintah",
    "perpres": "Peraturan Presiden",
    "kepres": "Keputusan Presiden",
    "inpres": "Instruksi Presiden",
    "permen": "Peraturan Menteri",
    "permenpanrb": "Peraturan Menteri Pendayagunaan Aparatur Negara dan Reformasi Birokrasi",
    "kepmenpanrb": "Keputusan Menteri Pendayagunaan Aparatur Negara dan Reformasi Birokrasi",
    "semenpanrb": "Surat Edaran Menteri Pendayagunaan Aparatur Negara dan Reformasi Birokrasi",
    "permenkominfo": "Peraturan Menteri Komunikasi dan Informatika",
    "semenkominfo": "Surat Edaran Menteri Komunikasi dan Informatika",
    "pojk": "Peraturan Otoritas Jasa Keuangan",
    "seojk": "Surat Edaran Otoritas Jasa Keuangan",
    "kepojk": "Keputusan Anggota Dewan Komisioner Otoritas Jasa Keuangan",
    "pbi": "Peraturan Bank Indonesia",
    "perbssn": "Peraturan Badan Siber dan Sandi Negara",
    "perlkpp": "Peraturan LKPP",
    "perda-prov": "Peraturan Daerah Provinsi",
    "pergub": "Peraturan Gubernur",
    "perda-kab": "Peraturan Daerah Kabupaten",
    "perbup": "Peraturan Bupati",
    "perda-kota": "Peraturan Daerah Kota",
    "perwali": "Peraturan Wali Kota",
    "perlur": "Peraturan Lurah",
}

HIERARKI_LEVEL = {
    "uud": 1,
    "tap-mpr": 2,
    "uu": 3,
    "perppu": 3,
    "pp": 4,
    "perpres": 5,
    "kepres": 5,
    "inpres": 5,
    "permen": 6,
}


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    lowered = ascii_value.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return re.sub(r"-{2,}", "-", slug) or "judul"


def nomor_3_digit(nomor: str) -> str:
    match = re.search(r"\d+", nomor)
    if not match:
        raise ValueError("nomor harus memuat angka untuk dibuat menjadi 3 digit")
    return f"{int(match.group(0)):03d}"


def quote_yaml(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def build_identity(args: argparse.Namespace) -> tuple[str, Path, str]:
    nomor_slug = nomor_3_digit(args.nomor)
    judul_slug = slugify(args.judul)
    jenis = args.jenis.lower()

    if args.tingkat == "pusat":
        folder_name = f"{jenis}-{args.tahun}-{nomor_slug}-{judul_slug}"
        regulation_id = f"{jenis}-{args.tahun}-{nomor_slug}"
        path = Path("regulasi") / "pusat" / jenis / str(args.tahun) / folder_name
        return regulation_id, path, folder_name

    if args.tingkat == "lembaga":
        if not args.lembaga:
            raise ValueError("--lembaga wajib untuk --tingkat lembaga")
        lembaga = args.lembaga.lower()
        folder_name = f"{jenis}-{args.tahun}-{nomor_slug}-{judul_slug}"
        regulation_id = f"{jenis}-{args.tahun}-{nomor_slug}"
        path = Path("regulasi") / "lembaga" / lembaga / str(args.tahun) / folder_name
        return regulation_id, path, folder_name

    if args.tingkat == "daerah":
        required = {
            "--level-daerah": args.level_daerah,
            "--kode-wilayah": args.kode_wilayah,
            "--nama-daerah": args.nama_daerah,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ValueError(f"{', '.join(missing)} wajib untuk --tingkat daerah")
        level = args.level_daerah.lower()
        kode = args.kode_wilayah.lower()
        nama_slug = slugify(args.nama_daerah)
        daerah_folder = f"{kode}-{nama_slug}"
        folder_name = f"{jenis}-{nama_slug}-{args.tahun}-{nomor_slug}-{judul_slug}"
        regulation_id = f"{jenis}-{kode}-{args.tahun}-{nomor_slug}"
        path = (
            Path("regulasi")
            / "daerah"
            / level
            / daerah_folder
            / jenis
            / str(args.tahun)
            / folder_name
        )
        return regulation_id, path, folder_name

    raise ValueError(f"tingkat tidak dikenal: {args.tingkat}")


def full_title(args: argparse.Namespace) -> str:
    jenis_lengkap = JENIS_LENGKAP.get(args.jenis.lower(), args.jenis)
    return f"{jenis_lengkap} Nomor {args.nomor} Tahun {args.tahun} tentang {args.judul}"


def render_files(args: argparse.Namespace, regulation_id: str) -> dict[str, str]:
    jenis = args.jenis.lower()
    jenis_lengkap = JENIS_LENGKAP.get(jenis, "belum_diisi")
    title = full_title(args)
    title_yaml = quote_yaml(title)
    judul_yaml = quote_yaml(args.judul)
    nomor_yaml = quote_yaml(args.nomor)
    jenis_lengkap_yaml = quote_yaml(jenis_lengkap)
    tingkat_yaml = quote_yaml(args.tingkat)
    status = "perlu_verifikasi"
    hierarki = HIERARKI_LEVEL.get(jenis)
    hierarki_text = "null" if hierarki is None else str(hierarki)
    wilayah_level = args.level_daerah or ""
    wilayah_kode = args.kode_wilayah or ""
    wilayah_nama = args.nama_daerah or ""

    return {
        "README.md": f"""# {title}

## Ringkasan

Ringkasan belum diisi. Ringkasan tidak boleh menggantikan teks resmi regulasi.

## Informasi Utama

| Elemen | Isi |
|---|---|
| Jenis | {jenis_lengkap} |
| Nomor | {args.nomor} |
| Tahun | {args.tahun} |
| Judul | {args.judul} |
| Status | {status} |
| Tingkat | {args.tingkat} |
| Sumber | belum_diisi |

## File

- [`dokumen.md`](dokumen.md)
- [`metadata.yml`](metadata.yml)
- [`source.yml`](source.yml)
- [`relasi.yml`](relasi.yml)
- [`quality-check.yml`](quality-check.yml)

## Catatan Konversi

Status konversi: draft.

## Peringatan

Dokumen Markdown ini adalah hasil konversi untuk kebutuhan pencarian, analisis, dan pemrosesan teks. Untuk rujukan hukum resmi, tetap gunakan sumber regulasi resmi.
""",
        "metadata.yml": f"""id: "{regulation_id}"
jenis: "{jenis}"
jenis_lengkap: {jenis_lengkap_yaml}
nomor: {nomor_yaml}
nomor_lengkap: {nomor_yaml}
tahun: {args.tahun}
judul: {judul_yaml}
judul_lengkap: {title_yaml}

tingkat: {tingkat_yaml}
hierarki_level: {hierarki_text}

lembaga_penerbit: []
pejabat_penetap: []

tanggal_ditetapkan: null
tanggal_diundangkan: null
tanggal_berlaku: null
tempat_ditetapkan: null

lembaran_negara:
  nomor: null
  tahun: null

tambahan_lembaran_negara:
  nomor: null

berita_negara:
  nomor: null
  tahun: null

tambahan_berita_negara:
  nomor: null

status:
  berlaku: null
  status_teks: "perlu_verifikasi"
  mulai_berlaku: null
  berakhir: null
  dicabut_oleh: []
  mencabut: []
  mengubah: []
  diubah_oleh: []

subjek: []
sektor: []
kata_kunci: []

wilayah:
  level: "{wilayah_level}"
  kode: "{wilayah_kode}"
  nama: "{wilayah_nama}"

sumber:
  nama: "belum_diisi"
  url: "belum_diisi"
  alternatif: []

file:
  markdown_utama: "dokumen.md"
  batang_tubuh: null
  penjelasan: null
  lampiran: []
  pdf_asli: "external"

konversi:
  metode: "belum_diisi"
  tanggal_konversi: null
  alat: "AI-assisted conversion"
  ocr: null
  status_kualitas: "draft"
  pemeriksa: null

catatan: []
""",
        "source.yml": f"""id: "{regulation_id}"
judul: {title_yaml}

pdf:
  stored_in_git: false

  source_url:
    - name: "belum_diisi"
      url: "belum_diisi"

  external_storage:
    provider: null
    bucket: null
    object_key: null
    url: null

  checksum:
    algorithm: "sha256"
    value: null

  file_size_bytes: null
  last_checked: null

html_source:
  available: null
  url: null

catatan: []
""",
        "dokumen.md": f"""---
id: "{regulation_id}"
jenis: "{jenis}"
nomor: {nomor_yaml}
tahun: {args.tahun}
judul: {title_yaml}
status: "perlu_verifikasi"
sumber: "belum_diisi"
---

# {title}

<!-- PAGE: 1 -->

## Catatan Konversi

Dokumen ini merupakan hasil konversi ke Markdown. Untuk rujukan hukum resmi, gunakan dokumen resmi dari sumber regulasi terkait.

---

## Teks Regulasi

Teks regulasi lengkap belum diisi.
""",
        "relasi.yml": f"""id: "{regulation_id}"

berdasarkan: []
mengingat: []

mencabut: []
dicabut_oleh: []

mengubah: []
diubah_oleh: []

melaksanakan: []
dilaksanakan_oleh: []

peraturan_pelaksana: []

terkait: []
""",
        "quality-check.yml": f"""id: "{regulation_id}"
status_konversi: "draft"

pemeriksaan:
  metadata:
    lengkap: false
    catatan: null

  struktur_markdown:
    heading_konsisten: false
    pasal_terdeteksi: false
    ayat_terdeteksi: false
    lampiran_terpisah: false
    catatan: null

  tabel:
    ada_tabel: null
    tabel_berhasil_dikonversi: null
    catatan: null

  gambar_bagan:
    ada_gambar: null
    ada_bagan: null
    sudah_dibuat_mermaid: null
    catatan: null

  halaman:
    page_marker: false
    jumlah_halaman_pdf: null
    jumlah_page_marker: null
    catatan: null

  validasi_manual:
    sudah_diperiksa: false
    pemeriksa: null
    tanggal: null
    catatan: null

risiko: []
""",
    }


def write_regulation(path: Path, files: dict[str, str], overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(f"folder sudah ada: {path}")
    path.mkdir(parents=True, exist_ok=True)
    for filename, content in files.items():
        target = path / filename
        if target.exists() and not overwrite:
            raise FileExistsError(f"file sudah ada: {target}")
        target.write_text(content, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Buat folder regulasi sesuai standar AGENTS.md."
    )
    parser.add_argument("--tingkat", choices=["pusat", "lembaga", "daerah"], required=True)
    parser.add_argument("--jenis", required=True, help="Jenis regulasi, contoh: uu, pp, perpres, pojk, perbup.")
    parser.add_argument("--tahun", type=int, required=True)
    parser.add_argument("--nomor", required=True, help="Nomor asli regulasi.")
    parser.add_argument("--judul", required=True, help="Judul setelah kata 'tentang'.")
    parser.add_argument("--lembaga", help="Kode lembaga untuk tingkat lembaga, contoh: ojk, bi, bssn.")
    parser.add_argument("--level-daerah", choices=["provinsi", "kabupaten", "kota"], help="Level daerah.")
    parser.add_argument("--kode-wilayah", help="Kode wilayah daerah.")
    parser.add_argument("--nama-daerah", help="Nama daerah tanpa kode wilayah.")
    parser.add_argument("--overwrite", action="store_true", help="Timpa file jika sudah ada.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        regulation_id, path, _folder_name = build_identity(args)
        files = render_files(args, regulation_id)
        write_regulation(path, files, args.overwrite)
    except (ValueError, FileExistsError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
