# Hugging Face datasets

`pyimdb.dataset` flattens the IMDb bulk dumps into tabular rows, one HF dataset
**config** per dump. Each config is a streaming row flattener over
[`pyimdb.bulk`](bulk-datasets.md). It never materializes a whole dump in
memory.

> ## Provenance & licence (read this first)
>
> The IMDb bulk datasets are licensed for **PERSONAL AND NON-COMMERCIAL USE
> ONLY**. See <https://developer.imdb.com/non-commercial-datasets/> and
> `PROVENANCE.md`. Any dataset built from these dumps inherits that restriction.
> **Do not publish or redistribute these datasets commercially**, and do not
> imply commercial redistribution rights. Carry the licence and attribution
> ("Information courtesy of IMDb (https://www.imdb.com). Used with permission.")
> in any dataset card.

## Configs

| config | source dump | join key | notable columns |
| --- | --- | --- | --- |
| `titles` | title.basics | `imdb_id` (tconst) | title_type, primary_title, start_year, genres |
| `names` | name.basics | `imdb_id` (nconst) | primary_name, birth_year, known_for_titles |
| `ratings` | title.ratings | `imdb_id` (tconst) | average_rating, num_votes |
| `principals` | title.principals | `imdb_id`×`name_id` | category, job, characters |
| `akas` | title.akas | `imdb_id` (titleId) | title, region, language |
| `crew` | title.crew | `imdb_id` (tconst) | directors, writers |
| `episodes` | title.episode | `imdb_id`×`series_id` | season_number, episode_number |

Every row carries `imdb_id`, so the configs join cleanly for cross-referencing
across sources.

## Streaming rows

```python
from pyimdb import dataset

for row in dataset.rows("ratings", limit=100):
    print(row)                       # {"imdb_id": ..., "average_rating": ...}

dataset.title_rows()
dataset.name_rows()
dataset.principal_rows()
dataset.aka_rows()
dataset.crew_rows()
dataset.episode_rows()
```

## Export to JSON Lines

```python
dataset.export_jsonl("ratings", "ratings.jsonl")          # one config
dataset.export_all("imdb_dataset", limit=1000)            # all seven configs
```

`export_jsonl` streams end to end (download → gzip → TSV → JSON line). Pass
`limit=N` to cap rows, or `path=` to read a specific local `.tsv.gz`.

## Building a `datasets.DatasetDict`

```python
from datasets import Dataset, DatasetDict
from pyimdb import dataset

dd = DatasetDict({
    cfg: Dataset.from_generator(lambda c=cfg: dataset.rows(c))
    for cfg in ("ratings", "titles")
})
```

---
[← IDs](ids.md) · [Home](../README.md) · [Reverse-engineered endpoints →](reverse-engineering.md)
