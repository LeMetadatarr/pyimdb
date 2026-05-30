"""Best-effort page crawl of a title page.

IMDb's WAF returns HTTP 202 to bare requests; this raises RuntimeError unless a
solver is configured. Set ``PYIMDB_FLARESOLVERR_URL=http://localhost:8191`` to clear
the challenge and return live HTML.
"""
import pyimdb

try:
    title = pyimdb.get_title("tt1375666")
    print(title.primary_title, title.average_rating, title.runtime_minutes)
except RuntimeError as e:
    print("page crawl unavailable:", e)
    print("Falling back to the suggestion API:")
    hit = pyimdb.first("inception")
    print(hit.imdb_id, hit.label, hit.year)
