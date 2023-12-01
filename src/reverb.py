import contextlib

from arsenic import Session, get_session
from arsenic.session import Element
from loguru import logger

from src.utils import service, browser


@contextlib.asynccontextmanager
async def log_in(username: str, password: str) -> Session:
    session: Session
    async with get_session(service, browser) as session:
        await session.get("https://reverb.com/ca/signin")
        await session.wait_for_element(20, "#user_session_login")
        login: Element = await session.get_element("#user_session_login")
        logger.info(f"Login to reverb.com as {username}")
        await login.send_keys(username)
        password_element: Element = await session.get_element("#password")
        await password_element.send_keys(password)

        button: Element = await session.get_element("input.button")
        await button.click()

        yield session
