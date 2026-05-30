---
name: pyimdb
description: Query IMDb titles and people via live search, GraphQL detail, and offline bulk datasets so AI agents can deliver structured movie/show/person information to blind, low-vision, or voice-only users who cannot navigate imdb.com.
---
# pyimdb — IMDb for agents

## When to use

A user asks about a film, TV show, or person ("What year did Inception come out?", "Who played Hannibal Lecter?", "What's the rating for Breaking Bad?") and cannot or should not be sent to a visual website. The agent fetches structured data and speaks or summarises it.

## Install

```bash
pip install pyimdb
```

## Core operations

### `search(query, scope="all")` / `search_titles(query)` / `search_names(query)`

Live suggestion API — no key, not WAF-gated.

```python
import pyimdb
hits = pyimdb.search_titles("inception")
hit = hits[0]
# hit.id → "tt1375666", hit.label → "Inception", hit.year → 2010
```

Returns a list of `SearchHit`: `.id` (tt…/nm…), `.label`, `.year`, `.year_end`, `.hit_type` (`HitType.TITLE` / `HitType.NAME`), `.stars` (list of top cast names), `.image_url`.
Use `search_names("cillian murphy")` to resolve a person to their `nm…` id.

---

### `get_title_detail(imdb_id: str) → TitleDetail`

Live GraphQL — no key, no solver needed.

```python
detail = pyimdb.get_title_detail("tt1375666")
print(detail.title, detail.year, detail.rating, detail.votes)
print(detail.plot)
for c in detail.credits[:5]:
    print(c.category, c.name, c.characters)
```

Returns `TitleDetail` with fields: `.title`, `.year`, `.title_type`, `.runtime_seconds`, `.rating` (float), `.votes` (int), `.plot` (plain text), `.genres` (list[str]), `.credits` (list[`CreditEntry`]: `.name_id`, `.name`, `.category`, `.characters`), `.akas` (list[`AkaEntry`]: `.text`, `.country`, `.language`), `.certificates` (list[`CertificateEntry`]: `.rating`, `.country`), `.release_date`, `.is_adult`.

---

### `get_name_detail(imdb_id: str) → NameDetail`

Live GraphQL — no key, no solver needed.

```python
detail = pyimdb.get_name_detail("nm0000093")
print(detail.name, detail.birth_year)
for kf in detail.known_for:
    print(kf.title_id, kf.title, kf.year)
```

Returns `NameDetail` with: `.name`, `.birth_year`, `.death_year`, `.professions` (list[str]), `.bio` (plain text), `.known_for` (list[`KnownForEntry`]: `.title_id`, `.title`, `.year`, `.characters`).

---

### `first(query, scope="all") → SearchHit | None`

Convenience: top suggestion in one call.

```python
hit = pyimdb.first("the godfather", scope="titles")
detail = pyimdb.get_title_detail(hit.id)
```

---

### Bulk / offline datasets

Download IMDb's public TSV dumps and stream them locally — no key required, but a one-time download per dataset is needed.

```python
from pyimdb import bulk

# one-time download (cached under bulk.cache_dir())
bulk.download("title.basics")
bulk.download("title.ratings")

# stream all titles
for title in pyimdb.stream_titles():
    ...  # Title: .imdb_id, .primary_title, .start_year, .genres, .title_type

# stream ratings
for rating in pyimdb.stream_ratings():
    ...  # Rating: .imdb_id, .average_rating, .num_votes

# look up a single title by id (scans both basics + ratings)
title = pyimdb.bulk_find_title("tt0068646")
rating = pyimdb.find_rating("tt0068646")

# stream cast/crew links
for principal in pyimdb.stream_principals():
    ...  # Principal: .imdb_id, .name_id, .category, .characters

# stream names
for name in pyimdb.stream_names():
    ...  # Name: .name_id, .primary_name, .birth_year, .known_for_titles
```

Bulk datasets: `title.basics`, `title.ratings`, `title.akas`, `title.episode`, `title.principals`, `name.basics`.

---

## Access notes

- **`search` / `search_titles` / `search_names`** — plain HTTPS to IMDb's suggestion CDN; no key, no solver, instant.
- **`get_title_detail` / `get_name_detail`** — plain HTTPS POST to `caching.graphql.imdb.com`; no key, no solver needed (not WAF-gated as of writing).
- **`get_title` / `get_name`** (page crawl, not shown above) — WAF-gated (HTTP 202); needs a FlareSolverr solver at `http://localhost:8191` via the `PYIMDB` env var. Avoid unless GraphQL is insufficient.
- **Bulk datasets** — public TSV gzip files from `datasets.imdbws.com`; call `bulk.download(name)` once, then stream locally forever.

## Speaking the results (accessibility)

- **Lead with a one-line summary**: title, year, rating, and runtime — e.g. "Inception, 2010, rated 8.8 out of 10, two hours and 28 minutes."
- **Offer depth on request**: say "I can read you the plot, the director, or the main cast — just ask." Then pull from `detail.plot`, `detail.credits`.
- **Answer cast questions by name**: when a user asks "who played X", filter `detail.credits` by `.characters` containing the character name and read the actor's `.name`.
- **Support follow-ups via person detail**: once you have a cast member's `name_id`, call `get_name_detail` to answer "what else has she been in?" by reading `known_for` entries aloud.
