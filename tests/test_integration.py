"""Integration tests for the Knoll bot."""

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.main import ask, knoll_agent
from src.tools import wikipedia_search


class TestIntegration:
    """Integration test cases."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    @patch("src.main.Runner")
    async def test_full_query_flow(self, mock_runner):
        """Test the full flow from user query to response."""
        # Arrange
        mock_update = MagicMock()
        mock_update.effective_user.id = 12345
        mock_update.effective_user.first_name = "Test User"
        mock_update.message.reply_text = AsyncMock()

        mock_context = MagicMock()
        mock_context.args = ["What", "is", "Python?"]

        mock_result = MagicMock()
        mock_result.final_output = "Python is a high-level programming language known for its simplicity and readability."
        mock_runner.run = AsyncMock(return_value=mock_result)

        # Act
        await ask(mock_update, mock_context)

        # Assert
        mock_runner.run.assert_called_once_with(knoll_agent, "What is Python?")
        mock_update.message.reply_text.assert_called_once_with(
            "Python is a high-level programming language known for its simplicity and readability."
        )

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Wikipedia tool integration test requires external API access")
    async def test_wikipedia_tool_integration(self):
        """Test Wikipedia tool integration."""
        # Arrange
        query = "Python programming language"

        # Act - call the underlying function using the tool's invoke method
        result = await wikipedia_search.invoke({"query": query})

        # Assert
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_agent_configuration(self):
        """Test that the agent is properly configured."""
        # Assert
        assert knoll_agent.name == "Knoll"
        assert knoll_agent.instructions is not None
        assert len(knoll_agent.instructions) > 0
        assert knoll_agent.model == "gpt-4.1-mini"
        assert len(knoll_agent.tools) > 0

    @pytest.mark.integration
    def test_environment_variables(self):
        """Test that required environment variables are available."""
        # Note: In CI, these might not be set, so we just check if they exist
        # The actual values are not important for this test
        assert "TELEGRAM_TOKEN" in os.environ or "TELEGRAM_TOKEN" in os.environ.keys()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_rate_limiting_integration(self):
        """Test rate limiting in integration context."""
        import time

        from src.main import MIN_MESSAGE_INTERVAL, last_message_time

        # Arrange
        mock_update = MagicMock()
        mock_update.effective_user.id = 99999
        mock_update.effective_user.first_name = "Rate Test User"
        mock_update.message.reply_text = AsyncMock()

        mock_context = MagicMock()
        mock_context.args = ["test query"]

        # Set recent message time
        last_message_time[mock_update.effective_user.id] = time.time()

        # Act
        await ask(mock_update, mock_context)

        # Assert
        mock_update.message.reply_text.assert_called_once_with(
            "Please wait a moment before asking another question..."
        )

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_handling_integration(self):
        """Test error handling in integration context."""
        # Arrange
        mock_update = MagicMock()
        mock_update.effective_user.id = 88888
        mock_update.effective_user.first_name = "Error Test User"
        mock_update.message.reply_text = AsyncMock()

        mock_context = MagicMock()
        mock_context.args = ["test query"]

        # Mock Runner to raise an exception
        with patch("src.main.Runner") as mock_runner:
            mock_runner.run = AsyncMock(side_effect=Exception("Integration test error"))

            # Act
            await ask(mock_update, mock_context)

            # Assert
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args[0][0]
            assert "Knoll encountered an error" in call_args

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_long_response_handling_integration(self):
        """Test long response handling in integration context."""
        # Arrange
        mock_update = MagicMock()
        mock_update.effective_user.id = 77777
        mock_update.effective_user.first_name = "Long Response User"
        mock_update.message.reply_text = AsyncMock()

        mock_context = MagicMock()
        mock_context.args = ["generate long response"]

        # Create a response longer than Telegram's limit
        long_response = "This is a very long response. " * 200  # Will be > 4096 chars

        with patch("src.main.Runner") as mock_runner:
            mock_result = MagicMock()
            mock_result.final_output = long_response
            mock_runner.run = AsyncMock(return_value=mock_result)

            # Act
            await ask(mock_update, mock_context)

            # Assert
            # Should be called multiple times for chunks
            assert mock_update.message.reply_text.call_count > 1


class TestAgentTools:
    """Test agent tools integration."""

    @pytest.mark.integration
    def test_agent_has_wikipedia_tool(self):
        """Test that the agent has Wikipedia tool configured."""
        tool_names = [
            tool.__name__ if hasattr(tool, "__name__") else str(tool)
            for tool in knoll_agent.tools
        ]
        assert any("wikipedia" in name.lower() for name in tool_names)

    @pytest.mark.integration
    def test_agent_has_web_search_tool(self):
        """Test that the agent has web search tool configured."""
        tool_names = [str(tool) for tool in knoll_agent.tools]
        assert any("WebSearchTool" in name for name in tool_names)

    @pytest.mark.integration
    def test_agent_model_settings(self):
        """Test that agent model settings are configured."""
        assert knoll_agent.model_settings is not None
        assert knoll_agent.model_settings.tool_choice == "auto"
