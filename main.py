import asyncio
import logging
from contextlib import suppress

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from bot import dp, register_admin_handlers
from config import (
    ADMIN_ID,
    BOT_TOKEN,
    CHECK_INTERVAL,
    MAX_STORED_ARTICLES,
)
from database import db
from formatter import format_news_post
from news_fetcher import get_latest_news


# ==========================================================
# LOGGING
# ==========================================================

logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(message)s"
    ),
)

logger = logging.getLogger(__name__)


# ==========================================================
# POSTING SETTINGS
# ==========================================================

CHANNEL_SEND_DELAY = 0.15
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2.0


# ==========================================================
# NORMALIZE CHANNEL
# ==========================================================

def normalize_channel(channel_id) -> str:
    """
    Convert common channel formats into a Telegram-compatible value.

    Examples:
        @mychannel
        mychannel
        -1001234567890
        https://t.me/mychannel
    """

    if channel_id is None:
        return ""

    value = str(channel_id).strip()

    if not value:
        return ""

    # Numeric Telegram channel ID
    if value.startswith("-100"):
        return value

    # Telegram URL
    if "t.me/" in value:
        value = value.split("t.me/", 1)[1]
        value = value.split("?", 1)[0]
        value = value.split("/", 1)[0]

    if value.startswith("@"):
        return value

    return f"@{value}"


# ==========================================================
# SEND ARTICLE TO ONE CHANNEL
# ==========================================================

async def send_article_to_channel(
    bot: Bot,
    article,
    channel_id: str,
    message: str,
) -> bool:
    """
    Resolve the channel first, then send using Telegram's
    real chat ID. This prevents PEER_ID_INVALID caused by
    bad/old channel references.
    """

    stored_channel = str(channel_id).strip()

    # ------------------------------------------------------
    # NORMALIZE CHANNEL
    # ------------------------------------------------------

    channel = normalize_channel(
        stored_channel
    )

    if not channel:

        logger.error(
            "Invalid empty channel reference: %r",
            stored_channel,
        )

        return False

    # ------------------------------------------------------
    # RESOLVE CHANNEL THROUGH TELEGRAM
    # ------------------------------------------------------

    try:

        chat = await bot.get_chat(
            chat_id=channel
        )

        real_chat_id = chat.id

        logger.info(
            "CHANNEL RESOLVED | stored=%s | telegram_id=%s | title=%s | username=%s",
            stored_channel,
            real_chat_id,
            getattr(chat, "title", ""),
            getattr(chat, "username", ""),
        )

    except TelegramBadRequest as exc:

        logger.error(
            "CHANNEL RESOLUTION FAILED | stored=%s | normalized=%s | error=%s",
            stored_channel,
            channel,
            exc,
        )

        return False

    except TelegramForbiddenError as exc:

        logger.error(
            "CHANNEL ACCESS DENIED | stored=%s | error=%s",
            stored_channel,
            exc,
        )

        return False

    except Exception as exc:

        logger.exception(
            "UNEXPECTED CHANNEL RESOLUTION ERROR | stored=%s | error=%s",
            stored_channel,
            exc,
        )

        return False

    # ------------------------------------------------------
    # DUPLICATE CHECK
    # ------------------------------------------------------

    if db.news_exists(
        article.article_id,
        str(real_chat_id),
    ):

        logger.info(
            "ALREADY POSTED | channel=%s | title=%s",
            real_chat_id,
            article.title,
        )

        return True

    # ------------------------------------------------------
    # RETRY LOOP
    # ------------------------------------------------------

    for attempt in range(
        1,
        MAX_RETRIES + 1,
    ):

        try:

            # ------------------------------------------------
            # SEND USING REAL TELEGRAM CHAT ID
            # ------------------------------------------------

            await bot.send_message(
                chat_id=real_chat_id,
                text=message,
                parse_mode="HTML",
                disable_web_page_preview=False,
            )

            # ------------------------------------------------
            # SAVE ONLY AFTER SUCCESS
            # ------------------------------------------------

            db.add_news(
                article_id=article.article_id,
                channel_id=str(real_chat_id),
                title=article.title,
                link=article.link,
                source=article.source,
                category=article.category,
            )

            logger.info(
                "POSTED | channel=%s | title=%s",
                real_chat_id,
                article.title,
            )

            return True

        except TelegramBadRequest as exc:

            error_text = str(exc)

            logger.warning(
                "TELEGRAM BAD REQUEST | channel=%s | attempt=%d/%d | error=%s",
                real_chat_id,
                attempt,
                MAX_RETRIES,
                error_text,
            )

            # Do not waste retries on an invalid peer.
            if "PEER_ID_INVALID" in error_text:

                logger.error(
                    "PEER_ID_INVALID | stored=%s | resolved=%s",
                    stored_channel,
                    real_chat_id,
                )

                return False

            if attempt < MAX_RETRIES:

                await asyncio.sleep(
                    RETRY_BASE_DELAY * attempt
                )

        except TelegramForbiddenError as exc:

            logger.error(
                "BOT HAS NO PERMISSION TO POST | channel=%s | error=%s",
                real_chat_id,
                exc,
            )

            return False

        except Exception as exc:

            logger.warning(
                "POST FAILED | channel=%s | attempt=%d/%d | error=%s",
                real_chat_id,
                attempt,
                MAX_RETRIES,
                exc,
            )

            if attempt < MAX_RETRIES:

                await asyncio.sleep(
                    RETRY_BASE_DELAY * attempt
                )

    logger.error(
        "FAILED PERMANENTLY | channel=%s | title=%s",
        real_chat_id,
        article.title,
    )

    return False


# ==========================================================
# PUBLISH ONE ARTICLE
# ==========================================================

async def publish_article(
    bot: Bot,
    article,
):
    """
    Send one article to every enabled channel.
    """

    channels = db.get_channel_ids(
        enabled_only=True
    )

    if not channels:

        logger.warning(
            "No active channels configured."
        )

        return

    # ------------------------------------------------------
    # FIND CHANNELS ALREADY POSTED
    # ------------------------------------------------------

    posted_channels = set(
        str(channel)
        for channel in db.get_posted_channels(
            article.article_id
        )
    )

    remaining_channels = [
        channel_id
        for channel_id in channels
        if str(channel_id) not in posted_channels
    ]

    if not remaining_channels:

        logger.info(
            "Article already posted to every active channel: %s",
            article.title,
        )

        return

    logger.info(
        "Publishing '%s' to %d channel(s).",
        article.title,
        len(remaining_channels),
    )

    # ------------------------------------------------------
    # FORMAT MESSAGE
    # ------------------------------------------------------

    message = format_news_post(
        article
    )

    successful = 0
    failed = 0

    # ------------------------------------------------------
    # SEND TO CHANNELS
    # ------------------------------------------------------

    for channel_id in remaining_channels:

        success = await send_article_to_channel(
            bot=bot,
            article=article,
            channel_id=str(channel_id),
            message=message,
        )

        if success:
            successful += 1
        else:
            failed += 1

        await asyncio.sleep(
            CHANNEL_SEND_DELAY
        )

    logger.info(
        "ARTICLE COMPLETE | success=%d | failed=%d | title=%s",
        successful,
        failed,
        article.title,
    )


# ==========================================================
# NEWS PUBLISHING LOOP
# ==========================================================

async def news_publishing_loop(
    bot: Bot,
):
    """
    Continuously checks the news feeds.
    """

    logger.info(
        "=========================================="
    )

    logger.info(
        "NEWS PUBLISHING SYSTEM STARTED"
    )

    logger.info(
        "=========================================="
    )

    while True:

        try:

            channel_count = db.get_channel_count(
                enabled_only=True
            )

            logger.info(
                "Active channels: %d",
                channel_count,
            )

            # ------------------------------------------------
            # NO CHANNELS
            # ------------------------------------------------

            if channel_count == 0:

                logger.info(
                    "No channels configured. "
                    "Use /addchannel @Channel from the admin account."
                )

            # ------------------------------------------------
            # FETCH NEWS
            # ------------------------------------------------

            logger.info(
                "Checking news sources..."
            )

            articles = get_latest_news()

            if not articles:

                logger.info(
                    "No news articles found."
                )

            else:

                logger.info(
                    "Found %d article(s).",
                    len(articles),
                )

                # ------------------------------------------------
                # PROCESS EACH ARTICLE
                # ------------------------------------------------

                for article in articles:

                    if channel_count == 0:
                        break

                    await publish_article(
                        bot=bot,
                        article=article,
                    )

                    await asyncio.sleep(
                        1
                    )

            # ------------------------------------------------
            # CLEAN OLD DATABASE RECORDS
            # ------------------------------------------------

            try:

                db.cleanup_old_news(
                    keep_count=MAX_STORED_ARTICLES
                )

            except Exception as exc:

                logger.exception(
                    "Database cleanup failed: %s",
                    exc,
                )

        except Exception as exc:

            logger.exception(
                "Unexpected error in news loop: %s",
                exc,
            )

        # ------------------------------------------------------
        # WAIT BEFORE NEXT CHECK
        # ------------------------------------------------------

        await asyncio.sleep(
            CHECK_INTERVAL
        )


# ==========================================================
# MAIN
# ==========================================================

async def main():

    logger.info(
        "=========================================="
    )

    logger.info(
        "WORLD BREAKING NEWS BOT"
    )

    logger.info(
        "=========================================="
    )

    # ------------------------------------------------------
    # REGISTER ADMIN HANDLERS
    # ------------------------------------------------------

    if ADMIN_ID:

        register_admin_handlers(
            ADMIN_ID
        )

    else:

        logger.warning(
            "ADMIN_ID is 0. "
            "Admin channel-management commands will not work."
        )

    # ------------------------------------------------------
    # CREATE TELEGRAM BOT
    # ------------------------------------------------------

    bot = Bot(
        token=BOT_TOKEN
    )

    # ------------------------------------------------------
    # TEST TELEGRAM CONNECTION
    # ------------------------------------------------------

    try:

        bot_info = await bot.get_me()

        logger.info(
            "Telegram connection successful."
        )

        logger.info(
            "Bot username: @%s",
            bot_info.username,
        )

        logger.info(
            "Bot ID: %s",
            bot_info.id,
        )

    except Exception as exc:

        logger.exception(
            "Telegram connection failed: %s",
            exc,
        )

        await bot.session.close()

        raise

    # ------------------------------------------------------
    # START NEWS TASK
    # ------------------------------------------------------

    news_task = asyncio.create_task(
        news_publishing_loop(
            bot
        )
    )

    try:

        # --------------------------------------------------
        # START TELEGRAM POLLING
        # --------------------------------------------------

        await dp.start_polling(
            bot
        )

    finally:

        # --------------------------------------------------
        # STOP NEWS TASK
        # --------------------------------------------------

        news_task.cancel()

        with suppress(
            asyncio.CancelledError
        ):
            await news_task

        # --------------------------------------------------
        # CLOSE TELEGRAM SESSION
        # --------------------------------------------------

        await bot.session.close()

        logger.info(
            "Bot stopped."
        )


# ==========================================================
# ENTRY POINT
# ==========================================================

if __name__ == "__main__":

    try:

        asyncio.run(
            main()
        )

    except KeyboardInterrupt:

        logger.info(
            "Application stopped manually."
        )
