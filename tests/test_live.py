"""Live smoke test against the suggestion API (the reliable, no-key path).

Skipped automatically when the network is unreachable. Run explicitly with::

    pytest tests/test_live.py -m live
"""
import pytest

import pyimdb

pytestmark = pytest.mark.live


def test_live_suggestion_search():
    try:
        hits = pyimdb.search("inception")
    except Exception as e:  # pragma: no cover - network-dependent
        pytest.skip(f"network unavailable: {e}")
    assert hits, "suggestion API returned no hits"
    top = hits[0]
    assert top.imdb_id.startswith("tt")
    assert top.label
