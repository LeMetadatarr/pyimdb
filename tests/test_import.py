import pyimdb


def test_version():
    assert pyimdb.__version__


def test_public_api():
    for name in ("search", "search_titles", "search_names", "download",
                 "stream_ratings", "get_title", "get_name", "title_to_extra",
                 "name_to_extra", "hit_to_extra", "canonical_imdb_id"):
        assert hasattr(pyimdb, name), name
