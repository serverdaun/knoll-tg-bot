[![CI](https://github.com/serverdaun/knoll-tg-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/serverdaun/knoll-tg-bot/actions/workflows/ci.yml)
[![CD](https://github.com/serverdaun/knoll-tg-bot/actions/workflows/deploy.yml/badge.svg)](https://github.com/serverdaun/knoll-tg-bot/actions/workflows/deploy.yml)

# Knoll Bot

A sophisticated Telegram bot powered by OpenAI agents that provides intelligent answers using Wikipedia and web search tools. Features webhook support, FastAPI integration, and comprehensive testing.

## Features

- 🤖 AI-powered responses using GPT-4.1
- 📚 Wikipedia search integration
- 🌐 Web search capabilities
- ⚡ Rate limiting and error handling
- 🌍 Multi-language support
- 🔗 Webhook support for production deployment
- 🚀 FastAPI integration with health checks
- 🐳 Docker containerization
- 📊 Comprehensive test coverage
- 🔒 Security-focused with non-root container user

## Architecture

The bot runs as a FastAPI application with webhook support for production deployments:

- **Webhook Mode**: Receives updates via HTTP webhooks (recommended for production)
- **Polling Mode**: Can also run in polling mode for development
- **Health Checks**: Built-in health check endpoints
- **Rate Limiting**: Intelligent rate limiting to prevent Telegram API limits

## Setup

### Prerequisites

- Python 3.12+
- Telegram Bot Token
- OpenAI API access

### Local Development

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
   # Using uv
   uv run python src/main.py
   
   # Or using make
   make run
   ```

### Docker Deployment

1. **Build the Docker image:**
   ```bash
   make docker-build
   ```

2. **Run with Docker:**
   ```bash
   make docker-run
   ```

### Production Deployment

For production deployment, set the following environment variables:

- `TELEGRAM_TOKEN`: Your Telegram bot token
- `WEBHOOK_URL`: Your webhook URL (e.g., `https://yourdomain.com`)
- `PORT`: Port to run the server on (default: 8080)

The bot will automatically configure webhooks when `WEBHOOK_URL` is set.

## Usage

Send `/ask <your question>` to the bot on Telegram to get AI-powered answers.

The bot supports:
- Multi-language responses
- Long message splitting (handles responses > 4096 characters)
- Rate limiting protection
- Error handling with user-friendly messages

## API Endpoints

When running as a FastAPI application, the following endpoints are available:

- `GET /`: Root endpoint with bot status
- `GET /health`: Health check endpoint
- `POST /webhook`: Telegram webhook endpoint

## Development

### Testing

```bash
# Run all tests
make test

# Run tests with coverage
make test-coverage

# Run unit tests only
make test-unit

# Run integration tests only
make test-integration
```

### Code Quality

```bash
# Format code
make format

# Run linting checks
make lint

# Clean up generated files
make clean
```

### Local CI

```bash
# Run all CI checks locally
make ci-local
```

## Project Structure

```
knoll-bot/
├── src/
│   ├── main.py          # Main application with FastAPI and Telegram bot
│   ├── prompts.py       # Agent instructions and prompts
│   └── tools.py         # Custom tools (Wikipedia search)
├── tests/               # Comprehensive test suite
├── Dockerfile           # Container configuration
├── Makefile            # Development commands
└── pyproject.toml      # Project configuration and dependencies
```

## Configuration

The bot uses the following environment variables:

- `TELEGRAM_TOKEN`: Required. Your Telegram bot token
- `WEBHOOK_URL`: Optional. Webhook URL for production deployment
- `PORT`: Optional. Server port (default: 8080)

## Requirements

- Python 3.12+
- Telegram Bot Token
- OpenAI API access
- For production: HTTPS endpoint for webhooks

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `make test`
5. Format code: `make format`
6. Submit a pull request

## License

This project is licensed under the MIT License.
