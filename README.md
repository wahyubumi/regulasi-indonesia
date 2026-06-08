# Regulasi Indonesia

Repository ini menyimpan hasil konversi regulasi Indonesia dalam format Markdown beserta metadata, sumber, relasi, indeks, taxonomy, dan catatan kualitas.

## Prinsip

- Teks regulasi utama disimpan lengkap di `dokumen.md` dan tidak diringkas.
- Ringkasan hanya ditempatkan di `README.md` setiap regulasi.
- PDF asli tidak disimpan di Git; sumber resmi dicatat di `source.yml`.
- Metadata yang belum pasti menggunakan `null`, `belum_diisi`, atau `perlu_verifikasi`.

## Struktur Utama

- `regulasi/` berisi folder regulasi mandiri.
- `staging/` berisi Markdown regulasi mentah sebelum diverifikasi dan dipindahkan ke struktur final.
- `pdf-local/` adalah folder lokal di root untuk merapikan PDF regulasi; folder ini diabaikan Git.
- `indeks/` berisi indeks regulasi untuk pencarian dan integrasi.
- `sources/` berisi indeks sumber PDF eksternal dan checksum.
- `taxonomy/` berisi taxonomy jenis, sektor, lembaga, wilayah, dan status.
- `scripts/` berisi alat bantu pembuatan dan validasi.
- `prompts/` berisi prompt kerja konversi dan ekstraksi.
- `docs/` berisi standar dan panduan kontribusi.

## Membuat Folder Regulasi

```bash
python3 scripts/create-regulation-folder.py \
  --tingkat pusat \
  --jenis perpres \
  --tahun 2019 \
  --nomor 39 \
  --judul "Satu Data Indonesia"
```

Output:

```text
regulasi/pusat/perpres/2019/perpres-2019-039-satu-data-indonesia/
```

## Peringatan

Markdown dalam repository ini ditujukan untuk pencarian, pembelajaran, analisis, dan integrasi AI. Untuk rujukan hukum resmi, gunakan dokumen resmi dari sumber penerbit regulasi.
