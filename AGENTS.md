# AGENTS.md

Repository ini adalah basis data regulasi Indonesia dalam format Markdown.

Dokumen ini menjadi instruksi kerja utama bagi AI coding agent, Codex CLI, dan kontributor manusia ketika membuat, mengubah, mengonversi, memvalidasi, dan mengindeks regulasi dalam repository ini.

---

## 1. Tujuan Repository

Repository ini bertujuan untuk:

1. Menyimpan hasil konversi regulasi Indonesia ke format Markdown.
2. Menyediakan metadata terstruktur untuk setiap regulasi.
3. Menyediakan indeks regulasi untuk pencarian, analisis, dan integrasi AI/RAG.
4. Menyediakan relasi antar regulasi seperti mencabut, mengubah, diubah oleh, dicabut oleh, dan peraturan pelaksana.
5. Menjadi knowledge base hukum/regulasi yang ringan, mudah di-clone, mudah diaudit, dan mudah diproses mesin.

Repository ini **tidak menyimpan PDF asli di Git** karena file PDF dapat membuat repository terlalu besar.

---

## 2. Prinsip Utama

1. Jangan mengubah substansi hukum.
2. Jangan meringkas isi regulasi di file utama `dokumen.md`.
3. Ringkasan hanya boleh dibuat di `README.md`.
4. Pertahankan struktur resmi regulasi:
   - Judul
   - Konsiderans
   - Diktum
   - BAB
   - Bagian
   - Paragraf
   - Pasal
   - Ayat
   - Huruf
   - Angka
   - Penjelasan
   - Lampiran
5. Simpan Markdown, YAML, CSV, Mermaid, dan file teks pendukung di Git.
6. Jangan menyimpan PDF, DOC, DOCX, XLS, XLSX, ZIP, RAR, 7Z, atau file biner besar di Git.
7. PDF asli hanya direferensikan melalui `source.yml`.
8. Jika sumber PDF tersedia, catat URL sumber resmi dan checksum bila memungkinkan.
9. Gunakan metadata yang konsisten untuk semua regulasi.
10. Gunakan penanda halaman PDF jika tersedia.
11. Semua hasil konversi harus dapat diaudit kembali ke sumber aslinya.
12. Jika ada keraguan terhadap hasil OCR atau konversi, tandai di `quality-check.yml`.
13. Jangan mengarang tanggal, nomor lembaran negara, status berlaku, atau relasi regulasi.
14. Jika data belum diketahui, gunakan nilai `null`, `belum_diisi`, atau `perlu_verifikasi`.

---

## 3. Struktur Repository

Gunakan struktur dasar berikut:

```text
regulasi-indonesia/
├── README.md
├── LICENSE
├── AGENTS.md
├── metadata-schema.md
├── .gitignore
├── indeks/
│   ├── index-regulasi.yml
│   ├── index-regulasi.csv
│   ├── index-subjek.yml
│   ├── index-tahun.yml
│   ├── index-lembaga.yml
│   ├── index-wilayah.yml
│   └── graph-relasi.yml
├── sources/
│   ├── pdf-index.yml
│   ├── source-mirror.yml
│   └── checksum-index.yml
├── taxonomy/
│   ├── jenis-regulasi.yml
│   ├── sektor.yml
│   ├── lembaga.yml
│   ├── wilayah.yml
│   └── status-regulasi.yml
├── regulasi/
│   ├── pusat/
│   │   ├── uud/
│   │   ├── tap-mpr/
│   │   ├── uu/
│   │   ├── perppu/
│   │   ├── pp/
│   │   ├── perpres/
│   │   ├── kepres/
│   │   ├── inpres/
│   │   └── permen/
│   ├── lembaga/
│   │   ├── ojk/
│   │   ├── bi/
│   │   ├── bssn/
│   │   ├── lkpp/
│   │   ├── bps/
│   │   └── kemendagri/
│   └── daerah/
│       ├── provinsi/
│       ├── kabupaten/
│       └── kota/
├── scripts/
│   ├── create-regulation-folder.py
│   ├── generate-index.py
│   ├── validate-metadata.py
│   ├── verify-checksum.py
│   └── check-links.py
├── prompts/
│   ├── convert-regulation-to-markdown.md
│   ├── extract-metadata.md
│   ├── detect-relations.md
│   └── quality-check.md
└── docs/
    ├── panduan-konversi.md
    ├── standar-markdown.md
    ├── standar-metadata.md
    └── standar-penamaan-file.md
```

---

## 4. Struktur Folder Setiap Regulasi

Setiap regulasi harus berada dalam satu folder mandiri.

Struktur minimal:

```text
[jenis]-[tahun]-[nomor]-[slug-judul]/
├── README.md
├── metadata.yml
├── source.yml
├── dokumen.md
├── relasi.yml
└── quality-check.yml
```

Struktur lengkap untuk regulasi yang memiliki penjelasan, lampiran, tabel, atau bagan:

```text
[jenis]-[tahun]-[nomor]-[slug-judul]/
├── README.md
├── metadata.yml
├── source.yml
├── dokumen.md
├── batang-tubuh.md
├── penjelasan.md
├── lampiran/
│   ├── lampiran-1.md
│   ├── lampiran-2.md
│   └── lampiran-3.md
├── assets/
│   ├── tables/
│   │   ├── tabel-001.csv
│   │   └── tabel-002.csv
│   ├── diagrams/
│   │   ├── bagan-001.mmd
│   │   └── bagan-001.md
│   └── images/
│       └── gambar-001.png
├── relasi.yml
└── quality-check.yml
```

Catatan:

- `dokumen.md` berisi teks regulasi lengkap.
- `batang-tubuh.md` digunakan jika regulasi perlu dipisahkan dari penjelasan dan lampiran.
- `penjelasan.md` digunakan jika regulasi memiliki penjelasan resmi.
- `lampiran/` digunakan untuk lampiran yang panjang.
- `assets/` hanya untuk file turunan kecil seperti CSV, Mermaid, atau gambar hasil ekstraksi yang benar-benar diperlukan.
- PDF asli tetap tidak disimpan di Git.

---

## 5. Pola Penempatan Folder

### 5.1 Regulasi Pusat

Format:

```text
regulasi/pusat/[jenis]/[tahun]/[jenis]-[tahun]-[nomor-3-digit]-[slug-judul]/
```

Contoh:

```text
regulasi/pusat/uu/2022/uu-2022-027-pelindungan-data-pribadi/
regulasi/pusat/pp/2019/pp-2019-071-penyelenggaraan-sistem-dan-transaksi-elektronik/
regulasi/pusat/perpres/2019/perpres-2019-039-satu-data-indonesia/
```

### 5.2 Regulasi Lembaga

Format:

```text
regulasi/lembaga/[lembaga]/[tahun]/[jenis]-[tahun]-[nomor-3-digit]-[slug-judul]/
```

Contoh:

```text
regulasi/lembaga/bssn/2021/perbssn-2021-004-manajemen-keamanan-informasi-spbe/
regulasi/lembaga/ojk/2020/pojk-2020-045-konglomerasi-keuangan/
```

### 5.3 Regulasi Daerah Provinsi

Format:

```text
regulasi/daerah/provinsi/[kode-wilayah]-[nama-provinsi]/[jenis]/[tahun]/[jenis]-[nama-daerah]-[tahun]-[nomor-3-digit]-[slug-judul]/
```

Contoh:

```text
regulasi/daerah/provinsi/91-papua/perda/2025/perda-prov-papua-2025-001-rpjmd/
regulasi/daerah/provinsi/34-diy/pergub/2024/pergub-diy-2024-012-judul/
```

### 5.4 Regulasi Daerah Kabupaten/Kota

Format:

```text
regulasi/daerah/kabupaten/[kode-wilayah]-[nama-kabupaten]/[jenis]/[tahun]/[jenis]-[nama-daerah]-[tahun]-[nomor-3-digit]-[slug-judul]/
regulasi/daerah/kota/[kode-wilayah]-[nama-kota]/[jenis]/[tahun]/[jenis]-[nama-daerah]-[tahun]-[nomor-3-digit]-[slug-judul]/
```

Contoh:

```text
regulasi/daerah/kabupaten/9109-mimika/perbup/2026/perbup-mimika-2026-001-judul/
regulasi/daerah/kota/9171-jayapura/perwali/2026/perwali-jayapura-2026-001-judul/
```

---

## 6. Pola Penamaan

Gunakan huruf kecil, angka, dan tanda hubung.

Format dasar:

```text
[jenis]-[tahun]-[nomor-3-digit]-[slug-judul]
```

Contoh:

```text
uu-2022-027-pelindungan-data-pribadi
pp-2019-071-penyelenggaraan-sistem-dan-transaksi-elektronik
perpres-2019-039-satu-data-indonesia
permenpanrb-2020-059-pemantauan-dan-evaluasi-spbe
perbssn-2021-004-manajemen-keamanan-informasi-spbe
```

Aturan slug:

1. Gunakan huruf kecil.
2. Ganti spasi dengan tanda hubung.
3. Hapus tanda baca yang tidak perlu.
4. Gunakan nomor 3 digit untuk menjaga urutan.
5. Jika nomor regulasi memiliki bentuk khusus seperti `8/POJK.03/2024`, buat slug aman seperti:
   ```text
   pojk-2024-008-judul-regulasi
   ```
   Lalu simpan nomor asli lengkap di `metadata.yml`.

---

## 7. File `metadata.yml`

Setiap regulasi wajib memiliki `metadata.yml`.

Template:

```yaml
id: ""
jenis: ""
jenis_lengkap: ""
nomor: ""
nomor_lengkap: ""
tahun: null
judul: ""
judul_lengkap: ""

tingkat: ""
hierarki_level: null

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
  level: ""
  kode: ""
  nama: ""

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
```

Aturan pengisian:

- Jangan mengisi nilai yang belum pasti.
- Gunakan `null` untuk data tanggal/angka yang belum diketahui.
- Gunakan `[]` untuk daftar kosong.
- `id` harus konsisten dengan nama folder.
- `judul_lengkap` harus mengikuti nama resmi regulasi.
- `status.status_teks` gunakan salah satu dari taxonomy status jika sudah tersedia.

---

## 8. File `source.yml`

Karena PDF tidak disimpan dalam Git, setiap regulasi wajib memiliki `source.yml`.

Template:

```yaml
id: ""
judul: ""

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
```

Aturan:

1. Jangan menyimpan PDF di Git.
2. Jika PDF diunduh dari JDIH, BPK, peraturan.go.id, atau sumber resmi lain, catat URL-nya.
3. Jika PDF disimpan di object storage, catat `provider`, `bucket`, `object_key`, dan `url` bila ada.
4. Jika checksum belum dihitung, isi `value: null`.
5. Jangan mengarang link sumber.

---

## 9. File `relasi.yml`

Setiap regulasi wajib memiliki `relasi.yml`.

Template:

```yaml
id: ""

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
```

Contoh entri relasi:

```yaml
terkait:
  - id: "pp-2019-071"
    judul: "Peraturan Pemerintah Nomor 71 Tahun 2019 tentang Penyelenggaraan Sistem dan Transaksi Elektronik"
    hubungan: "Berkaitan dengan penyelenggaraan sistem elektronik"
    status_verifikasi: "perlu_verifikasi"
```

Aturan:

1. Relasi harus berbasis teks regulasi atau sumber resmi.
2. Jangan menebak relasi jika tidak ada dasar.
3. Jika relasi belum diverifikasi, gunakan `status_verifikasi: perlu_verifikasi`.
4. ID regulasi dalam relasi harus mengikuti standar repository.

---

## 10. File `quality-check.yml`

Setiap regulasi wajib memiliki `quality-check.yml`.

Template:

```yaml
id: ""
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
```

Status konversi yang disarankan:

```text
draft
partial
needs_review
verified
deprecated
```

---

## 11. File `README.md` Setiap Regulasi

Setiap folder regulasi wajib memiliki `README.md`.

Template:

```markdown
# [Judul Lengkap Regulasi]

## Ringkasan

Tuliskan ringkasan singkat regulasi ini. Ringkasan tidak boleh menggantikan teks resmi regulasi.

## Informasi Utama

| Elemen | Isi |
|---|---|
| Jenis | |
| Nomor | |
| Tahun | |
| Judul | |
| Status | perlu_verifikasi |
| Tingkat | |
| Sumber | |

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
```

---

## 12. File `dokumen.md`

`dokumen.md` adalah file utama yang berisi teks regulasi lengkap.

Template:

```markdown
---
id: ""
jenis: ""
nomor: ""
tahun:
judul: ""
status: "perlu_verifikasi"
sumber: "belum_diisi"
---

# [Judul Lengkap Regulasi]

<!-- PAGE: 1 -->

## Catatan Konversi

Dokumen ini merupakan hasil konversi ke Markdown. Untuk rujukan hukum resmi, gunakan dokumen resmi dari sumber regulasi terkait.

---

## Teks Regulasi

[Tempelkan hasil konversi regulasi lengkap di sini.]
```

Aturan heading:

```markdown
# Judul Regulasi

## Konsiderans

### Menimbang

### Mengingat

## Diktum

## BAB I
## KETENTUAN UMUM

### Pasal 1

(1) Isi ayat.

(2) Isi ayat.
```

Aturan struktur:

1. `#` untuk judul utama.
2. `##` untuk bagian besar seperti Konsiderans, Diktum, BAB, Penjelasan, Lampiran.
3. `###` untuk Pasal.
4. Ayat ditulis dengan format `(1)`, `(2)`, `(3)`.
5. Huruf ditulis dengan format `a.`, `b.`, `c.`.
6. Angka ditulis dengan format `1.`, `2.`, `3.`.
7. Jangan mengubah isi norma hukum.
8. Jangan memperbaiki bahasa resmi regulasi kecuali jelas merupakan kesalahan OCR, dan tandai dalam catatan jika perlu.

---

## 13. Penanda Halaman

Jika hasil konversi berasal dari PDF, gunakan penanda halaman:

```markdown
<!-- PAGE: 1 -->
```

Aturan:

1. Penanda halaman diletakkan sedekat mungkin dengan awal teks halaman.
2. Nomor halaman harus mengikuti urutan PDF.
3. Jika halaman tidak dapat dipastikan, jangan mengarang nomor.
4. Catat kondisi di `quality-check.yml`.

---

## 14. Tabel

Untuk tabel kecil, gunakan Markdown table:

```markdown
| No | Uraian | Keterangan |
|---:|---|---|
| 1 | ... | ... |
| 2 | ... | ... |
```

Untuk tabel besar, simpan sebagai CSV:

```text
assets/tables/tabel-001.csv
```

Lalu tulis di Markdown:

```markdown
**Tabel 1. [Judul Tabel]**

Lihat file: [`assets/tables/tabel-001.csv`](assets/tables/tabel-001.csv)
```

Aturan:

1. Jangan memaksakan tabel besar menjadi Markdown jika merusak struktur.
2. Jika tabel hasil OCR meragukan, tandai di `quality-check.yml`.
3. Jika tabel penting terhadap substansi hukum, utamakan validasi manual.

---

## 15. Bagan, Diagram, dan Flowchart

Jika PDF memiliki bagan atau flowchart:

1. Simpan representasi Mermaid bila memungkinkan:
   ```text
   assets/diagrams/bagan-001.mmd
   ```
2. Buat penjelasan teks:
   ```text
   assets/diagrams/bagan-001.md
   ```
3. Di `dokumen.md`, beri rujukan:
   ```markdown
   **Bagan 1. [Judul Bagan]**

   Lihat representasi Mermaid: [`assets/diagrams/bagan-001.mmd`](assets/diagrams/bagan-001.mmd)
   ```

Aturan:

1. Mermaid harus mencerminkan isi bagan asli.
2. Jika tidak yakin, buat deskripsi teks, bukan diagram yang mengarang.
3. Catat status konversi bagan di `quality-check.yml`.

---

## 16. Indeks Repository

Setiap regulasi baru harus masuk ke:

```text
indeks/index-regulasi.yml
indeks/index-regulasi.csv
sources/pdf-index.yml
sources/checksum-index.yml
```

### 16.1 `indeks/index-regulasi.yml`

Format:

```yaml
- id: ""
  jenis: ""
  nomor: ""
  tahun: null
  judul: ""
  status: "perlu_verifikasi"
  tingkat: ""
  lembaga: []
  wilayah:
    level: ""
    kode: ""
    nama: ""
  path: ""
  metadata: ""
  source: ""
  subjek: []
  sektor: []
```

### 16.2 `indeks/index-regulasi.csv`

Kolom wajib:

```csv
id,jenis,nomor,tahun,judul,status,tingkat,lembaga,wilayah_kode,wilayah_nama,path,metadata,source,subjek,sektor
```

### 16.3 `sources/pdf-index.yml`

Format:

```yaml
- id: ""
  jenis: ""
  tahun: null
  nomor: ""
  judul: ""
  markdown_path: ""
  source_url: ""
  storage_key: null
  sha256: null
  status_pdf: "external"
```

### 16.4 `sources/checksum-index.yml`

Format:

```yaml
- id: ""
  algorithm: "sha256"
  value: null
  file_size_bytes: null
  checked_at: null
```

---

## 17. Taxonomy

Gunakan taxonomy untuk menjaga konsistensi istilah.

### 17.1 Jenis Regulasi

Contoh `taxonomy/jenis-regulasi.yml`:

```yaml
pusat:
  uud:
    nama: "Undang-Undang Dasar"
    level: 1
  tap_mpr:
    nama: "Ketetapan MPR"
    level: 2
  uu:
    nama: "Undang-Undang"
    level: 3
  perppu:
    nama: "Peraturan Pemerintah Pengganti Undang-Undang"
    level: 3
  pp:
    nama: "Peraturan Pemerintah"
    level: 4
  perpres:
    nama: "Peraturan Presiden"
    level: 5
  permen:
    nama: "Peraturan Menteri"
    level: 6

lembaga:
  pojk:
    nama: "Peraturan Otoritas Jasa Keuangan"
  pbi:
    nama: "Peraturan Bank Indonesia"
  perbssn:
    nama: "Peraturan Badan Siber dan Sandi Negara"
  perlkpp:
    nama: "Peraturan LKPP"

daerah:
  perda_prov:
    nama: "Peraturan Daerah Provinsi"
  pergub:
    nama: "Peraturan Gubernur"
  perda_kab:
    nama: "Peraturan Daerah Kabupaten"
  perbup:
    nama: "Peraturan Bupati"
  perda_kota:
    nama: "Peraturan Daerah Kota"
  perwali:
    nama: "Peraturan Wali Kota"
```

### 17.2 Status Regulasi

Contoh `taxonomy/status-regulasi.yml`:

```yaml
- id: berlaku
  nama: "Berlaku"

- id: tidak_berlaku
  nama: "Tidak Berlaku"

- id: dicabut
  nama: "Dicabut"

- id: diubah
  nama: "Diubah"

- id: mencabut
  nama: "Mencabut"

- id: perlu_verifikasi
  nama: "Perlu Verifikasi"
```

---

## 18. Larangan File dalam Git

File berikut tidak boleh di-commit:

```text
*.pdf
*.doc
*.docx
*.xls
*.xlsx
*.ppt
*.pptx
*.zip
*.rar
*.7z
*.tar
*.gz
*.tmp
*.log
storage/
downloads/
cache/
tmp/
```

`.gitignore` wajib mencakup pola di atas.

Jika ada kebutuhan menyimpan file biner kecil, pastikan alasan dicatat dan file tersebut memang diperlukan untuk memahami hasil konversi.

---

## 19. Script yang Disarankan

Repository sebaiknya memiliki script berikut:

### 19.1 `scripts/create-regulation-folder.py`

Fungsi:

- Membuat folder regulasi baru.
- Membuat `README.md`.
- Membuat `metadata.yml`.
- Membuat `source.yml`.
- Membuat `dokumen.md`.
- Membuat `relasi.yml`.
- Membuat `quality-check.yml`.

Contoh penggunaan:

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

### 19.2 `scripts/generate-index.py`

Fungsi:

- Membaca semua `metadata.yml`.
- Membuat ulang `indeks/index-regulasi.yml`.
- Membuat ulang `indeks/index-regulasi.csv`.

### 19.3 `scripts/validate-metadata.py`

Fungsi:

- Memastikan semua regulasi memiliki file wajib.
- Memastikan YAML valid.
- Memastikan ID konsisten dengan folder.
- Memastikan field wajib tersedia.

### 19.4 `scripts/verify-checksum.py`

Fungsi:

- Mengecek checksum PDF eksternal jika file tersedia lokal.
- Memperbarui `sources/checksum-index.yml`.

### 19.6 `scripts/batch-convert-local.py`

Fungsi:

- Mengonversi semua file PDF di `pdf-local/downloads/` ke Markdown di `staging/incoming/`.
- Memiliki fitur OCR otomatis via `ocrmypdf` untuk PDF hasil scan.
- Memiliki fitur pencegahan duplikat berlapis (melewati konversi jika regulasi sudah ada di `regulasi/` atau staging).
- Memindahkan PDF yang selesai diproses ke `pdf-local/processed/` sehingga folder `pdf-local/downloads/` tetap bersih.

---

## 20. Workflow Standar Pemrosesan PDF Regulasi Baru (Default Workflow)

Gunakan alur terotomatisasi standar berikut untuk memproses file PDF baru:

1. Tempatkan semua file PDF regulasi baru di `pdf-local/downloads/`.

2. Jalankan konversi batch lokal dan deduplikasi:
   ```bash
   python3 scripts/batch-convert-local.py
   ```

3. Jalankan impor ke struktur folder `regulasi/`:
   ```bash
   python3 scripts/process-incoming.py
   ```

4. Jalankan validasi struktur dan metadata:
   ```bash
   python3 scripts/validate-metadata.py
   ```

5. Generate ulang indeks repositori global:
   ```bash
   python3 scripts/generate-index.py
   ```

6. Pastikan file PDF tidak ikut masuk Git dan folder `pdf-local/downloads/` sudah bersih:
   ```bash
   git status
   ```

---

## 21. Workflow Konversi Manual (Alternatif)

Jika regulasi ditambahkan secara manual tanpa batch script:

1. Identifikasi sumber resmi PDF.
2. Jangan simpan PDF di Git.
3. Jika PDF diperlukan sementara, letakkan di folder lokal yang diabaikan Git, misalnya:
   ```text
   downloads/
   tmp/
   ```
4. Ekstrak teks.
5. Pertahankan struktur asli.
6. Tambahkan penanda halaman jika tersedia.
7. Perbaiki kesalahan OCR yang jelas, tetapi jangan mengubah substansi.
8. Tandai bagian yang meragukan.
9. Konversi tabel secara hati-hati.
10. Untuk tabel besar, gunakan CSV.
11. Untuk bagan, buat Mermaid atau deskripsi teks jika memungkinkan.
12. Isi `quality-check.yml`.

---

## 22. Standar Markdown

Gunakan gaya berikut:

```markdown
# Judul Regulasi

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

Dalam Peraturan ini yang dimaksud dengan:

1. ...
2. ...

### Pasal 2

(1) ...

(2) ...
```

Aturan:

1. Jangan mencampur nomor pasal dengan heading yang tidak konsisten.
2. Jangan mengubah kapitalisasi resmi jika merupakan bagian dari teks hukum.
3. Jangan menghapus frasa hukum seperti "Dengan Rahmat Tuhan Yang Maha Esa".
4. Jangan menghapus tanda tangan, tempat penetapan, dan tanggal jika tersedia.
5. Jangan menghapus bagian "Agar setiap orang mengetahuinya...".
6. Jangan menghapus penjelasan resmi.
7. Jangan menghapus lampiran.

---

## 23. Standar YAML

Aturan YAML:

1. Gunakan spasi, bukan tab.
2. Gunakan `null` untuk nilai kosong yang belum diketahui.
3. Gunakan `[]` untuk list kosong.
4. Gunakan tanda kutip untuk string yang mengandung tanda titik dua.
5. Jaga agar semua YAML valid.
6. Jangan menggunakan komentar berlebihan di YAML produksi.

---

## 24. Standar ID

ID regulasi harus stabil.

Format umum:

```text
[jenis]-[tahun]-[nomor-3-digit]
```

Contoh:

```text
uu-2022-027
pp-2019-071
perpres-2019-039
perbssn-2021-004
```

Untuk regulasi daerah:

```text
[jenis]-[kode-wilayah]-[tahun]-[nomor-3-digit]
```

Contoh:

```text
perda-prov-91-2025-001
perbup-9109-2026-001
perwali-9171-2026-001
```

Aturan:

1. ID tidak boleh berubah setelah dibuat.
2. ID digunakan di metadata, relasi, indeks, dan sitasi internal.
3. Jika ada duplikasi, tambahkan pembeda berbasis jenis atau wilayah.

---

## 25. Standar Sumber Resmi

Utamakan sumber resmi seperti:

1. JDIH lembaga penerbit.
2. JDIH BPK.
3. peraturan.go.id.
4. Situs resmi kementerian/lembaga.
5. Situs resmi pemerintah daerah.
6. Lembaran Negara/Berita Negara jika tersedia.

Aturan:

1. Jangan menggunakan blog atau situs tidak resmi sebagai sumber utama jika sumber resmi tersedia.
2. Jika hanya ada sumber tidak resmi, tandai `perlu_verifikasi`.
3. Catat semua sumber alternatif di `metadata.yml` dan `source.yml`.

---

## 26. Quality Gate Sebelum Commit

Sebelum commit, pastikan:

1. Tidak ada PDF atau file biner besar yang masuk Git.
2. Semua regulasi memiliki file wajib.
3. YAML valid.
4. Markdown bisa dibaca.
5. ID konsisten.
6. Folder mengikuti standar.
7. `source.yml` tersedia.
8. `quality-check.yml` mencatat risiko.
9. Indeks diperbarui.
10. Tidak ada substansi hukum yang diringkas di `dokumen.md`.

Checklist:

```bash
git status
python3 scripts/validate-metadata.py
python3 scripts/generate-index.py
python3 scripts/check-links.py
```

---

## 27. Instruksi untuk AI Agent

Jika AI agent bekerja di repository ini:

1. Baca `AGENTS.md` sebelum mengubah file.
2. Ikuti struktur folder dan metadata.
3. Jangan membuat PDF.
4. Jangan memasukkan PDF ke Git.
5. Jangan mengarang isi regulasi.
6. Jangan mengarang metadata.
7. Jangan membuat ringkasan sebagai pengganti teks regulasi.
8. Jika diminta membuat template, gunakan nilai placeholder yang jelas.
9. Jika diminta mengonversi dokumen, pertahankan isi lengkap.
10. Jika menemukan data yang belum pasti, tulis `perlu_verifikasi`.
11. Setelah membuat regulasi baru, update indeks.
12. Setelah mengubah metadata, jalankan validasi jika script tersedia.
13. Jika menemukan inkonsistensi, laporkan dalam catatan atau `quality-check.yml`.

---

## 28. Contoh Perintah untuk Codex CLI

Inisialisasi repository:

```bash
codex "
Berdasarkan AGENTS.md, buat struktur awal repository regulasi Indonesia Markdown.
Buat folder regulasi, indeks, sources, taxonomy, scripts, prompts, dan docs.
Buat template file awal yang valid.
Jangan membuat atau menyimpan PDF.
"
```

Membuat regulasi baru:

```bash
codex "
Gunakan standar AGENTS.md untuk membuat folder regulasi:
Peraturan Presiden Nomor 39 Tahun 2019 tentang Satu Data Indonesia.
Jangan isi dokumen.md dengan substansi jika sumber belum tersedia.
Buat metadata.yml, source.yml, relasi.yml, quality-check.yml, dan README.md.
"
```

Mengonversi hasil Markdown:

```bash
codex "
Rapikan dokumen.md regulasi ini sesuai standar AGENTS.md.
Pertahankan seluruh substansi hukum.
Jangan meringkas.
Perbaiki struktur heading, Pasal, ayat, huruf, dan angka.
Tambahkan catatan quality-check jika ada bagian yang meragukan.
"
```

Generate indeks:

```bash
codex "
Baca semua metadata.yml di folder regulasi.
Perbarui indeks/index-regulasi.yml dan indeks/index-regulasi.csv.
Pastikan semua path valid dan semua YAML tetap valid.
"
```

---

## 29. Catatan Lisensi

Repository ini berisi hasil konversi teks regulasi. Pastikan kebijakan lisensi repository dijelaskan di `LICENSE` dan `README.md`.

Jika ragu, gunakan lisensi yang memisahkan:

1. Kode/script repository.
2. Metadata dan struktur data.
3. Teks regulasi hasil konversi.

Teks regulasi resmi sebaiknya tetap merujuk pada sumber resmi masing-masing.

---

## 30. Peringatan

Markdown dalam repository ini ditujukan untuk:

- pencarian,
- pembelajaran,
- analisis,
- integrasi AI,
- penyusunan compliance matrix,
- penyusunan SOP,
- dan kebutuhan knowledge base.

Untuk rujukan hukum resmi, pengguna tetap harus merujuk pada dokumen resmi dari sumber penerbit regulasi.
