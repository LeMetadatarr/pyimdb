# Models

Typed dataclasses in `pyimdb.models`. Fields mirror the bulk-dataset columns
and the suggestion-API hit shape, so a model can be filled from either source.
Every model carries the canonical `imdb_id`. All have `.to_dict()` (it drops
empty values, and enums serialize to their string value).

## Enums

- `TitleType`: `title.basics.titleType` values: `movie`, `short`, `tvSeries`,
  `tvEpisode`, `tvMiniSeries`, `tvMovie`, `tvSpecial`, `tvShort`, `tvPilot`,
  `video`, `videoGame`, `musicVideo`, `audiobook`, `podcastSeries`,
  `podcastEpisode`, `unknown`. Use `TitleType.coerce(s)` for safe parsing.
- `HitType`: the suggestion-API `qid` category: `movie`, `tvSeries`,
  `tvMiniSeries`, `tvEpisode`, `short`, `video`, `videoGame`, `name`,
  `unknown`.

## SearchHit

A suggestion-API result. `imdb_id`, `label`, `kind` (`HitType`), `title_type`
(raw `q`), `year`, `end_year`, `image_url`, `stars`, `rank`. Properties:
`is_title`, `is_name`, `url`.

## Title

`imdb_id`, `title_type` (`TitleType`), `primary_title`, `original_title`,
`is_adult`, `start_year`, `end_year`, `runtime_minutes`, `genres`. Optional
joins: `average_rating`, `num_votes`, `directors`/`writers` (nconst lists),
`image_url`. Property: `url`.

## Name

`imdb_id` (nconst), `primary_name`, `birth_year`, `death_year`,
`primary_professions`, `known_for_titles` (tconst list), `image_url`.
Property: `url`.

## Rating

`imdb_id`, `average_rating`, `num_votes`.

## Aka

A localized/alternate title. `imdb_id` (parent title), `ordering`, `title`,
`region`, `language`, `types`, `attributes`, `is_original_title`.

## Principal

A cast/crew credit. `imdb_id` (title), `name_id` (person), `ordering`,
`category`, `job`, `characters`.

## Episode

`imdb_id` (the episode), `series_id` (parent series), `season_number`,
`episode_number`.

---
[← Page crawl](page-crawl.md) · [Home](../README.md) · [IDs →](ids.md)
