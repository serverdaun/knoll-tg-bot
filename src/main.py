import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager

from agents import Agent, ModelSettings, Runner, WebSearchTool, trace
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from telegram import Update
from telegram.error import RetryAfter
from telegram.ext import Application, CommandHandler, ContextTypes
import uvicorn

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

# Define the agent
knoll_agent = Agent(
    name="Knoll",
    instructions=AGENT_INSTRUCTIONS,
    model="gpt-4.1-mini",
    tools=[wikipedia_search, WebSearchTool()],
    model_settings=ModelSettings(tool_choice="auto"),
)


# Function for responding to /ask
async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    if webhook_url:
        await telegram_app.bot.set_webhook(url=f"{webhook_url}/webhook")
        logger.info(f"Webhook set to: {webhook_url}/webhook")
    else:
        logger.warning("WEBHOOK_URL not set, webhook not configured")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Telegram app and set up webhook
    try:
        await telegram_app.initialize()
        await setup_webhook()
    except Exception as e:
        logger.warning(f"Failed to initialize Telegram app: {e}")
        logger.info("Continuing without Telegram bot initialization")
    yield
    # Shutdown: Remove webhook and shutdown app
    try:
        await telegram_app.bot.delete_webhook()
        logger.info("Webhook removed")
    except Exception as e:
        logger.error(f"Error removing webhook: {e}")
    finally:
        try:
            await telegram_app.shutdown()
        except Exception as e:
            logger.error(f"Error shutting down Telegram app: {e}")


# Create FastAPI app with lifespan
web_app = FastAPI(title="Knoll Bot API", version="1.0.0", lifespan=lifespan)


@web_app.get("/")
async def root():
    return {"message": "Knoll Bot is running", "status": "healthy"}


@web_app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "knoll-bot"}


@web_app.post("/webhook")
async def webhook_handler(request: Request):
    """Handle incoming webhook updates from Telegram."""
    try:
        # Parse the incoming update
        update_data = await request.json()
        update = Update.de_json(update_data, telegram_app.bot)

        # Process the update
        await telegram_app.process_update(update)

        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    logger.info("Starting Knoll bot with webhook support...")
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(web_app, host="0.0.0.0", port=port)
