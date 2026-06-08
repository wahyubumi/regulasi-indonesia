#!/usr/bin/env python3
"""Generate repository indexes from regulation metadata."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
REGULASI_DIR = ROOT / "regulasi"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data or {}


def compact_entry(entry: dict) -> dict:
    return {
        "id": entry["id"],
        "jenis": entry["jenis"],
        "nomor": entry["nomor"],
        "tahun": entry["tahun"],
        "judul": entry["judul"],
        "path": entry["path"],
    }


def grouped_index(grouped: dict[str, list[dict]]) -> list[dict]:
    return [
        {
            "id": key,
            "jumlah": len(items),
            "regulasi": sorted(items, key=lambda item: (item["tahun"] or 0, item["jenis"], item["nomor"], item["id"])),
        }
        for key, items in sorted(grouped.items(), key=lambda item: item[0])
    ]


def relation_target_id(value) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return value.get("id") or value.get("target") or value.get("regulasi") or ""
    return ""


def relation_title(value) -> str:
    return value.get("judul") if isinstance(value, dict) else ""


def main() -> int:
    entries = []
    pdf_entries = []
    checksum_entries = []
    relasi_paths = []

    for metadata_path in sorted(REGULASI_DIR.glob("**/metadata.yml")):
        folder = metadata_path.parent
        metadata = read_yaml(metadata_path)
        source_path = folder / "source.yml"
        relasi_path = folder / "relasi.yml"
        source = read_yaml(source_path) if source_path.exists() else {}
        status = metadata.get("status") or {}
        wilayah = metadata.get("wilayah") or {}
        sumber = metadata.get("sumber") or {}
        pdf = source.get("pdf") or {}
        source_urls = pdf.get("source_url") or []
        first_source_url = ""
        if source_urls and isinstance(source_urls[0], dict):
            first_source_url = source_urls[0].get("url") or ""
        elif isinstance(sumber, dict):
            first_source_url = sumber.get("url") or ""

        entry = {
            "id": metadata.get("id") or "",
            "jenis": metadata.get("jenis") or "",
            "nomor": metadata.get("nomor") or "",
            "tahun": metadata.get("tahun"),
            "judul": metadata.get("judul") or "",
            "status": status.get("status_teks") or "perlu_verifikasi",
            "tingkat": metadata.get("tingkat") or "",
            "lembaga": metadata.get("lembaga_penerbit") or [],
            "wilayah": {
                "level": wilayah.get("level") or "",
                "kode": wilayah.get("kode") or "",
                "nama": wilayah.get("nama") or "",
            },
            "path": rel(folder),
            "metadata": rel(metadata_path),
            "source": rel(source_path) if source_path.exists() else "",
            "subjek": metadata.get("subjek") or [],
            "sektor": metadata.get("sektor") or [],
        }
        entries.append(entry)
        if relasi_path.exists():
            relasi_paths.append((entry["id"], relasi_path))

        pdf_entries.append(
            {
                "id": entry["id"],
                "jenis": entry["jenis"],
                "tahun": entry["tahun"],
                "nomor": entry["nomor"],
                "judul": entry["judul"],
                "markdown_path": rel(folder / "dokumen.md"),
                "source_url": first_source_url,
                "storage_key": None,
                "sha256": ((pdf.get("checksum") or {}).get("value") if isinstance(pdf, dict) else None),
                "status_pdf": "external",
            }
        )
        checksum = (pdf.get("checksum") or {}) if isinstance(pdf, dict) else {}
        pdf_size = pdf.get("file_size_bytes") if isinstance(pdf, dict) else None
        checksum_entries.append(
            {
                "id": entry["id"],
                "algorithm": checksum.get("algorithm") or "sha256",
                "value": checksum.get("value"),
                "file_size_bytes": pdf_size,
                "checked_at": pdf.get("last_checked") if isinstance(pdf, dict) else None,
            }
        )

    indeks_dir = ROOT / "indeks"
    sources_dir = ROOT / "sources"
    with (indeks_dir / "index-regulasi.yml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(entries, handle, allow_unicode=True, sort_keys=False)

    csv_fields = [
        "id",
        "jenis",
        "nomor",
        "tahun",
        "judul",
        "status",
        "tingkat",
        "lembaga",
        "wilayah_kode",
        "wilayah_nama",
        "path",
        "metadata",
        "source",
        "subjek",
        "sektor",
    ]
    with (indeks_dir / "index-regulasi.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=csv_fields)
        writer.writeheader()
        for entry in entries:
            writer.writerow(
                {
                    "id": entry["id"],
                    "jenis": entry["jenis"],
                    "nomor": entry["nomor"],
                    "tahun": entry["tahun"] if entry["tahun"] is not None else "",
                    "judul": entry["judul"],
                    "status": entry["status"],
                    "tingkat": entry["tingkat"],
                    "lembaga": ";".join(entry["lembaga"]),
                    "wilayah_kode": entry["wilayah"]["kode"],
                    "wilayah_nama": entry["wilayah"]["nama"],
                    "path": entry["path"],
                    "metadata": entry["metadata"],
                    "source": entry["source"],
                    "subjek": ";".join(entry["subjek"]),
                    "sektor": ";".join(entry["sektor"]),
                }
            )

    with (sources_dir / "pdf-index.yml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(pdf_entries, handle, allow_unicode=True, sort_keys=False)
    with (sources_dir / "checksum-index.yml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(checksum_entries, handle, allow_unicode=True, sort_keys=False)

    by_year = defaultdict(list)
    by_lembaga = defaultdict(list)
    by_wilayah = defaultdict(list)
    by_subjek = defaultdict(list)

    for entry in entries:
        compact = compact_entry(entry)
        year_key = str(entry["tahun"]) if entry["tahun"] is not None else "belum_diisi"
        by_year[year_key].append(dict(compact))

        lembaga_list = entry["lembaga"] or ["belum_diisi"]
        for lembaga in lembaga_list:
            by_lembaga[lembaga or "belum_diisi"].append(dict(compact))

        wilayah = entry["wilayah"] or {}
        wilayah_key = wilayah.get("kode") or wilayah.get("nama") or "nasional"
        wilayah_label = wilayah.get("nama") or ("Nasional" if wilayah_key == "nasional" else "belum_diisi")
        by_wilayah[f"{wilayah_key}|{wilayah_label}"].append(dict(compact))

        labels = list(entry.get("subjek") or []) + list(entry.get("sektor") or [])
        if not labels:
            labels = ["belum_diisi"]
        for label in labels:
            by_subjek[label or "belum_diisi"].append(dict(compact))

    wilayah_index = []
    for key, items in sorted(by_wilayah.items(), key=lambda item: item[0]):
        kode, nama = key.split("|", 1)
        wilayah_index.append(
            {
                "kode": kode,
                "nama": nama,
                "jumlah": len(items),
                "regulasi": sorted(items, key=lambda item: (item["tahun"] or 0, item["jenis"], item["nomor"], item["id"])),
            }
        )

    with (indeks_dir / "index-tahun.yml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(grouped_index(by_year), handle, allow_unicode=True, sort_keys=False)
    with (indeks_dir / "index-lembaga.yml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(grouped_index(by_lembaga), handle, allow_unicode=True, sort_keys=False)
    with (indeks_dir / "index-wilayah.yml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(wilayah_index, handle, allow_unicode=True, sort_keys=False)
    with (indeks_dir / "index-subjek.yml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(grouped_index(by_subjek), handle, allow_unicode=True, sort_keys=False)

    nodes = [compact_entry(entry) for entry in sorted(entries, key=lambda item: item["id"])]
    edges = []
    relation_fields = [
        "berdasarkan",
        "mengingat",
        "mencabut",
        "dicabut_oleh",
        "mengubah",
        "diubah_oleh",
        "melaksanakan",
        "dilaksanakan_oleh",
        "peraturan_pelaksana",
        "terkait",
    ]
    for source_id, relasi_path in relasi_paths:
        relasi = read_yaml(relasi_path)
        for relation_type in relation_fields:
            values = relasi.get(relation_type) or []
            if not isinstance(values, list):
                continue
            for value in values:
                target_id = relation_target_id(value)
                if not target_id:
                    continue
                edge = {
                    "source": source_id,
                    "target": target_id,
                    "type": relation_type,
                }
                title = relation_title(value)
                if title:
                    edge["target_judul"] = title
                if isinstance(value, dict) and value.get("status_verifikasi"):
                    edge["status_verifikasi"] = value["status_verifikasi"]
                edges.append(edge)

    with (indeks_dir / "graph-relasi.yml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump({"nodes": nodes, "edges": edges}, handle, allow_unicode=True, sort_keys=False)

    print(f"Generated {len(entries)} regulation index entries.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
