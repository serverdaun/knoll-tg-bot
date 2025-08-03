import asyncio
import logging
import os
import signal
import sys
import time
from contextlib import asynccontextmanager

import uvicorn
from agents import Agent, ModelSettings, Runner, WebSearchTool, trace
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from telegram import Update
from telegram.error import RetryAfter
from telegram.ext import Application, CommandHandler, ContextTypes

from src.prompts import AGENT_INSTRUCTIONS
from src.tools import wikipedia_search

# Set up logging to write logs to a file
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Rate limiting
last_message_time = {}
MIN_MESSAGE_INTERVAL = 2.0

# Health check state
app_start_time = time.time()
is_shutting_down = False

# Define the agent
knoll_agent = Agent(
    name="Knoll",
    instructions=AGENT_INSTRUCTIONS,
    model="gpt-4.1",
    tools=[wikipedia_search, WebSearchTool()],
    model_settings=ModelSettings(tool_choice="auto"),
)


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global is_shutting_down
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    is_shutting_down = True
    sys.exit(0)


# Register signal handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


# Function for responding to /ask
async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_shutting_down:
        logger.info("Ignoring message during shutdown")
        return

    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "Unknown"
    current_time = time.time()

    logger.info(f"User {user_name} (ID: {user_id}) sent a command")

    # Rate limiting check
    if user_id in last_message_time:
        time_since_last = current_time - last_message_time[user_id]
        if time_since_last < MIN_MESSAGE_INTERVAL:
            logger.info(
                f"User {user_name} hit rate limit - {time_since_last:.1f}s since last message"
            )
            try:
                await update.message.reply_text(
                    "Please wait a moment before asking another question..."
                )
            except RetryAfter as e:
                logger.warning(
                    f"Rate limit exceeded while sending rate limit message: {e.retry_after} seconds"
                )
            return

    user_query = " ".join(context.args)

    if not user_query:
        try:
            await update.message.reply_text("you forgot to ask ...")
        except RetryAfter as e:
            logger.warning(
                f"Rate limit exceeded while sending error message: {e.retry_after} seconds"
            )
        return

    logger.info(f"Processing query from {user_name}: {user_query[:50]}...")

    try:
        # Update last message time
        last_message_time[user_id] = current_time

        with trace("Knoll"):
            result = await Runner.run(knoll_agent, user_query)
            answer = result.final_output

        logger.info(f"Generated response for {user_name} ({len(answer)} characters)")

        # Add a small delay before sending response
        await asyncio.sleep(1.0)  # Increased delay

        # Handle long messages by splitting them
        if len(answer) > 4096:
            # Split long messages into chunks
            chunks = [answer[i : i + 4096] for i in range(0, len(answer), 4096)]
            logger.info(f"Splitting response for {user_name} into {len(chunks)} chunks")
            for i, chunk in enumerate(chunks):
                try:
                    await update.message.reply_text(chunk)
                    if i < len(chunks) - 1:  # Add delay between chunks
                        await asyncio.sleep(1.0)
                except RetryAfter as e:
                    logger.warning(
                        f"Rate limit exceeded while sending chunk {i+1}. Retry in {e.retry_after} seconds"
                    )
                    break
        else:
            # Wrap message sending in try-catch to handle RetryAfter
            try:
                await update.message.reply_text(answer)
            except RetryAfter as e:
                retry_after = e.retry_after
                logger.warning(
                    f"Rate limit exceeded while sending response. Retry in {retry_after} seconds"
                )
                # Try to send a shorter message
                try:
                    await update.message.reply_text(
                        f"Response ready but rate limited. Please wait {retry_after} seconds before asking again."
                    )
                except Exception as e:
                    logger.warning(f"Error sending rate limit message: {e}")
                    pass  # If even this fails, just log it

    except RetryAfter as e:
        # Handle Telegram rate limiting during agent execution
        retry_after = e.retry_after
        logger.warning(
            f"Rate limit exceeded during agent execution for {user_name}: {retry_after} seconds"
        )
        try:
            await update.message.reply_text(
                f"Rate limit exceeded. Please wait {retry_after} seconds before trying again."
            )
        except Exception:
            logger.warning(f"Rate limit exceeded: {retry_after} seconds")
    except Exception as e:
        logger.error(f"Error processing query for {user_name}: {e}")
        answer = f"Knoll encountered an error: {e}"
        try:
            await update.message.reply_text(answer)
        except RetryAfter as e:
            logger.warning(
                f"Rate limit exceeded while sending error message: {e.retry_after} seconds"
            )


# Define the Telegram application
telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()

# Register the command handler
telegram_app.add_handler(CommandHandler("ask", ask))


async def setup_webhook():
    """Set up the webhook URL."""
    webhook_url = os.getenv("WEBHOOK_URL")
    if not webhook_url:
        logger.warning("WEBHOOK_URL not set, webhook not configured")
        return False

    try:
        # Check if webhook is already set
        current_webhook = await telegram_app.bot.get_webhook_info()
        logger.info(f"Current webhook info: {current_webhook}")

        # Set the webhook
        success = await telegram_app.bot.set_webhook(url=f"{webhook_url}/webhook")
        if success:
            logger.info(f"Webhook successfully set to: {webhook_url}/webhook")
            return True
        else:
            logger.error("Failed to set webhook")
            return False
    except Exception as e:
        logger.error(f"Error setting up webhook: {e}")
        return False


async def check_webhook_status():
    """Check if webhook is properly configured."""
    try:
        webhook_info = await telegram_app.bot.get_webhook_info()
        logger.info(f"Webhook status: {webhook_info}")
        return webhook_info.get("url") is not None
    except Exception as e:
        logger.error(f"Error checking webhook status: {e}")
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Telegram app and set up webhook
    logger.info("Starting application...")
    webhook_configured = False

    try:
        await telegram_app.initialize()
        logger.info("Telegram app initialized")

        # Try to set up webhook with retries
        for attempt in range(3):
            try:
                webhook_configured = await setup_webhook()
                if webhook_configured:
                    logger.info("Telegram bot initialized successfully with webhook")
                    break
                else:
                    logger.warning(f"Webhook setup failed, attempt {attempt + 1}/3")
                    await asyncio.sleep(2)  # Wait before retry
            except Exception as e:
                logger.error(f"Webhook setup error on attempt {attempt + 1}: {e}")
                if attempt < 2:  # Don't sleep on last attempt
                    await asyncio.sleep(2)

        if not webhook_configured:
            logger.warning("Failed to configure webhook after 3 attempts")

    except Exception as e:
        logger.warning(f"Failed to initialize Telegram app: {e}")
        logger.info("Continuing without Telegram bot initialization")

    yield

    # Shutdown: Remove webhook and shutdown app
    logger.info("Shutting down application...")
    try:
        if webhook_configured:
            await telegram_app.bot.delete_webhook()
            logger.info("Webhook removed")
    except Exception as e:
        logger.error(f"Error removing webhook: {e}")
    finally:
        try:
            await telegram_app.shutdown()
            logger.info("Telegram app shutdown complete")
        except Exception as e:
            logger.error(f"Error shutting down Telegram app: {e}")


# Create FastAPI app with lifespan
web_app = FastAPI(title="Knoll Bot API", version="1.0.0", lifespan=lifespan)


@web_app.get("/")
async def root():
    return {
        "message": "Knoll Bot is running",
        "status": "healthy",
        "uptime": time.time() - app_start_time,
        "shutdown": is_shutting_down,
    }


@web_app.get("/health")
async def health_check():
    """Enhanced health check endpoint."""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")

    # Check if Telegram app is initialized
    telegram_status = "unknown"
    try:
        if hasattr(telegram_app, "bot") and telegram_app.bot:
            telegram_status = "connected"
        else:
            telegram_status = "not_initialized"
    except Exception as e:
        telegram_status = f"error: {str(e)}"

    return {
        "status": "healthy",
        "service": "knoll-bot",
        "uptime": time.time() - app_start_time,
        "telegram_status": telegram_status,
        "memory_usage": "ok",
    }


@web_app.get("/webhook-status")
async def webhook_status():
    """Check webhook configuration status."""
    try:
        webhook_info = await telegram_app.bot.get_webhook_info()
        return {
            "webhook_configured": webhook_info.get("url") is not None,
            "webhook_url": webhook_info.get("url"),
            "last_error_date": webhook_info.get("last_error_date"),
            "last_error_message": webhook_info.get("last_error_message"),
            "max_connections": webhook_info.get("max_connections"),
            "pending_update_count": webhook_info.get("pending_update_count"),
        }
    except Exception as e:
        return {"error": str(e), "webhook_configured": False}


@web_app.post("/webhook")
async def webhook_handler(request: Request):
    """Handle incoming webhook updates from Telegram."""
    if is_shutting_down:
        logger.info("Ignoring webhook during shutdown")
        return {"status": "shutting_down"}

    try:
        # Parse the incoming update
        update_data = await request.json()
        logger.info(
            f"Received webhook update: {update_data.get('update_id', 'unknown')}"
        )

        update = Update.de_json(update_data, telegram_app.bot)

        # Process the update
        await telegram_app.process_update(update)

        logger.info(f"Successfully processed webhook update: {update.update_id}")
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    logger.info("Starting Knoll bot with webhook support...")
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(web_app, host="0.0.0.0", port=port)
