from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import List, Optional

import yaml
from arsenic import Service, Browser, get_session, Session
from arsenic.errors import NoSuchElement, ArsenicTimeout
from loguru import logger
from pydantic import BaseModel, field_validator
from slugify import slugify

from src.utils import price_to_int, Year, template_environment, current_folder

static_data_file = current_folder / "static_data" / "guitar_models.yml"
static_data = yaml.safe_load(static_data_file.read_text())


class PriceGuide(BaseModel):
    low_bracket: Optional[int]
    high_bracket: Optional[int]

    @classmethod
    async def get(cls, session: Session) -> Optional[PriceGuide]:

        try:
            await session.wait_for_element(
                20, ".v2-csp-price-guide-module-content__estimates-container"
            )
            try:
                low_bracket_element = await session.get_element(
                    "span.price-display:nth-child(1)"
                )
                low_bracket = price_to_int(await low_bracket_element.get_text())
            except NoSuchElement:
                low_bracket = None
            try:
                high_bracket = await session.get_element(
                    "span.price-display:nth-child(3)"
                )
                high_bracket = price_to_int(await high_bracket.get_text())
            except NoSuchElement:
                high_bracket = None

            return cls(
                low_bracket=low_bracket,
                high_bracket=high_bracket,
            )

        except ArsenicTimeout:
            logger.debug(f"{await session.get_url()}: No price guide found, skipped")
            return None

        except NoSuchElement as e:
            logger.warning(f"{await session.get_url()}: {e}, {e.__class__.__name__}")
            return None
        except Exception as e:
            logger.error(f"{await session.get_url()}: {e}, {e.__class__.__name__}")
            return None


class Collections(Enum):
    wanna = "Wanna"
    owned = "Owned"
    no = "No"


class Editions(Enum):
    standard = "Standard"
    limited = "Limited"


class GuitarModel(BaseModel):
    name: str
    image: str
    url: str
    description: Optional[str] = None
    collection: Collections = Collections.wanna
    edition: Editions = Editions.standard
    slug: str
    year: Year
    price_guide: Optional[PriceGuide] = None
    finishes: List[str]

    @field_validator("url")
    @classmethod
    def update_url(cls, value, _):
        if value:
            return f"https://reverb.com{value}"
        return value

    @classmethod
    async def get_from_url(
        cls, service: Service, browser: Browser, model_url: str
    ) -> GuitarModel:
        logger.info(model_url)
        session: Session
        async with get_session(service, browser) as session:
            await session.get(model_url)
            name_element = await session.get_element(
                "tr.collapsing-list__item:nth-child(2) > td:nth-child(2)"
                " > ul:nth-child(1) > li:nth-child(1) > div:nth-child(1)"
            )
            name = await name_element.get_text()
            year = await session.get_element(
                "tr.collapsing-list__item:nth-child(4) > td:nth-child(2)"
            )
            year = Year(year=await year.get_text())
            finish_elements = await session.get_element(
                "tr.collapsing-list__item:nth-child(3) > td:nth-child(2) > ul:nth-child(1)"
            )
            finishes = [e for e in (await finish_elements.get_text()).split("\n")]
            image_element = await session.get_element(
                ".csp2-header__image > img:nth-child(1)"
            )
            slug = slugify(name)
            price_guide = await PriceGuide.get(session)
            image = await image_element.get_attribute("src")

            description = None
            collection = Collections.wanna
            edition = Editions.standard

            if slug in static_data:
                static = static_data[slug]
                collection = Collections(static["collection"])
                edition = Editions(static["edition"])
                description = static["description"]

            return cls(
                name=name,
                image=image,
                url=model_url,
                slug=slug,
                year=year,
                price_guide=price_guide,
                finishes=finishes,
                collection=collection,
                edition=edition,
                description=description,
            )

    async def to_md(self, folder: Path) -> Path:
        output = await self.render_md()
        output_file = folder / f"{self.slug}.md"
        output_file.write_text(output)

        return output_file

    async def render_md(
        self, template_name: str = "guitar_models/models.md.jinja2"
    ) -> str:
        template = template_environment.get_template(template_name)
        # Define data to fill in the placeholders
        # Render the template with data
        output = template.render(self.model_dump())
        return output
