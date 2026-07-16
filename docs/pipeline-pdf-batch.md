# Pipeline PDF regulasi lokal

Pipeline ini memproses PDF secara bertahap dan tidak mengubah atau menghapus PDF sumber.

## Inventarisasi

```bash
python3 scripts/inventory-pdf.py
```

Perintah tersebut menghasilkan `pdf-local/manifests/pdf-manifest.ndjson` (diabaikan Git). Setiap baris berisi path asal, ukuran, jumlah halaman, SHA-256, serta kandidat nomor/tahun/judul/tanggal.

## Konversi staging

```bash
python3 scripts/convert-pdf-local.py
```

Hasilnya berada di `staging/pdf-converted/` (diabaikan Git). Nama staging diawali potongan SHA-256 agar unik, kemudian nama sumber dan kandidat nama regulasi. Setiap Markdown memiliki YAML frontmatter, hash PDF asal, dan `<!-- PAGE: n -->`.

## Review dan promosi

Buat antrean review identitas:

```bash
python3 scripts/review-pdf-identities.py
```

Antrean berada di `pdf-local/manifests/identity-review.csv`. Kolom `approved` harus diubah menjadi `true` secara manual setelah nomor, judul, dan tanggal diverifikasi terhadap PDF/sumber resmi.

Promosi kandidat ber-skor tinggi ke penyimpanan lokal (salinan, bukan pemindahan):

```bash
python3 scripts/promote-reviewed-pdf.py --auto-candidates
```

Promosi manual penuh dapat dilakukan dengan mengisi `approved: true`, lalu menjalankan script tanpa `--auto-candidates`.

Setelah hash salinan diverifikasi, sumber asal dapat dibersihkan:

```bash
python3 scripts/cleanup-promoted-pdf.py       # dry-run
python3 scripts/cleanup-promoted-pdf.py --delete
```

Script hanya menghapus PDF yang masih ada di `downloads`, memiliki salinan target, dan hash sumber = hash target = hash manifest.

Jangan mempromosikan file hanya berdasarkan kandidat otomatis. Verifikasi identitas dari halaman PDF, terutama tanggal diundangkan, nomor, judul, dan kualitas OCR. Setelah lolos review, gunakan nama kanonik:

```text
YYYYMMDD__{id}__{slug-judul}.pdf
```

Tanggal yang dipakai adalah tanggal publikasi/diundangkan resmi. Jika tahun regulasi diketahui tetapi hari/bulan belum terbukti, gunakan prefix `YYYY0000`, misalnya `20240000__uu-2024-001__judul.pdf`. Gunakan `undated__` hanya jika tahun regulasi juga belum diketahui.

Untuk PDF scan dengan OCR buruk, lakukan OCR ulang ke berkas temporer dengan `ocrmypdf --force-ocr`; jangan menimpa PDF asli. Simpan hash PDF asli dan hasil OCR secara terpisah, lalu validasi nomor, judul, tanggal, dan pasal sebelum hasil OCR dipromosikan.

## Audit hash

SHA-256 pada manifest adalah hash byte PDF yang sedang diproses. Setelah PDF dipindahkan ke object storage, simpan kembali hash yang sama bersama URL/key penyimpanan dan ukuran byte di frontmatter atau `sumber.yml`. Perubahan hash berarti salinan baru dan tidak boleh menimpa salinan lama.
