"""Resolve a query to its canonical imdb_id and emit an external-id dict."""
import json

import pyimdb

hit = pyimdb.first("dune part two")
if hit:
    print("canonical imdb_id:", pyimdb.canonical_imdb_id(hit))
    print(json.dumps(pyimdb.hit_to_extra(hit), indent=2))
