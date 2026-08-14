"""Bulk-fetch technical specs sorted oldest-first, emit B&W/silent subset.

Reads title.basics into memory (movies only), sorts by start_year ascending,
then hits GraphQL for each. Writes two files:
  - technical_specs.jsonl      — all results (merged with any prior run)
  - bw_silent_movies.jsonl     — filtered subset: is_color=False OR is_silent=True

Resumable: skips imdb_ids already in technical_specs.jsonl.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import pyimdb
from pyimdb.graphql import get_technical_specs
from pyimdb import bulk

DEFAULT_DIR = Path.home() / "AgentWorkspaces/datasets/video/imdb"
TARGET_TYPES = {"movie", "short", "tvMovie", "tvSpecial"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(DEFAULT_DIR))
    ap.add_argument("--delay", type=float, default=0.3)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    out_dir = Path(args.dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    specs_path = out_dir / "technical_specs.jsonl"
    subset_path = out_dir / "bw_silent_movies.jsonl"

    pyimdb.set_delay(args.delay)

    # Load already-done IDs
    done: set = set()
    if specs_path.exists():
        for line in specs_path.read_text().splitlines():
            try:
                done.add(json.loads(line)["imdb_id"])
            except Exception:
                pass
    print(f"Already done: {len(done):,}", flush=True)

    # Load existing B&W/silent subset IDs
    existing_subset: set = set()
    if subset_path.exists():
        for line in subset_path.read_text().splitlines():
            try:
                existing_subset.add(json.loads(line)["imdb_id"])
            except Exception:
                pass

    # Build sorted title list (oldest first)
    print("Loading title list...", flush=True)
    titles = []
    for t in bulk.stream_titles():
        if t.title_type.value not in TARGET_TYPES:
            continue
        if t.imdb_id in done:
            continue
        titles.append((t.start_year or 9999, t.imdb_id))
    titles.sort()
    print(f"Titles to fetch: {len(titles):,} (oldest first, starting {titles[0][0] if titles else '?'})", flush=True)

    written = 0
    bw_silent = 0
    errors = 0
    t0 = time.time()

    with open(specs_path, "a", encoding="utf-8") as specs_fh, \
         open(subset_path, "a", encoding="utf-8") as subset_fh:

        for year, imdb_id in titles:
            try:
                specs = get_technical_specs(imdb_id)
            except Exception as exc:
                errors += 1
                if errors % 200 == 0:
                    print(f"  {errors} errors (last: {exc})", file=sys.stderr, flush=True)
                continue

            row = {
                "imdb_id": specs.imdb_id,
                "colorations": specs.colorations,
                "coloration_concept_ids": specs.coloration_concept_ids,
                "is_color": specs.is_color,
                "is_silent": specs.is_silent,
                "sound_mixes": specs.sound_mixes,
                "sound_mix_ids": specs.sound_mix_ids,
                "aspect_ratios": specs.aspect_ratios,
                "cameras": specs.cameras,
                "negative_formats": specs.negative_formats,
                "printed_formats": specs.printed_formats,
                "processes": specs.processes,
                "laboratories": specs.laboratories,
                "film_lengths": specs.film_lengths,
            }
            specs_fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            specs_fh.flush()
            written += 1

            # Emit to B&W/silent subset
            if specs.is_color is False or specs.is_silent is True:
                if imdb_id not in existing_subset:
                    subset_fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                    subset_fh.flush()
                    existing_subset.add(imdb_id)
                    bw_silent += 1

            if written % 1000 == 0:
                elapsed = time.time() - t0
                print(f"  {written:,} fetched  {bw_silent} B&W/silent  {errors} errors  {elapsed/written:.2f}s/title  year={year}", flush=True)

            if args.limit and written >= args.limit:
                break

    elapsed = time.time() - t0
    print(f"Done. {written:,} fetched, {bw_silent} B&W/silent, {errors} errors, {elapsed:.0f}s", flush=True)


if __name__ == "__main__":
    main()
