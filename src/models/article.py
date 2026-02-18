"""Article data models."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Article:
    """Single article from a news source."""

    title: str
    url: str
    source: str
    published: datetime | None = None
    summary: str = ""
    full_text: str = ""
    categories: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "published": self.published.isoformat() if self.published else None,
            "summary": self.summary,
            "full_text": self.full_text,
            "categories": self.categories,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Article":
        """Create Article from dictionary."""
        published = None
        if data.get("published"):
            published = datetime.fromisoformat(data["published"])
        return cls(
            title=data["title"],
            url=data["url"],
            source=data["source"],
            published=published,
            summary=data.get("summary", ""),
            full_text=data.get("full_text", ""),
            categories=data.get("categories", []),
        )


@dataclass
class DeduplicatedArticle:
    """Article after deduplication, may represent multiple related articles."""

    primary: Article
    related: list[Article] = field(default_factory=list)
    source_count: int = 1
    importance_score: float = 0.0

    def __post_init__(self) -> None:
        """Calculate importance score based on source count."""
        self.source_count = 1 + len(self.related)
        self.importance_score = self.source_count

    def get_all_sources(self) -> list[str]:
        """Get list of all sources covering this story."""
        sources = [self.primary.source]
        sources.extend(article.source for article in self.related)
        return sources

    def get_content(self, max_length: int = 2000) -> str:
        """Get the best available content, truncated to max_length."""
        content = self.primary.full_text or self.primary.summary
        if len(content) > max_length:
            content = content[:max_length] + "..."
        return content

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "primary": self.primary.to_dict(),
            "related": [article.to_dict() for article in self.related],
            "source_count": self.source_count,
            "importance_score": self.importance_score,
        }
