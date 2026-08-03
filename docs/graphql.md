# GraphQL: rich live detail

`pyimdb.get_title_detail` / `pyimdb.get_name_detail` call IMDb's private
GraphQL endpoint at `caching.graphql.imdb.com`. It needs no API key and is not
WAF-gated, so it is the reliable path for detail — cast with character names,
plot, localized titles, certificates, and biography — beyond what the
suggestion API or bulk datasets carry.

See [reverse-engineered endpoints](reverse-engineering.md#4-private-graphql-cachinggraphqlimdbcom)
for the raw request/response shapes this module builds on.

## Title detail

```python
import pyimdb

detail = pyimdb.get_title_detail("tt1375666")
print(detail.primary_title, detail.start_year, detail.average_rating, detail.num_votes)
print(detail.plot)
for c in detail.credits[:5]:
    print(c.category, c.name, c.characters)
```

`get_title_detail(imdb_id)` returns a [`TitleDetail`](#titledetail-fields).

### `TitleDetail` fields

| Field | Type | Notes |
| --- | --- | --- |
| `imdb_id` | `str` | canonical `tt…` |
| `title_type` | `str` | raw type id, e.g. `movie` |
| `title_type_text` | `str` | display label, e.g. `Movie` |
| `primary_title` | `Optional[str]` | |
| `start_year` | `Optional[int]` | |
| `end_year` | `Optional[int]` | series end year |
| `runtime_seconds` | `Optional[int]` | see also `.runtime_minutes` property |
| `average_rating` | `Optional[float]` | |
| `num_votes` | `Optional[int]` | |
| `plot` | `Optional[str]` | plain text |
| `genres` | `List[str]` | |
| `image_url` / `image_width` / `image_height` | | primary poster image |
| `is_adult` | `Optional[bool]` | |
| `release_day` / `release_month` / `release_year` / `release_country` | | |
| `credits` | `List[CreditEntry]` | `.name_id`, `.name`, `.category`, `.characters` |
| `akas` | `List[AkaEntry]` | `.text`, `.country_id`, `.country`, `.language_id`, `.language` |
| `certificates` | `List[CertificateEntry]` | `.rating`, `.country_id`, `.country`, `.rating_reason` |

Convenience properties: `.runtime_minutes`, `.directors`, `.writers`, `.cast`
(each filters `.credits` by category), `.url`. `.to_title()` downcasts to the
flat [`Title`](models.md) model. `.to_dict()` serializes recursively.

## Name detail

```python
import pyimdb

person = pyimdb.get_name_detail("nm0000093")
print(person.primary_name, person.birth_year)
for kf in person.known_for:
    print(kf.imdb_id, kf.title, kf.year)
```

`get_name_detail(imdb_id)` returns a [`NameDetail`](#namedetail-fields).

### `NameDetail` fields

| Field | Type | Notes |
| --- | --- | --- |
| `imdb_id` | `str` | canonical `nm…` |
| `primary_name` | `Optional[str]` | |
| `birth_year` / `birth_month` / `birth_day` | | |
| `death_year` / `death_month` / `death_day` | | |
| `primary_professions` | `List[str]` | |
| `image_url` / `image_width` / `image_height` | | primary headshot |
| `known_for` | `List[KnownForEntry]` | `.imdb_id`, `.title`, `.year` |
| `bio` | `Optional[str]` | plain text |

`.to_name()` downcasts to the flat [`Name`](models.md) model. `.to_dict()`
serializes recursively.

## Errors

`get_title_detail` / `get_name_detail` raise `requests.HTTPError` on a
non-2xx response and `ValueError` if the API returns no data for the id
(e.g. an id that does not exist).

---
[← Search](search.md) · [Home](../README.md) · [Bulk datasets →](bulk-datasets.md)
