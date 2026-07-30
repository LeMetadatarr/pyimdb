# Page crawl: best-effort, WAF-gated

`pyimdb.title.get_title(tt)` and `pyimdb.name.get_name(nm)` fetch
`https://www.imdb.com/title/<tt>/` and `/name/<nm>/` and parse the structured
metadata embedded in the page. This is the **least reliable** path.

## The WAF caveat

IMDb sits behind an Akamai/Cloudflare-style WAF that answers bare requests with
**HTTP 202** and a challenge stub, with no `ld+json` and no `__NEXT_DATA__`.
Verified live from this environment: plain `urllib`, `curl_cffi` TLS
impersonation, and an unconfigured `unblock_requests.CloudflareSession`
**all** receive 202.

So out of the box `get_title` / `get_name` raise `RuntimeError`. The suggestion
API and bulk datasets are the working paths and cover the vast majority of
metadata needs.

## Clearing the WAF (external solver)

To get live HTML you must route the transport through a solver that runs a real
browser. `pyimdb` uses `unblock_requests` with the `PYIMDB` env prefix:

```bash
export PYIMDB_FLARESOLVERR_URL=http://localhttp://localhost:8191
# optional:
export PYIMDB_FLARESOLVERR_TIMEOUT=60000      # ms
export PYIMDB_WAYBACK_FALLBACK=1              # fall back to the Internet Archive
```

With a solver reachable, `get_title` returns a populated `Title`.

## What gets parsed

Two JSON payloads in the page (not brittle CSS):

1. `<script type="application/ld+json">`: schema.org `Movie` / `TVSeries` /
   `Person`. Primary source for name, genres, runtime, `aggregateRating`,
   `datePublished`.
2. `__NEXT_DATA__`: the Next.js page-props blob (`extract_next_data`).

The GraphQL endpoint `https://caching.graphql.imdb.com/` is the same WAF-gated
origin and is left for a future enrichment path.

> **UNVERIFIED:** because the WAF blocks fetches from this environment, the
> selectors are derived from the published schema.org shapes, **not** from a
> cleared live fetch. Validate against real HTML before relying on the crawl.

## Parsing already-fetched HTML

If you obtain HTML another way, parse it directly (this part is fully tested
against a fixture):

```python
from pyimdb.title import parse_title, extract_ldjson, extract_next_data
title = parse_title(html, imdb_id="tt1375666")
```

---
[← Bulk datasets](bulk-datasets.md) · [Home](../README.md) · [Models →](models.md)
