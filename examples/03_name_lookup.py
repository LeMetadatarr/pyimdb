"""Look up a person by name (nm… hits) via the suggestion API."""
import pyimdb

for hit in pyimdb.search_names("greta gerwig"):
    print(hit.imdb_id, "|", hit.label, "| known for:", hit.stars)
