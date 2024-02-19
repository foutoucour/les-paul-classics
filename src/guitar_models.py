from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import List, Optional

from arsenic import Session
from arsenic.errors import NoSuchElement, ArsenicTimeout
from loguru import logger
from pydantic import BaseModel

from src.utils import price_to_int, Year, template_environment


class PriceGuide(BaseModel):
    low_bracket: Optional[int]
    high_bracket: Optional[int]
    average: Optional[int]

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

            average = None
            if low_bracket and high_bracket:
                average = int((low_bracket + high_bracket) / 2)

            return cls(
                low_bracket=low_bracket,
                high_bracket=high_bracket,
                average=average,
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
