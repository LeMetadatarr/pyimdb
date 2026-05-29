"""Converters from pyimdb models to ``ExternalIds.extra`` dicts.

Consumed by the metadatarr provider and any integration that serialises pyimdb
data into the mediavocab ``ExternalIds.extra`` key-space.

The headline key is the canonical **``imdb_id``** — emitted for *both* titles
(``tt…``) and names (``nm…``). IMDb's id is the dominant cross-reference anchor
in metadatarr's dominant-ID chain: nearly every other media-metadata source
(TMDb, TVDB, Trakt, Wikidata, …) carries an IMDb id, so a clean ``imdb_id``
lets metadatarr fan a single pyimdb hit out to the rest of the graph.

Key namespaces
--------------
Title:
    ``imdb_id``                  — canonical ``tt…`` (the anchor)
    ``imdb_title_type``          — e.g. "movie", "tvSeries"
    ``imdb_primary_title``
    ``imdb_original_title``
    ``imdb_year``                — int start year
    ``imdb_end_year``            — int (series)
    ``imdb_runtime_minutes``     — int
    ``imdb_genres``              — JSON array
    ``imdb_rating``              — float average
    ``imdb_votes``               — int
    ``imdb_is_adult``            — "1" when adult
    ``imdb_url``
    ``imdb_image_url``

Name:
    ``imdb_id``                  — canonical ``nm…`` (the anchor)
    ``imdb_name``
    ``imdb_birth_year``          — int
    ``imdb_death_year``          — int
    ``imdb_professions``         — JSON array
    ``imdb_known_for``           — JSON array of ``tt…``
    ``imdb_url``
    ``imdb_image_url``
"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING, Optional, Union

if TYPE_CHECKING:
    from pyimdb.models import Name, SearchHit, Title


def canonical_imdb_id(obj: Union["Title", "Name", "SearchHit", str]) -> Optional[str]:
    """Return the canonical ``tt…``/``nm…`` id for a model or raw id string."""
    if isinstance(obj, str):
        s = obj.strip()
        return s or None
    return getattr(obj, "imdb_id", None) or None


def is_title_id(imdb_id: Optional[str]) -> bool:
    return bool(imdb_id) and imdb_id.startswith("tt")


def is_name_id(imdb_id: Optional[str]) -> bool:
    return bool(imdb_id) and imdb_id.startswith("nm")


def title_to_extra(title: "Title") -> dict:
    """Convert a :class:`~pyimdb.models.Title` to an ``extra`` dict."""
    extra: dict = {
        "imdb_id": title.imdb_id,
        "imdb_url": title.url,
    }
    if title.title_type:
        extra["imdb_title_type"] = title.title_type.value
    if title.primary_title:
        extra["imdb_primary_title"] = title.primary_title
    if title.original_title:
        extra["imdb_original_title"] = title.original_title
    if title.start_year is not None:
        extra["imdb_year"] = str(title.start_year)
    if title.end_year is not None:
        extra["imdb_end_year"] = str(title.end_year)
    if title.runtime_minutes is not None:
        extra["imdb_runtime_minutes"] = str(title.runtime_minutes)
    if title.genres:
        extra["imdb_genres"] = json.dumps(title.genres)
    if title.average_rating is not None:
        extra["imdb_rating"] = str(title.average_rating)
    if title.num_votes is not None:
        extra["imdb_votes"] = str(title.num_votes)
    if title.is_adult:
        extra["imdb_is_adult"] = "1"
    if title.image_url:
        extra["imdb_image_url"] = title.image_url
    return extra


def name_to_extra(name: "Name") -> dict:
    """Convert a :class:`~pyimdb.models.Name` to an ``extra`` dict."""
    extra: dict = {
        "imdb_id": name.imdb_id,
        "imdb_url": name.url,
    }
    if name.primary_name:
        extra["imdb_name"] = name.primary_name
    if name.birth_year is not None:
        extra["imdb_birth_year"] = str(name.birth_year)
    if name.death_year is not None:
        extra["imdb_death_year"] = str(name.death_year)
    if name.primary_professions:
        extra["imdb_professions"] = json.dumps(name.primary_professions)
    if name.known_for_titles:
        extra["imdb_known_for"] = json.dumps(name.known_for_titles)
    if name.image_url:
        extra["imdb_image_url"] = name.image_url
    return extra


def hit_to_extra(hit: "SearchHit") -> dict:
    """Convert a :class:`~pyimdb.models.SearchHit` to an ``extra`` dict.

    Works for both title and name hits — the ``imdb_id`` anchor is set either
    way, with the most useful surface fields the suggestion API exposes.
    """
    extra: dict = {
        "imdb_id": hit.imdb_id,
        "imdb_url": hit.url,
    }
    if hit.label:
        if hit.is_name:
            extra["imdb_name"] = hit.label
        else:
            extra["imdb_primary_title"] = hit.label
    if hit.title_type:
        extra["imdb_title_type"] = hit.title_type
    if hit.year is not None:
        extra["imdb_year"] = str(hit.year)
    if hit.end_year is not None:
        extra["imdb_end_year"] = str(hit.end_year)
    if hit.image_url:
        extra["imdb_image_url"] = hit.image_url
    if hit.stars:
        extra["imdb_stars"] = json.dumps(hit.stars)
    return extra
