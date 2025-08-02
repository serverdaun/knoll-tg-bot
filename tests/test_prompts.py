"""Tests for the prompts module."""

from src.prompts import AGENT_INSTRUCTIONS


class TestPrompts:
    """Test cases for prompts functionality."""

    def test_agent_instructions_not_empty(self):
        """Test that agent instructions are not empty."""
        assert AGENT_INSTRUCTIONS is not None
        assert len(AGENT_INSTRUCTIONS.strip()) > 0

    def test_agent_instructions_contains_knoll(self):
        """Test that agent instructions mention Knoll."""
        assert "Knoll" in AGENT_INSTRUCTIONS

    def test_agent_instructions_contains_polite(self):
        """Test that agent instructions mention being polite."""
        assert "polite" in AGENT_INSTRUCTIONS.lower()

    def test_agent_instructions_contains_helpful(self):
        """Test that agent instructions mention being helpful."""
        assert "helpful" in AGENT_INSTRUCTIONS.lower()

    def test_agent_instructions_contains_wikipedia(self):
        """Test that agent instructions mention Wikipedia access."""
        assert "Wikipedia" in AGENT_INSTRUCTIONS

    def test_agent_instructions_contains_web_search(self):
        """Test that agent instructions mention web search tools."""
        assert "web search" in AGENT_INSTRUCTIONS.lower()

    def test_agent_instructions_contains_language_instruction(self):
        """Test that agent instructions mention responding in user's language."""
        assert "language" in AGENT_INSTRUCTIONS.lower()

    def test_agent_instructions_contains_plain_text_instruction(self):
        """Test that agent instructions mention using plain text."""
        assert "plain text" in AGENT_INSTRUCTIONS.lower()

    def test_agent_instructions_contains_courteous_instruction(self):
        """Test that agent instructions mention being courteous."""
        assert "courteous" in AGENT_INSTRUCTIONS.lower()

    def test_agent_instructions_format(self):
        """Test that agent instructions are properly formatted."""
        # Should be a multi-line string
        assert "\n" in AGENT_INSTRUCTIONS

        # Should not have leading/trailing whitespace issues
        lines = AGENT_INSTRUCTIONS.split("\n")
        assert all(line.strip() or line == "" for line in lines)

    def test_agent_instructions_length(self):
        """Test that agent instructions have reasonable length."""
        # Instructions should be substantial but not excessive
        assert 50 < len(AGENT_INSTRUCTIONS) < 2000
