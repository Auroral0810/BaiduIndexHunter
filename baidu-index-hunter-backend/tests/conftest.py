import pytest
from loguru import logger

@pytest.fixture(scope="session", autouse=True)
def cleanup_logger():
    """
    Session-scoped fixture to cleanup loguru sinks at the end of the test session.
    This prevents 'atexit' handlers in crawlers from logging to closed sinks.
    """
    yield
    # At the end of the session, remove all sinks to avoid I/O errors on closed files
    # when atexit handlers fire.
    logger.remove()
