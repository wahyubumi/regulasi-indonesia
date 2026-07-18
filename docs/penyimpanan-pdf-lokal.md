# Penyimpanan PDF Lokal

PDF regulasi tidak disimpan di Git. Untuk merapikan PDF di komputer lokal, gunakan folder root:

```text
pdf-local/
├── downloads/
├── processed/
├── ocr-staging/
└── by-regulation/
```

Aturan:

- `pdf-local/` diabaikan oleh `.gitignore`.
- Simpan PDF mentah yang baru diperoleh di `pdf-local/downloads/`.
- Gunakan `python3 scripts/batch-convert-local.py` untuk mengonversi PDF di `pdf-local/downloads/` secara terotomatisasi dengan fitur pencegahan duplikat.
- Setelah dikonversi dan diimpor ke `regulasi/`, PDF otomatis dipindahkan dari `pdf-local/downloads/` ke `pdf-local/processed/` atau `pdf-local/by-regulation/[id-regulasi]/`.
- Sumber resmi tetap dicatat di `source.yml`.
- Checksum dapat dicatat di `source.yml` dan `sources/checksum-index.yml` bila sudah dihitung.
