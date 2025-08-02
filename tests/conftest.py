"""Pytest configuration and common fixtures."""

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock

import pytest
from dotenv import load_dotenv

# Load environment variables for testing
load_dotenv()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_telegram_update():
    """Mock Telegram Update object."""
    update = MagicMock()
    update.effective_user.id = 123456789
    update.effective_user.first_name = "Test User"
    update.message.reply_text = AsyncMock()
    return update


@pytest.fixture
def mock_telegram_context():
    """Mock Telegram Context object."""
    context = MagicMock()
    context.args = ["test", "query"]
    return context


@pytest.fixture
def mock_bot():
    """Mock Telegram Bot object."""
    bot = MagicMock()
    bot.send_message = AsyncMock()
    return bot


@pytest.fixture
def sample_wikipedia_response():
    """Sample Wikipedia search response."""
    return "Wikipedia is a free online encyclopedia, created and edited by volunteers around the world."


@pytest.fixture
def mock_wikipedia_search(monkeypatch):
    """Mock Wikipedia search function."""

    async def mock_search(query: str) -> str:
        return f"Mock Wikipedia result for: {query}"

    monkeypatch.setattr("src.tools.wikipedia_search", mock_search)
    return mock_search


@pytest.fixture
def test_env_vars():
    """Set up test environment variables."""
    original_token = os.getenv("TELEGRAM_TOKEN")
    os.environ["TELEGRAM_TOKEN"] = "test_token_12345"
    yield
    if original_token:
        os.environ["TELEGRAM_TOKEN"] = original_token
    else:
        os.environ.pop("TELEGRAM_TOKEN", None)
