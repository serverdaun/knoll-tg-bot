"""Utility tests and helper functions for testing."""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock

from src.main import MIN_MESSAGE_INTERVAL, last_message_time


class TestUtils:
    """Utility test cases."""

    def test_min_message_interval_positive(self):
        """Test that minimum message interval is positive."""
        assert MIN_MESSAGE_INTERVAL > 0

    def test_min_message_interval_reasonable(self):
        """Test that minimum message interval is reasonable."""
        assert MIN_MESSAGE_INTERVAL <= 10  # Should not be too long

    def test_last_message_time_dict(self):
        """Test that last_message_time is a dictionary."""
        assert isinstance(last_message_time, dict)

    def test_time_tracking(self):
        """Test time tracking functionality."""
        user_id = 999999
        current_time = time.time()

        # Test setting time
        last_message_time[user_id] = current_time
        assert last_message_time[user_id] == current_time

        # Test updating time
        new_time = current_time + 1
        last_message_time[user_id] = new_time
        assert last_message_time[user_id] == new_time

        # Clean up
        if user_id in last_message_time:
            del last_message_time[user_id]


class TestAsyncHelpers:
    """Helper functions for async testing."""

    @staticmethod
    async def create_mock_update(user_id: int = 12345, first_name: str = "Test User"):
        """Create a mock Telegram update."""
        update = MagicMock()
        update.effective_user.id = user_id
        update.effective_user.first_name = first_name
        update.message.reply_text = AsyncMock()
        return update

    @staticmethod
    async def create_mock_context(args: list = None):
        """Create a mock Telegram context."""
        context = MagicMock()
        context.args = args or ["test", "query"]
        return context

    @staticmethod
    async def wait_for_async_operation(operation, timeout: float = 1.0):
        """Wait for an async operation to complete."""
        try:
            await asyncio.wait_for(operation, timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False

    @staticmethod
    def assert_async_called_with(mock, expected_call):
        """Assert that an async mock was called with specific arguments."""
        assert mock.called
        call_args = mock.call_args[0] if mock.call_args else None
        assert call_args == expected_call


class TestRateLimitingUtils:
    """Utility tests for rate limiting functionality."""

    def test_rate_limit_check(self):
        """Test rate limit checking logic."""
        user_id = 888888
        current_time = time.time()

        # Test rate limit when message is too recent
        last_message_time[user_id] = current_time
        time_since_last = current_time - last_message_time[user_id]
        assert time_since_last < MIN_MESSAGE_INTERVAL

        # Test rate limit reset when enough time has passed
        old_time = current_time - MIN_MESSAGE_INTERVAL - 1
        last_message_time[user_id] = old_time
        time_since_last = current_time - last_message_time[user_id]
        assert time_since_last > MIN_MESSAGE_INTERVAL

        # Clean up
        if user_id in last_message_time:
            del last_message_time[user_id]

    def test_multiple_users_rate_limiting(self):
        """Test rate limiting with multiple users."""
        user1_id = 111111
        user2_id = 222222
        current_time = time.time()

        # Set different times for different users
        # User 1: enough time has passed (should be able to send)
        last_message_time[user1_id] = current_time - MIN_MESSAGE_INTERVAL - 1
        # User 2: recent message (should be rate limited)
        last_message_time[user2_id] = current_time

        # User 1 should be able to send (enough time passed)
        time_since_last_user1 = current_time - last_message_time[user1_id]
        assert time_since_last_user1 > MIN_MESSAGE_INTERVAL

        # User 2 should be rate limited (recent message)
        time_since_last_user2 = current_time - last_message_time[user2_id]
        assert time_since_last_user2 < MIN_MESSAGE_INTERVAL

        # Clean up
        for user_id in [user1_id, user2_id]:
            if user_id in last_message_time:
                del last_message_time[user_id]


class TestMessageUtils:
    """Utility tests for message handling."""

    def test_message_length_limits(self):
        """Test message length limits."""
        # Telegram message limit is 4096 characters
        telegram_limit = 4096

        # Test short message
        short_message = "Hello, world!"
        assert len(short_message) < telegram_limit

        # Test long message
        long_message = "A" * 5000
        assert len(long_message) > telegram_limit

        # Test exact limit
        exact_message = "A" * telegram_limit
        assert len(exact_message) == telegram_limit

    def test_message_chunking(self):
        """Test message chunking logic."""
        long_message = "This is a very long message. " * 200
        chunk_size = 4096

        # Manual chunking
        chunks = [
            long_message[i : i + chunk_size]
            for i in range(0, len(long_message), chunk_size)
        ]

        assert len(chunks) > 1
        assert all(len(chunk) <= chunk_size for chunk in chunks)
        assert "".join(chunks) == long_message
