# Search: the suggestion API

The search backbone is IMDb's suggestion service. It needs no API key and is
not WAF-gated, so it is the reliable path for resolving a free-text query to a
canonical `imdb_id`.

## Endpoints

```
https://v3.sg.media-imdb.com/suggestion/x/<query>.json          # titles + names
https://v3.sg.media-imdb.com/suggestion/titles/x/<query>.json    # titles only
https://v3.sg.media-imdb.com/suggestion/names/x/<query>.json     # names only
```

`<query>` is lower-cased and URL-encoded. The response is
`{"d": [...hits...], "q": "...", "v": 1}`.

## Hit fields

Each entry in `d` maps onto a [`SearchHit`](models.md):

| JSON | SearchHit | meaning |
| --- | --- | --- |
| `id` | `imdb_id` | `tt…` (title) or `nm…` (name) |
| `l` | `label` | display label |
| `q` | `title_type` | raw type string, e.g. `feature` |
| `qid` | `kind` | `HitType` enum (`movie`, `tvSeries`, `name`, …) |
| `y` | `year` | release / start year |
| `yr` | `year` + `end_year` | range string `2011-2019` for series |
| `i` | `image_url` | poster / headshot |
| `s` | `stars` | known-for / top cast |

## API

```python
import pyimdb

pyimdb.search(query, scope="all")    # list[SearchHit], rank order
pyimdb.search_titles(query)          # tt… hits only
pyimdb.search_names(query)           # nm… hits only
pyimdb.first(query)                  # top hit or None
```

`scope` is `"all"`, `"titles"` or `"names"`. The general `/suggestion/x/`
endpoint can also return company (`co…`) and keyword (`in…`) ids, preserved
verbatim in `imdb_id`. Filter on `hit.is_title` / `hit.is_name` if you only
want titles or people.

## Notes

- Results are capped by IMDb (typically about 8 hits): it is a *suggestion*
  engine, not a full search index. For exhaustive enumeration use the
  [bulk datasets](bulk-datasets.md).
- Throttling is shared with the rest of the transport, tuned with
  `pyimdb.set_delay(seconds)`.

---
[← Quickstart](quickstart.md) · [Home](../README.md) · [GraphQL →](graphql.md)
