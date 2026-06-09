#!/usr/bin/env python3
"""Process staging/incoming Markdown files into regulation folders."""

from __future__ import annotations

import re
import shutil
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
INCOMING = ROOT / "staging" / "incoming"
REVIEWED = ROOT / "staging" / "reviewed"
REJECTED = ROOT / "staging" / "rejected"
REGULASI = ROOT / "regulasi"


JENIS_LENGKAP = {
    "uud": "Undang-Undang Dasar",
    "uu": "Undang-Undang",
    "pp": "Peraturan Pemerintah",
    "perpres": "Peraturan Presiden",
    "permen": "Peraturan Menteri",
    "permenpanrb": "Peraturan Menteri Pendayagunaan Aparatur Negara dan Reformasi Birokrasi",
    "kepmenpanrb": "Keputusan Menteri Pendayagunaan Aparatur Negara dan Reformasi Birokrasi",
    "semenpanrb": "Surat Edaran Menteri Pendayagunaan Aparatur Negara dan Reformasi Birokrasi",
    "permenkominfo": "Peraturan Menteri Komunikasi dan Informatika",
    "semenkominfo": "Surat Edaran Menteri Komunikasi dan Informatika",
    "pojk": "Peraturan Otoritas Jasa Keuangan",
    "seojk": "Surat Edaran Otoritas Jasa Keuangan",
    "kepojk": "Keputusan Anggota Dewan Komisioner Otoritas Jasa Keuangan",
    "perbssn": "Peraturan Badan Siber dan Sandi Negara",
    "perda-prov": "Peraturan Daerah Provinsi",
    "pergub": "Peraturan Gubernur",
    "perlur": "Peraturan Lurah",
}


@dataclass
class RegulationInfo:
    source_path: Path
    jenis: str
    tingkat: str
    nomor: str
    nomor_key: str
    tahun: int
    judul: str
    judul_lengkap: str
    lembaga: list[str]
    wilayah_level: str = ""
    wilayah_kode: str = ""
    wilayah_nama: str = ""

    @property
    def key(self) -> tuple[str, str, int, str, str]:
        return (self.jenis, self.nomor_key, self.tahun, self.tingkat, self.wilayah_kode)

    @property
    def regulation_id(self) -> str:
        if self.tingkat == "daerah":
            return f"{self.jenis}-{self.wilayah_kode}-{self.tahun}-{self.nomor_key}"
        return f"{self.jenis}-{self.tahun}-{self.nomor_key}"


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    lowered = ascii_value.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return re.sub(r"-{2,}", "-", slug) or "judul"


def nomor_key(value: str) -> str:
    match = re.search(r"\d+", value)
    if not match:
        return "000"
    return f"{int(match.group(0)):03d}"


def clean_title(value: str) -> str:
    value = re.sub(r"\s+", " ", value.replace("#", " ")).strip(" -:.;")
    value = re.sub(r"\s+DENGAN\s+RAK?HMAT.*$", "", value, flags=re.I).strip()
    value = re.sub(r"\bPDP\b$", "", value, flags=re.I).strip()
    value = re.sub(r"\bITE\b$", "", value, flags=re.I).strip()
    value = re.sub(r"\bUU HPP\b$", "", value, flags=re.I).strip()
    return value.title() if value.isupper() else value


def frontmatter(text: str) -> dict:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    try:
        data = yaml.safe_load(text[4:end]) or {}
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def strip_frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---", 4)
    if end == -1:
        return text
    return text[end + 4 :].lstrip()


def normalize_ocr_number_tokens(text: str) -> str:
    chars = list(text)
    for index, char in enumerate(chars):
        if char not in {"O", "o", "I", "l"}:
            continue
        previous_char = chars[index - 1] if index > 0 else ""
        next_char = chars[index + 1] if index + 1 < len(chars) else ""
        near_number = previous_char.isdigit() or next_char.isdigit()
        near_ocr_number = previous_char in {"O", "o", "I", "l"} and next_char.isdigit()
        if near_number or near_ocr_number:
            chars[index] = "0" if char in {"O", "o"} else "1"
    return "".join(chars)


def searchable_header(text: str) -> str:
    head = text[:8000]
    match = re.search(r"\bMenimbang\b", head, flags=re.I)
    if match:
        head = head[: match.start()]
    return normalize_ocr_number_tokens(flatten(head))


def normalize_pages(text: str) -> str:
    return re.sub(
        r"<!--\s*page\s*:?\s*(\d+)\s*-->",
        lambda match: f"<!-- PAGE: {match.group(1)} -->",
        text,
        flags=re.I,
    )


def flatten(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def title_after_tentang(text: str) -> str | None:
    h1_match = re.search(r"^#\s+(.+?)\s*$", text, flags=re.M)
    if h1_match:
        h1 = clean_title(h1_match.group(1))
        tentang = re.search(r"\btentang\s+(.+)$", h1, flags=re.I)
        if tentang:
            return clean_title(tentang.group(1))

    same_line_heading = re.search(r"^##[ \t]*TENTANG[ \t]+(.+?)\s*$", text, flags=re.I | re.M)
    if same_line_heading:
        return clean_title(same_line_heading.group(1))

    official_source = strip_frontmatter(text)
    head = official_source[:8000]
    menimbang = re.search(r"\bMenimbang\b", head, flags=re.I)
    if menimbang:
        head = head[: menimbang.start()]
    flat = flatten(head)
    first_title = re.search(
        r"\bTENTANG\b\s+(.+?)(?:\s+KAMI\s+PRESIDEN\b|\s+Presiden\s+Republik\s+Indonesia\b|\s+PRESIDEN\s+REPUBLIK\s+INDONESIA\b|\s+Menimbang\b|\s+Mengingat\b)",
        flat,
        flags=re.I,
    )
    if first_title:
        return clean_title(first_title.group(1))

    official_matches = list(
        re.finditer(r"\bTENTANG\b\s+(.+?)\s+DENGAN RAHMAT", flat, flags=re.I)
    )
    if official_matches:
        return clean_title(official_matches[-1].group(1))

    circular_match = re.search(
        r"\bTENTANG\b\s+(.+?)(?:\s+##?\s*1\.\s+Latar|\s+1\.\s+Latar|\s+1\.\s+Umum)",
        flat,
        flags=re.I,
    )
    if circular_match:
        return clean_title(circular_match.group(1))

    heading_match = re.search(
        r"^##\s*TENTANG\s*\n+##\s+(.+?)(?:\n\s*\n|\n---|\Z)",
        text,
        flags=re.I | re.M | re.S,
    )
    if heading_match:
        return clean_title(heading_match.group(1))

    match = re.search(
        r"\bTENTANG\b\s+(.+?)(?:\s+DENGAN RAHMAT|\s+DEWAN KOMISIONER|\s+PRESIDEN REPUBLIK|\s+GUBERNUR|\s+MENTERI|\s+Menimbang\b)",
        flat,
        flags=re.I,
    )
    if not match:
        return None
    title = match.group(1)
    title = re.sub(r"^#+\s*", "", title)
    title = re.sub(r"\s*---.*$", "", title).strip()
    return clean_title(title)


def title_from_filename(path: Path, jenis: str, nomor: str, tahun: int) -> str:
    stem = path.stem
    stem = re.sub(r"^(06-)?SEOJK[-_]\d+[-_]\d+[-_]?\d*", "", stem, flags=re.I)
    stem = re.sub(r"^(UU|PP|POJK|SEOJK|PERMEN|PERPRES|PERDA_PERGUB)[-_]", "", stem, flags=re.I)
    stem = re.sub(r"^No[-_]", "", stem, flags=re.I)
    stem = re.sub(str(tahun), "", stem)
    stem = re.sub(r"\bTahun\b", "", stem, flags=re.I)
    stem = re.sub(re.escape(nomor), "", stem)
    stem = re.sub(r"POJK[_-]?\d*", "", stem, flags=re.I)
    stem = re.sub(r"SEOJK[_-]?\d*", "", stem, flags=re.I)
    stem = re.sub(r"^\d{2}uu\d{3}$", "", stem, flags=re.I)
    stem = re.sub(r"[_-]+", " ", stem).strip()
    return clean_title(stem or jenis)


def title_from_menetapkan(text: str) -> str | None:
    head = strip_frontmatter(text)[:5000]
    flat = flatten(head)
    match = re.search(
        r"\bMenetapkan\s*:?\s+(?:UNDANG-UNDANG\s+(?:TENTANG|UNTUK)\s+)?(.+?)(?:\s+Pasal\s+I\.?\b|\s+PASAL\s+I\.?\b|\s+Pasal\s+1\.?\b)",
        flat,
        flags=re.I,
    )
    if not match:
        return None
    title = re.sub(r"\s+", " ", match.group(1)).strip(" .:")
    return clean_title(title)


def official_title(jenis: str, nomor: str, tahun: int, judul: str) -> str:
    jenis_lengkap = JENIS_LENGKAP.get(jenis, jenis)
    if jenis == "uud":
        return "Undang-Undang Dasar Negara Republik Indonesia Tahun 1945"
    if re.search(r"/\d{4}\b", nomor):
        return f"{jenis_lengkap} Nomor {nomor} tentang {judul}"
    return f"{jenis_lengkap} Nomor {nomor} Tahun {tahun} tentang {judul}"


def find_nomor_tahun(text: str, pattern: str) -> tuple[str, int] | None:
    match = re.search(pattern, text, flags=re.I | re.S)
    if not match:
        return None
    nomor = re.sub(r"\s+", "", match.group("nomor")).strip()
    groups = match.groupdict()
    tahun_text = next((value for name, value in groups.items() if name.startswith("tahun") and value), None)
    if tahun_text:
        return nomor, int(tahun_text)
    year_match = re.search(r"(19|20)\d{2}", nomor)
    if year_match:
        return nomor, int(year_match.group(0))
    return None


def infer_info(path: Path, text: str) -> RegulationInfo | None:
    fm = frontmatter(text)
    bentuk_singkat = str(fm.get("bentuk_singkat") or "").lower()
    bentuk = str(fm.get("bentuk") or "").lower()
    fm_nomor = fm.get("nomor")
    fm_tahun = fm.get("tahun")
    fm_tentang = fm.get("tentang") or fm.get("judul_pendek") or fm.get("judul")

    has_regulation_text = bool(
        re.search(r"\b(UNDANG-UNDANG|PERATURAN|KEPUTUSAN|SURAT\s+EDARAN|LEMBARAN\s+NEGARA)\b", text, flags=re.I)
    )
    if not fm and not has_regulation_text:
        return None

    fm_kind_map = {
        "uu": "uu",
        "pp": "pp",
        "peraturan pemerintah": "pp",
        "peraturan menteri": "permen",
        "permendagri": "permen",
        "peraturan menteri dalam negeri": "permen",
        "permenpanrb": "permenpanrb",
        "peraturan menteri pendayagunaan aparatur negara dan reformasi birokrasi": "permenpanrb",
        "kepmenpanrb": "kepmenpanrb",
        "keputusan menteri pendayagunaan aparatur negara dan reformasi birokrasi": "kepmenpanrb",
        "permenkominfo": "permenkominfo",
        "peraturan menteri komunikasi dan informatika": "permenkominfo",
    }
    fm_kind = fm_kind_map.get(bentuk_singkat) or fm_kind_map.get(bentuk)
    if fm_kind and fm_nomor is not None and fm_tahun:
        tahun = int(fm_tahun)
        nomor = str(fm_nomor)
        judul = clean_title(str(fm.get("tentang") or fm.get("judul_pendek") or title_from_filename(path, fm_kind, nomor, tahun)))
        if fm_kind == "uu":
            lembaga = ["Presiden Republik Indonesia", "Dewan Perwakilan Rakyat Republik Indonesia"]
        elif fm_kind == "pp":
            lembaga = ["Presiden Republik Indonesia"]
        elif fm_kind == "permen":
            lembaga = ["Kementerian Dalam Negeri"] if "dalam negeri" in bentuk else []
        else:
            lembaga = []
        return RegulationInfo(
            source_path=path,
            jenis=fm_kind,
            tingkat="pusat",
            nomor=nomor,
            nomor_key=nomor_key(nomor),
            tahun=tahun,
            judul=judul,
            judul_lengkap=official_title(fm_kind, nomor, tahun, judul),
            lembaga=lembaga,
        )

    if bentuk_singkat == "uud" or bentuk == "undang-undang dasar":
        return RegulationInfo(
            source_path=path,
            jenis="uud",
            tingkat="pusat",
            nomor="",
            nomor_key="000",
            tahun=int(fm_tahun or 1945),
            judul="Undang-Undang Dasar Negara Republik Indonesia",
            judul_lengkap="Undang-Undang Dasar Negara Republik Indonesia Tahun 1945",
            lembaga=["Panitia Persiapan Kemerdekaan Indonesia"],
        )

    if bentuk_singkat == "perlur" or bentuk == "peraturan lurah":
        tahun = int(fm_tahun or re.search(r"(19|20)\d{2}", path.stem).group(0))
        nomor = str(fm_nomor or nomor_key(path.stem).lstrip("0") or "0")
        judul = clean_title(str(fm_tentang or title_from_filename(path, "perlur", nomor, tahun)))
        return RegulationInfo(
            source_path=path,
            jenis="perlur",
            tingkat="daerah",
            nomor=nomor,
            nomor_key=nomor_key(nomor),
            tahun=tahun,
            judul=judul,
            judul_lengkap=official_title("perlur", nomor, tahun, judul),
            lembaga=["Pemerintah Kalurahan Sendangadi"],
            wilayah_level="kabupaten",
            wilayah_kode="3404",
            wilayah_nama="Sleman",
        )

    if bentuk_singkat in {"kep ojk", "kep-ojk"} or "keputusan anggota dewan komisioner otoritas jasa keuangan" in bentuk:
        tahun = int(fm_tahun or re.search(r"(19|20)\d{2}", path.stem).group(0))
        nomor = str(fm_nomor or nomor_key(path.stem).lstrip("0") or "0")
        judul = clean_title(str(fm_tentang or title_from_filename(path, "kepojk", nomor, tahun)))
        return RegulationInfo(
            source_path=path,
            jenis="kepojk",
            tingkat="lembaga",
            nomor=f"KEP-{nomor}/D.05/{tahun}" if "/" not in nomor else nomor,
            nomor_key=nomor_key(nomor),
            tahun=tahun,
            judul=judul,
            judul_lengkap=official_title("kepojk", f"KEP-{nomor}/D.05/{tahun}" if "/" not in nomor else nomor, tahun, judul),
            lembaga=["Otoritas Jasa Keuangan"],
        )

    flat = normalize_ocr_number_tokens(flatten(text))
    header = searchable_header(text)
    upper_stem = path.stem.upper()

    candidates = [
        (
            "perbssn",
            "lembaga",
            r"PERATURAN\s+BADAN\s+SIBER\s+DAN\s+SANDI\s+NEGARA.*?\bNOMOR\s+(?P<nomor>\d+)\s+TAHUN\s+(?P<tahun>\d{4})",
        ),
        (
            "semenpanrb",
            "pusat",
            r"SURAT\s+EDARAN\s+MENTERI\s+PENDAYAGUNAAN\s+APARATUR\s+NEGARA.*?\bNOMOR:?\s+(?P<nomor>\d+)\s+TAHUN\s+(?P<tahun>\d{4})",
        ),
        (
            "semenkominfo",
            "pusat",
            r"SURAT\s+EDARAN\s+MENTERI\s+KOMUNIKASI\s+DAN\s+INFORMATIKA.*?\bNOMOR\s+(?P<nomor>\d+)\s+TAHUN\s+(?P<tahun>\d{4})",
        ),
        (
            "permenpanrb",
            "pusat",
            r"PERATURAN\s+MENTERI\s+PENDAYAGUNAAN\s+APARATUR\s+NEGARA.*?\bNOMOR\s+(?P<nomor>\d+)\s+TAHUN\s+(?P<tahun>\d{4})",
        ),
        (
            "permenkominfo",
            "pusat",
            r"PERATURAN\s+MENTERI\s+KOMUNIKASI\s+DAN\s+INFORMATIKA.*?\bNOMOR\s+(?P<nomor>\d+)\s+TAHUN\s+(?P<tahun>\d{4})",
        ),
        (
            "kepmenpanrb",
            "pusat",
            r"KEPUTUSAN\s+MENTERI\s+PENDAYAGUNAAN\s+APARATUR\s+NEGARA.*?\bNOMOR\s+(?P<nomor>\d+)\s+TAHUN\s+(?P<tahun>\d{4})",
        ),
        (
            "seojk",
            "lembaga",
            r"SURAT\s+EDARAN\s+OTORITAS\s+JASA\s+KEUANGAN.*?\bNOMOR\s+(?P<nomor>\d+\s*/\s*SEOJK\.[\dA-Z.]+\s*/\s*(?P<tahun>\d{4}))",
        ),
        (
            "pojk",
            "lembaga",
            r"PERATURAN\s+OTORITAS\s+JASA\s+KEUANGAN.*?\bNOMOR\s+(?P<nomor>\d+(?:\s*/\s*POJK\.[\dA-Z.]+\s*/\s*(?P<tahun>\d{4}))?)(?:\s+TAHUN\s+(?P<tahun2>\d{4}))?",
        ),
        (
            "uu",
            "pusat",
            r"UNDANG-UNDANG\s+REPUBLIK\s+INDONESIA.*?\bNOMOR\s+(?P<nomor>\d+)\s*TAHUN\s*(?P<tahun>\d{4})?",
        ),
        (
            "pp",
            "pusat",
            r"PERATURAN\s+PEMERINTAH\s+REPUBLIK\s+INDONESIA.*?\bNOMOR\s+(?P<nomor>\d+)\s+TAHUN\s+(?P<tahun>\d{4})",
        ),
        (
            "perpres",
            "pusat",
            r"PERATURAN\s+PRESIDEN\s+REPUBLIK\s+INDONESIA.*?\bNOMOR\s+(?P<nomor>\d+)\s+TAHUN\s+(?P<tahun>\d{4})",
        ),
        (
            "permen",
            "pusat",
            r"PERATURAN\s+MENTERI.*?\bNOMOR\s+(?P<nomor>\d+)\s+TAHUN\s+(?P<tahun>\d{4})",
        ),
        (
            "pergub",
            "daerah",
            r"PERATURAN\s+GUBERNUR\s+PAPUA(?:\s+BARAT)?.*?\bNOMOR\s+(?P<nomor>\d+)\s+TAHUN\s+(?P<tahun>\d{4})",
        ),
        (
            "perda-prov",
            "daerah",
            r"PERATURAN\s+DAERAH\s+PROVINSI\s+PAPUA(?:\s+BARAT)?.*?\bNOMOR\s+(?P<nomor>\d+)\s+TAHUN\s+(?P<tahun>\d{4})",
        ),
    ]

    selected: tuple[str, str, str] | None = None
    for jenis, tingkat, pattern in candidates:
        inferred = find_nomor_tahun(header, pattern)
        if inferred:
            nomor, tahun = inferred
            selected = (jenis, tingkat, nomor)
            break
        if jenis.upper().replace("-", "_") in upper_stem:
            selected = (jenis, tingkat, "")

    if selected is None:
        short_name = re.fullmatch(r"(?P<yy>\d{2})uu(?P<nomor>\d{3})", path.stem, flags=re.I)
        if short_name:
            selected = ("uu", "pusat", str(int(short_name.group("nomor"))))
            tahun = 1900 + int(short_name.group("yy"))
        else:
            return None

    jenis, tingkat, nomor = selected
    if not nomor:
        short_name = re.fullmatch(r"(?P<yy>\d{2})uu(?P<nomor>\d{3})", path.stem, flags=re.I)
        if short_name:
            nomor = str(int(short_name.group("nomor")))
            tahun = 1900 + int(short_name.group("yy"))
        else:
            fallback = re.search(r"(?P<tahun>(?:19|20)\d{2}).*?(?P<nomor>\d+)", path.stem)
            if not fallback:
                fallback = re.search(r"(?P<nomor>\d+).*?(?P<tahun>(?:19|20)\d{2})", path.stem)
            if not fallback:
                return None
            nomor = fallback.group("nomor")
            tahun = int(fallback.group("tahun"))
    else:
        year_in_nomor = re.search(r"(19|20)\d{2}", nomor)
        tahun_match = re.search(
            rf"\bNOMOR\s+{re.escape(nomor)}\s+TAHUN\s+((?:19|20)\d{{2}})",
            flat,
            flags=re.I,
        )
        short_name = re.fullmatch(r"(?P<yy>\d{2})uu(?P<nomor>\d{3})", path.stem, flags=re.I)
        if short_name:
            tahun = 1900 + int(short_name.group("yy"))
        elif year_in_nomor:
            tahun = int(year_in_nomor.group(0))
        elif tahun_match:
            tahun = int(tahun_match.group(1))
        else:
            year_fallback = re.search(r"(19|20)\d{2}", path.stem)
            if not year_fallback:
                return None
            tahun = int(year_fallback.group(0))

    title = title_after_tentang(text) or title_from_menetapkan(text) or title_from_filename(path, jenis, nomor, tahun)
    if re.search(r"[\\[\\]{}]|\\.\\.\\.|SK No|PAGE:", title, flags=re.I):
        title = title_from_filename(path, jenis, nomor, tahun)
    if title.lower() in {jenis.lower(), "uu", "undang-undang"} or re.fullmatch(r"\d{2}uu\d*", title, flags=re.I):
        title = title_from_menetapkan(text) or title
    title = clean_title(title)

    lembaga: list[str]
    if jenis in {"pojk", "seojk", "kepojk"}:
        lembaga = ["Otoritas Jasa Keuangan"]
    elif jenis == "perbssn":
        lembaga = ["Badan Siber dan Sandi Negara"]
    elif jenis in {"permenpanrb", "kepmenpanrb", "semenpanrb"}:
        lembaga = ["Kementerian Pendayagunaan Aparatur Negara dan Reformasi Birokrasi"]
    elif jenis in {"permenkominfo", "semenkominfo"}:
        lembaga = ["Kementerian Komunikasi dan Informatika"]
    elif jenis == "uu":
        lembaga = ["Presiden Republik Indonesia", "Dewan Perwakilan Rakyat Republik Indonesia"]
    elif jenis in {"pp", "perpres"}:
        lembaga = ["Presiden Republik Indonesia"]
    elif jenis == "permen" and re.search(r"MENTERI\s+DALAM\s+NEGERI", flat, flags=re.I):
        lembaga = ["Kementerian Dalam Negeri"]
    elif jenis == "perda-prov":
        if re.search(r"PROVINSI\s+PAPUA\s+BARAT", flat, flags=re.I):
            lembaga = ["Pemerintah Provinsi Papua Barat", "Dewan Perwakilan Rakyat Papua Barat"]
        else:
            lembaga = ["Pemerintah Provinsi Papua", "Dewan Perwakilan Rakyat Papua"]
    elif jenis == "pergub":
        lembaga = ["Pemerintah Provinsi Papua Barat"] if re.search(r"GUBERNUR\s+PAPUA\s+BARAT", flat, flags=re.I) else ["Pemerintah Provinsi Papua"]
    else:
        lembaga = []

    wilayah_level = "provinsi" if jenis in {"perda-prov", "pergub"} else ""
    if jenis in {"perda-prov", "pergub"} and re.search(r"PAPUA\s+BARAT", flat, flags=re.I):
        wilayah_kode = "92"
        wilayah_nama = "Papua Barat"
    elif jenis in {"perda-prov", "pergub"}:
        wilayah_kode = "91"
        wilayah_nama = "Papua"
    else:
        wilayah_kode = ""
        wilayah_nama = ""

    return RegulationInfo(
        source_path=path,
        jenis=jenis,
        tingkat=tingkat,
        nomor=nomor,
        nomor_key=nomor_key(nomor),
        tahun=tahun,
        judul=title,
        judul_lengkap=official_title(jenis, nomor, tahun, title),
        lembaga=lembaga,
        wilayah_level=wilayah_level,
        wilayah_kode=wilayah_kode,
        wilayah_nama=wilayah_nama,
    )


def final_folder(info: RegulationInfo) -> Path:
    title_slug = slugify(info.judul)[:120].rstrip("-")
    if info.tingkat == "lembaga":
        if info.jenis in {"pojk", "seojk", "kepojk"}:
            lembaga_dir = "ojk"
        elif info.jenis == "perbssn":
            lembaga_dir = "bssn"
        else:
            lembaga_dir = "belum-diisi"
        return (
            REGULASI
            / "lembaga"
            / lembaga_dir
            / str(info.tahun)
            / f"{info.jenis}-{info.tahun}-{info.nomor_key}-{title_slug}"
        )
    if info.tingkat == "daerah":
        wilayah_slug = slugify(info.wilayah_nama)
        jenis_dir = "perda" if info.jenis == "perda-prov" else info.jenis
        return (
            REGULASI
            / "daerah"
            / info.wilayah_level
            / f"{info.wilayah_kode}-{wilayah_slug}"
            / jenis_dir
            / str(info.tahun)
            / f"{info.jenis}-{wilayah_slug}-{info.tahun}-{info.nomor_key}-{title_slug}"
        )
    if info.jenis == "uud":
        return (
            REGULASI
            / "pusat"
            / "uud"
            / str(info.tahun)
            / f"uud-{info.tahun}-{title_slug}"
        )
    return (
        REGULASI
        / "pusat"
        / ("permen" if info.jenis in {"permenpanrb", "kepmenpanrb", "semenpanrb", "permenkominfo", "semenkominfo"} else info.jenis)
        / str(info.tahun)
        / f"{info.jenis}-{info.tahun}-{info.nomor_key}-{title_slug}"
    )


def source_urls(text: str) -> list[str]:
    urls = re.findall(r"https?://[^\s)>\]]+", text)
    return sorted(dict.fromkeys(url.rstrip(".,;") for url in urls))


def quality(info: RegulationInfo, text: str, duplicate_notes: list[str]) -> dict:
    page_count = len(re.findall(r"<!--\s*PAGE:\s*\d+\s*-->", text, flags=re.I))
    risks = [
        "Sumber berasal dari staging/incoming dan perlu verifikasi manual terhadap dokumen resmi.",
        "Relasi regulasi belum diekstrak penuh dan perlu verifikasi manual.",
    ]
    if duplicate_notes:
        risks.extend(duplicate_notes)
    if re.search(r"\b(REPUELIK|RAHMATTUHAN|daLam|Miik)\b", text):
        risks.append("Terdapat indikasi kesalahan OCR pada teks.")
    return {
        "id": info.regulation_id,
        "status_konversi": "needs_review",
        "pemeriksaan": {
            "metadata": {"lengkap": False, "catatan": "Metadata dasar diisi dari teks staging; perlu verifikasi manual."},
            "struktur_markdown": {
                "heading_konsisten": False,
                "pasal_terdeteksi": bool(re.search(r"\bPasal\s+\d+", text, flags=re.I)),
                "ayat_terdeteksi": bool(re.search(r"\(\d+\)", text)),
                "lampiran_terpisah": False,
                "catatan": "Struktur Markdown dipertahankan dari file staging.",
            },
            "tabel": {
                "ada_tabel": "|" in text,
                "tabel_berhasil_dikonversi": None,
                "catatan": None,
            },
            "gambar_bagan": {
                "ada_gambar": bool(re.search(r"!\[", text)),
                "ada_bagan": None,
                "sudah_dibuat_mermaid": None,
                "catatan": None,
            },
            "halaman": {
                "page_marker": page_count > 0,
                "jumlah_halaman_pdf": None,
                "jumlah_page_marker": page_count or None,
                "catatan": None,
            },
            "validasi_manual": {
                "sudah_diperiksa": False,
                "pemeriksa": None,
                "tanggal": None,
                "catatan": None,
            },
        },
        "risiko": risks,
    }


def write_yaml(path: Path, data: dict | list) -> None:
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, allow_unicode=True, sort_keys=False)


def write_final(info: RegulationInfo, text: str, duplicate_notes: list[str]) -> Path:
    folder = final_folder(info)
    folder.mkdir(parents=True, exist_ok=False)
    urls = source_urls(text)
    source_name = "staging/incoming"
    source_url = urls[0] if urls else "belum_diisi"
    source_url_entries = [{"name": source_name if urls else "belum_diisi", "url": source_url}]
    normalized_text = normalize_pages(text).strip()

    (folder / "README.md").write_text(
        f"""# {info.judul_lengkap}

## Ringkasan

Ringkasan belum diisi. Ringkasan tidak boleh menggantikan teks resmi regulasi.

## Informasi Utama

| Elemen | Isi |
|---|---|
| Jenis | {JENIS_LENGKAP.get(info.jenis, info.jenis)} |
| Nomor | {info.nomor} |
| Tahun | {info.tahun} |
| Judul | {info.judul} |
| Status | perlu_verifikasi |
| Tingkat | {info.tingkat} |
| Sumber | {source_url} |

## File

- [`dokumen.md`](dokumen.md)
- [`metadata.yml`](metadata.yml)
- [`source.yml`](source.yml)
- [`relasi.yml`](relasi.yml)
- [`quality-check.yml`](quality-check.yml)

## Catatan Konversi

Status konversi: needs_review.

## Peringatan

Dokumen Markdown ini adalah hasil konversi untuk kebutuhan pencarian, analisis, dan pemrosesan teks. Untuk rujukan hukum resmi, tetap gunakan sumber regulasi resmi.
""",
        encoding="utf-8",
    )

    metadata = {
        "id": info.regulation_id,
        "jenis": info.jenis,
        "jenis_lengkap": JENIS_LENGKAP.get(info.jenis, "belum_diisi"),
        "nomor": info.nomor,
        "nomor_lengkap": info.nomor,
        "tahun": info.tahun,
        "judul": info.judul,
        "judul_lengkap": info.judul_lengkap,
        "tingkat": info.tingkat,
        "hierarki_level": None,
        "lembaga_penerbit": info.lembaga,
        "pejabat_penetap": [],
        "tanggal_ditetapkan": None,
        "tanggal_diundangkan": None,
        "tanggal_berlaku": None,
        "tempat_ditetapkan": None,
        "lembaran_negara": {"nomor": None, "tahun": None},
        "tambahan_lembaran_negara": {"nomor": None},
        "berita_negara": {"nomor": None, "tahun": None},
        "tambahan_berita_negara": {"nomor": None},
        "status": {
            "berlaku": None,
            "status_teks": "perlu_verifikasi",
            "mulai_berlaku": None,
            "berakhir": None,
            "dicabut_oleh": [],
            "mencabut": [],
            "mengubah": [],
            "diubah_oleh": [],
        },
        "subjek": [],
        "sektor": [],
        "kata_kunci": [],
        "wilayah": {
            "level": info.wilayah_level,
            "kode": info.wilayah_kode,
            "nama": info.wilayah_nama,
        },
        "sumber": {"nama": source_name, "url": source_url, "alternatif": urls[1:]},
        "file": {
            "markdown_utama": "dokumen.md",
            "batang_tubuh": None,
            "penjelasan": None,
            "lampiran": [],
            "pdf_asli": "external",
        },
        "konversi": {
            "metode": "staging markdown import",
            "tanggal_konversi": None,
            "alat": "AI-assisted conversion",
            "ocr": None,
            "status_kualitas": "needs_review",
            "pemeriksa": None,
        },
        "catatan": [f"Diimpor dari {info.source_path.relative_to(ROOT).as_posix()}."],
    }
    write_yaml(folder / "metadata.yml", metadata)
    write_yaml(
        folder / "source.yml",
        {
            "id": info.regulation_id,
            "judul": info.judul_lengkap,
            "pdf": {
                "stored_in_git": False,
                "source_url": source_url_entries,
                "external_storage": {"provider": None, "bucket": None, "object_key": None, "url": None},
                "checksum": {"algorithm": "sha256", "value": None},
                "file_size_bytes": None,
                "last_checked": None,
            },
            "html_source": {"available": None, "url": None},
            "catatan": ["Sumber awal berupa file Markdown di staging/incoming."],
        },
    )
    (folder / "dokumen.md").write_text(
        f"""---
id: "{info.regulation_id}"
jenis: "{info.jenis}"
nomor: "{info.nomor}"
tahun: {info.tahun}
judul: "{info.judul_lengkap.replace('"', '\\"')}"
status: "perlu_verifikasi"
sumber: "{source_url.replace('"', '\\"')}"
---

# {info.judul_lengkap}

## Catatan Konversi

Dokumen ini diimpor dari file Markdown staging. Untuk rujukan hukum resmi, gunakan dokumen resmi dari sumber regulasi terkait.

---

## Teks Regulasi

{normalized_text}
""",
        encoding="utf-8",
    )
    write_yaml(
        folder / "relasi.yml",
        {
            "id": info.regulation_id,
            "berdasarkan": [],
            "mengingat": [],
            "mencabut": [],
            "dicabut_oleh": [],
            "mengubah": [],
            "diubah_oleh": [],
            "melaksanakan": [],
            "dilaksanakan_oleh": [],
            "peraturan_pelaksana": [],
            "terkait": [],
        },
    )
    write_yaml(folder / "quality-check.yml", quality(info, normalized_text, duplicate_notes))
    return folder


def move_with_collision(source: Path, destination_dir: Path) -> Path:
    destination_dir.mkdir(parents=True, exist_ok=True)
    target = destination_dir / source.name
    if not target.exists():
        shutil.move(str(source), str(target))
        return target
    for index in range(1, 1000):
        candidate = destination_dir / f"{source.stem}-{index}{source.suffix}"
        if not candidate.exists():
            shutil.move(str(source), str(candidate))
            return candidate
    raise RuntimeError(f"could not move {source}")


def existing_regulation_ids() -> dict[str, Path]:
    ids: dict[str, Path] = {}
    for metadata_path in REGULASI.glob("**/metadata.yml"):
        try:
            data = yaml.safe_load(metadata_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            continue
        regulation_id = data.get("id")
        if regulation_id and regulation_id not in ids:
            ids[regulation_id] = metadata_path.parent
    return ids


def main() -> int:
    ignored_names = {".gitkeep", "README.md"}
    files = [path for path in sorted(INCOMING.glob("*.md")) if path.name not in ignored_names]
    existing_ids = existing_regulation_ids()
    inferred: list[tuple[RegulationInfo, str]] = []
    rejected: list[tuple[Path, str]] = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        info = infer_info(path, text)
        if not info:
            rejected.append((path, "Tidak dapat mengidentifikasi jenis/nomor/tahun secara aman."))
            continue
        inferred.append((info, text))

    by_key: dict[tuple[str, str, int, str, str], list[tuple[RegulationInfo, str]]] = {}
    for item in inferred:
        by_key.setdefault(item[0].key, []).append(item)

    processed: list[Path] = []
    duplicate_rejections: list[tuple[Path, str]] = []
    for items in by_key.values():
        items.sort(key=lambda item: len(item[1]), reverse=True)
        winner, winner_text = items[0]
        duplicate_notes = []
        existing_folder = existing_ids.get(winner.regulation_id)
        if existing_folder:
            rejected.append(
                (
                    winner.source_path,
                    f"Regulasi dengan id {winner.regulation_id} sudah ada di {existing_folder.relative_to(ROOT).as_posix()}.",
                )
            )
            for duplicate, _duplicate_text in items[1:]:
                duplicate_rejections.append(
                    (
                        duplicate.source_path,
                        f"Duplikat dari regulasi dengan id {winner.regulation_id} yang sudah ada di {existing_folder.relative_to(ROOT).as_posix()}.",
                    )
                )
            continue
        for duplicate, _duplicate_text in items[1:]:
            reason = f"Duplikat dari {winner.source_path.name} untuk {winner.regulation_id}."
            duplicate_notes.append(reason)
            duplicate_rejections.append((duplicate.source_path, reason))
        try:
            folder = write_final(winner, winner_text, duplicate_notes)
        except FileExistsError:
            rejected.append((winner.source_path, f"Folder final sudah ada: {final_folder(winner).relative_to(ROOT)}"))
            continue
        processed.append(folder)
        move_with_collision(winner.source_path, REVIEWED)

    for path, reason in rejected + duplicate_rejections:
        if path.exists():
            moved = move_with_collision(path, REJECTED)
            (moved.with_suffix(moved.suffix + ".reason.txt")).write_text(reason + "\n", encoding="utf-8")

    print(f"processed={len(processed)}")
    print(f"rejected={len(rejected) + len(duplicate_rejections)}")
    for folder in processed:
        print(folder.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
