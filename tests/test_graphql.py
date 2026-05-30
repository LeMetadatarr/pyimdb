"""Tests for pyimdb.graphql — the GraphQL live detail module.

Offline tests parse fixtures captured from the live endpoint.
Live tests (marked ``@pytest.mark.live``) hit ``caching.graphql.imdb.com``
and are skipped in CI unless ``-m live`` is passed.
"""
from __future__ import annotations

import json
import pathlib
import unittest.mock as mock

import pytest

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


# ─── helpers ──────────────────────────────────────────────────────────────────


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def _mock_post(fixture_name: str):
    """Return a context manager that patches _post() with fixture data."""
    data = _load(fixture_name)

    class _FakeResp:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return data

    return mock.patch("pyimdb.graphql._post", return_value=data)


# ─── TitleDetail offline ──────────────────────────────────────────────────────


class TestTitleDetailParsing:
    """Parse the Shawshank Redemption fixture without network."""

    @pytest.fixture(autouse=True)
    def _patch(self):
        fixture = _load("graphql_title_tt0111161.json")
        with mock.patch("pyimdb.graphql._post", return_value=fixture):
            yield

    def test_basic_fields(self):
        from pyimdb.graphql import get_title_detail

        td = get_title_detail("tt0111161")
        assert td.imdb_id == "tt0111161"
        assert td.primary_title == "The Shawshank Redemption"
        assert td.title_type == "movie"
        assert td.start_year == 1994
        assert td.end_year is None
        assert td.runtime_seconds == 8520
        assert td.runtime_minutes == 142

    def test_ratings(self):
        from pyimdb.graphql import get_title_detail

        td = get_title_detail("tt0111161")
        assert td.average_rating is not None
        assert td.average_rating >= 9.0
        assert td.num_votes is not None
        assert td.num_votes > 1_000_000

    def test_plot(self):
        from pyimdb.graphql import get_title_detail

        td = get_title_detail("tt0111161")
        assert td.plot is not None
        assert len(td.plot) > 20

    def test_genres(self):
        from pyimdb.graphql import get_title_detail

        td = get_title_detail("tt0111161")
        assert "Drama" in td.genres

    def test_image(self):
        from pyimdb.graphql import get_title_detail

        td = get_title_detail("tt0111161")
        assert td.image_url is not None
        assert "media-amazon.com" in td.image_url

    def test_credits_director(self):
        from pyimdb.graphql import get_title_detail

        td = get_title_detail("tt0111161")
        assert len(td.directors) >= 1
        director = td.directors[0]
        assert director.name_id == "nm0001104"
        assert "Darabont" in director.name
        assert director.category == "director"

    def test_credits_cast_with_characters(self):
        from pyimdb.graphql import get_title_detail

        td = get_title_detail("tt0111161")
        cast = td.cast
        assert len(cast) >= 2
        # Tim Robbins should be in cast
        names = [c.name for c in cast]
        assert any("Robbins" in n or "Freeman" in n for n in names)
        # At least one cast member should have a character name
        assert any(len(c.characters) > 0 for c in cast)

    def test_akas(self):
        from pyimdb.graphql import get_title_detail

        td = get_title_detail("tt0111161")
        assert len(td.akas) > 0
        aka = td.akas[0]
        assert aka.text
        assert aka.country_id is not None

    def test_certificates(self):
        from pyimdb.graphql import get_title_detail

        td = get_title_detail("tt0111161")
        assert len(td.certificates) > 0
        cert = td.certificates[0]
        assert cert.rating
        assert cert.country_id is not None

    def test_release_date(self):
        from pyimdb.graphql import get_title_detail

        td = get_title_detail("tt0111161")
        assert td.release_year == 1994
        assert td.release_country is not None

    def test_is_adult(self):
        from pyimdb.graphql import get_title_detail

        td = get_title_detail("tt0111161")
        assert td.is_adult is False

    def test_to_title_downcast(self):
        from pyimdb.graphql import get_title_detail
        from pyimdb.models import Title, TitleType

        td = get_title_detail("tt0111161")
        title = td.to_title()
        assert isinstance(title, Title)
        assert title.imdb_id == "tt0111161"
        assert title.title_type == TitleType.MOVIE
        assert title.runtime_minutes == 142
        assert "Drama" in title.genres
        assert len(title.directors) >= 1

    def test_to_dict(self):
        from pyimdb.graphql import get_title_detail

        td = get_title_detail("tt0111161")
        d = td.to_dict()
        assert isinstance(d, dict)
        assert d["imdb_id"] == "tt0111161"
        assert "credits" in d
        assert "akas" in d


# ─── Inception title fixture ──────────────────────────────────────────────────


class TestInceptionFixture:
    """Sanity-check the Inception fixture."""

    @pytest.fixture(autouse=True)
    def _patch(self):
        fixture = _load("graphql_title_tt1375666.json")
        with mock.patch("pyimdb.graphql._post", return_value=fixture):
            yield

    def test_inception_title(self):
        from pyimdb.graphql import get_title_detail

        td = get_title_detail("tt1375666")
        assert td.primary_title == "Inception"
        assert td.start_year == 2010
        assert td.title_type == "movie"
        assert len(td.credits) >= 1


# ─── NameDetail offline ───────────────────────────────────────────────────────


class TestNameDetailParsing:
    """Parse the Morgan Freeman fixture without network."""

    @pytest.fixture(autouse=True)
    def _patch(self):
        fixture = _load("graphql_name_nm0000151.json")
        with mock.patch("pyimdb.graphql._post", return_value=fixture):
            yield

    def test_basic_fields(self):
        from pyimdb.graphql import get_name_detail

        nd = get_name_detail("nm0000151")
        assert nd.imdb_id == "nm0000151"
        assert nd.primary_name == "Morgan Freeman"

    def test_birth_date(self):
        from pyimdb.graphql import get_name_detail

        nd = get_name_detail("nm0000151")
        assert nd.birth_year == 1937
        assert nd.birth_month == 6
        assert nd.birth_day == 1

    def test_death_date_none(self):
        from pyimdb.graphql import get_name_detail

        nd = get_name_detail("nm0000151")
        assert nd.death_year is None

    def test_professions(self):
        from pyimdb.graphql import get_name_detail

        nd = get_name_detail("nm0000151")
        assert len(nd.primary_professions) >= 1
        assert "Actor" in nd.primary_professions

    def test_image(self):
        from pyimdb.graphql import get_name_detail

        nd = get_name_detail("nm0000151")
        assert nd.image_url is not None
        assert "media-amazon.com" in nd.image_url

    def test_known_for(self):
        from pyimdb.graphql import get_name_detail

        nd = get_name_detail("nm0000151")
        assert len(nd.known_for) >= 1
        ids = [k.imdb_id for k in nd.known_for]
        # Shawshank should be in known-for
        assert "tt0111161" in ids
        # All should have titles
        assert all(k.title for k in nd.known_for)

    def test_bio(self):
        from pyimdb.graphql import get_name_detail

        nd = get_name_detail("nm0000151")
        assert nd.bio is not None
        assert len(nd.bio) > 50
        assert "Freeman" in nd.bio or "Morgan" in nd.bio

    def test_to_name_downcast(self):
        from pyimdb.graphql import get_name_detail
        from pyimdb.models import Name

        nd = get_name_detail("nm0000151")
        name = nd.to_name()
        assert isinstance(name, Name)
        assert name.imdb_id == "nm0000151"
        assert name.primary_name == "Morgan Freeman"
        assert name.birth_year == 1937
        assert "tt0111161" in name.known_for_titles

    def test_to_dict(self):
        from pyimdb.graphql import get_name_detail

        nd = get_name_detail("nm0000151")
        d = nd.to_dict()
        assert isinstance(d, dict)
        assert d["imdb_id"] == "nm0000151"
        assert "known_for" in d


# ─── Error handling ───────────────────────────────────────────────────────────


class TestErrorHandling:
    def test_unknown_id_raises(self):
        from pyimdb.graphql import get_title_detail

        error_resp = {
            "errors": [{"message": "Resource tt9999999 not found"}],
            "data": {"title": None},
        }
        with mock.patch("pyimdb.graphql._post", return_value=error_resp):
            with pytest.raises(ValueError, match="no 'title'"):
                get_title_detail("tt9999999")


# ─── Live tests ───────────────────────────────────────────────────────────────


@pytest.mark.live
class TestLiveGraphQL:
    """Hit the real GraphQL endpoint. Requires network and is skipped in CI."""

    def test_live_title(self):
        from pyimdb.graphql import get_title_detail

        td = get_title_detail("tt0111161")
        assert td.primary_title == "The Shawshank Redemption"
        assert td.average_rating >= 9.0
        assert len(td.credits) >= 1

    def test_live_name(self):
        from pyimdb.graphql import get_name_detail

        nd = get_name_detail("nm0000151")
        assert nd.primary_name == "Morgan Freeman"
        assert nd.birth_year == 1937
