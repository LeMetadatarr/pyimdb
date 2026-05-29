"""Join ratings + basics in a streaming pass to find well-voted movies.

Builds a small in-memory index of high-vote ratings, then streams basics once
to attach titles. Demonstrates streaming joins without loading whole dumps.
"""
import pyimdb

# Keep only strongly-voted titles to bound memory.
ratings = {
    r.imdb_id: r
    for r in pyimdb.stream_ratings()
    if (r.num_votes or 0) >= 1_000_000
}
print(f"{len(ratings)} titles with >=1M votes")

shown = 0
for t in pyimdb.stream_titles():
    r = ratings.get(t.imdb_id)
    if r and t.title_type.value == "movie":
        print(f"{r.average_rating}  {t.primary_title} ({t.start_year})")
        shown += 1
        if shown >= 25:
            break
