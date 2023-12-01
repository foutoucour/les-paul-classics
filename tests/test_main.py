import pytest

from src.main import update_mkdocs_nav_config


@pytest.mark.parametrize(
    "mkdocs,folder,paths,expected",
    [
        pytest.param(
            {},
            "guitars",
            ["aa", "bb", "cc"],
            {"nav": [{"guitars": ["guitars/aa", "guitars/bb", "guitars/cc"]}]},
            id="empty, guitar folder",
        ),
        pytest.param(
            {},
            "models",
            ["aa", "bb", "cc"],
            {"nav": [{"models": ["models/aa", "models/bb", "models/cc"]}]},
            id="empty, models folder",
        ),
        pytest.param(
            {},
            "models",
            ["bb", "aa", "cc"],
            {"nav": [{"models": ["models/aa", "models/bb", "models/cc"]}]},
            id="empty, models folder, ordered",
        ),
        pytest.param(
            {"guitars": ["11", "22", "33"]},
            "models",
            ["aa", "bb", "cc"],
            {
                "guitars": ["11", "22", "33"],
                "nav": [{"models": ["models/aa", "models/bb", "models/cc"]}],
            },
            id="existing nav empty",
        ),
        pytest.param(
            {"nav": [{"guitars": ["11", "22", "33"]}]},
            "models",
            ["aa", "bb", "cc"],
            {
                "nav": [
                    {"guitars": ["11", "22", "33"]},
                    {"models": ["models/aa", "models/bb", "models/cc"]},
                ]
            },
            id="existing nav pre-filled",
        ),
        pytest.param(
            {"nav": [{"models": ["11", "22", "33"]}]},
            "models",
            ["aa", "bb", "cc"],
            {
                "nav": [
                    {
                        "models": [
                            "11",
                            "22",
                            "33",
                            "models/aa",
                            "models/bb",
                            "models/cc",
                        ]
                    }
                ]
            },
            id="existing nav append",
        ),
        pytest.param(
            {"nav": [{"models": ["11", "22", "33", "models/aa"]}]},
            "models",
            ["aa", "bb", "cc"],
            {
                "nav": [
                    {
                        "models": [
                            "11",
                            "22",
                            "33",
                            "models/aa",
                            "models/bb",
                            "models/cc",
                        ]
                    }
                ]
            },
            id="existing nav no duplicata",
        ),
    ],
)
def test_update_mkdocs_nav_config(tmp_path, mkdocs, folder, paths, expected):
    res = update_mkdocs_nav_config(mkdocs, folder, paths)
    assert res == expected
