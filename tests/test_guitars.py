from pathlib import Path

import pytest

from src.guitars import Guitar
from tests.guitars_data import guitars


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "data,filename",
    [
        pytest.param(
            guitars["gibson-les-paul-classic-vintage-1993-japan-yamano-price-drop"],
            "test-previous-price-gibson-les-paul-classic-vintage-1993.md",
            id="happy path: accept offers, available, previous price",
        ),
        pytest.param(
            guitars["gibson-les-paul-classic-vintage-1993-japan-yamano-good-deal"],
            "test-good-deal-gibson-les-paul-classic-vintage-1993.md",
            id="happy path: good deal",
        ),
        pytest.param(
            guitars["gibson-les-paul-classic-vintage-1993-japan-yamano"],
            "test-gibson-les-paul-classic-vintage-1993.md",
            id="happy path: accept offers, available",
        ),
        pytest.param(
            guitars["gibson-1994-les-paul-classic-plemium-plus"],
            "test-gibson-1994-les-paul-classic-plemium-plus.md",
            id="happy path: no model, accept offers, ended, no price guide",
        ),
        pytest.param(
            guitars[
                "2003-gibson-les-paul-classic-triple-humbucker-electric-guitar-w-ohsc"
            ],
            "test-2003-gibson-les-paul-classic-triple-humbucker.md",
            id="happy path: no offers, sold",
        ),
    ],
)
@pytest.mark.parametrize(
    "template,folder",
    (
        pytest.param("prices.md.jinja2", "prices", id="prices"),
        pytest.param("tags.md.jinja2", "tags", id="tags"),
        pytest.param("titles.md.jinja2", "titles", id="titles"),
        pytest.param("details.md.jinja2", "details", id="details"),
    ),
)
async def test_render_pieces_md(data: dict, filename: str, template: str, folder: str):
    guitar = Guitar(**data)
    expected = Path("/".join(["expected", "guitars", folder, filename]))
    output = await guitar.render_md("/".join(["guitars", template]))
    assert output == expected.read_text()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "data,filename,folder",
    [
        pytest.param(
            guitars[
                "2003-gibson-les-paul-classic-triple-humbucker-electric-guitar-w-ohsc"
            ],
            "test-2003-gibson-les-paul-classic-triple-humbucker.md",
            "full",
            id="happy path: no offers, sold",
        )
    ],
)
async def test_render_full_md(data: dict, filename: str, folder: str):
    guitar = Guitar(**data)
    expected = Path("/".join(["expected", "guitars", folder, filename]))
    output = await guitar.render_md()
    assert output == expected.read_text()
