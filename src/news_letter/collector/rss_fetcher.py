"""RSS feed fetcher using feedparser."""

import logging
from datetime import datetime, timedelta, timezone
from time import mktime

import feedparser
import requests

from config.settings import FEEDS, HOURS_LOOKBACK, MAX_ARTICLES_PER_FEED
from src.models.article import Article

logger = logging.getLogger(__name__)

# Request settings
REQUEST_TIMEOUT = 15
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def parse_published_date(entry: dict) -> datetime | None:
    """Parse published date from RSS entry."""
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return datetime.fromtimestamp(mktime(entry.published_parsed), tz=timezone.utc)
    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        return datetime.fromtimestamp(mktime(entry.updated_parsed), tz=timezone.utc)
    return None


def is_within_lookback(published: datetime | None, hours: int = HOURS_LOOKBACK) -> bool:
    """Check if article is within the lookback period."""
    if not published:
        return True  # Include articles without date
    cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=hours)
    return published >= cutoff


def fetch_feed(feed_id: str, feed_config: dict) -> list[Article]:
    """Fetch articles from a single RSS feed."""
    url = feed_config.get("url")
    name = feed_config.get("name", feed_id)

    if not url:
        logger.warning(f"No URL configured for feed: {feed_id}")
        return []

    logger.info(f"Fetching feed: {name} ({url})")

    try:
        # Use requests to fetch feed (handles SSL properly)
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers={"User-Agent": USER_AGENT},
        )
        response.raise_for_status()
        feed = feedparser.parse(response.content)

        if feed.bozo and feed.bozo_exception:
            logger.debug(f"Feed parsing note for {name}: {feed.bozo_exception}")

        articles = []
        for entry in feed.entries[:MAX_ARTICLES_PER_FEED]:
            published = parse_published_date(entry)

            if not is_within_lookback(published):
                continue

            article = Article(
                title=entry.get("title", "").strip(),
                url=entry.get("link", ""),
                source=name,
                published=published,
                summary=entry.get("summary", "").strip(),
                categories=[
                    tag.term for tag in entry.get("tags", []) if hasattr(tag, "term")
                ],
            )

            if article.title and article.url:
                articles.append(article)

        logger.info(f"Fetched {len(articles)} articles from {name}")
        return articles

    except Exception as e:
        logger.error(f"Failed to fetch feed {name}: {e}")
        return []


def fetch_all_feeds() -> list[Article]:
    """Fetch articles from all configured feeds."""
    all_articles = []

    for feed_id, feed_config in FEEDS.items():
        articles = fetch_feed(feed_id, feed_config)
        all_articles.extend(articles)

    logger.info(f"Total articles fetched: {len(all_articles)}")
    return all_articles
