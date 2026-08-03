from pyimdb import name as name_mod
from pyimdb import title as title_mod
from pyimdb.models import TitleType


def test_parse_title_from_ldjson(fixtures):
    html = (fixtures / "title_page.html").read_text()
    assert not title_mod.is_blocked(html)
    t = title_mod.parse_title(html, imdb_id="tt1375666")
    assert t.imdb_id == "tt1375666"
    assert t.title_type is TitleType.MOVIE
    assert t.primary_title == "Inception"
    assert t.genres == ["Action", "Adventure", "Sci-Fi"]
    assert t.runtime_minutes == 148  # PT2H28M
    assert t.average_rating == 8.8
    assert t.num_votes == 2500000
    assert t.start_year == 2010


def test_extract_next_data(fixtures):
    html = (fixtures / "title_page.html").read_text()
    nd = title_mod.extract_next_data(html)
    assert nd["props"]["pageProps"]["tconst"] == "tt1375666"


def test_is_blocked_on_challenge():
    assert title_mod.is_blocked("<html><head><title>Just a moment...</title></head>")
    assert title_mod.is_blocked("")


def test_get_title_raises_on_block(monkeypatch):
    monkeypatch.setattr(title_mod.transport, "get_text", lambda url, **kw: "<html>Just a moment...</html>")
    try:
        title_mod.get_title("tt1375666")
        assert False, "expected RuntimeError"
    except RuntimeError as e:
        assert "WAF" in str(e)


def test_duration_minutes_zero_duration_not_dropped():
    # regression: "PT0H0M" used to collapse to None via `x or None`
    assert title_mod._duration_minutes({"duration": "PT0H0M"}) == 0
    assert title_mod._duration_minutes({"duration": "PT45M"}) == 45
    assert title_mod._duration_minutes({"duration": "PT2H"}) == 120
    assert title_mod._duration_minutes({"duration": "garbage"}) is None
    assert title_mod._duration_minutes({}) is None


def test_parse_name_ldjson():
    html = (
        '<script type="application/ld+json">'
        '{"@type":"Person","url":"/name/nm0634240/","name":"Christopher Nolan",'
        '"jobTitle":"Director, Writer","birthDate":"1970-07-30"}'
        "</script>"
    )
    n = name_mod.parse_name(html, imdb_id="nm0634240")
    assert n.imdb_id == "nm0634240"
    assert n.primary_name == "Christopher Nolan"
    assert n.birth_year == 1970
    assert "Director" in n.primary_professions
