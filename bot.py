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

from config import NEWS_CHANNEL
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
# KEYBOARD
# ==========================================================

def main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
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
            [
                InlineKeyboardButton(
                    text="📢 News Channel",
                    url=f"https://t.me/{NEWS_CHANNEL.lstrip('@')}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="ℹ️ Help",
                    callback_data="help",
                ),
            ],
        ]
    )


# ==========================================================
# START COMMAND
# ==========================================================

@dp.message(CommandStart())
async def start_handler(message: Message):
    user_id = message.from_user.id

    db.add_user(user_id)

    first_name = message.from_user.first_name

    await message.answer(
        format_welcome_message(first_name),
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
    await send_latest_news(message)


# ==========================================================
# ENABLE ALERTS COMMAND
# ==========================================================

@dp.message(Command("on"))
async def enable_alerts_handler(message: Message):
    user_id = message.from_user.id

    db.add_user(user_id)
    db.enable_alerts(user_id)

    await message.answer(
        format_alert_status(True),
        reply_markup=main_keyboard(),
    )


# ==========================================================
# DISABLE ALERTS COMMAND
# ==========================================================

@dp.message(Command("off"))
async def disable_alerts_handler(message: Message):
    user_id = message.from_user.id

    db.disable_alerts(user_id)

    await message.answer(
        format_alert_status(False),
        reply_markup=main_keyboard(),
    )


# ==========================================================
# LATEST NEWS FUNCTION
# ==========================================================

async def send_latest_news(message: Message):
    try:
        articles = get_latest_news()

        if not articles:
            await message.answer(
                "📰 <b>No new stories are available "
                "right now.</b>\n\n"
                "Please check again shortly.",
                reply_markup=main_keyboard(),
            )
            return

        # Show only a few stories to avoid flooding the user.
        articles = articles[:5]

        for article in articles:
            await message.answer(
                _format_simple_news(
                    article.title,
                    article.summary,
                    article.source,
                    article.link,
                )
            )

        await message.answer(
            "✅ That's the latest available news "
            "from the configured sources.",
            reply_markup=main_keyboard(),
        )

    except Exception as exc:
        logger.exception(
            "Error while getting latest news: %s",
            exc,
        )

        await message.answer(
            "⚠️ I couldn't retrieve the latest news "
            "right now. Please try again shortly.",
            reply_markup=main_keyboard(),
        )


# ==========================================================
# SIMPLE NEWS FORMAT
# ==========================================================

def _format_simple_news(
    title: str,
    summary: str,
    source: str,
    link: str,
) -> str:

    import html

    title = html.escape(title or "")
    summary = html.escape(summary or "")
    source = html.escape(source or "")
    link = html.escape(link or "", quote=True)

    text = f"📰 <b>{title}</b>\n\n"

    if summary:
        text += f"{summary}\n\n"

    if source:
        text += f"📌 <b>Source:</b> {source}\n\n"

    if link:
        text += (
            f'🔗 <a href="{link}">Read Full Story</a>'
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
# ADMIN STATS
# ==========================================================

def register_admin_handlers(admin_id: int):
    """
    Register admin-only commands.

    This function is called from main.py so that the
    configured ADMIN_ID controls access.
    """

    @dp.message(Command("stats"))
    async def stats_handler(
        message: Message,
    ):
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


# ==========================================================
# BOT RUNNER
# ==========================================================

async def run_bot(bot: Bot):
    logger.info(
        "Telegram bot polling started."
    )

    await dp.start_polling(bot)
