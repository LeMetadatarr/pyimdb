"""Flat, tabular rows from the IMDb bulk dumps for Hugging Face datasets.

One config per dump, each a streaming row flattener over :mod:`pyimdb.bulk`:

==============  ============================  ====================================
config          source dump                   join key
==============  ============================  ====================================
``titles``      title.basics (+ratings)       ``imdb_id`` (tconst)
``names``       name.basics                   ``imdb_id`` (nconst)
``ratings``     title.ratings                 ``imdb_id`` (tconst)
``principals``  title.principals              ``imdb_id`` × ``name_id``
``akas``        title.akas                    ``imdb_id`` (titleId)
``crew``        title.crew                    ``imdb_id`` (tconst)
``episodes``    title.episode                 ``imdb_id`` × ``series_id``
==============  ============================  ====================================

Every row carries ``imdb_id`` so the configs join cleanly for cross-referencing
across sources.

PROVENANCE: IMDb bulk datasets are **personal / non-commercial use only**. See
``PROVENANCE.md`` and ``docs/dataset.md``. Do not redistribute commercially.
"""
from __future__ import annotations

import json
from typing import Any, Dict, Iterable, Iterator, Optional

from pyimdb import bulk
from pyimdb._clean import to_int, tsv_list, tsv_value

CONFIGS = ("titles", "names", "ratings", "principals", "akas", "crew", "episodes")


# ---- per-config row flatteners ----------------------------------------

def title_rows(*, limit: Optional[int] = None, **kw: Any) -> Iterator[Dict[str, Any]]:
    for t in bulk.stream_titles(limit=limit, **kw):
        yield {
            "imdb_id": t.imdb_id,
            "title_type": t.title_type.value,
            "primary_title": t.primary_title,
            "original_title": t.original_title,
            "is_adult": bool(t.is_adult),
            "start_year": t.start_year,
            "end_year": t.end_year,
            "runtime_minutes": t.runtime_minutes,
            "genres": t.genres,
        }


def name_rows(*, limit: Optional[int] = None, **kw: Any) -> Iterator[Dict[str, Any]]:
    for n in bulk.stream_names(limit=limit, **kw):
        yield {
            "imdb_id": n.imdb_id,
            "primary_name": n.primary_name,
            "birth_year": n.birth_year,
            "death_year": n.death_year,
            "primary_professions": n.primary_professions,
            "known_for_titles": n.known_for_titles,
        }


def rating_rows(*, limit: Optional[int] = None, **kw: Any) -> Iterator[Dict[str, Any]]:
    for r in bulk.stream_ratings(limit=limit, **kw):
        yield {
            "imdb_id": r.imdb_id,
            "average_rating": r.average_rating,
            "num_votes": r.num_votes,
        }


def principal_rows(*, limit: Optional[int] = None, **kw: Any) -> Iterator[Dict[str, Any]]:
    for p in bulk.stream_principals(limit=limit, **kw):
        yield {
            "imdb_id": p.imdb_id,
            "name_id": p.name_id,
            "ordering": p.ordering,
            "category": p.category,
            "job": p.job,
            "characters": p.characters,
        }


def aka_rows(*, limit: Optional[int] = None, **kw: Any) -> Iterator[Dict[str, Any]]:
    for a in bulk.stream_akas(limit=limit, **kw):
        yield {
            "imdb_id": a.imdb_id,
            "ordering": a.ordering,
            "title": a.title,
            "region": a.region,
            "language": a.language,
            "types": a.types,
            "attributes": a.attributes,
            "is_original_title": a.is_original_title,
        }


def crew_rows(*, limit: Optional[int] = None, **kw: Any) -> Iterator[Dict[str, Any]]:
    # title.crew has its own shape (directors/writers as nconst lists).
    for row in bulk.stream_rows("title.crew", limit=limit, **kw):
        yield {
            "imdb_id": tsv_value(row.get("tconst")) or "",
            "directors": tsv_list(row.get("directors")),
            "writers": tsv_list(row.get("writers")),
        }


def episode_rows(*, limit: Optional[int] = None, **kw: Any) -> Iterator[Dict[str, Any]]:
    for e in bulk.stream_episodes(limit=limit, **kw):
        yield {
            "imdb_id": e.imdb_id,
            "series_id": e.series_id,
            "season_number": e.season_number,
            "episode_number": e.episode_number,
        }


_ROW_FUNCS = {
    "titles": title_rows,
    "names": name_rows,
    "ratings": rating_rows,
    "principals": principal_rows,
    "akas": aka_rows,
    "crew": crew_rows,
    "episodes": episode_rows,
}


def rows(config: str, **kw: Any) -> Iterator[Dict[str, Any]]:
    """Stream flat rows for a named *config* (one of :data:`CONFIGS`)."""
    if config not in _ROW_FUNCS:
        raise ValueError(f"unknown config {config!r}; choose from {CONFIGS}")
    return _ROW_FUNCS[config](**kw)


def export_jsonl(config: str, out_path: str, **kw: Any) -> int:
    """Stream a *config* to a JSON Lines file; return the row count written.

    Streams end-to-end (download→gzip→TSV→json line) — never materialises the
    whole dataset in memory. Pass ``limit=N`` to cap rows. Extra kwargs (e.g.
    ``path=`` to read a specific local dump) flow through to the row stream.
    """
    n = 0
    with open(out_path, "w", encoding="utf-8") as fh:
        for row in rows(config, **kw):
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
    return n


def export_all(out_dir: str, configs: Iterable[str] = CONFIGS, **kw: Any) -> Dict[str, int]:
    """Export several configs to ``<out_dir>/<config>.jsonl``; return counts."""
    import os

    os.makedirs(out_dir, exist_ok=True)
    counts: Dict[str, int] = {}
    for cfg in configs:
        counts[cfg] = export_jsonl(cfg, os.path.join(out_dir, f"{cfg}.jsonl"), **kw)
    return counts
