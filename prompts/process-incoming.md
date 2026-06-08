# Process Incoming Regulation Markdown

Gunakan prompt ini untuk memproses file Markdown regulasi yang berada di `staging/incoming/` ke struktur final repository.

## Tujuan

Baca setiap file Markdown di `staging/incoming/`, identifikasi regulasinya, buat folder final sesuai standar `AGENTS.md`, isi file wajib, pindahkan teks lengkap ke `dokumen.md`, catat sumber dan kualitas, lalu perbarui indeks bila script tersedia.

## Instruksi Utama

1. Baca `AGENTS.md`, `metadata-schema.md`, `staging/README.md`, dan prompt terkait di `prompts/` sebelum memproses file.
2. Jangan menyimpan PDF, DOC, DOCX, XLS, XLSX, ZIP, RAR, 7Z, atau file biner besar di Git.
3. Proses hanya file teks/Markdown dari `staging/incoming/`; abaikan `.gitkeep`.
4. Jangan mengubah substansi hukum.
5. Jangan meringkas isi regulasi di `dokumen.md`.
6. Jangan mengarang tanggal, nomor lembaran negara, status berlaku, relasi, atau URL sumber.
7. Jika data tidak ditemukan atau meragukan, gunakan `null`, `belum_diisi`, atau `perlu_verifikasi`.
8. Jika isi Markdown tampak hasil OCR atau hasil ekstraksi yang rusak, tetap pertahankan teks yang ada dan catat risikonya di `quality-check.yml`.
9. Jika ada duplikat, jangan membuat folder final kedua; pindahkan atau catat file duplikat ke `staging/rejected/` dengan alasan.
10. Setelah file berhasil diproses ke struktur final, pindahkan file staging asal ke `staging/reviewed/` atau buat catatan bahwa file tersebut sudah diproses.

## Alur Kerja

1. Inventarisasi file:
   ```bash
   find staging/incoming -maxdepth 1 -type f -name '*.md' | sort
   ```

2. Untuk setiap file, baca isi lengkap atau bagian awal yang cukup untuk mengidentifikasi:
   - jenis regulasi,
   - nomor,
   - tahun,
   - judul resmi,
   - lembaga penerbit,
   - tingkat regulasi,
   - wilayah jika regulasi daerah,
   - sumber URL jika tercantum,
   - status atau relasi jika eksplisit di teks.

3. Tentukan penempatan folder:
   - UU, Perppu, PP, Perpres, Kepres, Inpres, dan Permen masuk `regulasi/pusat/`.
   - POJK dan SEOJK masuk `regulasi/lembaga/ojk/`.
   - PBI masuk `regulasi/lembaga/bi/`.
   - Peraturan BSSN masuk `regulasi/lembaga/bssn/`.
   - Perda, Pergub, Perbup, dan Perwali masuk `regulasi/daerah/` hanya jika wilayahnya dapat diidentifikasi.
   - Jika tingkat atau wilayah tidak dapat dipastikan, jangan menebak; catat sebagai perlu verifikasi dan proses hanya bila path masih dapat ditentukan secara aman.

4. Buat folder final dengan `scripts/create-regulation-folder.py` bila jenisnya didukung. Contoh:
   ```bash
   python3 scripts/create-regulation-folder.py \
     --tingkat pusat \
     --jenis pp \
     --tahun 2019 \
     --nomor 71 \
     --judul "Penyelenggaraan Sistem dan Transaksi Elektronik"
   ```

5. Jika `scripts/create-regulation-folder.py` belum mendukung jenis regulasi tertentu, tambahkan dukungan secara konservatif sesuai taxonomy, lalu uji script.

6. Isi `dokumen.md` dengan teks regulasi lengkap dari file staging:
   - pertahankan struktur resmi,
   - rapikan heading bila jelas,
   - gunakan `### Pasal N` untuk pasal,
   - gunakan `(1)`, `(2)`, dan seterusnya untuk ayat,
   - jangan menghapus bagian tanda tangan, penjelasan, atau lampiran jika ada,
   - jangan membuat ringkasan sebagai pengganti teks.

7. Isi `metadata.yml`:
   - `id` harus sesuai standar repository,
   - `jenis`, `nomor`, `tahun`, `judul`, `judul_lengkap`, `tingkat`, dan `lembaga_penerbit` diisi jika jelas,
   - `status.status_teks` tetap `perlu_verifikasi` kecuali status resmi terbukti dari teks atau sumber resmi,
   - data tanggal, lembaran negara, berita negara, dan relasi hanya diisi bila eksplisit.

8. Isi `source.yml`:
   - jika URL sumber ada di file staging, pindahkan ke `pdf.source_url` atau `html_source.url` sesuai konteks,
   - jika sumber tidak ada, gunakan `belum_diisi`,
   - `pdf.stored_in_git` harus tetap `false`,
   - checksum tetap `null` jika file PDF asli tidak tersedia.

9. Isi `relasi.yml` hanya dari teks eksplisit:
   - `mengingat`,
   - `mencabut`,
   - `mengubah`,
   - `melaksanakan`,
   - atau relasi lain yang jelas.
   Jika belum diverifikasi, gunakan `status_verifikasi: perlu_verifikasi` pada entri relasi yang membutuhkan catatan.

10. Isi `quality-check.yml`:
    - tandai `metadata.lengkap` sesuai kondisi,
    - tandai deteksi pasal/ayat,
    - catat risiko OCR, potongan teks, duplikasi, tabel rusak, lampiran belum dipisah, atau sumber belum jelas,
    - gunakan `status_konversi: needs_review` bila hasil masih perlu pemeriksaan manual.

11. Isi `README.md` regulasi:
    - buat ringkasan singkat hanya jika isi regulasi cukup jelas,
    - jika belum yakin, tulis `Ringkasan belum diisi`,
    - pastikan peringatan rujukan hukum resmi tetap ada.

12. Perbarui indeks:
    - jalankan `python3 scripts/generate-index.py` jika tersedia,
    - jika belum tersedia, perbarui manual secara minimal:
      - `indeks/index-regulasi.yml`,
      - `indeks/index-regulasi.csv`,
      - `sources/pdf-index.yml`,
      - `sources/checksum-index.yml`.

13. Jalankan validasi bila script tersedia:
    ```bash
    python3 scripts/validate-metadata.py
    python3 scripts/check-links.py
    ```
    Jika script belum tersedia, lakukan pemeriksaan manual:
    - semua YAML valid,
    - semua folder punya `README.md`, `metadata.yml`, `source.yml`, `dokumen.md`, `relasi.yml`, dan `quality-check.yml`,
    - tidak ada PDF atau file biner besar,
    - ID konsisten dengan folder.

14. Laporkan hasil dengan ringkas:
    - jumlah file diproses,
    - daftar regulasi yang berhasil dibuat,
    - daftar file duplikat atau ditolak,
    - data yang masih `perlu_verifikasi`,
    - validasi yang berhasil atau gagal.

## Aturan Duplikat

Anggap file sebagai kandidat duplikat jika memiliki kombinasi sama:

- jenis,
- nomor,
- tahun,
- lembaga atau tingkat,
- dan judul yang sama atau sangat mirip.

Jika ada dua file seperti `PP_71_2019_...md` dan `PP_71_2019_...2.md`:

1. Bandingkan panjang dan kelengkapan isi.
2. Pilih versi paling lengkap sebagai sumber utama.
3. Simpan informasi duplikat di `quality-check.yml`.
4. Pindahkan versi yang tidak dipakai ke `staging/rejected/` atau biarkan dengan catatan bila pemindahan belum diminta.

## Penamaan Jenis Umum

Gunakan pemetaan berikut bila jelas dari file:

| Teks/File | Jenis | Tingkat | Lokasi |
|---|---|---|---|
| `UU` | `uu` | `pusat` | `regulasi/pusat/uu/` |
| `PP` | `pp` | `pusat` | `regulasi/pusat/pp/` |
| `Perpres` | `perpres` | `pusat` | `regulasi/pusat/perpres/` |
| `Permen` | `permen` | `pusat` | `regulasi/pusat/permen/` |
| `POJK` | `pojk` | `lembaga` | `regulasi/lembaga/ojk/` |
| `SEOJK` | `seojk` | `lembaga` | `regulasi/lembaga/ojk/` |
| `PBI` | `pbi` | `lembaga` | `regulasi/lembaga/bi/` |
| `Perda Provinsi` | `perda-prov` | `daerah` | `regulasi/daerah/provinsi/` |
| `Pergub` | `pergub` | `daerah` | `regulasi/daerah/provinsi/` |
| `Perbup` | `perbup` | `daerah` | `regulasi/daerah/kabupaten/` |
| `Perwali` | `perwali` | `daerah` | `regulasi/daerah/kota/` |

Jika mapping belum tersedia di taxonomy atau script, update taxonomy/script terlebih dahulu secara terukur.

## Batasan

- Jangan mencari sumber internet kecuali diminta secara eksplisit atau data sumber di file staging tidak cukup untuk diproses secara aman.
- Jangan membuat PDF.
- Jangan menghapus file staging tanpa alasan yang dicatat.
- Jangan melakukan commit kecuali diminta.
