"""Search IMDb via the suggestion API (no key, the reliable path)."""
import pyimdb

for hit in pyimdb.search("the matrix"):
    kind = "name" if hit.is_name else hit.title_type or hit.kind.value
    year = f" ({hit.year})" if hit.year else ""
    print(f"{hit.imdb_id}  {kind:10}  {hit.label}{year}")
