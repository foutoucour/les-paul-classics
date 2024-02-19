import asyncio
import csv
import json
import logging
import os
from decimal import Decimal
from pathlib import Path
from typing import List, Protocol

import typer
import yaml
from arsenic import Session
from loguru import logger
from mkdocs.utils import yaml_load

from guitars import Guitars, Guitar
from reverb import log_in
from utils import set_arsenic_log_level, Statuses

app = typer.Typer()


class Exporter(Protocol):
    async def __call__(self, guitars: Guitars):
        ...


class JsonExporter:
    async def __call__(self, guitars: Guitars):
        listing_json = Path("../listing.json")
        logger.info(f"Writing to {listing_json}")
        listing_json.write_text(guitars.model_dump_json(indent=4))


class GuitarOut(Guitar):
    """Guitar model used for serialization."""

    class Config:
        json_encoders = {Decimal: lambda v: float(round(v, 2))}


class CSVExporter:
    async def __call__(self, guitars: Guitars):
        fieldnames = list(Guitar.schema()["properties"].keys())

        with open("../listing.csv", "w") as fp:
            writer = csv.DictWriter(fp, fieldnames=fieldnames)
            logger.info(f"Writing to {fp.name}")
            writer.writeheader()
            for guitar in guitars.elements:
                writer.writerow(json.loads(GuitarOut(**guitar.dict()).json()))
            # listing_csv.write_text(guitars.model_dump_csv())


exporters: List[Exporter] = [JsonExporter(), CSVExporter()]


async def run():
    session: Session
    urls: List[str] = []
    pages = (
        "https://reverb.com/ca/my/favorites",
        # "https://reverb.com/ca/my/favorites/ended",
    )
    reverb_login = os.environ["REVERB_LOGIN"]
    reverb_password = os.environ["REVERB_PASSWORD"]
    async with log_in(reverb_login, reverb_password) as session:
        for page in pages:
            await session.get(page)
            logger.info(f"scanning {page}")
            # Wait for the list to appear
            await session.wait_for_element(20, ".rc-listing-card__title")
            logger.info("found list")
            items = await session.get_elements("div.rc-listing-card__header > div > a")
            urls.extend([await item.get_attribute("href") for item in items])

    logger.info(f"Found {len(urls)} guitars")
    guitars = await get_guitars(urls)
    for exporter in exporters:
        await exporter(guitars)
    logger.info("Done")


async def render_models(guitars: Guitars):
    logger.info("Starting")
    path = Path("../docs/Models")
    path.mkdir(parents=True, exist_ok=True)
    unique = {
        guitar.model.name: guitar.model for guitar in guitars.elements if guitar.model
    }

    for guitar_model in unique.values():
        await guitar_model.to_md(path)
    logger.info("Done")


async def get_guitars(urls: List[str]) -> Guitars:
    logger.info("Starting")
    output = await asyncio.gather(
        *(Guitar.get_from_url(f"https://reverb.com{url}") for url in urls)
    )
    output = [o for o in output if o is not None]
    guitars = Guitars(elements=output)
    return guitars


def update_mkdocs():
    # use the loader from mkdocs to handle special constructors they uses
    logger.info("Updating mkdocs.yml")
    mkdocs = yaml_load(Path("../mkdocs.yml").open())
    for status in Statuses:
        data = update_mkdocs_nav_config(
            mkdocs,
            status.value,
            os.listdir(f"../docs/Guitars/{status.value}"),
            parent_folder="Guitars",
        )
        Path("../mkdocs.yml").write_text(yaml.dump(data))

    data = update_mkdocs_nav_config(
        mkdocs,
        "Models",
        os.listdir("../docs/Models"),
    )

    Path("../mkdocs.yml").write_text(yaml.dump(data))


def update_mkdocs_nav_config(
    mkdocs: dict, folder: str, paths: List[str], parent_folder: str = ""
) -> dict:
    base = mkdocs.setdefault("nav", [])

    if parent_folder:
        folder_paths = sorted(f"{parent_folder}/{folder}/{p}" for p in paths)
    else:
        folder_paths = sorted(f"{folder}/{p}" for p in paths)

    for item in base:
        if folder in item:
            content = set(item[folder])
            content.update(folder_paths)
            item[folder] = sorted(content)
            return mkdocs
    else:
        base.append({folder: folder_paths})
        return mkdocs


@app.command()
def main():
    set_arsenic_log_level(logging.WARNING)
    asyncio.run(run())


if __name__ == "__main__":
    main()
