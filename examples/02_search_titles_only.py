"""Restrict the suggestion search to titles (tt…) only."""
import pyimdb

for hit in pyimdb.search_titles("blade runner"):
    print(hit.imdb_id, hit.year, hit.label, "|", hit.stars)
