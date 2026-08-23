import html
import logging
from typing import Optional

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from config import NEWS_CHANNELS
from database import db
from formatter import (
    format_admin_stats,
    format_alert_status,
    format_help_message,
    format_welcome_message,
)
from news_fetcher import get_latest_news


# ==========================================================
# LOGGING
# ==========================================================

logger = logging.getLogger(__name__)


# ==========================================================
# DISPATCHER
# ==========================================================

dp = Dispatcher()


# ==========================================================
# CHANNEL LINK
# ==========================================================

def get_main_channel_url() -> Optional[str]:
    """
    Returns a usable public-channel URL when the first
    configured channel is a username such as @MyChannel.

    Numeric channel IDs cannot be converted into public
    t.me links automatically.
    """

    if not NEWS_CHANNELS:
        return None

    channel = str(NEWS_CHANNELS[0]).strip()

    if channel.startswith("@"):
        username = channel[1:].strip()

        if username:
            return f"https://t.me/{username}"

    return None


# ==========================================================
# MAIN KEYBOARD
# ==========================================================

def main_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="📰 Latest News",
                callback_data="latest_news",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🔔 Enable Alerts",
                callback_data="enable_alerts",
            ),
            InlineKeyboardButton(
                text="🔕 Disable Alerts",
                callback_data="disable_alerts",
            ),
        ],
    ]

    channel_url = get_main_channel_url()

    if channel_url:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="📢 News Channel",
                    url=channel_url,
                ),
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="ℹ️ Help",
                callback_data="help",
            ),
        ]
    )

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


# ==========================================================
# START COMMAND
# ==========================================================

@dp.message(CommandStart())
async def start_handler(message: Message):

    if not message.from_user:
        return

    user_id = message.from_user.id

    db.add_user(user_id)

    first_name = (
        message.from_user.first_name
        or ""
    )

    await message.answer(
        format_welcome_message(
            first_name
        ),
        reply_markup=main_keyboard(),
    )


# ==========================================================
# HELP COMMAND
# ==========================================================

@dp.message(Command("help"))
async def help_handler(message: Message):

    await message.answer(
        format_help_message(),
        reply_markup=main_keyboard(),
    )


# ==========================================================
# LATEST NEWS COMMAND
# ==========================================================

@dp.message(Command("news"))
async def news_handler(message: Message):

    await send_latest_news(
        message
    )


# ==========================================================
# ENABLE ALERTS
# ==========================================================

@dp.message(Command("on"))
async def enable_alerts_handler(
    message: Message,
):

    if not message.from_user:
        return

    user_id = message.from_user.id

    db.add_user(user_id)
    db.enable_alerts(user_id)

    await message.answer(
        format_alert_status(True),
        reply_markup=main_keyboard(),
    )


# ==========================================================
# DISABLE ALERTS
# ==========================================================

@dp.message(Command("off"))
async def disable_alerts_handler(
    message: Message,
):

    if not message.from_user:
        return

    user_id = message.from_user.id

    db.disable_alerts(user_id)

    await message.answer(
        format_alert_status(False),
        reply_markup=main_keyboard(),
    )


# ==========================================================
# SEND LATEST NEWS
# ==========================================================

async def send_latest_news(
    message: Message,
):

    try:

        articles = get_latest_news()

        if not articles:

            await message.answer(
                "📰 <b>No recent stories are available "
                "right now.</b>\n\n"
                "Please try again shortly.",
                reply_markup=main_keyboard(),
            )

            return

        # Keep the bot from flooding a user.
        articles = articles[:5]

        for article in articles:

            await message.answer(
                format_user_news(
                    article
                ),
                disable_web_page_preview=False,
            )

            # Small delay between messages.
            import asyncio

            await asyncio.sleep(0.5)

        await message.answer(
            "✅ <b>That's the latest available news.</b>",
            reply_markup=main_keyboard(),
        )

    except Exception as exc:

        logger.exception(
            "Failed to retrieve latest news: %s",
            exc,
        )

        await message.answer(
            "⚠️ <b>Unable to retrieve the latest "
            "news right now.</b>\n\n"
            "Please try again shortly.",
            reply_markup=main_keyboard(),
        )


# ==========================================================
# FORMAT USER NEWS
# ==========================================================

def format_user_news(
    article,
) -> str:

    title = html.escape(
        article.title or ""
    )

    summary = html.escape(
        article.summary or ""
    )

    source = html.escape(
        article.source or ""
    )

    link = html.escape(
        article.link or "",
        quote=True,
    )

    text = (
        f"📰 <b>{title}</b>\n\n"
    )

    if summary:

        # Keep direct bot replies shorter.
        if len(summary) > 700:
            summary = (
                summary[:697].rsplit(
                    " ",
                    1
                )[0]
                + "..."
            )

        text += (
            f"{summary}\n\n"
        )

    if source:

        text += (
            f"📌 <b>Source:</b> "
            f"{source}\n\n"
        )

    if link:

        text += (
            f'🔗 <a href="{link}">'
            f"Read Full Story"
            f"</a>"
        )

    return text


# ==========================================================
# LATEST NEWS BUTTON
# ==========================================================

@dp.callback_query(
    F.data == "latest_news"
)
async def latest_news_callback(
    callback: CallbackQuery,
):

    await callback.answer()

    if callback.message:

        await send_latest_news(
            callback.message
        )


# ==========================================================
# ENABLE ALERTS BUTTON
# ==========================================================

@dp.callback_query(
    F.data == "enable_alerts"
)
async def enable_alerts_callback(
    callback: CallbackQuery,
):

    user_id = callback.from_user.id

    db.add_user(user_id)
    db.enable_alerts(user_id)

    await callback.answer(
        "🔔 Alerts enabled!"
    )

    if callback.message:

        await callback.message.answer(
            format_alert_status(True),
            reply_markup=main_keyboard(),
        )


# ==========================================================
# DISABLE ALERTS BUTTON
# ==========================================================

@dp.callback_query(
    F.data == "disable_alerts"
)
async def disable_alerts_callback(
    callback: CallbackQuery,
):

    user_id = callback.from_user.id

    db.add_user(user_id)
    db.disable_alerts(user_id)

    await callback.answer(
        "🔕 Alerts disabled."
    )

    if callback.message:

        await callback.message.answer(
            format_alert_status(False),
            reply_markup=main_keyboard(),
        )


# ==========================================================
# HELP BUTTON
# ==========================================================

@dp.callback_query(
    F.data == "help"
)
async def help_callback(
    callback: CallbackQuery,
):

    await callback.answer()

    if callback.message:

        await callback.message.answer(
            format_help_message(),
            reply_markup=main_keyboard(),
        )


# ==========================================================
# ADMIN COMMANDS
# ==========================================================

def register_admin_handlers(
    admin_id: int,
):

    @dp.message(Command("stats"))
    async def stats_handler(
        message: Message,
    ):

        if not message.from_user:
            return

        if message.from_user.id != admin_id:

            await message.answer(
                "❌ You are not authorized "
                "to use this command."
            )

            return

        user_count = db.get_user_count()

        await message.answer(
            format_admin_stats(
                user_count
            )
        )

    @dp.message(Command("channels"))
    async def channels_handler(
        message: Message,
    ):

        if not message.from_user:
            return

        if message.from_user.id != admin_id:

            await message.answer(
                "❌ You are not authorized "
                "to use this command."
            )

            return

        count = len(
            NEWS_CHANNELS
        )

        await message.answer(
            "📢 <b>Channel Configuration</b>\n\n"
            f"Total configured channels: "
            f"<b>{count}</b>\n\n"
            "The news publisher will attempt "
            "to post new articles to every "
            "configured channel."
        )


# ==========================================================
# BOT RUNNER
# ==========================================================

async def run_bot(
    bot: Bot,
):

    logger.info(
        "Telegram bot polling started."
    )

    await dp.start_polling(
        bot
    )
