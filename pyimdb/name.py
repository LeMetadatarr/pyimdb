"""Best-effort page crawl for ``/name/<nm>/`` — UNVERIFIED LIVE.

Same WAF caveat as :mod:`pyimdb.title`: IMDb answers bare requests with
``HTTP 202``. Configure ``PYIMDB_FLARESOLVERR_URL`` to clear the challenge.
Selectors target the schema.org ``Person`` ld+json payload and are UNVERIFIED
against live HTML.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from pyimdb import transport
from pyimdb._clean import clean, clean_or_none, extract_imdb_id, to_int
from pyimdb.models import Name
from pyimdb.title import extract_ldjson, extract_next_data, is_blocked  # noqa: F401


def name_url(imdb_id: str) -> str:
    return f"{transport.SITE_BASE}/name/{imdb_id}/"


def _known_for(ld: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    for key in ("knownFor", "performerIn", "sameAs"):
        val = ld.get(key)
        if isinstance(val, list):
            for item in val:
                tid = extract_imdb_id(clean_or_none(
                    item.get("url") if isinstance(item, dict) else str(item)
                ))
                if tid:
                    out.append(tid)
    return out


def _professions(ld: Dict[str, Any]) -> List[str]:
    job = ld.get("jobTitle")
    if isinstance(job, str):
        return [clean(j) for j in re.split(r"[,/]", job) if clean(j)]
    if isinstance(job, list):
        return [clean(str(j)) for j in job if clean(str(j))]
    return []


def parse_name(html: str, imdb_id: Optional[str] = None) -> Name:
    """Parse a name page's HTML into a :class:`~pyimdb.models.Name`.

    UNVERIFIED against live IMDb HTML — derived from the schema.org ``Person``
    schema, not a cleared fetch.
    """
    ld = extract_ldjson(html) or {}
    nid = imdb_id or extract_imdb_id(clean_or_none(ld.get("url"))) or ""
    birth = clean_or_none((ld.get("birthDate") or "")) if isinstance(ld.get("birthDate"), str) else None
    death = clean_or_none((ld.get("deathDate") or "")) if isinstance(ld.get("deathDate"), str) else None
    return Name(
        imdb_id=nid,
        primary_name=clean_or_none(ld.get("name")),
        birth_year=to_int(birth[:4]) if birth else None,
        death_year=to_int(death[:4]) if death else None,
        primary_professions=_professions(ld),
        known_for_titles=_known_for(ld),
        image_url=clean_or_none(ld.get("image")),
    )


def get_name(imdb_id: str) -> Name:
    """Fetch and parse a name page (best-effort; may hit the WAF).

    Raises :class:`RuntimeError` on a WAF challenge — configure
    ``PYIMDB_FLARESOLVERR_URL`` to clear it.
    """
    html = transport.get_text(name_url(imdb_id), headers={"Accept": "text/html"})
    if is_blocked(html):
        raise RuntimeError(
            f"IMDb WAF blocked the page crawl for {imdb_id} (HTTP 202 / challenge). "
            "Configure PYIMDB_FLARESOLVERR_URL to use a solver, or use "
            "pyimdb.search / pyimdb.bulk instead."
        )
    return parse_name(html, imdb_id=imdb_id)
