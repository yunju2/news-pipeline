"""Article deduplication using title similarity."""

import logging
from difflib import SequenceMatcher

from config.settings import MAX_NEWSLETTER_ARTICLES, SIMILARITY_THRESHOLD
from src.models.article import Article, DeduplicatedArticle

logger = logging.getLogger(__name__)


def normalize_title(title: str) -> str:
    """Normalize title for comparison."""
    # Lowercase and remove common suffixes
    title = title.lower().strip()

    # Remove source names that might be appended
    suffixes = [
        " - techcrunch",
        " - the verge",
        " - bloomberg",
        " - cnbc",
        " | techcrunch",
        " | the verge",
        " | bloomberg",
        " | cnbc",
    ]
    for suffix in suffixes:
        if title.endswith(suffix):
            title = title[: -len(suffix)]

    return title.strip()


def title_similarity(title1: str, title2: str) -> float:
    """Calculate similarity between two titles using SequenceMatcher."""
    t1 = normalize_title(title1)
    t2 = normalize_title(title2)
    return SequenceMatcher(None, t1, t2).ratio()


def find_similar_article(
    article: Article,
    groups: list[DeduplicatedArticle],
    threshold: float = SIMILARITY_THRESHOLD,
) -> DeduplicatedArticle | None:
    """Find an existing group that this article is similar to."""
    for group in groups:
        if title_similarity(article.title, group.primary.title) >= threshold:
            return group

        # Also check against related articles
        for related in group.related:
            if title_similarity(article.title, related.title) >= threshold:
                return group

    return None


def deduplicate_articles(articles: list[Article]) -> list[DeduplicatedArticle]:
    """
    Deduplicate articles by title similarity.

    Groups similar articles together and ranks by importance (source count).
    """
    if not articles:
        return []

    logger.info(f"Deduplicating {len(articles)} articles...")

    groups: list[DeduplicatedArticle] = []

    # Sort articles by published date (newest first) for better primary selection
    sorted_articles = sorted(
        articles,
        key=lambda a: a.published or a.published,
        reverse=True,
    )

    for article in sorted_articles:
        similar_group = find_similar_article(article, groups)

        if similar_group:
            # Add to existing group if from different source
            if article.source != similar_group.primary.source:
                if article.source not in similar_group.get_all_sources():
                    similar_group.related.append(article)
                    similar_group.source_count = 1 + len(similar_group.related)
                    similar_group.importance_score = similar_group.source_count
        else:
            # Create new group
            groups.append(DeduplicatedArticle(primary=article))

    # Sort by importance score (source count), then by date
    groups.sort(
        key=lambda g: (g.importance_score, g.primary.published or g.primary.published),
        reverse=True,
    )

    logger.info(f"Deduplicated to {len(groups)} unique stories")

    # Limit to max newsletter articles
    top_articles = groups[:MAX_NEWSLETTER_ARTICLES]
    logger.info(f"Selected top {len(top_articles)} articles for newsletter")

    return top_articles
