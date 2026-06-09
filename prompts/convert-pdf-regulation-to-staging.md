# Convert PDF Regulation to Staging Markdown

Gunakan prompt ini untuk mengonversi PDF regulasi Indonesia menjadi satu file Markdown mentah yang siap ditempatkan di `staging/incoming/`.

Output prompt ini **belum** menjadi dokumen final repository. File hasil konversi masih harus diproses dengan `prompts/process-incoming.md` agar masuk ke struktur final `regulasi/`.

## Tujuan

Konversi seluruh isi PDF regulasi ke Markdown secara lengkap, dapat diaudit ke halaman PDF, dan aman untuk diproses mesin tanpa mengubah substansi hukum.

## Output

Keluarkan **hanya Markdown mentah**. Jangan menambahkan pembuka seperti "berikut hasilnya" atau penutup apa pun.

Mulai langsung dengan penanda halaman pertama:

```markdown
<!-- PAGE: 1 -->
```

## Aturan Utama

1. Jangan meringkas, memendekkan, menafsirkan, atau menyusun ulang substansi hukum.
2. Pertahankan seluruh bagian yang ada:
   - judul,
   - konsiderans,
   - diktum,
   - BAB,
   - bagian,
   - paragraf,
   - pasal,
   - ayat,
   - huruf,
   - angka,
   - penjelasan,
   - lampiran,
   - tabel,
   - tanda tangan,
   - tempat dan tanggal penetapan/pengundangan.
3. Jangan mengarang teks yang tidak terbaca.
4. Jika teks tidak terbaca, tulis `[tidak terbaca]`.
5. Jika hasil OCR meragukan, pertahankan teks terbaik yang terbaca dan beri catatan singkat dalam Markdown:
   ```markdown
   <!-- OCR-UNCERTAIN: bagian ini perlu verifikasi manual -->
   ```
6. Jangan membuat metadata lengkap, relasi, status berlaku, checksum, atau sumber URL jika tidak tampak eksplisit di PDF.
7. Jangan membuat wiki-link atau ID regulasi secara otomatis.
8. Jangan menyimpan atau menyarankan penyimpanan PDF di Git.

## Penanda Halaman

Gunakan penanda halaman untuk setiap halaman PDF.

Format wajib:

```markdown
<!-- PAGE: X -->
```

Aturan:

- Letakkan penanda sedekat mungkin dengan awal teks halaman.
- Nomor `X` mengikuti nomor halaman PDF, bukan nomor halaman cetak di dokumen.
- Tetap beri penanda untuk halaman kosong, sampul, lampiran, dan halaman tanda tangan.
- Jika halaman kosong atau hanya gambar tanpa teks, tulis:
  ```markdown
  <!-- PAGE: X -->

  [halaman kosong atau gambar tanpa teks terbaca]
  ```

## Struktur Markdown

Gunakan struktur berikut untuk regulasi berbahasa Indonesia:

```markdown
# [JUDUL LENGKAP REGULASI]

## Konsiderans

### Menimbang

a. bahwa ...

### Mengingat

1. ...

## Diktum

MEMUTUSKAN:

Menetapkan: ...

## BAB I
## KETENTUAN UMUM

### Pasal 1

(1) ...

(2) ...
```

Aturan heading:

- `#` untuk judul utama regulasi.
- `##` untuk bagian besar seperti `Konsiderans`, `Diktum`, `BAB`, `Penjelasan`, dan `Lampiran`.
- `###` untuk `Pasal`.
- Jangan gunakan `#### Pasal`.
- Jangan mengubah kapitalisasi resmi jika merupakan bagian dari teks hukum.
- Jangan menghapus frasa seperti `DENGAN RAHMAT TUHAN YANG MAHA ESA`.

## Ayat, Huruf, dan Angka

Gunakan format:

```markdown
(1) Isi ayat.

(2) Isi ayat.

a. isi huruf;

b. isi huruf;

1. isi angka;

2. isi angka.
```

Aturan:

- Jangan mengubah nomor pasal, ayat, huruf, atau angka menjadi bullet `-` atau `*`.
- Jangan memperbaiki redaksi hukum kecuali jelas merupakan kesalahan OCR.
- Jika memperbaiki OCR yang jelas, jangan ubah substansi.

## Tabel

Untuk tabel kecil dan sedang, gunakan Markdown table:

```markdown
| No | Uraian | Keterangan |
|---:|---|---|
| 1 | ... | ... |
| 2 | ... | ... |
```

Aturan:

- Pertahankan urutan kolom dan baris.
- Pertahankan angka, satuan, mata uang, tanda baca, dan catatan kaki.
- Jangan ubah tabel menjadi paragraf atau bullet.
- Jika tabel terlalu besar, rumit, memiliki banyak sel gabung, atau hasil OCR tidak dapat dipercaya, jangan memaksakan tabel Markdown. Gunakan placeholder:
  ```markdown
  **Tabel [nomor/judul jika ada]**

  [tabel besar/kompleks perlu ekstraksi manual ke CSV dari halaman PDF X-Y]
  ```
- Jika tabel terpotong halaman, letakkan `<!-- PAGE: X -->` di posisi page break sedekat mungkin tanpa menghilangkan baris.

## Lampiran

Untuk lampiran:

```markdown
## Lampiran

### Lampiran I

[isi lampiran]
```

Aturan:

- Lampiran teks harus ditranskrip lengkap.
- Lampiran tabel mengikuti aturan tabel.
- Lampiran gambar, peta, bagan, atau formulir yang tidak dapat dibaca penuh diberi placeholder:
  ```markdown
  [gambar/bagan/formulir pada halaman PDF X perlu ekstraksi manual]
  ```
- Jangan menggambar ulang diagram jika tidak yakin.

## Metadata Ringkas Opsional

Jika informasi identitas regulasi jelas dari PDF, boleh tambahkan frontmatter ringkas di awal file **setelah penanda halaman pertama tidak diperlukan** hanya jika sistem konversi mendukungnya.

Namun default yang disarankan untuk staging adalah **tanpa frontmatter**, karena metadata final akan diekstrak saat `process-incoming`.

Jika tetap memakai frontmatter, gunakan hanya field aman:

```yaml
---
jenis: "belum_diisi"
nomor: "belum_diisi"
tahun: null
judul: "belum_diisi"
sumber: "pdf"
status: "perlu_verifikasi"
---
```

Jangan isi field yang belum pasti.

## Nama File Staging

Jika perlu menyarankan nama file, taruh sebagai komentar paling akhir:

```markdown
<!-- suggested-staging-filename: tahun-jenis-nomor-judul.md -->
```

Aturan:

- Gunakan huruf kecil, angka, dan tanda hubung.
- Format utama:
  ```text
  tahun-jenis-nomor-judul.md
  ```
- Gunakan nomor asli secukupnya agar tidak ambigu.
- Jika nomor regulasi sederhana, boleh gunakan nomor tanpa padding untuk nama staging, misalnya `2022-uu-27-pelindungan-data-pribadi.md`.
- Jika nomor memiliki format khusus, ubah menjadi slug aman:
  - `1/POJK.05/2017` menjadi `2017-pojk-1-pojk-05-2017-perizinan-usaha.md`
  - `23/SEOJK.05/2023` menjadi `2023-seojk-23-seojk-05-2023-penilaian-kemampuan.md`
- Jika ada beberapa versi dari sumber berbeda, tambahkan suffix sumber atau tanggal unduh:
  ```text
  2019-pp-71-penyelenggaraan-sistem-transaksi-elektronik-jdih-bpk.md
  2019-pp-71-penyelenggaraan-sistem-transaksi-elektronik-peraturan-go-id.md
  2019-pp-71-penyelenggaraan-sistem-transaksi-elektronik-2026-06-09.md
  ```
- Jika nama file sudah ada di `staging/incoming/`, jangan menimpa. Tambahkan suffix:
  ```text
  -v2
  -source-2
  -ocr-2
  ```
- Jangan gunakan komentar ini sebagai bagian substansi regulasi.
- Komentar ini boleh dihapus saat masuk `dokumen.md` final.

Contoh:

```markdown
<!-- suggested-staging-filename: 2019-perpres-39-satu-data-indonesia.md -->
<!-- suggested-staging-filename: 2021-perbssn-4-manajemen-keamanan-informasi-spbe.md -->
<!-- suggested-staging-filename: 2024-pojk-11-pelaporan-permintaan-informasi-debitur-slik.md -->
```

## Larangan

- Jangan meringkas.
- Jangan menghapus daftar isi kecuali diminta eksplisit; jika daftar isi tidak dikonversi, beri catatan.
- Jangan mengarang sumber URL.
- Jangan mengarang status berlaku.
- Jangan mengarang relasi mencabut/mengubah/dicabut oleh.
- Jangan membuat analisis hukum.
- Jangan menambahkan komentar di luar Markdown hasil konversi.
- Jangan menyimpan PDF di Git.
