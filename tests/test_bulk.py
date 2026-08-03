from pyimdb import bulk
from pyimdb.models import TitleType


def test_stream_titles_fixture(fixtures):
    path = fixtures / "title.basics.sample.tsv.gz"
    titles = list(bulk.stream_titles(path=path))
    assert len(titles) == 3
    inception = titles[0]
    assert inception.imdb_id == "tt1375666"
    assert inception.title_type is TitleType.MOVIE
    assert inception.start_year == 2010
    assert inception.end_year is None  # \N -> None
    assert inception.runtime_minutes == 148
    assert inception.genres == ["Action", "Adventure", "Sci-Fi"]
    got = titles[1]
    assert got.title_type is TitleType.TV_SERIES
    assert got.end_year == 2019
    game = titles[2]
    assert game.title_type is TitleType.VIDEO_GAME
    assert game.genres == []


def test_stream_limit(fixtures):
    path = fixtures / "title.basics.sample.tsv.gz"
    assert len(list(bulk.stream_titles(path=path, limit=1))) == 1


def test_stream_ratings(fixtures):
    path = fixtures / "title.ratings.sample.tsv.gz"
    ratings = {r.imdb_id: r for r in bulk.stream_ratings(path=path)}
    assert ratings["tt1375666"].average_rating == 8.8
    assert ratings["tt1375666"].num_votes == 2500000


def test_stream_names(fixtures):
    path = fixtures / "name.basics.sample.tsv.gz"
    names = {n.imdb_id: n for n in bulk.stream_names(path=path)}
    nolan = names["nm0634240"]
    assert nolan.primary_name == "Christopher Nolan"
    assert nolan.birth_year == 1970
    assert nolan.death_year is None
    assert "director" in nolan.primary_professions
    assert nolan.known_for_titles == ["tt1375666", "tt0816692"]


def test_stream_akas(fixtures):
    path = fixtures / "title.akas.sample.tsv.gz"
    akas = list(bulk.stream_akas(path=path))
    assert {a.region for a in akas} == {"US", "BR"}
    assert all(a.imdb_id == "tt1375666" for a in akas)


def test_stream_principals(fixtures):
    path = fixtures / "title.principals.sample.tsv.gz"
    principals = list(bulk.stream_principals(path=path))
    actor = next(p for p in principals if p.category == "actor")
    assert actor.name_id == "nm0000138"
    assert actor.characters == ["Cobb"]


def test_stream_episodes(fixtures):
    path = fixtures / "title.episode.sample.tsv.gz"
    ep = list(bulk.stream_episodes(path=path))[0]
    assert ep.imdb_id == "tt1480055"
    assert ep.series_id == "tt0944947"
    assert ep.season_number == 1
    assert ep.episode_number == 1


def test_dataset_url_and_path():
    assert bulk.dataset_url("title.ratings").endswith("title.ratings.tsv.gz")
    assert str(bulk.local_path("title.ratings")).endswith("title.ratings.tsv.gz")


def test_download_closes_response_on_write_failure(tmp_path, monkeypatch):
    # regression: an interrupted download used to leak the streamed response
    # (never closed) because `download()` had no try/finally around it.
    closed = []

    class FakeResp:
        def iter_content(self, chunk_size):
            yield b"partial-bytes"
            raise IOError("connection dropped")

        def close(self):
            closed.append(True)

    monkeypatch.setattr(bulk.transport, "get", lambda url, **kw: FakeResp())
    monkeypatch.setattr(bulk, "cache_dir", lambda: tmp_path)

    try:
        bulk.download("title.ratings", force=True)
        assert False, "expected IOError"
    except IOError:
        pass

    assert closed == [True]


def test_stream_raw_text():
    import gzip
    import io
    blob = io.BytesIO()
    with gzip.GzipFile(fileobj=blob, mode="wb") as f:
        f.write(b"tconst\taverageRating\tnumVotes\ntt1\t7.0\t10\n")
    rows = list(bulk.stream_raw_text(blob.getvalue()))
    assert rows[0]["tconst"] == "tt1"
