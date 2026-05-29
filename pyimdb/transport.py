"""HTTP transport for IMDb endpoints.

Three live data paths share one transport layer:

- the **suggestion API** (``v3.sg.media-imdb.com``) — fast JSON search, no key,
  not WAF-gated;
- the **bulk datasets** (``datasets.imdbws.com``) — gzip TSV dumps, no key;
- **page crawl** (``www.imdb.com``) — gated by an Akamai/Cloudflare-style WAF
  that answers bare requests with ``HTTP 202``. Clearing it needs an external
  solver (FlareSolverr), wired through :mod:`unblock_requests`.

The session is an :class:`unblock_requests.CloudflareSession` when that package
is installed (anti-bot transport: TLS impersonation, optional FlareSolverr,
optional Wayback fallback), falling back to ``curl_cffi`` and then plain
``requests``. Environment knobs use the ``PYIMDB`` prefix, e.g.
``PYIMDB_TRANSPORT``, ``PYIMDB_FLARESOLVERR_URL`` — see
:mod:`unblock_requests` for the full list.
"""
from __future__ import annotations

import time
from typing import Any, Optional

SUGGEST_BASE = "https://v3.sg.media-imdb.com"
DATASETS_BASE = "https://datasets.imdbws.com"
SITE_BASE = "https://www.imdb.com"
GRAPHQL_BASE = "https://caching.graphql.imdb.com"

ENV_PREFIX = "PYIMDB"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": SITE_BASE + "/",
}

_session: Optional[Any] = None
_last_request: float = 0.0
_min_delay: float = 0.5  # seconds between requests


def set_delay(seconds: float) -> None:
    """Set the minimum delay between HTTP requests."""
    global _min_delay
    _min_delay = max(0.0, seconds)


def _make_session() -> Any:
    try:
        from unblock_requests import CloudflareSession

        session = CloudflareSession(env_prefix=ENV_PREFIX, wayback_fallback=True)
        session.headers.update(_HEADERS)
        return session
    except ImportError:
        pass

    try:
        import curl_cffi.requests as cffi_requests  # type: ignore
        from curl_cffi import BrowserType

        supported = {e.value for e in BrowserType}
        for candidate in ("firefox120", "firefox135", "chrome124", "chrome136"):
            if candidate in supported:
                impersonate = candidate
                break
        else:
            impersonate = next(iter(supported))
        session = cffi_requests.Session(impersonate=impersonate)
        session.headers.update(_HEADERS)
        return session
    except ImportError:
        import requests

        session = requests.Session()
        session.headers.update(_HEADERS)
        return session


def get_session() -> Any:
    global _session
    if _session is None:
        _session = _make_session()
    return _session


def set_session(session: Any) -> None:
    """Inject a custom session (tests, custom transports)."""
    global _session
    _session = session


def reset_session() -> None:
    global _session
    _session = None


def _throttle() -> None:
    global _last_request
    elapsed = time.time() - _last_request
    if elapsed < _min_delay:
        time.sleep(_min_delay - elapsed)
    _last_request = time.time()


def get(url: str, **kwargs: Any) -> Any:
    """Throttled GET returning the raw response object."""
    _throttle()
    kwargs.setdefault("timeout", 30)
    resp = get_session().get(url, **kwargs)
    resp.raise_for_status()
    return resp


def get_json(url: str, **kwargs: Any) -> Any:
    """GET *url* and decode the body as JSON."""
    return get(url, **kwargs).json()


def get_text(url: str, **kwargs: Any) -> str:
    """GET *url* and return the response text."""
    return get(url, **kwargs).text
