# Reverse-engineered IMDb endpoints

This page documents the undocumented (private/unofficial) IMDb endpoints that
pyimdb targets, and distinguishes them from IMDb's official, documented data paths.
Everything here is derived directly from the client source; no endpoint or field
is speculative.

---

## 1. Suggestion API — `v3.sg.media-imdb.com`

### Status

Undocumented. This is IMDb's own autocomplete backend, exposed to the browser's
search box. There is no public contract, no versioning guarantee, and no API key
mechanism.

### URL scheme

```
https://v3.sg.media-imdb.com/suggestion/x/<query>.json          # titles + names + other
https://v3.sg.media-imdb.com/suggestion/titles/x/<query>.json    # titles only
https://v3.sg.media-imdb.com/suggestion/names/x/<query>.json     # names only
```

The `x` path segment is a fixed shard letter that appears in every observed URL
(`/suggestion/x/`, `/suggestion/titles/x/`, `/suggestion/names/x/`). IMDb's own
front-end does not vary this letter in practice; the client hard-codes `x` for all
three scopes (see `pyimdb/search.py: _suggest_url`).

`<query>` is lower-cased and percent-encoded (`urllib.parse.quote`). No other query
parameters are sent.

### Response shape

```json
{
  "d": [ <hit>, ... ],
  "q": "<echo of query>",
  "v": 1
}
```

`d` is the hit list (typically up to ~8 entries); `v` is an opaque schema version
(always `1` in observed responses). The top-level object may also carry `"e"` on
error or empty results.

Each hit object:

| Field | Type | Meaning |
| --- | --- | --- |
| `id` | string | Canonical IMDb id: `tt…` (title), `nm…` (name), `co…` (company), `in…` (keyword) |
| `l` | string | Display label (title or person name) |
| `q` | string | Raw type string, e.g. `feature`, `TV series` |
| `qid` | string | Machine type token, e.g. `movie`, `tvSeries`, `tvEpisode`, `name` |
| `y` | int | Release year (single year or series start year) |
| `yr` | string | Year range for series, e.g. `"2011-2019"`; absent for movies |
| `i` | object or list | Image: `{"imageUrl": "...", ...}` or legacy `[url, w, h]` tuple |
| `s` | string or list | Known-for / top cast, comma-separated string or list |

The client maps these onto `SearchHit` in `pyimdb/search.py: hit_from_json`.

### What the client does with it

`pyimdb.search(query, scope)` builds the URL, fetches it unauthenticated, and
iterates `data["d"]`. Hits that lack an `id` field are dropped. The result list
preserves rank order from the API response.

### Why it is the reliable path

The suggestion service is not WAF-gated and requires no credentials. From the
`pyimdb/transport.py` docstring: the endpoint "answers bare requests with no
challenge." It is therefore the preferred resolution path when all you need is a
canonical id or basic metadata for a known-name query.

---

## 2. IMDb title and name pages — `www.imdb.com`

### Status

Publicly accessible HTML, but gated by an **Akamai WAF** (also described in
`pyimdb/title.py` and `pyimdb/name.py` as "Akamai/Cloudflare-style"). This is not
a private API — the page content is public — but the WAF makes programmatic
access unreliable without an external solver.

### URLs

```
https://www.imdb.com/title/<tt…>/
https://www.imdb.com/name/<nm…>/
```

### WAF behaviour — **UNVERIFIED LIVE**

From `pyimdb/title.py`:

> Verified live from this environment: plain `urllib`, `curl_cffi` impersonation,
> and an unconfigured `CloudflareSession` all receive 202.

The WAF returns **HTTP 202** with a JavaScript challenge stub. The stub contains
no `application/ld+json` script tag and no `__NEXT_DATA__` blob — the two payloads
the parsers target. The `is_blocked` heuristic in `pyimdb/title.py` detects this by
looking for challenge markers (`just a moment`, `challenge-platform`, `cf-mitigated`,
`/errors/`) and by the absence of both payloads.

To get live HTML you must route the transport through FlareSolverr:

```bash
export PYIMDB_FLARESOLVERR_URL=http://localhost:8191
```

### What the client parses (when it gets real HTML)

The parsers target two embedded JSON payloads — **not** brittle CSS selectors:

1. **`<script type="application/ld+json">`** — schema.org `Movie` / `TVSeries` /
   `Person` object embedded in the page. Fields used:
   - title page: `@type`, `name`, `alternateName`, `duration` (ISO-8601),
     `genre`, `image`, `aggregateRating.ratingValue`,
     `aggregateRating.ratingCount`, `datePublished`, `url`
   - name page: `name`, `birthDate`, `deathDate`, `jobTitle`, `image`, `url`,
     `knownFor`, `performerIn`, `sameAs`

2. **`__NEXT_DATA__`** — Next.js page props blob embedded in a `<script
   id="__NEXT_DATA__">` tag. Parsed but not yet used for field extraction (reserved
   for future enrichment).

The parsers (`pyimdb/title.py: parse_title`, `pyimdb/name.py: parse_name`) are
derived from the schema.org shapes and are **UNVERIFIED against live IMDb HTML**
because the WAF blocks fetches in the development environment.

### Caveat

The page-crawl path raises `RuntimeError` immediately if `is_blocked` returns
`True`. For production use, prefer the suggestion API and bulk datasets.

---

## 3. Official bulk datasets — `datasets.imdbws.com`

### Status

**Documented and officially supported.** This is the public data path. IMDb
publishes these dumps at `https://developer.imdb.com/non-commercial-datasets/`.

### Files

```
https://datasets.imdbws.com/title.basics.tsv.gz
https://datasets.imdbws.com/title.ratings.tsv.gz
https://datasets.imdbws.com/title.akas.tsv.gz
https://datasets.imdbws.com/title.crew.tsv.gz
https://datasets.imdbws.com/title.episode.tsv.gz
https://datasets.imdbws.com/title.principals.tsv.gz
https://datasets.imdbws.com/name.basics.tsv.gz
```

Gzip-compressed tab-separated values. No key required. Licensed for
**personal and non-commercial use only** — see `PROVENANCE.md` and
`docs/dataset.md`.

The client streams these files one row at a time via `pyimdb/bulk.py:
stream_rows`; nothing is loaded entirely into memory.

---

## 4. Private GraphQL — `caching.graphql.imdb.com`

### Status

**Active — verified live.** IMDb's web app sends GraphQL queries to this
endpoint. It accepts raw POST requests with no authentication token and is
**not WAF-gated** — plain HTTPS works without any solver.

Implemented in `pyimdb/graphql.py`.

### Endpoint

```
POST https://caching.graphql.imdb.com/
```

### Required headers

```
accept:               application/graphql+json, application/json
content-type:         application/json
origin:               https://www.imdb.com
referer:              https://www.imdb.com/
x-imdb-client-name:  imdb-web-next
x-imdb-user-language: en-US
x-imdb-user-country: US
```

The `origin` + `referer` headers appear to be the access gate — requests
without them (or with wrong values) are blocked by Amazon Midway auth.

### Request shape

```json
{
  "query": "...",
  "variables": { "id": "tt0111161" }
}
```

IMDb's own web app also sends GET requests with
`?operationName=…&extensions={"persistedQuery":{"sha256Hash":"…"}}` for
cached (persisted) queries. The raw POST approach used here does not
require knowing the hash — the endpoint accepts any valid query string.

### Title detail — `TitleDetail`

Operation name used internally: `TitleDetail`. Fields retrieved and verified:

| GraphQL field | Model field | Notes |
| --- | --- | --- |
| `title.id` | `imdb_id` | `tt…` |
| `title.titleText.text` | `primary_title` | |
| `title.titleType.id` | `title_type` | `"movie"`, `"tvSeries"`, … |
| `title.titleType.text` | `title_type_text` | human label |
| `title.releaseYear.year` | `start_year` | |
| `title.releaseYear.endYear` | `end_year` | series only |
| `title.runtime.seconds` | `runtime_seconds` | divide by 60 for minutes |
| `title.ratingsSummary.aggregateRating` | `average_rating` | |
| `title.ratingsSummary.voteCount` | `num_votes` | |
| `title.plot.plotText.plainText` | `plot` | short synopsis |
| `title.genres.genres[].text` | `genres` | list of strings |
| `title.primaryImage.{url,width,height}` | `image_url`, `image_width`, `image_height` | |
| `title.isAdult` | `is_adult` | bool |
| `title.releaseDate.{day,month,year}` | `release_day/month/year` | |
| `title.releaseDate.country.text` | `release_country` | |
| `title.principalCredits[].category.id` + `.credits[].name` | `credits` (→ `CreditEntry`) | directors, writers, cast |
| Cast `... on Cast { characters }` | `CreditEntry.characters` | character names via inline fragment |
| `title.akas(first: N).edges[].node` | `akas` (→ `AkaEntry`) | text, country, language |
| `title.certificates(first: N).edges[].node` | `certificates` (→ `CertificateEntry`) | rating + country |

Connections that require pagination (`akas`, `certificates`, `principalCredits`)
require the `first` or `last` parameter.  The `Cast` type is a union member, so
`characters` must be accessed via an inline fragment `... on Cast { characters { name } }`.

### Name detail — `NameDetail`

Operation name: `NameDetail`. Fields retrieved and verified:

| GraphQL field | Model field |
| --- | --- |
| `name.id` | `imdb_id` |
| `name.nameText.text` | `primary_name` |
| `name.birthDate.dateComponents.{year,month,day}` | `birth_year/month/day` |
| `name.deathDate.dateComponents.{year,month,day}` | `death_year/month/day` |
| `name.primaryProfessions[].category.text` | `primary_professions` |
| `name.primaryImage.{url,width,height}` | `image_url/width/height` |
| `name.knownFor(first: N).edges[].node.title` | `known_for` (→ `KnownForEntry`) |
| `name.bio.text.plainText` | `bio` |

### Response example (abridged)

```json
{
  "data": {
    "title": {
      "id": "tt0111161",
      "titleText": { "text": "The Shawshank Redemption" },
      "titleType": { "id": "movie", "text": "Movie" },
      "releaseYear": { "year": 1994, "endYear": null },
      "runtime": { "seconds": 8520 },
      "ratingsSummary": { "aggregateRating": 9.3, "voteCount": 3192642 },
      "plot": { "plotText": { "plainText": "A wrongfully convicted banker…" } },
      "genres": { "genres": [{ "text": "Drama" }] },
      "principalCredits": [
        {
          "category": { "id": "director", "text": "Director" },
          "credits": [{ "name": { "id": "nm0001104", "nameText": { "text": "Frank Darabont" } } }]
        },
        {
          "category": { "id": "cast", "text": "Stars" },
          "credits": [
            {
              "name": { "id": "nm0000209", "nameText": { "text": "Tim Robbins" } },
              "characters": [{ "name": "Andy Dufresne" }]
            }
          ]
        }
      ]
    }
  }
}
```

Full responses are saved as offline test fixtures in `tests/fixtures/`:
- `graphql_title_tt0111161.json` — The Shawshank Redemption
- `graphql_title_tt1375666.json` — Inception
- `graphql_name_nm0000151.json` — Morgan Freeman

---

## Summary table

| Endpoint | Documented? | Key? | WAF? | pyimdb status |
| --- | --- | --- | --- | --- |
| `v3.sg.media-imdb.com/suggestion/…` | No — private autocomplete backend | None | None | **Active — reliable** |
| `caching.graphql.imdb.com` | No — private GraphQL | None (origin header gate) | None | **Active — verified live** |
| `www.imdb.com/title/<tt>/` | Public HTML | None | AWS WAF (HTTP 202) | Active — best-effort, solver needed |
| `www.imdb.com/name/<nm>/` | Public HTML | None | AWS WAF (HTTP 202) | Active — best-effort, solver needed |
| `datasets.imdbws.com/*.tsv.gz` | **Yes — official** | None | None | **Active — reliable** |
