# Staging

Folder ini digunakan untuk menampung file Markdown regulasi hasil perolehan dari internet sebelum dipindahkan ke struktur final `regulasi/`.

## Struktur

- `incoming/` untuk file Markdown mentah yang baru dikumpulkan.
- `reviewed/` untuk file Markdown yang sudah diperiksa dan siap dikonversi ke folder regulasi final. Folder ini diabaikan Git.
- `rejected/` untuk file yang tidak digunakan, duplikat, atau tidak dapat diverifikasi. Folder ini diabaikan Git.

## Aturan

- Simpan hanya file teks seperti `.md`, `.txt`, `.yml`, `.yaml`, `.csv`, atau `.mmd`.
- Jangan simpan PDF, DOC, DOCX, XLS, XLSX, ZIP, RAR, 7Z, atau file biner besar di folder ini.
- Catat URL sumber resmi di dalam file Markdown atau metadata sementara jika tersedia.
- Jangan menganggap file di staging sebagai teks regulasi final sebelum diverifikasi.
- Setelah valid, pindahkan ke folder final menggunakan `scripts/create-regulation-folder.py`.

## Contoh Nama File

```text
incoming/perpres-2019-039-satu-data-indonesia.md
incoming/uu-2022-027-pelindungan-data-pribadi.md
```
