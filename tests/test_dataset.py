import json

from pyimdb import dataset


def test_configs():
    assert set(dataset.CONFIGS) == {
        "titles", "names", "ratings", "principals", "akas", "crew", "episodes"
    }


def test_title_rows(fixtures):
    path = fixtures / "title.basics.sample.tsv.gz"
    rows = list(dataset.title_rows(path=path))
    assert rows[0]["imdb_id"] == "tt1375666"
    assert rows[0]["genres"] == ["Action", "Adventure", "Sci-Fi"]
    assert rows[0]["is_adult"] is False


def test_crew_rows(fixtures):
    path = fixtures / "title.crew.sample.tsv.gz"
    rows = list(dataset.crew_rows(path=path))
    assert rows[0]["imdb_id"] == "tt1375666"
    assert rows[0]["directors"] == ["nm0634240"]
    assert rows[0]["writers"] == ["nm0634240"]


def test_rows_dispatch_unknown():
    try:
        list(dataset.rows("nope"))
        assert False
    except ValueError:
        pass


def test_export_jsonl(tmp_path, fixtures):
    path = fixtures / "title.ratings.sample.tsv.gz"
    out = tmp_path / "ratings.jsonl"
    n = dataset.export_jsonl("ratings", str(out), path=path)
    assert n == 2
    lines = out.read_text().splitlines()
    assert json.loads(lines[0])["imdb_id"] == "tt1375666"
