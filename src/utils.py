from __future__ import annotations

import logging
import os
from enum import Enum
from pathlib import Path
from typing import Annotated

import structlog
from arsenic import services, browsers
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel, validator, Field


def price_to_int(string: str) -> int:
    return int(
        string.split("$")[1].replace(",", "").split(".")[0].split("CAD")[0].strip()
    )


class Statuses(Enum):
    AVAILABLE = "Available"
    ENDED = "Ended"
    SOLD = "Sold"
    # UNKNOWN = "Unknown"


def set_arsenic_log_level(level=logging.WARNING):
    # Create logger
    logger = logging.getLogger("arsenic")

    # We need factory, to return application-wide logger
    def logger_factory():
        return logger

    structlog.configure(logger_factory=logger_factory)
    logger.setLevel(level)


class Year(BaseModel):
    year: str
    start: Annotated[int, Field(validate_default=True)] = 0
    end: Annotated[int, Field(validate_default=True)] = 0

    @validator("start", always=True)
    def validate_start(cls, value, values):
        return int(values["year"].split("-")[0])

    @validator("end", always=True)
    def validate_end(cls, value, values):
        return int(values["year"].split("-")[-1])


defined_models_urls = {
    "Les Paul Special": "/ca/p/gibson-les-paul-special-2019-present",
}
service = services.Geckodriver(log_file=os.devnull)
browser = browsers.Firefox(
    **{
        "moz:firefoxOptions": {
            "args": [
                "-headless",
                "-log",
                "{'level': 'warning'}",
            ]
        }
    }
)

current_folder = Path(__file__).parent
template_environment = Environment(
    loader=FileSystemLoader(f"{current_folder}/templates"),
    trim_blocks=True,
    lstrip_blocks=True,
)
