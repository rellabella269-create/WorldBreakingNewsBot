import os
import sqlite3
from datetime import datetime, timezone

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
    def __init__(self, db_path: str = DATABASE_PATH):
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
            # ------------------------------------------------

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS posted_news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id TEXT NOT NULL UNIQUE,
                    title TEXT,
                    link TEXT,
                    source TEXT,
                    category TEXT,
                    posted_at TEXT NOT NULL
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
            # BOT SETTINGS
            # ------------------------------------------------

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
                """
            )

            connection.commit()

        finally:
            connection.close()

    # ======================================================
    # NEWS
    # ======================================================

    def news_exists(self, article_id: str) -> bool:
        connection = self.connect()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT 1
                FROM posted_news
                WHERE article_id = ?
                LIMIT 1
                """,
                (article_id,)
            )

            return cursor.fetchone() is not None

        finally:
            connection.close()

    # ======================================================

    def add_news(
        self,
        article_id: str,
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
                    title,
                    link,
                    source,
                    category,
                    posted_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    article_id,
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

    def get_recent_news(self, limit: int = 100):
        connection = self.connect()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    article_id,
                    title,
                    link,
                    source,
                    category,
                    posted_at
                FROM posted_news
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,)
            )

            return cursor.fetchall()

        finally:
            connection.close()

    # ======================================================

    def cleanup_old_news(self, keep_count: int = 5000):
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
                (keep_count,)
            )

            connection.commit()

        finally:
            connection.close()

    # ======================================================
    # USERS
    # ======================================================

    def add_user(self, user_id: int):
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

    def remove_user(self, user_id: int):
        connection = self.connect()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE users
                SET alerts_enabled = 0
                WHERE user_id = ?
                """,
                (user_id,)
            )

            connection.commit()

        finally:
            connection.close()

    # ======================================================

    def enable_alerts(self, user_id: int):
        connection = self.connect()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE users
                SET alerts_enabled = 1
                WHERE user_id = ?
                """,
                (user_id,)
            )

            connection.commit()

        finally:
            connection.close()

    # ======================================================

    def disable_alerts(self, user_id: int):
        connection = self.connect()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE users
                SET alerts_enabled = 0
                WHERE user_id = ?
                """,
                (user_id,)
            )

            connection.commit()

        finally:
            connection.close()

    # ======================================================

    def get_active_users(self):
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
                row["user_id"]
                for row in rows
            ]

        finally:
            connection.close()

    # ======================================================

    def user_exists(self, user_id: int) -> bool:
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
                (user_id,)
            )

            return cursor.fetchone() is not None

        finally:
            connection.close()

    # ======================================================
    # USER COUNT
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

    def set_setting(self, key: str, value: str):
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
                DO UPDATE SET value = excluded.value
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
        default=None
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
                (key,)
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
