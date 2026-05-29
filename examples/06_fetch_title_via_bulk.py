"""Resolve a tt… id to a full Title by scanning the bulk basics dump.

This streams title.basics (large) and stops at the match, then joins the
rating. For a label-only need, prefer the suggestion API (much faster).
"""
import pyimdb

# Resolve a query to an id first (cheap), then enrich from the bulk dump.
hit = pyimdb.first("the godfather")
if hit and hit.is_title:
    title = pyimdb.bulk_find_title(hit.imdb_id)
    if title:
        print(title.imdb_id, title.primary_title, title.start_year)
        print("rating:", title.average_rating, "votes:", title.num_votes)
        print("genres:", title.genres)
