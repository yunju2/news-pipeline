"""News collection module."""

from .rss_fetcher import fetch_all_feeds
from .article_extractor import extract_full_text

__all__ = ["fetch_all_feeds", "extract_full_text"]
