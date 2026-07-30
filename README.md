# pyimdb

Python metadata client for IMDb. Resolves free-text queries to canonical IMDb
ids and pulls structured metadata.
It scrapes **structured metadata only**. It never scrapes media files.

Three data paths, in order of reliability:

| Path | What | Key? | Status |
| --- | --- | --- | --- |
| **Suggestion API** | `v3.sg.media-imdb.com` autocomplete, the search backbone | none | works |
| **Bulk datasets** | `datasets.imdbws.com` gzip TSV dumps, the dataset backbone, streamed | none | works |
| **Page crawl** | `www.imdb.com` title/name pages, ld+json + `__NEXT_DATA__` | needs solver | best-effort (WAF / HTTP 202) |

No OMDb / official IMDb API key is used or needed.

## Install

```bash
pip install -e .            # core
pip install -e .[stealth]   # + curl_cffi TLS impersonation
```

## Use

```python
import pyimdb

# search (reliable, no key)
for hit in pyimdb.search("inception"):
    print(hit.imdb_id, hit.year, hit.label)

# canonical id + external-id dict
hit = pyimdb.first("dune part two")
pyimdb.canonical_imdb_id(hit)      # "tt15239678"
pyimdb.hit_to_extra(hit)           # {"imdb_id": "tt15239678", ...}

# bulk datasets, streamed (never loads whole files)
for rating in pyimdb.stream_ratings(limit=10):
    print(rating.imdb_id, rating.average_rating, rating.num_votes)

# page crawl (best-effort, raises on WAF unless a solver is configured)
title = pyimdb.get_title("tt1375666")
```

## The WAF caveat

IMDb's WAF returns **HTTP 202** to bare requests, so the page crawl is gated.
Configure an external solver to clear it:

```bash
export PYIMDB_FLARESOLVERR_URL=http://localhost:8191
```

The suggestion API and bulk datasets are the working paths and cover almost all
metadata needs. See [`docs/page-crawl.md`](docs/page-crawl.md).

## Provenance / licence

The IMDb bulk datasets are **personal and non-commercial use only**. See
[`PROVENANCE.md`](PROVENANCE.md) and [`docs/dataset.md`](docs/dataset.md).

## Docs

- [Quickstart](docs/quickstart.md)
- [Search (suggestion API)](docs/search.md)
- [Bulk datasets](docs/bulk-datasets.md)
- [Page crawl & caveats](docs/page-crawl.md)
- [Models](docs/models.md)
- [IDs / external-id converters](docs/ids.md)
- [HF datasets](docs/dataset.md)
- [Reverse-engineered endpoints](docs/reverse-engineering.md)

## TODO

- Wire up CI via the `gh-automations` reusable workflows (no `.github/workflows`
  yet).
- Validate the page-crawl selectors against live HTML once a solver is wired in
  (currently UNVERIFIED, derived from the schema.org shapes).
- GraphQL enrichment path (`caching.graphql.imdb.com`, same WAF origin).
