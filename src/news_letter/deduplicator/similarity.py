"""Article deduplication using title similarity."""

from datetime import datetime
from difflib import SequenceMatcher
from default_config import DEFAULT_CONFIG
from src.news_letter.models import Article, DeduplicatedArticle

_CONFIG = DEFAULT_CONFIG["news_pipeline"]


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
    threshold: float | None = None,
) -> DeduplicatedArticle | None:
    """Find an existing group that this article is similar to."""
    if threshold is None:
        threshold = _CONFIG["similarity_threshold"]
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
    config = DEFAULT_CONFIG

    groups: list[DeduplicatedArticle] = []

    # Sort articles by published date (newest first) for better primary selection
    sorted_articles = sorted(
        articles,
        key=lambda a: a.published if a.published else datetime.min,
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
        key=lambda g: (
            g.importance_score,
            g.primary.published if g.primary.published else datetime.min,
        ),
        reverse=True,
    )

    # Limit to max newsletter articles
    max_articles = _CONFIG["max_newsletter_articles"]
    top_articles = groups[:max_articles]

    return top_articles
