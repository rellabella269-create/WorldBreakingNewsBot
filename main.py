import asyncio
import logging
from contextlib import suppress

from aiogram import Bot

from bot import dp, register_admin_handlers
from config import (
    ADMIN_ID,
    BOT_TOKEN,
    CHECK_INTERVAL,
    MAX_STORED_ARTICLES,
    NEWS_CHANNELS,
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
# SETTINGS FOR MANY CHANNELS
# ==========================================================

# Small delay between channel posts.
# This helps avoid sending a huge burst of requests.
CHANNEL_SEND_DELAY = 0.15

# Maximum number of retry attempts for a failed post.
MAX_RETRIES = 3


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
    Send one article to one Telegram channel.

    Returns:
        True  = successfully posted
        False = failed
    """

    # ------------------------------------------------------
    # ALREADY POSTED?
    # ------------------------------------------------------

    if db.news_exists(
        article.article_id,
        str(channel_id),
    ):
        return True

    # ------------------------------------------------------
    # RETRIES
    # ------------------------------------------------------

    for attempt in range(
        1,
        MAX_RETRIES + 1,
    ):
        try:
            await bot.send_message(
                chat_id=channel_id,
                text=message,
                parse_mode="HTML",
                disable_web_page_preview=False,
            )

            # ------------------------------------------------
            # SAVE SUCCESSFUL POST
            # ------------------------------------------------

            db.add_news(
                article_id=article.article_id,
                channel_id=str(channel_id),
                title=article.title,
                link=article.link,
                source=article.source,
                category=article.category,
            )

            logger.info(
                "SUCCESS | %s | %s",
                channel_id,
                article.title,
            )

            return True

        except Exception as exc:
            logger.warning(
                "FAILED | channel=%s | attempt=%d/%d | %s",
                channel_id,
                attempt,
                MAX_RETRIES,
                exc,
            )

            if attempt < MAX_RETRIES:
                await asyncio.sleep(
                    1.5 * attempt
                )

    logger.error(
        "PERMANENT FAILURE | channel=%s | article=%s",
        channel_id,
        article.title,
    )

    return False


# ==========================================================
# SEND ARTICLE TO ALL CHANNELS
# ==========================================================

async def publish_article_to_all_channels(
    bot: Bot,
    article,
) -> tuple[int, int]:
    """
    Publish one article to every configured channel.

    Returns:
        (successful_posts, failed_posts)
    """

    message = format_news_post(
        article
    )

    success_count = 0
    failed_count = 0

    logger.info(
        "Publishing article to %d channel(s): %s",
        len(NEWS_CHANNELS),
        article.title,
    )

    for channel_id in NEWS_CHANNELS:

        success = await send_article_to_channel(
            bot=bot,
            article=article,
            channel_id=channel_id,
            message=message,
        )

        if success:
            success_count += 1
        else:
            failed_count += 1

        # --------------------------------------------------
        # DELAY BETWEEN CHANNEL REQUESTS
        # --------------------------------------------------

        await asyncio.sleep(
            CHANNEL_SEND_DELAY
        )

    return (
        success_count,
        failed_count,
    )


# ==========================================================
# NEWS PUBLISHING LOOP
# ==========================================================

async def news_publishing_loop(
    bot: Bot,
):
    """
    Continuously check news feeds and publish new articles
    to all configured Telegram channels.
    """

    logger.info(
        "=========================================="
    )

    logger.info(
        "NEWS PUBLISHING SYSTEM STARTED"
    )

    logger.info(
        "Configured channels: %d",
        len(NEWS_CHANNELS),
    )

    logger.info(
        "Check interval: %d seconds",
        CHECK_INTERVAL,
    )

    logger.info(
        "=========================================="
    )

    while True:

        try:
            logger.info(
                "Checking for new news..."
            )

            articles = get_latest_news()

            if not articles:
                logger.info(
                    "No articles found."
                )

            else:

                logger.info(
                    "Found %d article(s).",
                    len(articles),
                )

                # --------------------------------------------------
                # PROCESS ARTICLES
                # --------------------------------------------------

                for article in articles:

                    # ------------------------------------------------
                    # CHECK WHETHER EVERY CHANNEL ALREADY RECEIVED IT
                    # ------------------------------------------------

                    posted_channels = set(
                        db.get_posted_channels(
                            article.article_id
                        )
                    )

                    all_channels = {
                        str(channel)
                        for channel in NEWS_CHANNELS
                    }

                    remaining_channels = (
                        all_channels - posted_channels
                    )

                    # ------------------------------------------------
                    # EVERYTHING ALREADY POSTED
                    # ------------------------------------------------

                    if not remaining_channels:
                        logger.info(
                            "Already posted everywhere: %s",
                            article.title,
                        )
                        continue

                    logger.info(
                        "Article needs posting to %d channel(s): %s",
                        len(remaining_channels),
                        article.title,
                    )

                    # ------------------------------------------------
                    # FORMAT ONCE
                    # ------------------------------------------------

                    message = format_news_post(
                        article
                    )

                    success_count = 0
                    failed_count = 0

                    # ------------------------------------------------
                    # POST TO REMAINING CHANNELS
                    # ------------------------------------------------

                    for channel_id in NEWS_CHANNELS:

                        channel_id = str(
                            channel_id
                        )

                        # Skip channels that already received it.
                        if channel_id in posted_channels:
                            continue

                        success = await send_article_to_channel(
                            bot=bot,
                            article=article,
                            channel_id=channel_id,
                            message=message,
                        )

                        if success:
                            success_count += 1
                        else:
                            failed_count += 1

                        await asyncio.sleep(
                            CHANNEL_SEND_DELAY
                        )

                    # ------------------------------------------------
                    # SUMMARY
                    # ------------------------------------------------

                    logger.info(
                        "ARTICLE COMPLETE | "
                        "success=%d | failed=%d | title=%s",
                        success_count,
                        failed_count,
                        article.title,
                    )

                    # ------------------------------------------------
                    # SMALL BREAK BEFORE NEXT ARTICLE
                    # ------------------------------------------------

                    await asyncio.sleep(1)

            # ------------------------------------------------------
            # DATABASE CLEANUP
            # ------------------------------------------------------

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
                "Unexpected error in news publishing loop: %s",
                exc,
            )

        # ----------------------------------------------------------
        # WAIT UNTIL NEXT CHECK
        # ----------------------------------------------------------

        await asyncio.sleep(
            CHECK_INTERVAL
        )


# ==========================================================
# STARTUP
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
    # SHOW CHANNEL COUNT
    # ------------------------------------------------------

    logger.info(
        "Loaded %d Telegram channels.",
        len(NEWS_CHANNELS),
    )

    if len(NEWS_CHANNELS) > 100:
        logger.info(
            "100+ channel mode enabled."
        )

    # ------------------------------------------------------
    # REGISTER ADMIN COMMANDS
    # ------------------------------------------------------

    if ADMIN_ID:
        register_admin_handlers(
            ADMIN_ID
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
            "Could not connect to Telegram: %s",
            exc,
        )

        await bot.session.close()

        raise

    # ------------------------------------------------------
    # START NEWS SYSTEM
    # ------------------------------------------------------

    news_task = asyncio.create_task(
        news_publishing_loop(
            bot
        )
    )

    try:

        # --------------------------------------------------
        # START TELEGRAM BOT
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
