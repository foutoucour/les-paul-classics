from __future__ import annotations

from pathlib import Path
from typing import Optional

from arsenic import get_session, Session
from arsenic.errors import NoSuchElement
from loguru import logger
from pydantic import BaseModel
from slugify import slugify

from src.guitar_models import GuitarModel
from src.utils import (
    price_to_int,
    Statuses,
    defined_models_urls,
    service,
    browser,
    template_environment,
)


class Guitar(BaseModel):
    url: str
    name: str
    slug: str
    location: str
    image: str
    model: Optional[GuitarModel] = None
    previous_price: Optional[int]
    discount: Optional[int]
    price: int
    shipping_price: int
    accept_offers: bool
    status: Statuses

    @classmethod
    async def get_from_url(cls, guitar_url) -> Optional[Guitar]:
        logger.info(guitar_url)

        session: Session
        async with get_session(service, browser) as session:
            await session.get(guitar_url)

            try:
                # Name of the guitar
                name_element = await session.get_element("h1")
                name = await name_element.get_text()

                try:
                    previous_price_element = await session.get_element(
                        ".price-with-shipping__price__original"
                    )
                    previous_price_text = await previous_price_element.get_text()
                    previous_price = price_to_int(previous_price_text)
                except NoSuchElement:
                    previous_price = None

                try:
                    discount_element = await session.get_element(".ribbon-view")
                    discount_text = await discount_element.get_text()
                    discount = int(discount_text.split("%")[0])
                except NoSuchElement:
                    discount = None

                price_element = await session.get_element(
                    "span.price-display:nth-child(2)"
                )
                price_text = await price_element.get_text()
                price = price_to_int(price_text)

                shipping_price_element = await session.get_element(
                    "span.price-display:nth-child(1)"
                )
                shipping_price_text = await shipping_price_element.get_text()
                shipping_price = price_to_int(shipping_price_text)

                location_element = await session.get_element(
                    ".item2-shop-overview__location"
                )
                location = await location_element.get_text()

                try:
                    accept_offers_element = await session.get_element(".offer-action")
                    accept_offers = bool(await accept_offers_element.get_text())
                except NoSuchElement:
                    accept_offers = False

                try:
                    text_element = await session.get_element(
                        ".color-primary > div:nth-child(1)"
                    )
                    text = await text_element.get_text()
                    if "ENDED" in text:
                        status = Statuses.ENDED
                    elif "SOLD" in text:
                        status = Statuses.SOLD
                except NoSuchElement:
                    status = Statuses.AVAILABLE

                model = None
                try:
                    model_element = await session.get_element(
                        ".item2-product-module__title"
                    )
                    model_url = await model_element.get_attribute("href")
                except NoSuchElement:
                    model_element = await session.get_element(
                        "tr.collapsing-list__item:nth-child(4) > td:nth-child(2) >"
                        " ul:nth-child(1) > li:nth-child(1) > div:nth-child(1)"
                    )
                    model_name = await model_element.get_text()
                    model_url = defined_models_urls.get(model_name, "")

                if model_url:
                    model = await GuitarModel.get_from_url(
                        service, browser, f"https://reverb.com{model_url}"
                    )

                image_element = await session.get_element(
                    "div.lightbox-image__thumb:nth-child(1) > div:nth-child(1) > img:nth-child(1)"
                )
                image = await image_element.get_attribute("src")

                # Constructing the item
                guitar = cls(
                    url=guitar_url,
                    name=name,
                    image=image,
                    slug=slugify(name),
                    model=model,
                    location=location,
                    previous_price=previous_price,
                    discount=discount,
                    price=price,
                    shipping_price=shipping_price,
                    accept_offers=accept_offers,
                    status=status,
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
