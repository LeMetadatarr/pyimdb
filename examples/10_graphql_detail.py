"""Fetch rich title/person detail via IMDb's GraphQL endpoint.

Not WAF-gated, no key needed. See docs/graphql.md for the full field list.
"""
import pyimdb

detail = pyimdb.get_title_detail("tt1375666")
print(detail.primary_title, detail.start_year, detail.average_rating, detail.num_votes)
print(detail.plot)
for c in detail.cast[:5]:
    print(c.category, c.name, c.characters)

person = pyimdb.get_name_detail("nm0000093")
print(person.primary_name, person.birth_year)
for kf in person.known_for[:5]:
    print(kf.imdb_id, kf.title, kf.year)
