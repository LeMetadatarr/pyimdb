import json

import pytest

import importlib

from pyimdb.models import HitType

# `pyimdb.search` the attribute is the public search() function (house pattern,
# mirrors pyiafd); the module object lives under its import path.
search = importlib.import_module("pyimdb.search")


def _load(fixtures):
    return json.loads((fixtures / "suggestion_inception.json").read_text())


def test_hit_from_json_title(fixtures):
    data = _load(fixtures)
    hit = search.hit_from_json(data["d"][0], rank=0)
    assert hit.imdb_id == "tt1375666"
    assert hit.is_title and not hit.is_name
    assert hit.kind is HitType.MOVIE
    assert hit.year == 2010
    assert hit.label == "Inception"
    assert "Leonardo DiCaprio" in hit.stars
    assert hit.image_url == "https://example.com/inception.jpg"
    assert hit.url == "https://www.imdb.com/title/tt1375666/"


def test_hit_from_json_name(fixtures):
    data = _load(fixtures)
    hit = search.hit_from_json(data["d"][1])
    assert hit.imdb_id == "nm0634240"
    assert hit.is_name
    assert hit.kind is HitType.NAME
    assert hit.url == "https://www.imdb.com/name/nm0634240/"


def test_year_range(fixtures):
    data = _load(fixtures)
    hit = search.hit_from_json(data["d"][2])
    assert hit.year == 2011
    assert hit.end_year == 2019


def test_search_offline(monkeypatch, fixtures):
    data = _load(fixtures)
    monkeypatch.setattr(search.transport, "get_json", lambda url, **kw: data)
    hits = search.search("inception")
    assert len(hits) == 3
    assert hits[0].imdb_id == "tt1375666"
    # scope filters
    monkeypatch.setattr(search.transport, "get_json", lambda url, **kw: data)
    assert all(h.is_name for h in search.search_names("inception"))
    monkeypatch.setattr(search.transport, "get_json", lambda url, **kw: data)
    assert all(h.is_title for h in search.search_titles("inception"))


def test_empty_query():
    assert search.search("") == []


def test_suggest_url():
    assert "/suggestion/x/" in search._suggest_url("a b", "all")
    assert "/suggestion/titles/x/" in search._suggest_url("a", "titles")
    assert "/suggestion/names/x/" in search._suggest_url("a", "names")
