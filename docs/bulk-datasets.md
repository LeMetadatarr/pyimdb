# Bulk datasets

The dataset backbone. IMDb publishes daily gzipped TSV dumps at
`https://datasets.imdbws.com/`. No key is required. The files are large
(`title.basics` is about 1.5 GB uncompressed, about 10M rows), so `pyimdb.bulk`
**streams** every file. It gzip-decompresses on the fly, and a `csv` reader
yields one row dict at a time. Nothing loads a whole file into memory.

> **Licence:** the IMDb datasets are for **personal and non-commercial use
> only**. See [dataset.md](dataset.md) and `PROVENANCE.md`. Do not redistribute
> commercially.

## The seven dumps

| name | file | model | id column |
| --- | --- | --- | --- |
| `title.basics` | title.basics.tsv.gz | `Title` | `tconst` |
| `title.ratings` | title.ratings.tsv.gz | `Rating` | `tconst` |
| `title.akas` | title.akas.tsv.gz | `Aka` | `titleId` |
| `title.crew` | title.crew.tsv.gz | (raw) | `tconst` |
| `title.episode` | title.episode.tsv.gz | `Episode` | `tconst` |
| `title.principals` | title.principals.tsv.gz | `Principal` | `tconst`×`nconst` |
| `name.basics` | name.basics.tsv.gz | `Name` | `nconst` |

IMDb encodes missing cells as `\N`. `pyimdb` decodes that to `None` / `[]`.

## Cache + download

Files cache under `~/.cache/pyimdb` (override with `PYIMDB_CACHE_DIR`) and are
fetched on demand the first time you stream them.

```python
from pyimdb import bulk

bulk.download("title.ratings")          # idempotent, streams to disk
bulk.local_path("title.ratings")        # cache path
bulk.cache_dir()                        # the cache directory
```

## Streaming

```python
import pyimdb

# typed streams (one model per row)
for r in pyimdb.stream_ratings(limit=10): ...
for t in pyimdb.stream_titles(): ...
for n in pyimdb.stream_names(): ...
pyimdb.stream_akas()
pyimdb.stream_episodes()
pyimdb.stream_principals()

# raw row dicts (keyed by TSV header)
for row in pyimdb.stream_rows("title.crew"): ...
```

Every stream takes `limit=N` (cap rows, useful for sampling),
`download_if_missing=False` (fail instead of fetching), and `path=` (read a
specific local `.tsv.gz`, for example a test fixture).

## Lookups

A lookup does a linear scan over a dump. This is fine for a one-off, but
prefer the [suggestion API](search.md) when you only need a label:

```python
pyimdb.bulk_find_title("tt1375666")   # Title (+ rating joined)
pyimdb.find_rating("tt1375666")       # Rating
pyimdb.bulk_find_name("nm0634240")    # Name
```

## Streaming joins

To attach ratings to titles without loading either dump whole, build a bounded
index from one stream and consult it while streaming the other. See
`examples/07_top_rated_movies.py`.

---
[← Search](search.md) · [Home](../README.md) · [Page crawl →](page-crawl.md)
