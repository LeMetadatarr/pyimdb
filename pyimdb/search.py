"""Search via the IMDb suggestion API — the search backbone.

The suggestion service answers JSON with no API key and is not WAF-gated::

    https://v3.sg.media-imdb.com/suggestion/x/<query>.json          # everything
    https://v3.sg.media-imdb.com/suggestion/titles/x/<query>.json    # titles only
    https://v3.sg.media-imdb.com/suggestion/names/x/<query>.json     # names only

Each hit carries ``id`` (``tt…``/``nm…``), ``l`` (label), ``q``/``qid`` (type),
``y`` (year), ``yr`` (year range for series), ``i`` (image) and ``s`` (stars /
known-for). These are mapped onto :class:`~pyimdb.models.SearchHit`.
"""
from __future__ import annotations

from typing import Iterator, List, Optional
from urllib.parse import quote

from pyimdb import transport
from pyimdb._clean import clean, clean_or_none, to_int
from pyimdb.models import HitType, SearchHit


def _suggest_url(query: str, scope: str) -> str:
    q = quote(query.strip().lower())
    if scope == "titles":
        path = f"/suggestion/titles/x/{q}.json"
    elif scope == "names":
        path = f"/suggestion/names/x/{q}.json"
    else:
        path = f"/suggestion/x/{q}.json"
    return f"{transport.SUGGEST_BASE}{path}"


def _parse_year_range(hit: dict) -> tuple[Optional[int], Optional[int]]:
    yr = hit.get("yr")
    if isinstance(yr, str) and "-" in yr:
        parts = yr.split("-", 1)
        return to_int(parts[0]), to_int(parts[1])
    y = to_int(hit.get("y"))
    return y, None


def _stars(hit: dict) -> List[str]:
    s = hit.get("s")
    if isinstance(s, str):
        return [clean(part) for part in s.split(",") if clean(part)]
    if isinstance(s, list):
        return [clean(str(part)) for part in s if clean(str(part))]
    return []


def _image_url(hit: dict) -> Optional[str]:
    img = hit.get("i")
    if isinstance(img, dict):
        return clean_or_none(img.get("imageUrl") or img.get("url"))
    if isinstance(img, list) and img:
        return clean_or_none(str(img[0]))
    return clean_or_none(img if isinstance(img, str) else None)


def hit_from_json(hit: dict, rank: Optional[int] = None) -> SearchHit:
    """Build a :class:`SearchHit` from one raw suggestion-API entry."""
    imdb_id = clean(hit.get("id"))
    start_year, end_year = _parse_year_range(hit)
    return SearchHit(
        imdb_id=imdb_id,
        label=clean(hit.get("l")),
        kind=HitType.coerce(hit.get("qid")),
        title_type=clean_or_none(hit.get("q")),
        year=start_year,
        end_year=end_year,
        image_url=_image_url(hit),
        stars=_stars(hit),
        rank=rank,
    )


def search(query: str, scope: str = "all") -> List[SearchHit]:
    """Search the suggestion API.

    Args:
        query: free-text query (title or person name).
        scope: ``"all"`` (default), ``"titles"`` or ``"names"``.

    Returns the list of :class:`~pyimdb.models.SearchHit`, in rank order.
    """
    if not query or not query.strip():
        return []
    data = transport.get_json(_suggest_url(query, scope))
    out: List[SearchHit] = []
    for i, hit in enumerate(data.get("d", []) or []):
        if not hit.get("id"):
            continue
        out.append(hit_from_json(hit, rank=i))
    return out


def search_titles(query: str) -> List[SearchHit]:
    """Search titles only (``tt…`` hits)."""
    return [h for h in search(query, scope="titles") if h.is_title]


def search_names(query: str) -> List[SearchHit]:
    """Search names only (``nm…`` hits)."""
    return [h for h in search(query, scope="names") if h.is_name]


def first(query: str, scope: str = "all") -> Optional[SearchHit]:
    """Return the top-ranked hit, or ``None``."""
    hits = search(query, scope=scope)
    return hits[0] if hits else None


def iter_search(queries: Iterator[str], scope: str = "all") -> Iterator[SearchHit]:
    """Yield hits across many queries (one request each)."""
    for q in queries:
        yield from search(q, scope=scope)
