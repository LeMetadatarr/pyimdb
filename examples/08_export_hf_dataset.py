"""Export bulk dumps to JSON Lines, one file per HF dataset config.

Streamed end to end. ``limit`` keeps this example quick; remove it for the
full export. PROVENANCE: IMDb datasets are personal / non-commercial use only.
"""
import pyimdb

counts = pyimdb.dataset.export_all(
    "imdb_dataset",
    configs=("ratings", "titles", "names"),
    limit=1000,
)
print("rows written per config:", counts)
