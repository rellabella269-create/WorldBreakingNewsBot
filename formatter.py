import html
import re
from typing import Optional

from config import (
    CATEGORY_HASHTAGS,
    MAX_MESSAGE_LENGTH,
    SUMMARY_MAX_LENGTH,
)
from news_fetcher import NewsArticle


# ==========================================================
# TEXT CLEANING
# ==========================================================

def clean_text(text: str) -> str:
    """
    Clean text before sending it to Telegram.
    """

    if not text:
        return ""

    # Remove HTML tags.
    text = re.sub(
        r"<[^>]+>",
        " ",
        text,
    )

    # Decode HTML entities.
    text = html.unescape(text)

    # Normalize whitespace.
    text = re.sub(
        r"\s+",
        " ",
        text,
    ).strip()

    return text


# ==========================================================
# TRIM TEXT
# ==========================================================

def trim_text(
    text: str,
    max_length: int,
) -> str:
    """
    Trim text without cutting words unnecessarily.
    """

    text = clean_text(text)

    if len(text) <= max_length:
        return text

    shortened = text[:max_length].rsplit(
        " ",
        1,
    )[0]

    return shortened.rstrip(
        ".,;:!?-"
    ) + "..."


# ==========================================================
# CREATE SUMMARY
# ==========================================================

def create_summary(
    article: NewsArticle,
) -> str:
    """
    Create a short readable summary from the RSS description.

    This does not invent facts. It only cleans and shortens
    the information supplied by the news feed.
    """

    summary = clean_text(
        article.summary
    )

    if not summary:
        return ""

    return trim_text(
        summary,
        SUMMARY_MAX_LENGTH,
    )


# ==========================================================
# CATEGORY EMOJI
# ==========================================================

CATEGORY_EMOJIS = {
    "World": "🌍",
    "Politics": "🏛️",
    "Business": "💰",
    "Technology": "💻",
    "Sports": "🏆",
    "Science": "🔬",
    "Entertainment": "🎬",
}


# ==========================================================
# GET CATEGORY EMOJI
# ==========================================================

def get_category_emoji(
    category: str,
) -> str:

    return CATEGORY_EMOJIS.get(
        category,
        "📰",
    )


# ==========================================================
# HASHTAGS
# ==========================================================

def get_hashtags(
    category: str,
) -> str:

    return CATEGORY_HASHTAGS.get(
        category,
        "#News #BreakingNews",
    )


# ==========================================================
# FORMAT NEWS POST
# ==========================================================

def format_news_post(
    article: NewsArticle,
) -> str:
    """
    Build the Telegram channel post.
    """

    emoji = get_category_emoji(
        article.category
    )

    summary = create_summary(
        article
    )

    hashtags = get_hashtags(
        article.category
    )

    title = clean_text(
        article.title
    )

    source = clean_text(
        article.source
    )

    # ------------------------------------------------------
    # HEADLINE
    # ------------------------------------------------------

    message_parts = [
        f"🚨 <b>{html.escape(title)}</b>",
        "",
    ]

    # ------------------------------------------------------
    # SUMMARY
    # ------------------------------------------------------

    if summary:
        message_parts.extend(
            [
                html.escape(summary),
                "",
            ]
        )

    # ------------------------------------------------------
    # CATEGORY
    # ------------------------------------------------------

    message_parts.extend(
        [
            f"{emoji} <b>Category:</b> "
            f"{html.escape(article.category)}",
            "",
        ]
    )

    # ------------------------------------------------------
    # SOURCE
    # ------------------------------------------------------

    if source:
        message_parts.extend(
            [
                f"📰 <b>Source:</b> "
                f"{html.escape(source)}",
                "",
            ]
        )

    # ------------------------------------------------------
    # SOURCE LINK
    # ------------------------------------------------------

    if article.link:
        safe_link = html.escape(
            article.link,
            quote=True,
        )

        message_parts.append(
            f'🔗 <a href="{safe_link}">'
            f"Read Full Story"
            f"</a>"
        )

    # ------------------------------------------------------
    # HASHTAGS
    # ------------------------------------------------------

    message_parts.extend(
        [
            "",
            hashtags,
        ]
    )

    message = "\n".join(
        message_parts
    )

    # ------------------------------------------------------
    # TELEGRAM LIMIT
    # ------------------------------------------------------

    if len(message) <= MAX_MESSAGE_LENGTH:
        return message

    # If the message is too long, rebuild it
    # using a shorter summary.
    shorter_summary = trim_text(
        summary,
        350,
    )

    message_parts = [
        f"🚨 <b>{html.escape(title)}</b>",
        "",
    ]

    if shorter_summary:
        message_parts.extend(
            [
                html.escape(shorter_summary),
                "",
            ]
        )

    message_parts.extend(
        [
            f"{emoji} <b>Category:</b> "
            f"{html.escape(article.category)}",
            "",
        ]
    )

    if source:
        message_parts.extend(
            [
                f"📰 <b>Source:</b> "
                f"{html.escape(source)}",
                "",
            ]
        )

    if article.link:
        safe_link = html.escape(
            article.link,
            quote=True,
        )

        message_parts.append(
            f'🔗 <a href="{safe_link}">'
            f"Read Full Story"
            f"</a>"
        )

    message_parts.extend(
        [
            "",
            hashtags,
        ]
    )

    message = "\n".join(
        message_parts
    )

    return message[:MAX_MESSAGE_LENGTH]


# ==========================================================
# BOT START MESSAGE
# ==========================================================

def format_welcome_message(
    first_name: Optional[str] = None,
) -> str:

    if first_name:
        greeting = (
            f"👋 <b>Welcome, "
            f"{html.escape(first_name)}!</b>"
        )
    else:
        greeting = (
            "👋 <b>Welcome to "
            "World Breaking News!</b>"
        )

    return (
        f"{greeting}\n\n"
        "🌍 Get important news and major "
        "developments from around the world.\n\n"
        "🚨 Our system checks trusted news "
        "sources for new stories and delivers "
        "updates quickly.\n\n"
        "🔔 Use the buttons below to control "
        "your news alerts."
    )


# ==========================================================
# BOT HELP MESSAGE
# ==========================================================

def format_help_message() -> str:

    return (
        "ℹ️ <b>How the News Alert Bot works</b>\n\n"
        "📰 <b>Latest News</b> — Get the latest "
        "available news.\n\n"
        "🔔 <b>Enable Alerts</b> — Receive news "
        "alerts from the bot.\n\n"
        "🔕 <b>Disable Alerts</b> — Stop personal "
        "news alerts.\n\n"
        "🌍 The main channel remains available "
        "for everyone."
    )


# ==========================================================
# BOT STATUS MESSAGE
# ==========================================================

def format_alert_status(
    enabled: bool,
) -> str:

    if enabled:
        return (
            "🔔 <b>News alerts are ON.</b>\n\n"
            "You will receive new breaking-news "
            "notifications when available."
        )

    return (
        "🔕 <b>News alerts are OFF.</b>\n\n"
        "You will no longer receive personal "
        "news notifications."
    )


# ==========================================================
# ADMIN STATUS MESSAGE
# ==========================================================

def format_admin_stats(
    user_count: int,
) -> str:

    return (
        "📊 <b>Bot Statistics</b>\n\n"
        f"👥 Active/registered users: "
        f"<b>{user_count}</b>"
    )
