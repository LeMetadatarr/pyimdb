# IDs and external-id converters

`pyimdb.ids` converts models into flat `str -> str` dicts of namespaced external
IDs, anchored on `imdb_id`, for cross-referencing across sources.

## The `imdb_id` anchor

The headline key is **`imdb_id`**, emitted for *both* titles (`tt…`) and
names (`nm…`). Nearly every other media-metadata source (TMDb, TVDB, Trakt,
Wikidata, and others) carries an IMDb id, so a clean `imdb_id` enables
cross-referencing across sources.

```python
import pyimdb

hit = pyimdb.first("dune part two")
pyimdb.canonical_imdb_id(hit)     # "tt15239678"
pyimdb.canonical_imdb_id("tt1")   # passthrough for raw ids
pyimdb.is_title_id("tt1")         # True
pyimdb.is_name_id("nm1")          # True
```

## Converters

```python
pyimdb.title_to_extra(title)   # tt… anchor + title surface
pyimdb.name_to_extra(name)     # nm… anchor + person surface
pyimdb.hit_to_extra(hit)       # works for title OR name hits
```

### Title keys

`imdb_id`, `imdb_url`, `imdb_title_type`, `imdb_primary_title`,
`imdb_original_title`, `imdb_year`, `imdb_end_year`, `imdb_runtime_minutes`,
`imdb_genres` (JSON array), `imdb_rating`, `imdb_votes`, `imdb_is_adult`,
`imdb_image_url`.

### Name keys

`imdb_id`, `imdb_url`, `imdb_name`, `imdb_birth_year`, `imdb_death_year`,
`imdb_professions` (JSON array), `imdb_known_for` (JSON array of `tt…`),
`imdb_image_url`.

### Hit keys

`hit_to_extra` sets the `imdb_id` anchor plus whatever the suggestion API gave:
`imdb_primary_title` / `imdb_name` (depending on the hit kind), `imdb_url`,
`imdb_title_type`, `imdb_year`, `imdb_end_year`, `imdb_image_url`, `imdb_stars`.

All scalar values are stringified (the `extra` key-space is string-valued).
List values are JSON-encoded.

---
[← Models](models.md) · [Home](../README.md) · [HF datasets →](dataset.md)
