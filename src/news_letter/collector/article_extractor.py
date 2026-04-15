"""Article full text extractor using trafilatura."""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import trafilatura

from default_config import DEFAULT_CONFIG
from src.news_letter.models.schema import Article

MAX_CONTENT_LENGTH = DEFAULT_CONFIG["news_pipeline"]["max_content_length"]

logger = logging.getLogger(__name__)

# Request settings
REQUEST_TIMEOUT = 15
MAX_WORKERS = 5
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def fetch_html(url: str) -> str | None:
    """Fetch HTML content from URL."""
    try:
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers={"User-Agent": USER_AGENT},
        )
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logger.debug(f"Failed to fetch {url}: {e}")
        return None


def extract_text_from_html(html: str) -> str | None:
    """Extract main text content from HTML using trafilatura."""
    try:
        text = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=False,
            no_fallback=False,
        )
        return text
    except Exception as e:
        logger.debug(f"Trafilatura extraction failed: {e}")
        return None


def extract_article_text(article: Article) -> Article:
    """Extract full text for a single article."""
    if article.full_text:
        return article

    html = fetch_html(article.url)
    if not html:
        logger.debug(f"Could not fetch HTML for: {article.title[:50]}")
        return article

    text = extract_text_from_html(html)
    if text:
        # Truncate to max length
        if len(text) > MAX_CONTENT_LENGTH:
            text = text[:MAX_CONTENT_LENGTH] + "..."
        article.full_text = text
        logger.debug(f"Extracted {len(text)} chars for: {article.title[:50]}")
    else:
        logger.debug(f"No text extracted for: {article.title[:50]}")

    return article


def _prefetch_html(article: Article) -> tuple[Article, str | None]:
    """Fetch HTML in parallel but keep parser work single-threaded."""
    if article.full_text:
        return article, None
    return article, fetch_html(article.url)


def extract_full_text(articles: list[Article]) -> list[Article]:
    """Extract full text while avoiding concurrent trafilatura parsing crashes."""
    logger.info(f"Extracting full text for {len(articles)} articles...")

    prefetched: list[tuple[Article, str | None]] = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(_prefetch_html, article): article for article in articles
        }

        for future in as_completed(futures):
            try:
                prefetched.append(future.result())
            except Exception as e:
                article = futures[future]
                logger.error(f"HTML fetch failed for {article.title[:50]}: {e}")
                prefetched.append((article, None))

    results = []
    for article, html in prefetched:
        if article.full_text or not html:
            results.append(article)
            continue

        text = extract_text_from_html(html)
        if text:
            if len(text) > MAX_CONTENT_LENGTH:
                text = text[:MAX_CONTENT_LENGTH] + "..."
            article.full_text = text
            logger.debug(f"Extracted {len(text)} chars for: {article.title[:50]}")
        else:
            logger.debug(f"No text extracted for: {article.title[:50]}")
        results.append(article)

    # Count successful extractions
    extracted = sum(1 for a in results if a.full_text)
    logger.info(f"Successfully extracted text for {extracted}/{len(results)} articles")

    return results
