# Knoll Bot

A Telegram bot powered by OpenAI agents that provides helpful answers using Wikipedia and web search tools.

## Features

- 🤖 AI-powered responses using GPT-4
- 📚 Wikipedia search integration
- 🌐 Web search capabilities
- ⚡ Rate limiting and error handling
- 🌍 Multi-language support

## Setup

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Set environment variables:**
   ```bash
   cp .env.example .env
   # Add your TELEGRAM_TOKEN to .env
   ```

3. **Run the bot:**
   ```bash
   uv run python src/main.py
   ```

## Usage

Send `/ask <your question>` to the bot on Telegram to get AI-powered answers.

## Requirements

- Python 3.12+
- Telegram Bot Token
- OpenAI API access
