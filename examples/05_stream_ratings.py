"""Stream the (small) ratings dump and print the first few rows.

Caps at 20 rows so it does not download or parse the whole file when you only
want a taste. Drop ``limit=`` to process everything (still streamed).
"""
import pyimdb

for rating in pyimdb.stream_ratings(limit=20):
    print(rating.imdb_id, rating.average_rating, rating.num_votes)
