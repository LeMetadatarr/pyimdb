# Provenance & licensing

`pyimdb` reads structured metadata from IMDb through three sources. Their terms
differ — know which path produced your data.

## Bulk datasets — PERSONAL & NON-COMMERCIAL USE ONLY

`https://datasets.imdbws.com/` (`title.basics`, `title.ratings`, `title.akas`,
`title.crew`, `title.episode`, `title.principals`, `name.basics`).

> These data are licensed by IMDb for **personal and non-commercial use only**.
> See <https://developer.imdb.com/non-commercial-datasets/>.

- Do **not** redistribute the dumps, or datasets derived from them,
  commercially.
- Any HF dataset built via `pyimdb.dataset` inherits this restriction. Carry
  the attribution required by IMDb in the dataset card:
  *"Information courtesy of IMDb (https://www.imdb.com). Used with permission."*
- This tool does **not** grant or imply any commercial redistribution right.

## Suggestion API

`https://v3.sg.media-imdb.com/suggestion/...` — IMDb's autocomplete service.
Used for resolving free-text queries to canonical ids. Fetch responsibly:
respect throttling (`pyimdb.set_delay`) and use only for legitimate metadata
cataloguing.

## Page crawl

`https://www.imdb.com/title/...` and `/name/...` — subject to IMDb's
Conditions of Use and a WAF that blocks automated access (HTTP 202). Only the
embedded structured metadata (schema.org `ld+json`, `__NEXT_DATA__`) is parsed.

## Scope

`pyimdb` scrapes **structured metadata only** (ids, titles, years, ratings,
credits) for cataloguing. It does **not** fetch, host, or redistribute media
files.
