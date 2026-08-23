import os

from dotenv import load_dotenv


# ==========================================================
# LOAD ENVIRONMENT VARIABLES
# ==========================================================

load_dotenv()


# ==========================================================
# TELEGRAM BOT
# ==========================================================

BOT_TOKEN = os.getenv(
    "BOT_TOKEN",
    ""
).strip()

if not BOT_TOKEN:
    raise ValueError(
        "BOT_TOKEN is missing. "
        "Add BOT_TOKEN to your Railway Variables."
    )


# ==========================================================
# ADMIN
# ==========================================================

ADMIN_ID_RAW = os.getenv(
    "ADMIN_ID",
    "0"
).strip()

try:
    ADMIN_ID = int(ADMIN_ID_RAW)
except ValueError:
    ADMIN_ID = 0


# ==========================================================
# 100+ TELEGRAM CHANNELS
# ==========================================================

NEWS_CHANNELS_RAW = os.getenv(
    "NEWS_CHANNELS",
    ""
).strip()


def parse_channels(value: str):
    """
    Convert a comma-separated channel list into a clean list.

    Examples:

    @channelone,@channeltwo

    or

    -1001234567890,-1009876543210
    """

    channels = []

    for item in value.split(","):

        channel = item.strip()

        if not channel:
            continue

        if channel not in channels:
            channels.append(channel)

    return channels


NEWS_CHANNELS = parse_channels(
    NEWS_CHANNELS_RAW
)


if not NEWS_CHANNELS:
    raise ValueError(
        "NEWS_CHANNELS is missing. "
        "Add at least one Telegram channel username "
        "or numeric channel ID."
    )


# ==========================================================
# NEWS CHECK SETTINGS
# ==========================================================

CHECK_INTERVAL = int(
    os.getenv(
        "CHECK_INTERVAL",
        "30"
    )
)

if CHECK_INTERVAL < 10:
    CHECK_INTERVAL = 10


MAX_ARTICLES_PER_FEED = int(
    os.getenv(
        "MAX_ARTICLES_PER_FEED",
        "10"
    )
)

if MAX_ARTICLES_PER_FEED < 1:
    MAX_ARTICLES_PER_FEED = 1


MAX_STORED_ARTICLES = int(
    os.getenv(
        "MAX_STORED_ARTICLES",
        "5000"
    )
)

if MAX_STORED_ARTICLES < 100:
    MAX_STORED_ARTICLES = 100


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

    "World":
        "#WorldNews #BreakingNews",

    "Politics":
        "#Politics #PoliticalNews",

    "Business":
        "#Business #BusinessNews",

    "Technology":
        "#Technology #TechNews",

    "Sports":
        "#Sports #SportsNews",

    "Science":
        "#Science #ScienceNews",

    "Entertainment":
        "#Entertainment #EntertainmentNews",
}


# ==========================================================
# MESSAGE SETTINGS
# ==========================================================

MAX_MESSAGE_LENGTH = 4096

SUMMARY_MAX_LENGTH = 700

MIN_TITLE_LENGTH = 10


# ==========================================================
# USER ALERT SETTINGS
# ==========================================================

ENABLE_USER_ALERTS = True

MAX_USERS = 100000


# ==========================================================
# LOGGING
# ==========================================================

LOG_LEVEL = os.getenv(
    "LOG_LEVEL",
    "INFO"
).upper()


# ==========================================================
# APPLICATION INFORMATION
# ==========================================================

APP_NAME = "World Breaking News Bot"

VERSION = "2.0.0"


# ==========================================================
# CHANNEL INFORMATION
# ==========================================================

CHANNEL_COUNT = len(
    NEWS_CHANNELS
)


# ==========================================================
# STARTUP INFORMATION
# ==========================================================

print(
    f"Loaded {CHANNEL_COUNT} Telegram channel(s)."
)

if CHANNEL_COUNT >= 100:
    print(
        "100+ channel mode enabled."
    )
