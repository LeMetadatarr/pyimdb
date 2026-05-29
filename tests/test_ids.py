import json

from pyimdb import ids
from pyimdb.models import HitType, Name, SearchHit, Title, TitleType


def test_title_to_extra():
    t = Title(
        imdb_id="tt1375666",
        title_type=TitleType.MOVIE,
        primary_title="Inception",
        original_title="Inception",
        start_year=2010,
        runtime_minutes=148,
        genres=["Action", "Sci-Fi"],
        average_rating=8.8,
        num_votes=2500000,
    )
    extra = ids.title_to_extra(t)
    assert extra["imdb_id"] == "tt1375666"
    assert extra["imdb_url"] == "https://www.imdb.com/title/tt1375666/"
    assert extra["imdb_title_type"] == "movie"
    assert extra["imdb_year"] == "2010"
    assert json.loads(extra["imdb_genres"]) == ["Action", "Sci-Fi"]
    assert extra["imdb_rating"] == "8.8"


def test_name_to_extra():
    n = Name(
        imdb_id="nm0634240",
        primary_name="Christopher Nolan",
        birth_year=1970,
        primary_professions=["director"],
        known_for_titles=["tt1375666"],
    )
    extra = ids.name_to_extra(n)
    assert extra["imdb_id"] == "nm0634240"
    assert extra["imdb_url"] == "https://www.imdb.com/name/nm0634240/"
    assert extra["imdb_name"] == "Christopher Nolan"
    assert json.loads(extra["imdb_known_for"]) == ["tt1375666"]


def test_hit_to_extra_title_and_name():
    th = SearchHit(imdb_id="tt1375666", label="Inception", kind=HitType.MOVIE, year=2010)
    nh = SearchHit(imdb_id="nm0634240", label="Christopher Nolan", kind=HitType.NAME)
    te = ids.hit_to_extra(th)
    ne = ids.hit_to_extra(nh)
    assert te["imdb_id"] == "tt1375666" and te["imdb_primary_title"] == "Inception"
    assert ne["imdb_id"] == "nm0634240" and ne["imdb_name"] == "Christopher Nolan"


def test_canonical_id_helpers():
    assert ids.canonical_imdb_id("tt1375666") == "tt1375666"
    assert ids.canonical_imdb_id(Title(imdb_id="tt1")) == "tt1"
    assert ids.is_title_id("tt1") and not ids.is_title_id("nm1")
    assert ids.is_name_id("nm1") and not ids.is_name_id("tt1")
