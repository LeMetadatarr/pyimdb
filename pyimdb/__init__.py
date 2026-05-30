"""pyimdb — Python metadata client for IMDb.

Three live data paths, in order of reliability:

- :mod:`pyimdb.search` — the **suggestion API** (no key, not WAF-gated).
- :mod:`pyimdb.bulk` — the **bulk datasets** (no key; streaming gzip TSV).
- :mod:`pyimdb.title` / :mod:`pyimdb.name` — **page crawl**, best-effort and
  WAF-gated (HTTP 202); needs a FlareSolverr solver via the ``PYIMDB`` env.

:mod:`pyimdb.ids` emits the canonical ``imdb_id`` anchor for cross-referencing across sources.
"""
from pyimdb.version import __version__
from pyimdb.models import (
    Aka,
    Episode,
    HitType,
    Name,
    Principal,
    Rating,
    SearchHit,
    Title,
    TitleType,
)
from pyimdb.search import (
    first,
    search,
    search_names,
    search_titles,
)
from pyimdb import bulk, dataset, ids
from pyimdb.bulk import (
    download,
    find_name as bulk_find_name,
    find_rating,
    find_title as bulk_find_title,
    stream_akas,
    stream_episodes,
    stream_names,
    stream_principals,
    stream_ratings,
    stream_rows,
    stream_titles,
)
from pyimdb.ids import (
    canonical_imdb_id,
    hit_to_extra,
    is_name_id,
    is_title_id,
    name_to_extra,
    title_to_extra,
)
from pyimdb.name import get_name, parse_name
from pyimdb.title import get_title, parse_title
from pyimdb.transport import reset_session, set_delay, set_session

__all__ = [
    "__version__",
    # models
    "Aka",
    "Episode",
    "HitType",
    "Name",
    "Principal",
    "Rating",
    "SearchHit",
    "Title",
    "TitleType",
    # search (suggestion API)
    "search",
    "search_titles",
    "search_names",
    "first",
    # bulk datasets
    "bulk",
    "download",
    "stream_rows",
    "stream_titles",
    "stream_names",
    "stream_ratings",
    "stream_akas",
    "stream_episodes",
    "stream_principals",
    "bulk_find_title",
    "bulk_find_name",
    "find_rating",
    # page crawl (best-effort)
    "get_title",
    "parse_title",
    "get_name",
    "parse_name",
    # ids / external-id converters
    "ids",
    "canonical_imdb_id",
    "is_title_id",
    "is_name_id",
    "title_to_extra",
    "name_to_extra",
    "hit_to_extra",
    # dataset
    "dataset",
    # transport
    "set_delay",
    "reset_session",
    "set_session",
]
