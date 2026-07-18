import os
import subprocess
import re
from pathlib import Path
import pypdf

# Konfigurasi Path
ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "pdf-local" / "downloads"
OCR_STAGING = ROOT / "pdf-local" / "ocr-staging"
STAGING_DIR = ROOT / "staging" / "incoming"

def is_scanned_pdf(pdf_path: Path) -> bool:
    try:
        reader = pypdf.PdfReader(pdf_path)
        total_text_len = 0
        for page in reader.pages[:3]: # Cek 3 halaman pertama
            text = page.extract_text() or ""
            total_text_len += len(text.strip())
        return total_text_len < 50
    except Exception as e:
        print(f"Peringatan saat memeriksa PDF: {e}")
        return True # Default ke scanned jika gagal membaca

def run_ocr(input_path: Path, output_path: Path) -> bool:
    print(f"Menjalankan OCR menggunakan ocrmypdf pada: {input_path.name}...")
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
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print("OCR selesai dengan sukses.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Gagal menjalankan OCR: {e.stderr}")
        return False

def convert_pdf_to_text(pdf_path: Path) -> list[str]:
    print(f"Mengekstrak teks menggunakan pdftotext dari: {pdf_path.name}...")
    try:
        result = subprocess.run(
            ["pdftotext", "-layout", "-enc", "UTF-8", str(pdf_path), "-"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", check=True
        )
        # Pisahkan berdasarkan Form Feed (\f)
        pages = re.split(r"\f", result.stdout)
        return [page.rstrip() for page in pages if page.strip()]
    except Exception as e:
        print(f"❌ Gagal mengekstrak teks: {e}")
        return []

def main():
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    
    target_files = [
        ("Perpres Nomor 16 Tahun 2018.pdf", {"bentuk_singkat": "perpres", "nomor": "16", "tahun": 2018, "tentang": "Pengadaan Barang/Jasa Pemerintah"}),
        ("Perpres Nomor 12 Tahun 2021.pdf", {"bentuk_singkat": "perpres", "nomor": "12", "tahun": 2021, "tentang": "Perubahan atas Peraturan Presiden Nomor 16 Tahun 2018 tentang Pengadaan Barang/Jasa Pemerintah"}),
        ("Peraturan Presiden Nomor 46 Tahun 2025.pdf", {"bentuk_singkat": "perpres", "nomor": "46", "tahun": 2025, "tentang": "Perubahan Kedua atas Peraturan Presiden Nomor 16 Tahun 2018 tentang Pengadaan Barang/Jasa Pemerintah"}),
        ("Nomor_21_Tahun_2022.pdf", {"bentuk_singkat": "uu", "nomor": "21", "tahun": 2022, "tentang": "Provinsi Nusa Tenggara Timur"})
    ]

    for filename, meta in target_files:
        pdf_path = PDF_DIR / filename
        if not pdf_path.exists():
            print(f"❌ File tidak ditemukan: {pdf_path}")
            continue
            
        print(f"\n--- Memproses {filename} ---")
        
        # Tentukan apakah file memerlukan OCR
        scanned = is_scanned_pdf(pdf_path)
        active_pdf_path = pdf_path
        
        if scanned:
            ocr_pdf_path = OCR_STAGING / f"{pdf_path.stem}.ocr.pdf"
            if not ocr_pdf_path.exists():
                success = run_ocr(pdf_path, ocr_pdf_path)
                if not success:
                    print(f"❌ Gagal memproses OCR untuk {filename}. Dilewati.")
                    continue
            else:
                print(f"Menggunakan file OCR yang sudah ada: {ocr_pdf_path.name}")
            active_pdf_path = ocr_pdf_path
        
        # Ekstrak teks
        pages = convert_pdf_to_text(active_pdf_path)
        if not pages:
            print(f"❌ Tidak ada teks yang diekstrak untuk {filename}.")
            continue
            
        # Tulis ke staging/incoming
        output_filename = pdf_path.stem + ".md"
        output_path = STAGING_DIR / output_filename
        
        # Buat isi file markdown
        markdown_lines = []
        markdown_lines.append("---")
        # Catatan: frontmatter forms
        # process-incoming.py menggunakan bentuk_singkat/bentuk, nomor, tahun, tentang
        if meta["bentuk_singkat"] == "uu":
            markdown_lines.append(f"bentuk_singkat: {meta['bentuk_singkat']}")
            markdown_lines.append(f"nomor: {meta['nomor']}")
            markdown_lines.append(f"tahun: {meta['tahun']}")
            markdown_lines.append(f"tentang: {meta['tentang']}")
        markdown_lines.append("---")
        markdown_lines.append("")
        
        # Tambahkan teks tiap halaman dengan page markers
        for i, page_text in enumerate(pages, 1):
            markdown_lines.append(f"<!-- page: {i} -->")
            markdown_lines.append("")
            markdown_lines.append(page_text)
            markdown_lines.append("")
            
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(markdown_lines))
            
        print(f"✅ Berhasil menyimpan Markdown ke: {output_path.relative_to(ROOT)}")

if __name__ == "__main__":
    main()
