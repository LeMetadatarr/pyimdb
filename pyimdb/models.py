"""Typed dataclasses for IMDb entities.

The fields mirror the IMDb bulk-dataset columns (``datasets.imdbws.com``) and
the suggestion-API hit shape, so a model can be populated from either source.
Every model carries the canonical ``imdb_id`` (``tt…`` for titles / episodes,
``nm…`` for names) — the cross-reference anchor consumed by :mod:`pyimdb.ids`.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional


class TitleType(str, Enum):
    """``titleType`` values seen in ``title.basics.tsv``."""

    MOVIE = "movie"
    SHORT = "short"
    TV_SERIES = "tvSeries"
    TV_EPISODE = "tvEpisode"
    TV_MINI_SERIES = "tvMiniSeries"
    TV_MOVIE = "tvMovie"
    TV_SPECIAL = "tvSpecial"
    TV_SHORT = "tvShort"
    TV_PILOT = "tvPilot"
    VIDEO = "video"
    VIDEO_GAME = "videoGame"
    MUSIC_VIDEO = "musicVideo"
    AUDIOBOOK = "audiobook"
    PODCAST_SERIES = "podcastSeries"
    PODCAST_EPISODE = "podcastEpisode"
    UNKNOWN = "unknown"

    @classmethod
    def coerce(cls, value: Optional[str]) -> "TitleType":
        if not value:
            return cls.UNKNOWN
        try:
            return cls(value)
        except ValueError:
            return cls.UNKNOWN


class HitType(str, Enum):
    """The ``q``/``qid`` category on a suggestion-API hit."""

    MOVIE = "movie"
    TV_SERIES = "tvSeries"
    TV_MINI_SERIES = "tvMiniSeries"
    TV_EPISODE = "tvEpisode"
    SHORT = "short"
    VIDEO = "video"
    VIDEO_GAME = "videoGame"
    NAME = "name"
    UNKNOWN = "unknown"

    @classmethod
    def coerce(cls, value: Optional[str]) -> "HitType":
        if not value:
            return cls.UNKNOWN
        try:
            return cls(value)
        except ValueError:
            return cls.UNKNOWN


def _drop_none(d: dict) -> dict:
    return {k: v for k, v in d.items() if v not in (None, [], {})}


@dataclass
class SearchHit:
    """One result from the suggestion API.

    ``imdb_id`` is the raw ``tt…``/``nm…`` id. ``kind`` distinguishes a title
    hit from a name hit.
    """

    imdb_id: str
    label: str
    kind: HitType = HitType.UNKNOWN
    title_type: Optional[str] = None  # the raw `q` value, e.g. "feature"
    year: Optional[int] = None
    end_year: Optional[int] = None
    image_url: Optional[str] = None
    stars: List[str] = field(default_factory=list)  # `s` — known-for / cast
    rank: Optional[int] = None

    @property
    def is_name(self) -> bool:
        return self.imdb_id.startswith("nm")

    @property
    def is_title(self) -> bool:
        return self.imdb_id.startswith("tt")

    @property
    def url(self) -> str:
        seg = "name" if self.is_name else "title"
        return f"https://www.imdb.com/{seg}/{self.imdb_id}/"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["kind"] = self.kind.value
        return _drop_none(d)


@dataclass
class Rating:
    """A row of ``title.ratings.tsv``."""

    imdb_id: str
    average_rating: Optional[float] = None
    num_votes: Optional[int] = None

    def to_dict(self) -> dict:
        return _drop_none(asdict(self))


@dataclass
class Aka:
    """A localized/alternate title — a row of ``title.akas.tsv``.

    ``imdb_id`` is the parent title (the ``titleId`` column).
    """

    imdb_id: str
    ordering: Optional[int] = None
    title: Optional[str] = None
    region: Optional[str] = None
    language: Optional[str] = None
    types: List[str] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    is_original_title: Optional[bool] = None

    def to_dict(self) -> dict:
        return _drop_none(asdict(self))


@dataclass
class Principal:
    """A cast/crew credit — a row of ``title.principals.tsv``."""

    imdb_id: str  # the title (tconst)
    name_id: str  # the person (nconst)
    ordering: Optional[int] = None
    category: Optional[str] = None  # actor, director, writer, ...
    job: Optional[str] = None
    characters: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return _drop_none(asdict(self))


@dataclass
class Episode:
    """An episode↔series link — a row of ``title.episode.tsv``.

    ``imdb_id`` is the episode's own ``tt…``; ``series_id`` is its parent
    series.
    """

    imdb_id: str
    series_id: Optional[str] = None
    season_number: Optional[int] = None
    episode_number: Optional[int] = None

    def to_dict(self) -> dict:
        return _drop_none(asdict(self))


@dataclass
class Title:
    """A title — ``title.basics`` joined with optional ``ratings``/``crew``."""

    imdb_id: str
    title_type: TitleType = TitleType.UNKNOWN
    primary_title: Optional[str] = None
    original_title: Optional[str] = None
    is_adult: Optional[bool] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    runtime_minutes: Optional[int] = None
    genres: List[str] = field(default_factory=list)
    # enrichment (optional joins)
    average_rating: Optional[float] = None
    num_votes: Optional[int] = None
    directors: List[str] = field(default_factory=list)  # nconst ids
    writers: List[str] = field(default_factory=list)  # nconst ids
    image_url: Optional[str] = None

    @property
    def url(self) -> str:
        return f"https://www.imdb.com/title/{self.imdb_id}/"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["title_type"] = self.title_type.value
        return _drop_none(d)


@dataclass
class Name:
    """A person — a row of ``name.basics.tsv``."""

    imdb_id: str  # nconst
    primary_name: Optional[str] = None
    birth_year: Optional[int] = None
    death_year: Optional[int] = None
    primary_professions: List[str] = field(default_factory=list)
    known_for_titles: List[str] = field(default_factory=list)  # tconst ids
    image_url: Optional[str] = None

    @property
    def url(self) -> str:
        return f"https://www.imdb.com/name/{self.imdb_id}/"

    def to_dict(self) -> dict:
        return _drop_none(asdict(self))
