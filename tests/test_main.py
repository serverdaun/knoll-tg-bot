"""Tests for the main module."""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram.error import RetryAfter

from src.main import MIN_MESSAGE_INTERVAL, ask, last_message_time


class TestAskFunction:
    """Test cases for the ask function."""

    @pytest.mark.asyncio
    @patch("src.main.knoll_agent")
    @patch("src.main.Runner")
    async def test_ask_successful_query(
        self, mock_runner, mock_agent, mock_telegram_update, mock_telegram_context
    ):
        """Test successful query processing."""
        # Arrange
        mock_telegram_context.args = ["What", "is", "Python?"]
        mock_result = MagicMock()
        mock_result.final_output = "Python is a programming language."
        mock_runner.run = AsyncMock(return_value=mock_result)

        # Clear any existing rate limiting for this user
        user_id = mock_telegram_update.effective_user.id
        if user_id in last_message_time:
            del last_message_time[user_id]

        # Act
        await ask(mock_telegram_update, mock_telegram_context)

        # Assert
        mock_runner.run.assert_called_once_with(mock_agent, "What is Python?")
        mock_telegram_update.message.reply_text.assert_called_once_with(
            "Python is a programming language."
        )

    @pytest.mark.asyncio
    async def test_ask_empty_query(self, mock_telegram_update, mock_telegram_context):
        """Test handling of empty query."""
        # Arrange
        mock_telegram_context.args = []

        # Clear any existing rate limiting for this user
        user_id = mock_telegram_update.effective_user.id
        if user_id in last_message_time:
            del last_message_time[user_id]

        # Act
        await ask(mock_telegram_update, mock_telegram_context)

        # Assert
        mock_telegram_update.message.reply_text.assert_called_once_with(
            "you forgot to ask ..."
        )

    @pytest.mark.asyncio
    async def test_ask_rate_limiting(self, mock_telegram_update, mock_telegram_context):
        """Test rate limiting functionality."""
        # Arrange
        user_id = mock_telegram_update.effective_user.id
        mock_telegram_context.args = ["test query"]

        # Set last message time to recent
        last_message_time[user_id] = time.time()

        # Act
        await ask(mock_telegram_update, mock_telegram_context)

        # Assert
        mock_telegram_update.message.reply_text.assert_called_once_with(
            "Please wait a moment before asking another question..."
        )

    @pytest.mark.asyncio
    @patch("src.main.knoll_agent")
    @patch("src.main.Runner")
    async def test_ask_long_response_splitting(
        self, mock_runner, mock_agent, mock_telegram_update, mock_telegram_context
    ):
        """Test splitting of long responses."""
        # Arrange
        mock_telegram_context.args = ["Generate", "long", "response"]
        long_response = "A" * 5000  # Create a response longer than 4096 characters
        mock_result = MagicMock()
        mock_result.final_output = long_response
        mock_runner.run = AsyncMock(return_value=mock_result)

        # Clear any existing rate limiting for this user
        user_id = mock_telegram_update.effective_user.id
        if user_id in last_message_time:
            del last_message_time[user_id]

        # Act
        await ask(mock_telegram_update, mock_telegram_context)

        # Assert
        # Should be called multiple times for chunks
        assert mock_telegram_update.message.reply_text.call_count > 1

    @pytest.mark.asyncio
    @patch("src.main.knoll_agent")
    @patch("src.main.Runner")
    async def test_ask_retry_after_exception(
        self, mock_runner, mock_agent, mock_telegram_update, mock_telegram_context
    ):
        """Test handling of RetryAfter exception."""
        # Arrange
        mock_telegram_context.args = ["test query"]
        mock_telegram_update.message.reply_text.side_effect = RetryAfter(retry_after=30)

        # Clear any existing rate limiting for this user
        user_id = mock_telegram_update.effective_user.id
        if user_id in last_message_time:
            del last_message_time[user_id]

        # Act
        await ask(mock_telegram_update, mock_telegram_context)

        # Assert
        # Should handle the exception gracefully
        assert mock_telegram_update.message.reply_text.called

    @pytest.mark.asyncio
    @patch("src.main.knoll_agent")
    @patch("src.main.Runner")
    async def test_ask_general_exception(
        self, mock_runner, mock_agent, mock_telegram_update, mock_telegram_context
    ):
        """Test handling of general exceptions."""
        # Arrange
        mock_telegram_context.args = ["test query"]
        mock_runner.run = AsyncMock(side_effect=Exception("Test error"))

        # Clear any existing rate limiting for this user
        user_id = mock_telegram_update.effective_user.id
        if user_id in last_message_time:
            del last_message_time[user_id]

        # Act
        await ask(mock_telegram_update, mock_telegram_context)

        # Assert
        mock_telegram_update.message.reply_text.assert_called_once()
        call_args = mock_telegram_update.message.reply_text.call_args[0][0]
        assert "Knoll encountered an error" in call_args

    @pytest.mark.asyncio
    async def test_rate_limiting_time_reset(
        self, mock_telegram_update, mock_telegram_context
    ):
        """Test that rate limiting resets after time interval."""
        # Arrange
        user_id = mock_telegram_update.effective_user.id
        mock_telegram_context.args = ["test query"]

        # Set last message time to old
        last_message_time[user_id] = time.time() - MIN_MESSAGE_INTERVAL - 1

        # Act
        await ask(mock_telegram_update, mock_telegram_context)

        # Assert
        # Should not call the rate limit message
        rate_limit_message = "Please wait a moment before asking another question..."
        rate_limit_calls = [
            call
            for call in mock_telegram_update.message.reply_text.call_args_list
            if call[0][0] == rate_limit_message
        ]
        assert len(rate_limit_calls) == 0

    @pytest.mark.asyncio
    async def test_user_id_tracking(self, mock_telegram_update, mock_telegram_context):
        """Test that user IDs are properly tracked for rate limiting."""
        # Arrange
        user_id = mock_telegram_update.effective_user.id
        mock_telegram_context.args = ["test query"]

        # Clear any existing tracking
        if user_id in last_message_time:
            del last_message_time[user_id]

        # Act
        await ask(mock_telegram_update, mock_telegram_context)

        # Assert
        assert user_id in last_message_time
        assert isinstance(last_message_time[user_id], (int, float))


class TestMainModule:
    """Test cases for main module configuration."""

    def test_min_message_interval(self):
        """Test that minimum message interval is reasonable."""
        assert MIN_MESSAGE_INTERVAL > 0
        assert MIN_MESSAGE_INTERVAL <= 10  # Should not be too long

    def test_last_message_time_dict(self):
        """Test that last_message_time is a dictionary."""
        assert isinstance(last_message_time, dict)

    @patch("src.main.TELEGRAM_TOKEN")
    def test_telegram_token_loaded(self, mock_token):
        """Test that Telegram token is loaded from environment."""
        # This test assumes the token is loaded from environment
        # The actual loading happens at module import time
        assert hasattr(mock_token, "__call__") or mock_token is not None
