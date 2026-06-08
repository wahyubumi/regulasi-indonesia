# Metadata Schema

Setiap regulasi wajib memiliki `metadata.yml` dengan struktur berikut.

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

Aturan utama:

- Jangan mengisi data yang belum pasti.
- Gunakan `null` untuk tanggal dan angka yang belum diketahui.
- Gunakan `[]` untuk daftar kosong.
- `id` harus konsisten dengan nama folder dan indeks.
