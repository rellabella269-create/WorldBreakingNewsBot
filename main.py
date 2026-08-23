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
    NEWS_CHANNEL,
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
# NEWS POSTING LOOP
# ==========================================================

async def news_publishing_loop(bot: Bot):
    """
    Continuously checks configured news feeds and publishes
    new stories to the main Telegram channel.
    """

    logger.info(
        "News publishing system started."
    )

    logger.info(
        "Target channel: %s",
        NEWS_CHANNEL,
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
                posted_count = 0

                for article in articles:

                    # --------------------------------------------------
                    # DUPLICATE CHECK
                    # --------------------------------------------------

                    if db.news_exists(
                        article.article_id
                    ):
                        continue

                    # --------------------------------------------------
                    # FORMAT NEWS
                    # --------------------------------------------------

                    message = format_news_post(
                        article
                    )

                    # --------------------------------------------------
                    # POST TO CHANNEL
                    # --------------------------------------------------

                    try:
                        await bot.send_message(
                            chat_id=NEWS_CHANNEL,
                            text=message,
                            parse_mode="HTML",
                            disable_web_page_preview=False,
                        )

                        # ------------------------------------------------
                        # SAVE ONLY AFTER SUCCESSFUL POST
                        # ------------------------------------------------

                        db.add_news(
                            article_id=article.article_id,
                            title=article.title,
                            link=article.link,
                            source=article.source,
                            category=article.category,
                        )

                        posted_count += 1

                        logger.info(
                            "Posted news: %s",
                            article.title,
                        )

                        # Small delay between posts so the channel
                        # does not get flooded when many stories arrive.
                        await asyncio.sleep(2)

                    except Exception as exc:
                        logger.exception(
                            "Failed to post article '%s': %s",
                            article.title,
                            exc,
                        )

                if posted_count:
                    logger.info(
                        "Posted %d new article(s).",
                        posted_count,
                    )
                else:
                    logger.info(
                        "No new articles to publish."
                    )

            # ----------------------------------------------------------
            # DATABASE CLEANUP
            # ----------------------------------------------------------

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

        # --------------------------------------------------------------
        # WAIT BEFORE NEXT CHECK
        # --------------------------------------------------------------

        await asyncio.sleep(
            CHECK_INTERVAL
        )


# ==========================================================
# STARTUP
# ==========================================================

async def main():
    """
    Start the Telegram bot and the automatic news publisher.
    """

    logger.info(
        "=========================================="
    )

    logger.info(
        "Starting World Breaking News Bot"
    )

    logger.info(
        "=========================================="
    )

    # ------------------------------------------------------
    # REGISTER ADMIN COMMANDS
    # ------------------------------------------------------

    if ADMIN_ID:
        register_admin_handlers(
            ADMIN_ID
        )

    # ------------------------------------------------------
    # CREATE BOT
    # ------------------------------------------------------

    bot = Bot(
        token=BOT_TOKEN
    )

    # ------------------------------------------------------
    # TEST BOT CONNECTION
    # ------------------------------------------------------

    try:
        bot_info = await bot.get_me()

        logger.info(
            "Bot connected successfully."
        )

        logger.info(
            "Bot username: @%s",
            bot_info.username,
        )

    except Exception as exc:
        logger.exception(
            "Could not connect to Telegram: %s",
            exc,
        )

        await bot.session.close()

        raise

    # ------------------------------------------------------
    # START NEWS TASK
    # ------------------------------------------------------

    news_task = asyncio.create_task(
        news_publishing_loop(bot)
    )

    try:
        # --------------------------------------------------
        # START TELEGRAM POLLING
        # --------------------------------------------------

        await dp.start_polling(bot)

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
        # CLOSE BOT SESSION
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
        asyncio.run(main())

    except KeyboardInterrupt:
        logger.info(
            "Application stopped manually."
        )
