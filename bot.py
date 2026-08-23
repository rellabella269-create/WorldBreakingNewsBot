import asyncio
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

from config import ADMIN_ID
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
# MAIN KEYBOARD
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
# LATEST NEWS
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

        # Do not flood the user.
        articles = articles[:5]

        for article in articles:

            await message.answer(
                format_user_news(
                    article
                ),
                disable_web_page_preview=False,
            )

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
# USER NEWS FORMAT
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

    if len(summary) > 700:
        summary = (
            summary[:697].rsplit(
                " ",
                1
            )[0]
            + "..."
        )

    text = (
        f"📰 <b>{title}</b>\n\n"
    )

    if summary:
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
# ADMIN CHECK
# ==========================================================

def is_admin(message: Message) -> bool:

    if not message.from_user:
        return False

    return (
        ADMIN_ID != 0
        and message.from_user.id == ADMIN_ID
    )


# ==========================================================
# EXTRACT COMMAND ARGUMENT
# ==========================================================

def get_command_argument(
    message: Message,
) -> Optional[str]:

    if not message.text:
        return None

    parts = message.text.split(
        maxsplit=1
    )

    if len(parts) < 2:
        return None

    value = parts[1].strip()

    if not value:
        return None

    return value


# ==========================================================
# NORMALIZE CHANNEL INPUT
# ==========================================================

def normalize_channel_input(
    value: str,
) -> str:

    value = value.strip()

    # Remove Telegram URL formats if the admin pastes one.
    value = value.replace(
        "https://t.me/",
        "",
    )

    value = value.replace(
        "http://t.me/",
        "",
    )

    value = value.strip()

    if value.startswith("@"):
        return value

    # Numeric IDs remain numeric.
    if value.startswith("-100"):
        return value

    # If someone enters a plain public username,
    # convert it to @username.
    return f"@{value}"


# ==========================================================
# ADD CHANNEL
# ==========================================================

@dp.message(Command("addchannel"))
async def add_channel_handler(
    message: Message,
):

    if not is_admin(message):

        await message.answer(
            "❌ You are not authorized to manage channels."
        )

        return

    channel_input = get_command_argument(
        message
    )

    if not channel_input:

        await message.answer(
            "❌ Please provide a channel username or ID.\n\n"
            "<b>Example:</b>\n"
            "<code>/addchannel @MyNewsChannel</code>\n\n"
            "You can also use a numeric channel ID:\n"
            "<code>/addchannel -1001234567890</code>"
        )

        return

    channel_input = normalize_channel_input(
        channel_input
    )

    status_message = await message.answer(
        "🔎 Checking the channel..."
    )

    try:

        # --------------------------------------------------
        # GET CHANNEL INFORMATION
        # --------------------------------------------------

        chat = await message.bot.get_chat(
            channel_input
        )

        # --------------------------------------------------
        # CHECK BOT'S ADMIN STATUS
        # --------------------------------------------------

        bot_user = await message.bot.get_me()

        bot_member = await message.bot.get_chat_member(
            chat_id=chat.id,
            user_id=bot_user.id,
        )

        # --------------------------------------------------
        # CHECK ADMIN RIGHTS
        # --------------------------------------------------

        is_creator = (
            bot_member.status == "creator"
        )

        is_administrator = (
            bot_member.status == "administrator"
        )

        can_post = getattr(
            bot_member,
            "can_post_messages",
            False,
        )

        if not (
            is_creator
            or (
                is_administrator
                and can_post
            )
        ):

            await status_message.edit_text(
                "❌ <b>The bot cannot post in this channel.</b>\n\n"
                "Add this bot as an administrator of the channel "
                "and give it permission to post messages.\n\n"
                f"Channel: <code>{html.escape(str(chat.id))}</code>"
            )

            return

        # --------------------------------------------------
        # SAVE CHANNEL
        # --------------------------------------------------

        username = getattr(
            chat,
            "username",
            None,
        )

        if username:
            username = f"@{username}"

        else:
            username = ""

        was_added = db.add_channel(
            channel_id=str(chat.id),
            channel_username=username,
        )

        # --------------------------------------------------
        # SUCCESS MESSAGE
        # --------------------------------------------------

        display_name = (
            html.escape(
                chat.title
                or "Unnamed Channel"
            )
        )

        if was_added:

            await status_message.edit_text(
                "✅ <b>Channel added successfully!</b>\n\n"
                f"📢 <b>Name:</b> {display_name}\n"
                f"🆔 <b>ID:</b> <code>{chat.id}</code>\n"
                f"🔗 <b>Username:</b> "
                f"<code>{html.escape(username or 'Private channel')}</code>\n\n"
                "📰 New news will now be sent to this channel.\n\n"
                f"📊 Total active channels: "
                f"<b>{db.get_channel_count()}</b>"
            )

        else:

            await status_message.edit_text(
                "✅ <b>This channel is already registered.</b>\n\n"
                f"📢 <b>Name:</b> {display_name}\n"
                f"🆔 <b>ID:</b> <code>{chat.id}</code>\n\n"
                f"📊 Total active channels: "
                f"<b>{db.get_channel_count()}</b>"
            )

    except Exception as exc:

        logger.exception(
            "Failed to add channel %s: %s",
            channel_input,
            exc,
        )

        await status_message.edit_text(
            "❌ <b>Could not add this channel.</b>\n\n"
            "Make sure:\n"
            "• The channel username/ID is correct.\n"
            "• The channel exists.\n"
            "• The bot has been added to the channel.\n"
            "• The bot is an administrator.\n"
            "• The bot can post messages.\n\n"
            f"Error: <code>{html.escape(str(exc))}</code>"
        )


# ==========================================================
# LIST CHANNELS
# ==========================================================

@dp.message(Command("channels"))
async def channels_handler(
    message: Message,
):

    if not is_admin(message):

        await message.answer(
            "❌ You are not authorized to view the channel list."
        )

        return

    channels = db.get_channels(
        enabled_only=False
    )

    if not channels:

        await message.answer(
            "📢 <b>No channels have been added yet.</b>\n\n"
            "Use:\n"
            "<code>/addchannel @YourChannel</code>"
        )

        return

    lines = [
        "📢 <b>Managed Channels</b>",
        "",
        f"Total: <b>{len(channels)}</b>",
        "",
    ]

    for index, channel in enumerate(
        channels,
        start=1,
    ):

        username = (
            channel["channel_username"]
            or "Private/ID channel"
        )

        status = (
            "✅"
            if channel["enabled"]
            else "🔴"
        )

        lines.append(
            f"{index}. {status} "
            f"<b>{html.escape(username)}</b>\n"
            f"   🆔 <code>{html.escape(str(channel['channel_id']))}</code>"
        )

    # Telegram message limit protection.
    full_text = "\n\n".join(
        lines
    )

    if len(full_text) <= 4000:

        await message.answer(
            full_text
        )

        return

    # Send in chunks for large lists.
    current = (
        "📢 <b>Managed Channels</b>\n\n"
        f"Total: <b>{len(channels)}</b>\n\n"
    )

    for index, channel in enumerate(
        channels,
        start=1,
    ):

        username = (
            channel["channel_username"]
            or "Private/ID channel"
        )

        status = (
            "✅"
            if channel["enabled"]
            else "🔴"
        )

        line = (
            f"{index}. {status} "
            f"<b>{html.escape(username)}</b>\n"
            f"   🆔 <code>{html.escape(str(channel['channel_id']))}</code>\n\n"
        )

        if (
            len(current) + len(line)
            > 3800
        ):

            await message.answer(
                current
            )

            current = ""

        current += line

    if current:

        await message.answer(
            current
        )


# ==========================================================
# REMOVE CHANNEL
# ==========================================================

@dp.message(Command("removechannel"))
async def remove_channel_handler(
    message: Message,
):

    if not is_admin(message):

        await message.answer(
            "❌ You are not authorized to manage channels."
        )

        return

    channel_input = get_command_argument(
        message
    )

    if not channel_input:

        await message.answer(
            "❌ Please provide the channel username or ID.\n\n"
            "<b>Example:</b>\n"
            "<code>/removechannel @MyNewsChannel</code>"
        )

        return

    channel_input = normalize_channel_input(
        channel_input
    )

    try:

        # --------------------------------------------------
        # Resolve the username/ID to Telegram's real ID.
        # --------------------------------------------------

        chat = await message.bot.get_chat(
            channel_input
        )

        removed = db.remove_channel(
            str(chat.id)
        )

        if removed:

            await message.answer(
                "✅ <b>Channel removed.</b>\n\n"
                f"📢 {html.escape(chat.title or 'Channel')}\n"
                f"🆔 <code>{chat.id}</code>\n\n"
                "New news will no longer be sent to this channel.\n\n"
                f"📊 Active channels remaining: "
                f"<b>{db.get_channel_count()}</b>"
            )

        else:

            await message.answer(
                "ℹ️ This channel was not registered.\n\n"
                f"🆔 <code>{chat.id}</code>"
            )

    except Exception as exc:

        logger.exception(
            "Failed to remove channel %s: %s",
            channel_input,
            exc,
        )

        await message.answer(
            "❌ Could not find or remove this channel.\n\n"
            f"Error: <code>{html.escape(str(exc))}</code>"
        )


# ==========================================================
# DISABLE CHANNEL
# ==========================================================

@dp.message(Command("disablechannel"))
async def disable_channel_handler(
    message: Message,
):

    if not is_admin(message):

        await message.answer(
            "❌ You are not authorized to manage channels."
        )

        return

    channel_input = get_command_argument(
        message
    )

    if not channel_input:

        await message.answer(
            "❌ Example:\n"
            "<code>/disablechannel @MyNewsChannel</code>"
        )

        return

    channel_input = normalize_channel_input(
        channel_input
    )

    try:

        chat = await message.bot.get_chat(
            channel_input
        )

        disabled = db.disable_channel(
            str(chat.id)
        )

        if disabled:

            await message.answer(
                "🔴 <b>Channel disabled.</b>\n\n"
                f"📢 {html.escape(chat.title or 'Channel')}\n\n"
                "The bot will keep the channel in its database "
                "but will temporarily stop sending news to it."
            )

        else:

            await message.answer(
                "ℹ️ This channel is not currently registered."
            )

    except Exception as exc:

        logger.exception(
            "Failed to disable channel: %s",
            exc,
        )

        await message.answer(
            "❌ Could not disable this channel.\n\n"
            f"Error: <code>{html.escape(str(exc))}</code>"
        )


# ==========================================================
# ENABLE CHANNEL
# ==========================================================

@dp.message(Command("enablechannel"))
async def enable_channel_handler(
    message: Message,
):

    if not is_admin(message):

        await message.answer(
            "❌ You are not authorized to manage channels."
        )

        return

    channel_input = get_command_argument(
        message
    )

    if not channel_input:

        await message.answer(
            "❌ Example:\n"
            "<code>/enablechannel @MyNewsChannel</code>"
        )

        return

    channel_input = normalize_channel_input(
        channel_input
    )

    try:

        chat = await message.bot.get_chat(
            channel_input
        )

        enabled = db.enable_channel(
            str(chat.id)
        )

        if enabled:

            await message.answer(
                "✅ <b>Channel enabled.</b>\n\n"
                f"📢 {html.escape(chat.title or 'Channel')}\n\n"
                "New news will be sent to this channel again."
            )

        else:

            await message.answer(
                "ℹ️ This channel is not currently registered.\n\n"
                "Use:\n"
                f"<code>/addchannel {html.escape(channel_input)}</code>"
            )

    except Exception as exc:

        logger.exception(
            "Failed to enable channel: %s",
            exc,
        )

        await message.answer(
            "❌ Could not enable this channel.\n\n"
            f"Error: <code>{html.escape(str(exc))}</code>"
        )


# ==========================================================
# ADMIN STATS
# ==========================================================

@dp.message(Command("stats"))
async def stats_handler(
    message: Message,
):

    if not is_admin(message):

        await message.answer(
            "❌ You are not authorized to use this command."
        )

        return

    user_count = db.get_user_count()

    channel_count = db.get_channel_count(
        enabled_only=True
    )

    all_channel_count = db.get_channel_count(
        enabled_only=False
    )

    await message.answer(
        "📊 <b>Bot Statistics</b>\n\n"
        f"👥 Users: <b>{user_count}</b>\n"
        f"📢 Active channels: <b>{channel_count}</b>\n"
        f"📚 Stored channels: <b>{all_channel_count}</b>"
    )


# ==========================================================
# ADMIN HELP
# ==========================================================

@dp.message(Command("adminhelp"))
async def admin_help_handler(
    message: Message,
):

    if not is_admin(message):

        await message.answer(
            "❌ You are not authorized."
        )

        return

    await message.answer(
        "🛠️ <b>Admin Commands</b>\n\n"

        "➕ <code>/addchannel @Channel</code>\n"
        "Add a channel.\n\n"

        "📋 <code>/channels</code>\n"
        "Show all registered channels.\n\n"

        "❌ <code>/removechannel @Channel</code>\n"
        "Remove a channel permanently.\n\n"

        "🔴 <code>/disablechannel @Channel</code>\n"
        "Temporarily stop posting to a channel.\n\n"

        "🟢 <code>/enablechannel @Channel</code>\n"
        "Resume posting to a disabled channel.\n\n"

        "📊 <code>/stats</code>\n"
        "Show users and channel statistics."
    )


# ==========================================================
# REGISTER ADMIN HANDLERS
# ==========================================================

def register_admin_handlers(
    admin_id: int,
):
    """
    Kept for compatibility with main.py.

    Admin commands are registered directly above,
    and authorization is checked against ADMIN_ID.
    """

    logger.info(
        "Admin system enabled for user ID %s",
        admin_id,
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
