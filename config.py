import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()


# ==========================================================
# TELEGRAM BOT
# ==========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

if not BOT_TOKEN:
    raise ValueError(
        "BOT_TOKEN is missing. Add your Telegram bot token to the .env file."
    )


# ==========================================================
# ADMIN
# ==========================================================

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))


# ==========================================================
# MAIN NEWS CHANNEL
# ==========================================================

NEWS_CHANNEL = os.getenv(
    "NEWS_CHANNEL",
    "@WorldBreakingNews247"
).strip()


# ==========================================================
# BOT SETTINGS
# ==========================================================

# How often the bot checks news sources, in seconds.
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "30"))

# Maximum number of news articles processed in one feed check.
MAX_ARTICLES_PER_FEED = int(
    os.getenv("MAX_ARTICLES_PER_FEED", "10")
)

# Number of articles the bot keeps in its database.
MAX_STORED_ARTICLES = int(
    os.getenv("MAX_STORED_ARTICLES", "5000")
)


# ==========================================================
# DATABASE
# ==========================================================

DATABASE_PATH = os.getenv(
    "DATABASE_PATH",
    "data/news.db"
).strip()


# ==========================================================
# RSS NEWS SOURCES
# ==========================================================

NEWS_FEEDS = [
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://feeds.bbci.co.uk/news/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://feeds.skynews.com/feeds/rss/world.xml",
    "https://www.theguardian.com/world/rss",
]


# ==========================================================
# NEWS CATEGORIES
# ==========================================================

CATEGORY_KEYWORDS = {
    "World": [
        "world",
        "international",
        "global",
        "international relations",
        "diplomatic",
        "foreign",
    ],

    "Politics": [
        "president",
        "prime minister",
        "government",
        "election",
        "parliament",
        "senate",
        "congress",
        "minister",
        "political",
        "politics",
    ],

    "Business": [
        "business",
        "company",
        "companies",
        "economy",
        "economic",
        "market",
        "markets",
        "bank",
        "banks",
        "industry",
        "ceo",
    ],

    "Technology": [
        "technology",
        "tech",
        "artificial intelligence",
        "ai",
        "software",
        "computer",
        "smartphone",
        "internet",
        "cybersecurity",
        "google",
        "apple",
        "microsoft",
        "meta",
    ],

    "Sports": [
        "football",
        "soccer",
        "basketball",
        "nba",
        "tennis",
        "cricket",
        "formula 1",
        "f1",
        "boxing",
        "ufc",
        "sports",
    ],

    "Science": [
        "science",
        "scientist",
        "research",
        "study",
        "space",
        "nasa",
        "astronomy",
        "physics",
        "biology",
    ],

    "Entertainment": [
        "movie",
        "film",
        "music",
        "celebrity",
        "actor",
        "actress",
        "singer",
        "entertainment",
        "hollywood",
    ],
}


# ==========================================================
# HASHTAGS
# ==========================================================

CATEGORY_HASHTAGS = {
    "World": "#WorldNews #BreakingNews",

    "Politics": "#Politics #PoliticalNews",

    "Business": "#Business #BusinessNews",

    "Technology": "#Technology #TechNews",

    "Sports": "#Sports #SportsNews",

    "Science": "#Science #ScienceNews",

    "Entertainment": "#Entertainment #EntertainmentNews",
}


# ==========================================================
# TELEGRAM POST SETTINGS
# ==========================================================

# Maximum length of a Telegram message.
MAX_MESSAGE_LENGTH = 4096

# Maximum length used for the generated summary.
SUMMARY_MAX_LENGTH = 700

# Minimum title length accepted.
MIN_TITLE_LENGTH = 10


# ==========================================================
# USER BOT SETTINGS
# ==========================================================

# Whether users can receive breaking-news notifications.
ENABLE_USER_ALERTS = True

# Maximum number of users stored for alerts.
MAX_USERS = 100000


# ==========================================================
# LOGGING
# ==========================================================

LOG_LEVEL = os.getenv(
    "LOG_LEVEL",
    "INFO"
).upper()


# ==========================================================
# APPLICATION SETTINGS
# ==========================================================

APP_NAME = "World Breaking News Bot"
VERSION = "1.0.0"


# ==========================================================
# VALIDATION
# ==========================================================

if not NEWS_CHANNEL:
    raise ValueError(
        "NEWS_CHANNEL is missing. Add your Telegram channel username."
    )

if CHECK_INTERVAL < 10:
    CHECK_INTERVAL = 10

if MAX_ARTICLES_PER_FEED < 1:
    MAX_ARTICLES_PER_FEED = 1

if MAX_STORED_ARTICLES < 100:
    MAX_STORED_ARTICLES = 100
