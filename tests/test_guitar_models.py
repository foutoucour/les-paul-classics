from pathlib import Path

import pytest

from src.guitar_models import GuitarModel
from tests.guitars_data import guitars


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "data,filename",
    [
        pytest.param(
            guitars["gibson-les-paul-classic-vintage-1993-japan-yamano-price-drop"],
            "test-les-paul-classic.md",
            id="happy path: accept offers, available, previous price",
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
    guitar_model = GuitarModel(**data["model"])
    expected = Path("/".join(["expected", "guitar_models", folder, filename]))
    output = await guitar_model.render_md("/".join(["guitar_models", template]))
    assert output == expected.read_text()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "data,filename,folder",
    [
        pytest.param(
            guitars[
                "2003-gibson-les-paul-classic-triple-humbucker-electric-guitar-w-ohsc"
            ],
            "test-les-paul-classic-3-pickups.md",
            "full",
            id="happy path: no offers, sold",
        )
    ],
)
async def test_render_full_md(data: dict, filename: str, folder: str):
    guitar_model = GuitarModel(**data["model"])
    expected = Path("/".join(["expected", "guitar_models", folder, filename]))
    output = await guitar_model.render_md()
    assert output == expected.read_text()
