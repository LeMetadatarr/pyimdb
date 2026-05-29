"""Small normalisation helpers for IMDb data."""
from __future__ import annotations

import html
import re
import unicodedata
from typing import Optional

_TT_RE = re.compile(r"\btt\d{7,}\b")
_NM_RE = re.compile(r"\bnm\d{7,}\b")


def clean(text: Optional[str]) -> str:
    """Unescape HTML entities, NFKC-normalise, collapse whitespace, strip."""
    if not text:
        return ""
    text = html.unescape(str(text))
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def clean_or_none(text: Optional[str]) -> Optional[str]:
    """Like :func:`clean` but returns ``None`` for empty / placeholder values."""
    val = clean(text)
    if not val or val.lower() in ("none", "n/a", "-", "\\n"):
        return None
    return val


def to_int(value: object) -> Optional[int]:
    """Parse an int, treating IMDb's ``\\N`` sentinel and junk as ``None``."""
    if value is None:
        return None
    s = str(value).strip()
    if not s or s == "\\N":
        return None
    try:
        return int(s)
    except ValueError:
        m = re.search(r"-?\d+", s)
        return int(m.group()) if m else None


def to_float(value: object) -> Optional[float]:
    """Parse a float, treating ``\\N`` and junk as ``None``."""
    if value is None:
        return None
    s = str(value).strip()
    if not s or s == "\\N":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def tsv_value(value: object) -> Optional[str]:
    """Decode one IMDb TSV cell: ``\\N`` → ``None``, else the stripped string."""
    if value is None:
        return None
    s = str(value)
    if s == "\\N" or s == "":
        return None
    return s


def tsv_list(value: object) -> list:
    """Decode a comma-separated IMDb TSV cell into a list (``\\N`` → ``[]``)."""
    v = tsv_value(value)
    if v is None:
        return []
    return [part for part in (p.strip() for p in v.split(",")) if part]


def extract_imdb_id(value: Optional[str]) -> Optional[str]:
    """Pull the first ``tt…`` or ``nm…`` id out of *value*."""
    if not value:
        return None
    m = _TT_RE.search(value) or _NM_RE.search(value)
    return m.group(0) if m else None
