# Quickstart

`pyimdb` is a metadata client for IMDb. It exposes three data paths:

| Path | Module | Reliability | Key? |
| --- | --- | --- | --- |
| Suggestion API | [`search`](search.md) | works | none |
| Bulk datasets | [`bulk`](bulk-datasets.md) | works | none |
| Page crawl | [`title`/`name`](page-crawl.md) | best-effort (WAF) | needs solver |

## Install

```bash
pip install -e .            # core (requests + unblock_requests)
pip install -e .[stealth]   # adds curl_cffi TLS impersonation
```

## Search (the reliable path)

```python
import pyimdb

for hit in pyimdb.search("inception"):
    print(hit.imdb_id, hit.kind.value, hit.year, hit.label)

pyimdb.search_titles("blade runner")   # tt… only
pyimdb.search_names("greta gerwig")    # nm… only
top = pyimdb.first("dune part two")    # best hit or None
```

Every hit carries the canonical `imdb_id` — see [ids / external-id converters](ids.md).

## Bulk datasets

```python
# stream — never loads the whole file
for rating in pyimdb.stream_ratings(limit=10):
    print(rating.imdb_id, rating.average_rating, rating.num_votes)
```

See [bulk-datasets](bulk-datasets.md) for the streaming model and cache.

## Page crawl (best-effort)

```python
try:
    title = pyimdb.get_title("tt1375666")
except RuntimeError as e:
    print(e)   # WAF (HTTP 202) — configure a solver, see page-crawl.md
```

## Models

All entities are typed dataclasses with `.to_dict()` — see [models](models.md).
