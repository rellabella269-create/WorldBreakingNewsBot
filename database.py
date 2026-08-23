import os
import sqlite3
from datetime import datetime, timezone
from typing import List, Optional

from config import DATABASE_PATH


# ==========================================================
# CREATE DATABASE FOLDER
# ==========================================================

db_folder = os.path.dirname(DATABASE_PATH)

if db_folder:
    os.makedirs(db_folder, exist_ok=True)


# ==========================================================
# DATABASE CLASS
# ==========================================================

class Database:

    def __init__(
        self,
        db_path: str = DATABASE_PATH
    ):
        self.db_path = db_path
        self._create_tables()

    # ======================================================
    # CONNECTION
    # ======================================================

    def connect(self):
        connection = sqlite3.connect(
            self.db_path,
            check_same_thread=False
        )

        connection.row_factory = sqlite3.Row

        return connection

    # ======================================================
    # CREATE TABLES
    # ======================================================

    def _create_tables(self):

        connection = self.connect()

        try:
            cursor = connection.cursor()

            # ------------------------------------------------
            # POSTED NEWS
            #
            # Each article/channel combination is stored
            # separately.
            # ------------------------------------------------

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS posted_news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id TEXT NOT NULL,
                    channel_id TEXT NOT NULL,
                    title TEXT,
                    link TEXT,
                    source TEXT,
                    category TEXT,
                    posted_at TEXT NOT NULL,

                    UNIQUE(article_id, channel_id)
                )
                """
            )

            # ------------------------------------------------
            # MANAGED CHANNELS
            #
            # Channels added by the admin through:
            #
            # /addchannel @MyChannel
            # ------------------------------------------------

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS channels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id TEXT NOT NULL UNIQUE,
                    channel_username TEXT,
                    added_at TEXT NOT NULL,
                    enabled INTEGER DEFAULT 1
                )
                """
            )

            # ------------------------------------------------
            # USERS
            # ------------------------------------------------

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    joined_at TEXT NOT NULL,
                    alerts_enabled INTEGER DEFAULT 1
                )
                """
            )

            # ------------------------------------------------
            # SETTINGS
            # ------------------------------------------------

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
                """
            )

            # ------------------------------------------------
            # INDEXES
            # ------------------------------------------------

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_posted_news_article
                ON posted_news(article_id)
                """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_posted_news_channel
                ON posted_news(channel_id)
                """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_posted_news_time
                ON posted_news(posted_at)
                """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_channels_enabled
                ON channels(enabled)
                """
            )

            connection.commit()

        finally:
            connection.close()

    # ======================================================
    # CHANNEL MANAGEMENT
    # ======================================================

    def add_channel(
        self,
        channel_id: str,
        channel_username: str = ""
    ) -> bool:
        """
        Add a Telegram channel to the managed channel list.

        Returns:
            True  = newly added
            False = already existed
        """

        connection = self.connect()

        try:
            cursor = connection.cursor()

            added_at = datetime.now(
                timezone.utc
            ).isoformat()

            cursor.execute(
                """
                INSERT INTO channels
                (
                    channel_id,
                    channel_username,
                    added_at,
                    enabled
                )
                VALUES (?, ?, ?, 1)

                ON CONFLICT(channel_id)
                DO UPDATE SET
                    channel_username = excluded.channel_username,
                    enabled = 1
                """,
                (
                    str(channel_id),
                    channel_username,
                    added_at
                )
            )

            connection.commit()

            return cursor.rowcount > 0

        finally:
            connection.close()

    # ======================================================

    def remove_channel(
        self,
        channel_id: str
    ) -> bool:
        """
        Permanently remove a channel from the managed list.
        """

        connection = self.connect()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                DELETE FROM channels
                WHERE channel_id = ?
                """,
                (
                    str(channel_id),
                )
            )

            connection.commit()

            return cursor.rowcount > 0

        finally:
            connection.close()

    # ======================================================

    def disable_channel(
        self,
        channel_id: str
    ) -> bool:

        connection = self.connect()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE channels
                SET enabled = 0
                WHERE channel_id = ?
                """,
                (
                    str(channel_id),
                )
            )

            connection.commit()

            return cursor.rowcount > 0

        finally:
            connection.close()

    # ======================================================

    def enable_channel(
        self,
        channel_id: str
    ) -> bool:

        connection = self.connect()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE channels
                SET enabled = 1
                WHERE channel_id = ?
                """,
                (
                    str(channel_id),
                )
            )

            connection.commit()

            return cursor.rowcount > 0

        finally:
            connection.close()

    # ======================================================

    def channel_exists(
        self,
        channel_id: str
    ) -> bool:

        connection = self.connect()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT 1
                FROM channels
                WHERE channel_id = ?
                LIMIT 1
                """,
                (
                    str(channel_id),
                )
            )

            return cursor.fetchone() is not None

        finally:
            connection.close()

    # ======================================================

    def get_channels(
        self,
        enabled_only: bool = True
    ) -> List[dict]:
        """
        Return managed channels.
        """

        connection = self.connect()

        try:
            cursor = connection.cursor()

            if enabled_only:

                cursor.execute(
                    """
                    SELECT
                        id,
                        channel_id,
                        channel_username,
                        added_at,
                        enabled
                    FROM channels
                    WHERE enabled = 1
                    ORDER BY id ASC
                    """
                )

            else:

                cursor.execute(
                    """
                    SELECT
                        id,
                        channel_id,
                        channel_username,
                        added_at,
                        enabled
                    FROM channels
                    ORDER BY id ASC
                    """
                )

            rows = cursor.fetchall()

            return [
                dict(row)
                for row in rows
            ]

        finally:
            connection.close()

    # ======================================================

    def get_channel_ids(
        self,
        enabled_only: bool = True
    ) -> List[str]:

        connection = self.connect()

        try:
            cursor = connection.cursor()

            if enabled_only:

                cursor.execute(
                    """
                    SELECT channel_id
                    FROM channels
                    WHERE enabled = 1
                    ORDER BY id ASC
                    """
                )

            else:

                cursor.execute(
                    """
                    SELECT channel_id
                    FROM channels
                    ORDER BY id ASC
                    """
                )

            rows = cursor.fetchall()

            return [
                str(row["channel_id"])
                for row in rows
            ]

        finally:
            connection.close()

    # ======================================================

    def get_channel_count(
        self,
        enabled_only: bool = True
    ) -> int:

        connection = self.connect()

        try:
            cursor = connection.cursor()

            if enabled_only:

                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM channels
                    WHERE enabled = 1
                    """
                )

            else:

                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM channels
                    """
                )

            result = cursor.fetchone()

            return int(result[0])

        finally:
            connection.close()

    # ======================================================
    # NEWS TRACKING
    # ======================================================

    def news_exists(
        self,
        article_id: str,
        channel_id: str
    ) -> bool:

        connection = self.connect()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT 1
                FROM posted_news
                WHERE article_id = ?
                  AND channel_id = ?
                LIMIT 1
                """,
                (
                    article_id,
                    str(channel_id)
                )
            )

            return cursor.fetchone() is not None

        finally:
            connection.close()

    # ======================================================

    def get_posted_channels(
        self,
        article_id: str
    ) -> List[str]:

        connection = self.connect()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT channel_id
                FROM posted_news
                WHERE article_id = ?
                """,
                (
                    article_id,
                )
            )

            rows = cursor.fetchall()

            return [
                str(row["channel_id"])
                for row in rows
            ]

        finally:
            connection.close()

    # ======================================================

    def add_news(
        self,
        article_id: str,
        channel_id: str,
        title: str = "",
        link: str = "",
        source: str = "",
        category: str = "World"
    ) -> bool:

        connection = self.connect()

        try:
            cursor = connection.cursor()

            posted_at = datetime.now(
                timezone.utc
            ).isoformat()

            cursor.execute(
                """
                INSERT OR IGNORE INTO posted_news
                (
                    article_id,
                    channel_id,
                    title,
                    link,
                    source,
                    category,
                    posted_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    article_id,
                    str(channel_id),
                    title,
                    link,
                    source,
                    category,
                    posted_at
                )
            )

            connection.commit()

            return cursor.rowcount > 0

        finally:
            connection.close()

    # ======================================================

    def get_recent_news(
        self,
        limit: int = 100
    ):

        connection = self.connect()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    article_id,
                    channel_id,
                    title,
                    link,
                    source,
                    category,
                    posted_at
                FROM posted_news
                ORDER BY id DESC
                LIMIT ?
                """,
                (
                    limit,
                )
            )

            return cursor.fetchall()

        finally:
            connection.close()

    # ======================================================

    def cleanup_old_news(
        self,
        keep_count: int = 5000
    ):

        connection = self.connect()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                DELETE FROM posted_news
                WHERE id NOT IN (
                    SELECT id
                    FROM posted_news
                    ORDER BY id DESC
                    LIMIT ?
                )
                """,
                (
                    keep_count,
                )
            )

            connection.commit()

        finally:
            connection.close()

    # ======================================================
    # USER MANAGEMENT
    # ======================================================

    def add_user(
        self,
        user_id: int
    ):

        connection = self.connect()

        try:
            cursor = connection.cursor()

            joined_at = datetime.now(
                timezone.utc
            ).isoformat()

            cursor.execute(
                """
                INSERT INTO users
                (
                    user_id,
                    joined_at,
                    alerts_enabled
                )
                VALUES (?, ?, 1)

                ON CONFLICT(user_id)
                DO UPDATE SET
                    alerts_enabled = 1
                """,
                (
                    user_id,
                    joined_at
                )
            )

            connection.commit()

        finally:
            connection.close()

    # ======================================================

    def enable_alerts(
        self,
        user_id: int
    ):

        connection = self.connect()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO users
                (
                    user_id,
                    joined_at,
                    alerts_enabled
                )
                VALUES (?, ?, 1)

                ON CONFLICT(user_id)
                DO UPDATE SET
                    alerts_enabled = 1
                """,
                (
                    user_id,
                    datetime.now(
                        timezone.utc
                    ).isoformat()
                )
            )

            connection.commit()

        finally:
            connection.close()

    # ======================================================

    def disable_alerts(
        self,
        user_id: int
    ):

        connection = self.connect()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO users
                (
                    user_id,
                    joined_at,
                    alerts_enabled
                )
                VALUES (?, ?, 0)

                ON CONFLICT(user_id)
                DO UPDATE SET
                    alerts_enabled = 0
                """,
                (
                    user_id,
                    datetime.now(
                        timezone.utc
                    ).isoformat()
                )
            )

            connection.commit()

        finally:
            connection.close()

    # ======================================================

    def get_active_users(self) -> List[int]:

        connection = self.connect()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT user_id
                FROM users
                WHERE alerts_enabled = 1
                """
            )

            rows = cursor.fetchall()

            return [
                int(row["user_id"])
                for row in rows
            ]

        finally:
            connection.close()

    # ======================================================

    def user_exists(
        self,
        user_id: int
    ) -> bool:

        connection = self.connect()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT 1
                FROM users
                WHERE user_id = ?
                LIMIT 1
                """,
                (
                    user_id,
                )
            )

            return cursor.fetchone() is not None

        finally:
            connection.close()

    # ======================================================

    def get_user_count(self) -> int:

        connection = self.connect()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM users
                """
            )

            result = cursor.fetchone()

            return int(result[0])

        finally:
            connection.close()

    # ======================================================
    # SETTINGS
    # ======================================================

    def set_setting(
        self,
        key: str,
        value: str
    ):

        connection = self.connect()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO settings
                (
                    key,
                    value
                )
                VALUES (?, ?)

                ON CONFLICT(key)
                DO UPDATE SET
                    value = excluded.value
                """,
                (
                    key,
                    value
                )
            )

            connection.commit()

        finally:
            connection.close()

    # ======================================================

    def get_setting(
        self,
        key: str,
        default: Optional[str] = None
    ):

        connection = self.connect()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT value
                FROM settings
                WHERE key = ?
                LIMIT 1
                """,
                (
                    key,
                )
            )

            row = cursor.fetchone()

            if row is None:
                return default

            return row["value"]

        finally:
            connection.close()


# ==========================================================
# GLOBAL DATABASE INSTANCE
# ==========================================================

db = Database()
