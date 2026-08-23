import hashlib
import logging
import re
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urlparse

import feedparser

from config import (
    NEWS_FEEDS,
    MAX_ARTICLES_PER_FEED,
    CATEGORY_KEYWORDS,
)


# ==========================================================
# LOGGING
# ==========================================================

logger = logging.getLogger(__name__)


# ==========================================================
# ARTICLE MODEL
# ==========================================================

@dataclass
class NewsArticle:
    article_id: str
    title: str
    link: str
    summary: str
    source: str
    category: str
    published: str = ""


# ==========================================================
# NEWS FETCHER
# ==========================================================

class NewsFetcher:

    def __init__(
        self,
        feeds: Optional[List[str]] = None,
        max_articles_per_feed: int = MAX_ARTICLES_PER_FEED,
    ):
        self.feeds = feeds or NEWS_FEEDS
        self.max_articles_per_feed = max_articles_per_feed

    # ======================================================
    # FETCH ALL NEWS
    # ======================================================

    def fetch_all(self) -> List[NewsArticle]:
        articles: List[NewsArticle] = []

        for feed_url in self.feeds:
            try:
                feed_articles = self.fetch_feed(feed_url)
                articles.extend(feed_articles)

            except Exception as exc:
                logger.exception(
                    "Failed to fetch feed %s: %s",
                    feed_url,
                    exc,
                )

        return self._remove_duplicates(articles)

    # ======================================================
    # FETCH ONE FEED
    # ======================================================

    def fetch_feed(self, feed_url: str) -> List[NewsArticle]:
        logger.info("Fetching news from: %s", feed_url)

        parsed = feedparser.parse(feed_url)

        if getattr(parsed, "bozo", False):
            logger.warning(
                "Feed parser warning for %s: %s",
                feed_url,
                getattr(
                    parsed,
                    "bozo_exception",
                    "Unknown feed error",
                ),
            )

        if not parsed.entries:
            logger.warning(
                "No articles found in feed: %s",
                feed_url,
            )
            return []

        source = self._get_source_name(
            parsed,
            feed_url,
        )

        articles: List[NewsArticle] = []

        for entry in parsed.entries[
            : self.max_articles_per_feed
        ]:
            article = self._parse_entry(
                entry,
                source,
            )

            if article:
                articles.append(article)

        return articles

    # ======================================================
    # PARSE ENTRY
    # ======================================================

    def _parse_entry(
        self,
        entry,
        source: str,
    ) -> Optional[NewsArticle]:

        title = self._clean_text(
            getattr(entry, "title", "")
        )

        link = self._clean_url(
            getattr(entry, "link", "")
        )

        if not title or not link:
            return None

        summary = self._extract_summary(entry)

        published = (
            getattr(entry, "published", "")
            or getattr(entry, "updated", "")
            or ""
        )

        article_id = self._create_article_id(
            title,
            link,
        )

        category = self.detect_category(
            title,
            summary,
        )

        return NewsArticle(
            article_id=article_id,
            title=title,
            link=link,
            summary=summary,
            source=source,
            category=category,
            published=published,
        )

    # ======================================================
    # SUMMARY EXTRACTION
    # ======================================================

    def _extract_summary(self, entry) -> str:

        summary = (
            getattr(entry, "summary", "")
            or getattr(entry, "description", "")
            or ""
        )

        return self._clean_text(summary)

    # ======================================================
    # CLEAN TEXT
    # ======================================================

    @staticmethod
    def _clean_text(text: str) -> str:

        if not text:
            return ""

        # Remove HTML tags.
        text = re.sub(
            r"<[^>]+>",
            " ",
            text,
        )

        # Decode common HTML entities.
        replacements = {
            "&amp;": "&",
            "&quot;": '"',
            "&#39;": "'",
            "&apos;": "'",
            "&lt;": "<",
            "&gt;": ">",
            "&nbsp;": " ",
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        # Normalize whitespace.
        text = re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

        return text

    # ======================================================
    # CLEAN URL
    # ======================================================

    @staticmethod
    def _clean_url(url: str) -> str:

        if not url:
            return ""

        url = url.strip()

        if not url.startswith(
            ("http://", "https://")
        ):
            return ""

        return url

    # ======================================================
    # ARTICLE ID
    # ======================================================

    @staticmethod
    def _create_article_id(
        title: str,
        link: str,
    ) -> str:

        raw = f"{title}|{link}".lower()

        return hashlib.sha256(
            raw.encode("utf-8")
        ).hexdigest()

    # ======================================================
    # SOURCE NAME
    # ======================================================

    @staticmethod
    def _get_source_name(
        parsed,
        feed_url: str,
    ) -> str:

        feed_title = ""

        try:
            feed_title = (
                getattr(
                    parsed.feed,
                    "title",
                    "",
                )
                or ""
            )
        except Exception:
            feed_title = ""

        feed_title = NewsFetcher._clean_text(
            feed_title
        )

        if feed_title:
            return feed_title

        hostname = urlparse(feed_url).netloc.lower()

        hostname = hostname.replace(
            "www.",
            "",
        )

        source_map = {
            "bbc.co.uk": "BBC News",
            "bbc.com": "BBC News",
            "nytimes.com": "The New York Times",
            "skynews.com": "Sky News",
            "theguardian.com": "The Guardian",
        }

        return source_map.get(
            hostname,
            hostname.title(),
        )

    # ======================================================
    # CATEGORY DETECTION
    # ======================================================

    @staticmethod
    def detect_category(
        title: str,
        summary: str,
    ) -> str:

        text = (
            f"{title} {summary}"
        ).lower()

        scores = {}

        for category, keywords in CATEGORY_KEYWORDS.items():
            score = 0

            for keyword in keywords:
                keyword = keyword.lower()

                if keyword in text:
                    score += 1

            scores[category] = score

        # Find category with highest score.
        best_category = max(
            scores,
            key=scores.get,
        )

        # No useful keyword match.
        if scores.get(best_category, 0) == 0:
            return "World"

        return best_category

    # ======================================================
    # REMOVE DUPLICATES
    # ======================================================

    @staticmethod
    def _remove_duplicates(
        articles: List[NewsArticle],
    ) -> List[NewsArticle]:

        seen = set()
        unique_articles = []

        for article in articles:
            if article.article_id in seen:
                continue

            seen.add(article.article_id)
            unique_articles.append(article)

        return unique_articles

    # ======================================================
    # FILTER VALID ARTICLES
    # ======================================================

    @staticmethod
    def filter_articles(
        articles: List[NewsArticle],
    ) -> List[NewsArticle]:

        filtered = []

        for article in articles:

            # Ignore extremely short headlines.
            if len(article.title.strip()) < 10:
                continue

            # Ignore articles without a source link.
            if not article.link:
                continue

            filtered.append(article)

        return filtered


# ==========================================================
# GLOBAL FETCHER
# ==========================================================

fetcher = NewsFetcher()


# ==========================================================
# HELPER FUNCTION
# ==========================================================

def get_latest_news() -> List[NewsArticle]:
    """
    Fetch the latest news from all configured feeds.
    """
    articles = fetcher.fetch_all()

    return fetcher.filter_articles(
        articles
    )
