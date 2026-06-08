# Penyimpanan PDF Lokal

PDF regulasi tidak disimpan di Git. Untuk merapikan PDF di komputer lokal, gunakan folder root:

```text
pdf-local/
├── incoming/
├── by-regulation/
└── by-source/
```

Aturan:

- `pdf-local/` diabaikan oleh `.gitignore`.
- Simpan PDF mentah yang baru diperoleh di `pdf-local/incoming/`.
- Setelah cocok dengan regulasi final, pindahkan manual ke `pdf-local/by-regulation/[id-regulasi]/`.
- Sumber resmi tetap dicatat di `source.yml`.
- Checksum dapat dicatat di `source.yml` dan `sources/checksum-index.yml` bila sudah dihitung.
