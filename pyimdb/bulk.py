"""Stream-parse the IMDb bulk datasets — the dataset backbone.

The dumps at ``https://datasets.imdbws.com/`` are gzipped TSV. They are large
(``title.basics`` is ~1.5 GB uncompressed, ~10M rows), so every function here
**streams** — gzip-decompress on the fly and a ``csv`` reader yields one row
dict at a time. Nothing loads a whole file into memory.

Files are cached on disk (``~/.cache/pyimdb`` by default, override with
``PYIMDB_CACHE_DIR``) and fetched on demand. Each raw-row stream has a typed
variant that maps the dict onto a :mod:`pyimdb.models` dataclass.

PROVENANCE: the IMDb datasets are licensed for **personal and non-commercial
use only**. See ``PROVENANCE.md`` and ``docs/dataset.md``.
"""
from __future__ import annotations

import csv
import gzip
import io
import os
from pathlib import Path
from typing import Any, Dict, Iterator, Optional

from pyimdb import transport
from pyimdb._clean import to_float, to_int, tsv_list, tsv_value
from pyimdb.models import (
    Aka,
    Episode,
    Name,
    Principal,
    Rating,
    Title,
    TitleType,
)

# The seven canonical dumps.
DATASETS = {
    "title.basics": "title.basics.tsv.gz",
    "title.ratings": "title.ratings.tsv.gz",
    "title.akas": "title.akas.tsv.gz",
    "title.crew": "title.crew.tsv.gz",
    "title.episode": "title.episode.tsv.gz",
    "title.principals": "title.principals.tsv.gz",
    "name.basics": "name.basics.tsv.gz",
}

# csv field-size guard: some `characters`/`knownForTitles` cells are long.
csv.field_size_limit(10 * 1024 * 1024)


def cache_dir() -> Path:
    """Resolve the on-disk cache directory (``PYIMDB_CACHE_DIR`` or default)."""
    env = os.environ.get("PYIMDB_CACHE_DIR")
    base = Path(env) if env else Path.home() / ".cache" / "pyimdb"
    base.mkdir(parents=True, exist_ok=True)
    return base


def dataset_url(name: str) -> str:
    """Full download URL for a dataset name (e.g. ``"title.ratings"``)."""
    fname = DATASETS.get(name, name if name.endswith(".gz") else f"{name}.tsv.gz")
    return f"{transport.DATASETS_BASE}/{fname}"


def local_path(name: str) -> Path:
    """Cache path for a dataset name."""
    fname = DATASETS.get(name, name if name.endswith(".gz") else f"{name}.tsv.gz")
    return cache_dir() / fname


def download(name: str, *, force: bool = False, chunk: int = 1 << 20) -> Path:
    """Fetch a dataset to the cache (idempotent unless *force*).

    Returns the local ``.tsv.gz`` path. Streams to disk in *chunk*-byte
    blocks — the compressed file is never held in memory.
    """
    path = local_path(name)
    if path.exists() and not force and path.stat().st_size > 0:
        return path
    url = dataset_url(name)
    resp = transport.get(url, stream=True)
    try:
        tmp = path.with_suffix(path.suffix + ".part")
        with open(tmp, "wb") as fh:
            for block in resp.iter_content(chunk_size=chunk):
                if block:
                    fh.write(block)
        tmp.replace(path)
    finally:
        resp.close()
    return path


def _open_local(path: Path) -> io.TextIOBase:
    return io.TextIOWrapper(gzip.open(path, "rb"), encoding="utf-8", newline="")


def stream_rows(
    name: str,
    *,
    limit: Optional[int] = None,
    download_if_missing: bool = True,
    path: Optional[Path] = None,
) -> Iterator[Dict[str, Any]]:
    """Yield raw row dicts (keyed by TSV header) from a dataset.

    Streams gzip→TSV one row at a time. ``limit`` caps the number of rows
    yielded — handy for sampling without reading the whole file. Pass *path*
    to read a specific local ``.tsv.gz`` (skips download).
    """
    if path is None:
        path = local_path(name)
        if not path.exists() or path.stat().st_size == 0:
            if not download_if_missing:
                raise FileNotFoundError(
                    f"{path} not cached; call download({name!r}) first "
                    f"or pass download_if_missing=True"
                )
            download(name)
    fh = _open_local(path)
    try:
        reader = csv.DictReader(fh, delimiter="\t", quoting=csv.QUOTE_NONE)
        for i, row in enumerate(reader):
            if limit is not None and i >= limit:
                break
            yield row
    finally:
        fh.close()


def stream_raw_text(gz_bytes: bytes, *, limit: Optional[int] = None) -> Iterator[Dict[str, Any]]:
    """Parse an in-memory gzip TSV blob (used by tests/fixtures)."""
    fh = io.TextIOWrapper(gzip.GzipFile(fileobj=io.BytesIO(gz_bytes)), encoding="utf-8", newline="")
    reader = csv.DictReader(fh, delimiter="\t", quoting=csv.QUOTE_NONE)
    for i, row in enumerate(reader):
        if limit is not None and i >= limit:
            break
        yield row


# ---- typed-row mappers -------------------------------------------------

def row_to_title(row: Dict[str, Any]) -> Title:
    return Title(
        imdb_id=tsv_value(row.get("tconst")) or "",
        title_type=TitleType.coerce(tsv_value(row.get("titleType"))),
        primary_title=tsv_value(row.get("primaryTitle")),
        original_title=tsv_value(row.get("originalTitle")),
        is_adult=(tsv_value(row.get("isAdult")) == "1"),
        start_year=to_int(row.get("startYear")),
        end_year=to_int(row.get("endYear")),
        runtime_minutes=to_int(row.get("runtimeMinutes")),
        genres=tsv_list(row.get("genres")),
    )


def row_to_rating(row: Dict[str, Any]) -> Rating:
    return Rating(
        imdb_id=tsv_value(row.get("tconst")) or "",
        average_rating=to_float(row.get("averageRating")),
        num_votes=to_int(row.get("numVotes")),
    )


def row_to_aka(row: Dict[str, Any]) -> Aka:
    is_orig = tsv_value(row.get("isOriginalTitle"))
    return Aka(
        imdb_id=tsv_value(row.get("titleId")) or "",
        ordering=to_int(row.get("ordering")),
        title=tsv_value(row.get("title")),
        region=tsv_value(row.get("region")),
        language=tsv_value(row.get("language")),
        types=tsv_list(row.get("types")),
        attributes=tsv_list(row.get("attributes")),
        is_original_title=(None if is_orig is None else is_orig == "1"),
    )


def row_to_episode(row: Dict[str, Any]) -> Episode:
    return Episode(
        imdb_id=tsv_value(row.get("tconst")) or "",
        series_id=tsv_value(row.get("parentTconst")),
        season_number=to_int(row.get("seasonNumber")),
        episode_number=to_int(row.get("episodeNumber")),
    )


def row_to_principal(row: Dict[str, Any]) -> Principal:
    return Principal(
        imdb_id=tsv_value(row.get("tconst")) or "",
        name_id=tsv_value(row.get("nconst")) or "",
        ordering=to_int(row.get("ordering")),
        category=tsv_value(row.get("category")),
        job=tsv_value(row.get("job")),
        characters=_parse_characters(row.get("characters")),
    )


def row_to_name(row: Dict[str, Any]) -> Name:
    return Name(
        imdb_id=tsv_value(row.get("nconst")) or "",
        primary_name=tsv_value(row.get("primaryName")),
        birth_year=to_int(row.get("birthYear")),
        death_year=to_int(row.get("deathYear")),
        primary_professions=tsv_list(row.get("primaryProfession")),
        known_for_titles=tsv_list(row.get("knownForTitles")),
    )


def _parse_characters(value: Any) -> list:
    """``characters`` is a JSON array string like ``["Cobb"]``."""
    v = tsv_value(value)
    if not v:
        return []
    import json

    try:
        out = json.loads(v)
        if isinstance(out, list):
            return [str(x) for x in out]
    except (ValueError, TypeError):
        pass
    return [v]


# ---- typed streams -----------------------------------------------------

def stream_titles(**kw: Any) -> Iterator[Title]:
    """Stream ``title.basics`` as :class:`~pyimdb.models.Title`."""
    for row in stream_rows("title.basics", **kw):
        yield row_to_title(row)


def stream_ratings(**kw: Any) -> Iterator[Rating]:
    """Stream ``title.ratings`` as :class:`~pyimdb.models.Rating`."""
    for row in stream_rows("title.ratings", **kw):
        yield row_to_rating(row)


def stream_akas(**kw: Any) -> Iterator[Aka]:
    """Stream ``title.akas`` as :class:`~pyimdb.models.Aka`."""
    for row in stream_rows("title.akas", **kw):
        yield row_to_aka(row)


def stream_episodes(**kw: Any) -> Iterator[Episode]:
    """Stream ``title.episode`` as :class:`~pyimdb.models.Episode`."""
    for row in stream_rows("title.episode", **kw):
        yield row_to_episode(row)


def stream_principals(**kw: Any) -> Iterator[Principal]:
    """Stream ``title.principals`` as :class:`~pyimdb.models.Principal`."""
    for row in stream_rows("title.principals", **kw):
        yield row_to_principal(row)


def stream_names(**kw: Any) -> Iterator[Name]:
    """Stream ``name.basics`` as :class:`~pyimdb.models.Name`."""
    for row in stream_rows("name.basics", **kw):
        yield row_to_name(row)


# ---- lookups -----------------------------------------------------------

def find_title(imdb_id: str, *, with_rating: bool = True, **kw: Any) -> Optional[Title]:
    """Scan ``title.basics`` for a single ``tt…`` id (optionally join rating).

    A linear scan over a large dump — fine for a one-off, but prefer the
    suggestion API (:func:`pyimdb.search.first`) when you only need the label.
    """
    found: Optional[Title] = None
    for row in stream_rows("title.basics", **kw):
        if row.get("tconst") == imdb_id:
            found = row_to_title(row)
            break
    if found and with_rating:
        rating = find_rating(imdb_id, **kw)
        if rating:
            found.average_rating = rating.average_rating
            found.num_votes = rating.num_votes
    return found


def find_rating(imdb_id: str, **kw: Any) -> Optional[Rating]:
    """Scan ``title.ratings`` for one ``tt…`` id."""
    for row in stream_rows("title.ratings", **kw):
        if row.get("tconst") == imdb_id:
            return row_to_rating(row)
    return None


def find_name(imdb_id: str, **kw: Any) -> Optional[Name]:
    """Scan ``name.basics`` for one ``nm…`` id."""
    for row in stream_rows("name.basics", **kw):
        if row.get("nconst") == imdb_id:
            return row_to_name(row)
    return None
