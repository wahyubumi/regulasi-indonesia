#!/usr/bin/env python3
"""Validate required regulation files and YAML syntax."""

from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "README.md",
    "metadata.yml",
    "source.yml",
    "dokumen.md",
    "relasi.yml",
    "quality-check.yml",
}


def main() -> int:
    errors: list[str] = []
    for metadata_path in sorted((ROOT / "regulasi").glob("**/metadata.yml")):
        folder = metadata_path.parent
        missing = sorted(name for name in REQUIRED if not (folder / name).exists())
        for name in missing:
            errors.append(f"{folder.relative_to(ROOT)} missing {name}")
        try:
            metadata = yaml.safe_load(metadata_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            errors.append(f"{metadata_path.relative_to(ROOT)} invalid YAML: {exc}")
            continue
        if not metadata.get("id"):
            errors.append(f"{metadata_path.relative_to(ROOT)} missing id")
        for yaml_path in folder.glob("*.yml"):
            try:
                yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
            except yaml.YAMLError as exc:
                errors.append(f"{yaml_path.relative_to(ROOT)} invalid YAML: {exc}")

    if errors:
        for error in errors:
            print(f"error: {error}")
        return 1

    print("metadata ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
