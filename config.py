try:
    channel = str(channel_id).strip()

    # Convert public channel usernames to Telegram format
    if not channel.startswith("@") and not channel.startswith("-100"):
        channel = f"@{channel}"

    # Resolve the channel first
    chat = await bot.get_chat(chat_id=channel)

    # Send using Telegram's real chat ID
    await bot.send_message(
        chat_id=chat.id,
        text=message,
        parse_mode="HTML",
        disable_web_page_preview=False,
    )

    db.add_news(
        article_id=article.article_id,
        channel_id=str(chat.id),
        title=article.title,
        link=article.link,
        source=article.source,
        category=article.category,
    )

    logger.info(
        "POSTED | channel=%s | title=%s",
        chat.id,
        article.title,
    )

    return True

except TelegramBadRequest as exc:
    logger.error(
        "CHANNEL ERROR | channel=%s | error=%s",
        channel_id,
        exc,
    )
    return False

except TelegramForbiddenError as exc:
    logger.error(
        "BOT HAS NO PERMISSION | channel=%s | error=%s",
        channel_id,
        exc,
    )
    return False

except Exception as exc:
    logger.exception(
        "POST FAILED | channel=%s | error=%s",
        channel_id,
        exc,
    )
    return False
