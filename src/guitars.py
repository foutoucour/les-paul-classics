from __future__ import annotations

from pathlib import Path
from typing import Optional

from arsenic import get_session, Session
from arsenic.errors import NoSuchElement
from loguru import logger
from pydantic import BaseModel

from src.utils import (
    price_to_int,
    defined_models_urls,
    service,
    browser,
    template_environment,
)


class Guitar(BaseModel):
    url: str
    name: str
    model: str
    price: int
    shipping_price: int
    accept_offers: bool

    @classmethod
    async def get_from_url(cls, guitar_url) -> Optional[Guitar]:
        logger.info(guitar_url)

        session: Session
        async with get_session(service, browser) as session:
            await session.get(guitar_url)

            try:
                # Name of the guitar
                await session.wait_for_element(20, "h1")
                name_element = await session.get_element("h1")
                name = await name_element.get_text()
                logger.debug(f"Name: {name}")

                price_element = await session.get_element(
                    "span.price-display:nth-child(2)"
                )
                price_text = await price_element.get_text()
                price = price_to_int(price_text)
                logger.debug(f"Price: {price}")

                try:
                    shipping_price_element = await session.get_element(
                        "span.price-display:nth-child(1)"
                    )
                    shipping_price_text = await shipping_price_element.get_text()
                    shipping_price = price_to_int(shipping_price_text)
                except NoSuchElement:
                    shipping_price = 0

                logger.debug(f"Shipping price: {shipping_price}")

                try:
                    accept_offers_element = await session.get_element(".offer-action")
                    accept_offers = bool(await accept_offers_element.get_text())
                except NoSuchElement:
                    accept_offers = False

                logger.debug(f"Accept offers: {accept_offers}")

                try:
                    model_element = await session.get_element(
                        ".item2-product-module__title"
                    )
                    model_url = await model_element.get_attribute("href")
                    model_url = "".join(["https://reverb.com", model_url])
                except NoSuchElement:
                    model_element = await session.get_element(
                        "tr.collapsing-list__item:nth-child(4) > td:nth-child(2) >"
                        " ul:nth-child(1) > li:nth-child(1) > div:nth-child(1)"
                    )
                    model_name = await model_element.get_text()
                    model_url = defined_models_urls.get(model_name, "")

                logger.debug(f"Model: {model_url}")

                guitar = cls(
                    url=guitar_url,
                    name=name,
                    model=model_url,
                    price=price,
                    shipping_price=shipping_price,
                    accept_offers=accept_offers,
                )
                return guitar

            except Exception as e:
                logger.error(f"{await session.get_url()}: {e}, {e.__class__.__name__}")
                return None

    async def to_md(self, folder: Path) -> Path:
        output = await self.render_md()
        output_file = folder / f"{self.slug}.md"
        output_file.write_text(output)

        return output_file

    async def render_md(self, template_name: str = "guitars/guitars.md.jinja2") -> str:
        template = template_environment.get_template(template_name)
        # Define data to fill in the placeholders
        # Render the template with data
        output = template.render(self.model_dump())
        return output


class Guitars(BaseModel):
    elements: list[Guitar]
