"""Bulk-fetch technical specs (color/B&W/silent/sound/format) for all movies.

Reads the full title.basics dump to get movie IDs, then hits the GraphQL API
(no WAF, no solver needed) for each title's technical specifications.  The
output is a resumable JSONL — restart and it skips already-fetched IDs.

Output columns
--------------
imdb_id, colorations[], coloration_concept_ids[], is_color, is_silent,
sound_mixes[], sound_mix_ids[], aspect_ratios[], cameras[],
negative_formats[], printed_formats[], processes[], laboratories[],
film_lengths[]

Key boolean flags
-----------------
is_color   : True=colour  False=B&W  None=unknown
is_silent  : True=silent  False=has sound  None=unknown

Usage
-----
    python examples/10_technical_specs_bulk.py
    python examples/10_technical_specs_bulk.py --out /data/imdb_tech.jsonl
    python examples/10_technical_specs_bulk.py --delay 0.5 --limit 10000
    python examples/10_technical_specs_bulk.py --types movie short tvMovie
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

DEFAULT_OUT = Path.home() / ".cache" / "pyimdb" / "technical_specs.jsonl"
DEFAULT_TYPES = {"movie", "short", "tvMovie", "tvSpecial"}


def load_done(out: Path) -> set:
    done: set = set()
    if not out.exists():
        return done
    with open(out) as fh:
        for line in fh:
            try:
                done.add(json.loads(line)["imdb_id"])
            except Exception:
                pass
    return done


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="Output JSONL path")
    ap.add_argument("--delay", type=float, default=0.3, help="Seconds between GraphQL requests")
    ap.add_argument("--limit", type=int, default=None, help="Stop after N rows written")
    ap.add_argument("--types", nargs="+", default=list(DEFAULT_TYPES),
                    help="Title types to include (default: movie short tvMovie tvSpecial)")
    args = ap.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    pyimdb.set_delay(args.delay)

    title_types = set(args.types)
    done = load_done(out)
    print(f"Already done: {len(done):,}", flush=True)

    written = 0
    errors = 0
    t0 = time.time()

    with open(out, "a", encoding="utf-8") as fh:
        for title in bulk.stream_titles():
            if title.title_type.value not in title_types:
                continue
            if title.imdb_id in done:
                continue

            try:
                specs = get_technical_specs(title.imdb_id)
            except Exception as exc:
                errors += 1
                if errors % 100 == 0:
                    print(f"  {errors} errors so far (last: {exc})", file=sys.stderr, flush=True)
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
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            fh.flush()
            done.add(title.imdb_id)
            written += 1

            if written % 1000 == 0:
                elapsed = time.time() - t0
                rate = written / elapsed
                print(f"  {written:,} written  {errors} errors  {rate:.1f}/s", flush=True)

            if args.limit and written >= args.limit:
                break

    elapsed = time.time() - t0
    print(f"Done. {written:,} rows written, {errors} errors, {elapsed:.0f}s", flush=True)


if __name__ == "__main__":
    main()
