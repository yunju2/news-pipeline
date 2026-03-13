#!/usr/bin/env python3
"""
Daily Tech Newsletter Pipeline

Collects articles from TechCrunch, Bloomberg, The Verge, and CNBC,
deduplicates them, and generates a Korean newsletter using Gemini API.

Usage:
    python pipeline.py              # Run for today
    python pipeline.py --date 2026-02-05  # Run for specific date
"""

import argparse
import json
import logging
import sys
from datetime import datetime

from config.settings import get_articles_dir, get_output_dir
from src.news_letter.collector.article_extractor import extract_full_text
from src.news_letter.collector.bloomberg_fetcher import fetch_bloomberg
from src.news_letter.collector.rss_fetcher import fetch_all_feeds
from src.news_letter.deduplicator.similarity import deduplicate_articles
from src.generator.groq_client import generate_newsletter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Daily Tech Newsletter Generator",
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Date for newsletter (YYYY-MM-DD format). Defaults to today.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    return parser.parse_args()


def get_target_date(date_str: str | None) -> datetime:
    """Parse date string or return today's date."""
    if date_str:
        return datetime.strptime(date_str, "%Y-%m-%d")
    return datetime.now()


def save_articles_json(articles: list, date_str: str) -> None:
    """Save raw articles to JSON for debugging."""
    output_dir = get_articles_dir(date_str)
    filepath = output_dir / "raw_articles.json"

    data = [article.to_dict() for article in articles]

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved raw articles to {filepath}")


def save_newsletter(newsletter: str, date_str: str) -> str:
    """Save generated newsletter to markdown file."""
    output_dir = get_output_dir(date_str)
    filepath = output_dir / "newsletter.md"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(newsletter)

    logger.info(f"Saved newsletter to {filepath}")
    return str(filepath)


def main() -> int:
    """Main pipeline entry point."""
    args = parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Get target date
    target_date = get_target_date(args.date)
    date_str = target_date.strftime("%Y-%m-%d")
    logger.info(f"Generating newsletter for: {date_str}")

    try:
        # Step 1: Fetch articles from all feeds
        logger.info("=" * 50)
        logger.info("Step 1: Fetching articles from RSS feeds...")
        articles = fetch_all_feeds()

        # Also fetch Bloomberg with fallback
        bloomberg_articles = fetch_bloomberg()
        # Remove duplicates from main fetch
        existing_urls = {a.url for a in articles}
        for ba in bloomberg_articles:
            if ba.url not in existing_urls:
                articles.append(ba)

        if not articles:
            logger.error("No articles collected. Check feed configurations.")
            return 1

        logger.info(f"Total articles collected: {len(articles)}")

        # Step 2: Extract full text
        logger.info("=" * 50)
        logger.info("Step 2: Extracting full text...")
        articles = extract_full_text(articles)

        # Save raw articles for debugging
        save_articles_json(articles, date_str)

        # Step 3: Deduplicate and rank
        logger.info("=" * 50)
        logger.info("Step 3: Deduplicating and ranking articles...")
        deduplicated = deduplicate_articles(articles)

        if not deduplicated:
            logger.error("No articles after deduplication.")
            return 1

        # Log top stories
        logger.info("Top stories:")
        for i, article in enumerate(deduplicated[:5], 1):
            sources = ", ".join(article.get_all_sources())
            logger.info(f"  {i}. [{sources}] {article.primary.title[:60]}...")

        # Step 4: Generate newsletter
        logger.info("=" * 50)
        logger.info("Step 4: Generating newsletter with Groq API...")
        newsletter = generate_newsletter(deduplicated, target_date)

        if not newsletter:
            logger.error("Newsletter generation failed.")
            return 1

        # Step 5: Save output
        logger.info("=" * 50)
        logger.info("Step 5: Saving newsletter...")
        output_path = save_newsletter(newsletter, date_str)

        logger.info("=" * 50)
        logger.info("Pipeline completed successfully!")
        logger.info(f"Newsletter saved to: {output_path}")

        return 0

    except Exception as e:
        logger.exception(f"Pipeline failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
