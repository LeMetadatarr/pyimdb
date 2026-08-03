"""Best-effort page crawl for ``/title/<tt>/`` — UNVERIFIED LIVE.

IMDb's Akamai/Cloudflare-style WAF answers bare requests from most server
environments with ``HTTP 202`` and a challenge stub (no ld+json, no
``__NEXT_DATA__``). Verified live from this environment: plain ``urllib``,
``curl_cffi`` impersonation, and an unconfigured
:class:`unblock_requests.CloudflareSession` all receive 202.

To get live HTML you must point the transport at an external solver
(FlareSolverr) via the ``PYIMDB`` env knobs, e.g.::

    PYIMDB_FLARESOLVERR_URL=http://localhost:8191

This module parses whatever HTML the transport returns:

1. ``<script type="application/ld+json">`` — schema.org ``Movie``/``TVSeries``;
2. the ``__NEXT_DATA__`` JSON blob (Next.js page props).

The selectors target those two JSON payloads (stable schema.org / Next props
shapes), **not** brittle CSS — but they are UNVERIFIED against live IMDb HTML
because the WAF blocks fetches here. Prefer :mod:`pyimdb.search` and
:mod:`pyimdb.bulk` for production.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from pyimdb import transport
from pyimdb._clean import clean, clean_or_none, extract_imdb_id, to_int
from pyimdb.models import Title, TitleType

_LDJSON_RE = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE,
)
_NEXTDATA_RE = re.compile(
    r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE,
)

_CHALLENGE_MARKERS = ("just a moment", "challenge-platform", "cf-mitigated", "/errors/")


def title_url(imdb_id: str) -> str:
    return f"{transport.SITE_BASE}/title/{imdb_id}/"


def is_blocked(html: str) -> bool:
    """Heuristic: did the WAF serve a challenge/stub instead of the page?"""
    if not html:
        return True
    head = html[:2000].lower()
    if any(m in head for m in _CHALLENGE_MARKERS):
        return True
    return ("application/ld+json" not in html) and ("__next_data__" not in head)


def extract_ldjson(html: str) -> Optional[Dict[str, Any]]:
    """Return the first ld+json object describing a title, if present."""
    for raw in _LDJSON_RE.findall(html or ""):
        try:
            obj = json.loads(raw.strip())
        except ValueError:
            continue
        if isinstance(obj, dict):
            return obj
    return None


def extract_next_data(html: str) -> Optional[Dict[str, Any]]:
    """Return the parsed ``__NEXT_DATA__`` blob, if present."""
    m = _NEXTDATA_RE.search(html or "")
    if not m:
        return None
    try:
        return json.loads(m.group(1).strip())
    except ValueError:
        return None


def _genres(ld: Dict[str, Any]) -> List[str]:
    g = ld.get("genre")
    if isinstance(g, str):
        return [clean(g)]
    if isinstance(g, list):
        return [clean(x) for x in g if clean(str(x))]
    return []


def _duration_minutes(ld: Dict[str, Any]) -> Optional[int]:
    # schema.org duration is ISO-8601, e.g. "PT2H28M".
    dur = ld.get("duration")
    if not isinstance(dur, str):
        return None
    h = re.search(r"(\d+)H", dur)
    m = re.search(r"(\d+)M", dur)
    if h is None and m is None:
        return None
    return (int(h.group(1)) * 60 if h else 0) + (int(m.group(1)) if m else 0)


def _map_ldtype(ld_type: Optional[str]) -> TitleType:
    mapping = {
        "Movie": TitleType.MOVIE,
        "TVSeries": TitleType.TV_SERIES,
        "TVEpisode": TitleType.TV_EPISODE,
        "TVMovie": TitleType.TV_MOVIE,
        "VideoGame": TitleType.VIDEO_GAME,
        "CreativeWorkSeries": TitleType.TV_SERIES,
    }
    return mapping.get(ld_type or "", TitleType.UNKNOWN)


def parse_title(html: str, imdb_id: Optional[str] = None) -> Title:
    """Parse a title page's HTML into a :class:`~pyimdb.models.Title`.

    Uses the ld+json payload primarily. UNVERIFIED against live IMDb HTML —
    selectors are derived from the schema.org schema, not a cleared fetch.
    """
    ld = extract_ldjson(html) or {}
    tid = imdb_id or extract_imdb_id(clean_or_none(ld.get("url"))) or ""
    rating_obj = ld.get("aggregateRating") or {}
    title = Title(
        imdb_id=tid,
        title_type=_map_ldtype(ld.get("@type")),
        primary_title=clean_or_none(ld.get("name")),
        original_title=clean_or_none(ld.get("alternateName")) or clean_or_none(ld.get("name")),
        runtime_minutes=_duration_minutes(ld),
        genres=_genres(ld),
        image_url=clean_or_none(ld.get("image")),
    )
    if isinstance(rating_obj, dict):
        rv = rating_obj.get("ratingValue")
        cv = rating_obj.get("ratingCount")
        if rv is not None:
            try:
                title.average_rating = float(rv)
            except (TypeError, ValueError):
                pass
        title.num_votes = to_int(cv)
    # start year from datePublished
    dp = clean_or_none(ld.get("datePublished"))
    if dp:
        title.start_year = to_int(dp[:4])
    return title


def get_title(imdb_id: str) -> Title:
    """Fetch and parse a title page (best-effort; may hit the WAF).

    Raises :class:`RuntimeError` if the transport returns a WAF challenge —
    configure ``PYIMDB_FLARESOLVERR_URL`` to clear it.
    """
    html = transport.get_text(title_url(imdb_id), headers={"Accept": "text/html"})
    if is_blocked(html):
        raise RuntimeError(
            f"IMDb WAF blocked the page crawl for {imdb_id} (HTTP 202 / challenge). "
            "Configure PYIMDB_FLARESOLVERR_URL to use a solver, or use "
            "pyimdb.search / pyimdb.bulk instead."
        )
    return parse_title(html, imdb_id=imdb_id)
