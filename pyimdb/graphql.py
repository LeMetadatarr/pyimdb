"""Live detail via IMDb's private GraphQL API — ``caching.graphql.imdb.com``.

IMDb's web app sends POST requests with raw GraphQL queries (or GET with
``extensions.persistedQuery.sha256Hash`` for persisted queries) to::

    https://caching.graphql.imdb.com/

The endpoint requires **no authentication token** — it relies on the
``origin`` / ``referer`` headers matching ``https://www.imdb.com`` and
the ``x-imdb-client-name`` header being set.  It is **not WAF-gated**:
plain HTTPS POST works without any solver.

**POST shape** (used here — no persisted hash needed)::

    POST https://caching.graphql.imdb.com/
    Content-Type: application/json
    origin: https://www.imdb.com
    referer: https://www.imdb.com/
    x-imdb-client-name: imdb-web-next
    x-imdb-user-language: en-US
    x-imdb-user-country: US

    {"query": "...", "variables": {"id": "tt0111161"}}

**Title detail** fields returned:
``id``, ``titleText``, ``titleType``, ``releaseYear``, ``runtime``
(seconds), ``ratingsSummary`` (aggregateRating, voteCount), ``plot``
(plainText), ``genres``, ``primaryImage`` (url, width, height),
``principalCredits`` (director/writer/cast with character names),
``akas`` (text, country, language), ``certificates`` (rating, country),
``isAdult``, ``releaseDate``.

**Name detail** fields returned:
``id``, ``nameText``, ``birthDate`` (year/month/day), ``deathDate``,
``primaryProfessions``, ``primaryImage``, ``knownFor`` (first 5 titles),
``bio`` (plainText).

Both endpoints are **verified live** against ``caching.graphql.imdb.com``
(direct HTTPS POST, no solver).  See ``docs/reverse-engineering.md`` for
the full response shapes with example payloads.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from pyimdb import transport
from pyimdb.models import (
    Name,
    Title,
    TitleType,
    _drop_none,
)

# ─── GraphQL headers ────────────────────────────────────────────────────────

_GQL_HEADERS = {
    "accept": "application/graphql+json, application/json",
    "content-type": "application/json",
    "origin": "https://www.imdb.com",
    "referer": "https://www.imdb.com/",
    "x-imdb-client-name": "imdb-web-next",
    "x-imdb-user-language": "en-US",
    "x-imdb-user-country": "US",
}

# ─── Rich detail models ──────────────────────────────────────────────────────


@dataclass
class CreditEntry:
    """One principal credit (cast, director, writer)."""

    name_id: str
    name: str
    category: str  # "director" | "writer" | "cast" | …
    characters: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return _drop_none(asdict(self))


@dataclass
class AkaEntry:
    """One localized title from the GraphQL ``akas`` connection."""

    text: str
    country_id: Optional[str] = None
    country: Optional[str] = None
    language_id: Optional[str] = None
    language: Optional[str] = None

    def to_dict(self) -> dict:
        return _drop_none(asdict(self))


@dataclass
class CertificateEntry:
    """One content rating (certificate) from the GraphQL API."""

    rating: str
    country_id: Optional[str] = None
    country: Optional[str] = None
    rating_reason: Optional[str] = None

    def to_dict(self) -> dict:
        return _drop_none(asdict(self))


@dataclass
class TitleDetail:
    """Rich title detail fetched from the GraphQL API.

    Extends the flat :class:`~pyimdb.models.Title` with live fields not
    available from the bulk datasets:  character names in cast credits,
    localized titles (akas), content certificates, plot text, and release
    date.
    """

    imdb_id: str
    title_type: str = ""
    title_type_text: str = ""
    primary_title: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    runtime_seconds: Optional[int] = None
    average_rating: Optional[float] = None
    num_votes: Optional[int] = None
    plot: Optional[str] = None
    genres: List[str] = field(default_factory=list)
    image_url: Optional[str] = None
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    is_adult: Optional[bool] = None
    release_day: Optional[int] = None
    release_month: Optional[int] = None
    release_year: Optional[int] = None
    release_country: Optional[str] = None
    credits: List[CreditEntry] = field(default_factory=list)
    akas: List[AkaEntry] = field(default_factory=list)
    certificates: List[CertificateEntry] = field(default_factory=list)

    @property
    def runtime_minutes(self) -> Optional[int]:
        if self.runtime_seconds is not None:
            return self.runtime_seconds // 60
        return None

    @property
    def directors(self) -> List[CreditEntry]:
        return [c for c in self.credits if c.category == "director"]

    @property
    def writers(self) -> List[CreditEntry]:
        return [c for c in self.credits if c.category == "writer"]

    @property
    def cast(self) -> List[CreditEntry]:
        return [c for c in self.credits if c.category == "cast"]

    @property
    def url(self) -> str:
        return f"https://www.imdb.com/title/{self.imdb_id}/"

    def to_title(self) -> Title:
        """Downcast to the base :class:`~pyimdb.models.Title` model."""
        return Title(
            imdb_id=self.imdb_id,
            title_type=TitleType.coerce(self.title_type),
            primary_title=self.primary_title,
            original_title=self.primary_title,
            is_adult=self.is_adult,
            start_year=self.start_year,
            end_year=self.end_year,
            runtime_minutes=self.runtime_minutes,
            genres=list(self.genres),
            average_rating=self.average_rating,
            num_votes=self.num_votes,
            directors=[c.name_id for c in self.directors],
            writers=[c.name_id for c in self.writers],
            image_url=self.image_url,
        )

    def to_dict(self) -> dict:
        d = asdict(self)
        d["credits"] = [c.to_dict() for c in self.credits]
        d["akas"] = [a.to_dict() for a in self.akas]
        d["certificates"] = [c.to_dict() for c in self.certificates]
        return _drop_none(d)


@dataclass
class KnownForEntry:
    """One «known for» title on a name detail."""

    imdb_id: str
    title: Optional[str] = None
    year: Optional[int] = None

    def to_dict(self) -> dict:
        return _drop_none(asdict(self))


@dataclass
class NameDetail:
    """Rich person detail fetched from the GraphQL API."""

    imdb_id: str
    primary_name: Optional[str] = None
    birth_year: Optional[int] = None
    birth_month: Optional[int] = None
    birth_day: Optional[int] = None
    death_year: Optional[int] = None
    death_month: Optional[int] = None
    death_day: Optional[int] = None
    primary_professions: List[str] = field(default_factory=list)
    image_url: Optional[str] = None
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    known_for: List[KnownForEntry] = field(default_factory=list)
    bio: Optional[str] = None

    @property
    def url(self) -> str:
        return f"https://www.imdb.com/name/{self.imdb_id}/"

    def to_name(self) -> Name:
        """Downcast to the base :class:`~pyimdb.models.Name` model."""
        return Name(
            imdb_id=self.imdb_id,
            primary_name=self.primary_name,
            birth_year=self.birth_year,
            death_year=self.death_year,
            primary_professions=list(self.primary_professions),
            known_for_titles=[k.imdb_id for k in self.known_for],
            image_url=self.image_url,
        )

    def to_dict(self) -> dict:
        d = asdict(self)
        d["known_for"] = [k.to_dict() for k in self.known_for]
        return _drop_none(d)


# ─── GraphQL queries ─────────────────────────────────────────────────────────

_TITLE_QUERY = """
query TitleDetail($id: ID!) {
  title(id: $id) {
    id
    titleText { text }
    titleType { id text }
    releaseYear { year endYear }
    runtime { seconds }
    ratingsSummary { aggregateRating voteCount }
    plot { plotText { plainText } }
    genres { genres { text } }
    primaryImage { url width height }
    principalCredits {
      category { id text }
      credits {
        name { id nameText { text } }
        ... on Cast { characters { name } }
      }
    }
    akas(first: 20) {
      edges {
        node {
          text
          country { id text }
          language { id text }
        }
      }
    }
    certificates(first: 10) {
      edges {
        node {
          rating
          ratingReason
          country { id text }
        }
      }
    }
    isAdult
    releaseDate {
      day month year
      country { id text }
    }
  }
}
"""

_NAME_QUERY = """
query NameDetail($id: ID!) {
  name(id: $id) {
    id
    nameText { text }
    birthDate { dateComponents { year month day } }
    deathDate { dateComponents { year month day } }
    primaryProfessions { category { text } }
    primaryImage { url width height }
    knownFor(first: 5) {
      edges {
        node {
          title {
            id
            titleText { text }
            releaseYear { year }
          }
        }
      }
    }
    bio { text { plainText } }
  }
}
"""


# ─── Low-level request helper ─────────────────────────────────────────────────


def _post(query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
    """POST a raw GraphQL query and return the parsed response body."""
    payload = json.dumps({"query": query, "variables": variables}).encode()
    resp = transport.get_session().post(
        transport.GRAPHQL_BASE,
        data=payload,
        headers=_GQL_HEADERS,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def _check(data: Dict[str, Any], key: str) -> Dict[str, Any]:
    """Extract ``data[key]`` or raise with any GraphQL errors."""
    errors = data.get("errors") or []
    top = (data.get("data") or {}).get(key)
    if top is None:
        msgs = "; ".join(e.get("message", str(e)) for e in errors)
        raise ValueError(f"GraphQL returned no {key!r}: {msgs or 'no data'}")
    return top  # type: ignore[return-value]


# ─── Parsing helpers ──────────────────────────────────────────────────────────


def _parse_credits(principal_credits: List[Dict]) -> List[CreditEntry]:
    out: List[CreditEntry] = []
    for group in principal_credits or []:
        cat_id = (group.get("category") or {}).get("id", "")
        for credit in group.get("credits") or []:
            name_node = credit.get("name") or {}
            chars = [c["name"] for c in (credit.get("characters") or []) if c.get("name")]
            out.append(
                CreditEntry(
                    name_id=name_node.get("id", ""),
                    name=(name_node.get("nameText") or {}).get("text", ""),
                    category=cat_id,
                    characters=chars,
                )
            )
    return out


def _parse_akas(akas_connection: Optional[Dict]) -> List[AkaEntry]:
    if not akas_connection:
        return []
    out: List[AkaEntry] = []
    for edge in (akas_connection.get("edges") or []):
        node = edge.get("node") or {}
        country = node.get("country") or {}
        language = node.get("language") or {}
        out.append(
            AkaEntry(
                text=node.get("text", ""),
                country_id=country.get("id"),
                country=country.get("text"),
                language_id=language.get("id"),
                language=language.get("text"),
            )
        )
    return out


def _parse_certs(certs_connection: Optional[Dict]) -> List[CertificateEntry]:
    if not certs_connection:
        return []
    out: List[CertificateEntry] = []
    for edge in (certs_connection.get("edges") or []):
        node = edge.get("node") or {}
        country = node.get("country") or {}
        out.append(
            CertificateEntry(
                rating=node.get("rating", ""),
                country_id=country.get("id"),
                country=country.get("text"),
                rating_reason=node.get("ratingReason"),
            )
        )
    return out


def _parse_date_components(dc: Optional[Dict]) -> tuple:
    if not dc:
        return None, None, None
    c = dc.get("dateComponents") or {}
    return c.get("year"), c.get("month"), c.get("day")


# ─── Public API ───────────────────────────────────────────────────────────────


def get_title_detail(imdb_id: str) -> TitleDetail:
    """Fetch rich title detail from IMDb's GraphQL API.

    Args:
        imdb_id: canonical ``tt…`` identifier.

    Returns:
        :class:`TitleDetail` with title type, year, runtime, genres,
        plot, ratings, principal cast (with character names), directors,
        writers, localized titles (akas), content certificates, and
        release date.

    Raises:
        ``requests.HTTPError`` on a non-2xx response.
        ``ValueError`` if the API returns no data for the id.
    """
    raw = _check(_post(_TITLE_QUERY, {"id": imdb_id}), "title")

    release_year_node = raw.get("releaseYear") or {}
    ratings = raw.get("ratingsSummary") or {}
    plot_node = ((raw.get("plot") or {}).get("plotText") or {})
    genres_node = raw.get("genres") or {}
    image = raw.get("primaryImage") or {}
    rd = raw.get("releaseDate") or {}
    rd_country = rd.get("country") or {}
    tt_node = raw.get("titleType") or {}

    return TitleDetail(
        imdb_id=raw.get("id", imdb_id),
        title_type=tt_node.get("id", ""),
        title_type_text=tt_node.get("text", ""),
        primary_title=(raw.get("titleText") or {}).get("text"),
        start_year=release_year_node.get("year"),
        end_year=release_year_node.get("endYear"),
        runtime_seconds=(raw.get("runtime") or {}).get("seconds"),
        average_rating=ratings.get("aggregateRating"),
        num_votes=ratings.get("voteCount"),
        plot=plot_node.get("plainText"),
        genres=[g.get("text", "") for g in (genres_node.get("genres") or []) if g.get("text")],
        image_url=image.get("url"),
        image_width=image.get("width"),
        image_height=image.get("height"),
        is_adult=raw.get("isAdult"),
        release_day=rd.get("day"),
        release_month=rd.get("month"),
        release_year=rd.get("year"),
        release_country=rd_country.get("text"),
        credits=_parse_credits(raw.get("principalCredits") or []),
        akas=_parse_akas(raw.get("akas")),
        certificates=_parse_certs(raw.get("certificates")),
    )


def get_name_detail(imdb_id: str) -> NameDetail:
    """Fetch rich person detail from IMDb's GraphQL API.

    Args:
        imdb_id: canonical ``nm…`` identifier.

    Returns:
        :class:`NameDetail` with name, birth/death dates (year/month/day),
        professions, primary image, top known-for titles, and biography.

    Raises:
        ``requests.HTTPError`` on a non-2xx response.
        ``ValueError`` if the API returns no data for the id.
    """
    raw = _check(_post(_NAME_QUERY, {"id": imdb_id}), "name")

    by, bm, bd = _parse_date_components(raw.get("birthDate"))
    dy, dm, dd = _parse_date_components(raw.get("deathDate"))
    image = raw.get("primaryImage") or {}
    professions = [
        (p.get("category") or {}).get("text", "")
        for p in (raw.get("primaryProfessions") or [])
        if (p.get("category") or {}).get("text")
    ]
    known_for: List[KnownForEntry] = []
    for edge in ((raw.get("knownFor") or {}).get("edges") or []):
        node = edge.get("node") or {}
        title_node = node.get("title") or {}
        ry = (title_node.get("releaseYear") or {}).get("year")
        known_for.append(
            KnownForEntry(
                imdb_id=title_node.get("id", ""),
                title=(title_node.get("titleText") or {}).get("text"),
                year=ry,
            )
        )
    bio_node = (raw.get("bio") or {}).get("text") or {}

    return NameDetail(
        imdb_id=raw.get("id", imdb_id),
        primary_name=(raw.get("nameText") or {}).get("text"),
        birth_year=by,
        birth_month=bm,
        birth_day=bd,
        death_year=dy,
        death_month=dm,
        death_day=dd,
        primary_professions=professions,
        image_url=image.get("url"),
        image_width=image.get("width"),
        image_height=image.get("height"),
        known_for=known_for,
        bio=bio_node.get("plainText"),
    )
