"""Bloomberg specific fetcher with fallback strategies."""

import logging
from datetime import datetime, timedelta, timezone
from time import mktime

import feedparser
import requests

from src.news_letter.utils import load_feeds
from src.news_letter.models import Article
from default_config import DEFAULT_CONFIG

logger = logging.getLogger(__name__)

# Request settings
REQUEST_TIMEOUT = 15
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def fetch_rss_content(url: str) -> str | None:
    """Fetch RSS content using requests."""
    try:
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers={"User-Agent": USER_AGENT},
        )
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        logger.debug(f"Failed to fetch {url}: {e}")
        return None


def fetch_bloomberg_direct() -> list[Article]:
    """Try to fetch Bloomberg articles from their direct RSS feed."""
    feeds = load_feeds()
    bloomberg_config = feeds.get("bloomberg", {})
    url = bloomberg_config.get("url")

    if not url:
        return []

    logger.info(f"Trying Bloomberg direct RSS: {url}")

    try:
        content = fetch_rss_content(url)
        if not content:
            logger.warning("Bloomberg direct RSS: failed to fetch")
            return []

        feed = feedparser.parse(content)

        if not feed.entries:
            logger.warning("Bloomberg direct RSS failed or empty")
            return []

        articles = []
        hours = DEFAULT_CONFIG["news_pipeline"]["hours_lookback"]
        max_per_feed = DEFAULT_CONFIG["news_pipeline"]["max_articles_per_feed"]
        cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=hours)

        for entry in feed.entries[:max_per_feed]:
            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = datetime.fromtimestamp(
                    mktime(entry.published_parsed), tz=timezone.utc
                )

            if published and published < cutoff:
                continue

            article = Article(
                title=entry.get("title", "").strip(),
                url=entry.get("link", ""),
                source="Bloomberg",
                published=published,
                summary=entry.get("summary", "").strip(),
            )

            if article.title and article.url:
                articles.append(article)

        if articles:
            logger.info(f"Bloomberg direct RSS: {len(articles)} articles")
            return articles

    except Exception as e:
        logger.warning(f"Bloomberg direct RSS error: {e}")

    return []


def fetch_bloomberg_google_news() -> list[Article]:
    """Fetch Bloomberg articles via Google News RSS as fallback."""
    feeds = load_feeds()
    bloomberg_config = feeds.get("bloomberg", {})
    fallback_url = bloomberg_config.get("fallback_url")

    if not fallback_url:
        fallback_url = "https://news.google.com/rss/search?q=site:bloomberg.com&hl=en-US&gl=US&ceid=US:en"

    logger.info("Using Google News fallback for Bloomberg")

    try:
        content = fetch_rss_content(fallback_url)
        if not content:
            logger.warning("Google News RSS: failed to fetch")
            return []

        feed = feedparser.parse(content)

        articles = []
        hours = DEFAULT_CONFIG["news_pipeline"]["hours_lookback"]
        max_per_feed = DEFAULT_CONFIG["news_pipeline"]["max_articles_per_feed"]
        cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=hours)

        for entry in feed.entries[:max_per_feed]:
            # Google News wraps the original URL
            url = entry.get("link", "")

            # Skip if not actually Bloomberg
            if "bloomberg.com" not in url.lower():
                continue

            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = datetime.fromtimestamp(
                    mktime(entry.published_parsed), tz=timezone.utc
                )

            if published and published < cutoff:
                continue

            title = entry.get("title", "").strip()
            # Google News often appends " - Bloomberg" to titles
            if title.endswith(" - Bloomberg"):
                title = title[:-12].strip()

            article = Article(
                title=title,
                url=url,
                source="Bloomberg",
                published=published,
                summary=entry.get("summary", "").strip(),
            )

            if article.title and article.url:
                articles.append(article)

        logger.info(f"Google News fallback: {len(articles)} Bloomberg articles")
        return articles

    except Exception as e:
        logger.error(f"Google News fallback error: {e}")
        return []


def fetch_bloomberg() -> list[Article]:
    """Fetch Bloomberg articles with 2-stage fallback."""
    # Stage 1: Try direct RSS
    articles = fetch_bloomberg_direct()

    if articles:
        return articles

    # Stage 2: Fall back to Google News
    logger.info("Bloomberg direct RSS empty, trying Google News fallback")
    return fetch_bloomberg_google_news()
