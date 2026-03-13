import copy
import logging
from rich.console import Console

from src.news_letter.collector.article_extractor import extract_full_text
from src.news_letter.collector.bloomberg_fetcher import fetch_bloomberg
from src.news_letter.collector.rss_fetcher import fetch_all_feeds
from src.news_letter.deduplicator.similarity import deduplicate_articles
from src.news_letter.utils import (
    get_raw_articles_path,
    get_newsletter_path,
    get_date,
)
from src.news_letter.s3 import put_object
from src.agents.reporter.reporter import Report
from default_config import DEFAULT_CONFIG
from src.llm_client.openai_client import OpenAIClient
from src.llm_client.groq_client import GroqClient
from src.llm_client.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

USER_CONFIG = copy.copy(DEFAULT_CONFIG)
console = Console()


def article_pipeline():
    date_str = get_date()
    try:
        # Step 1: Fetch articles from all feeds
        console.print("Step 1: Fetching articles from RSS feeds...")
        articles = fetch_all_feeds()

        # Also fetch Bloomberg with fallback
        bloomberg_articles = fetch_bloomberg()
        existing_urls = {a.url for a in articles}
        for ba in bloomberg_articles:
            if ba.url not in existing_urls:
                articles.append(ba)

        # Step 2: Extract full text
        console.print("Step 2: Extracting full text...")
        articles = extract_full_text(articles)

        # save raw articles
        data = [article.to_dict() for article in articles]
        raw_path = get_raw_articles_path(date_str)
        put_object(data, raw_path)

        # Step 3: Deduplicate and rank
        console.print("Step 3: Deduplicating and ranking articles...")
        deduplicated = deduplicate_articles(articles)

        # Log top stories summary
        console.print(
            f"\n[bold green]Successfully deduplicated! Total: {len(deduplicated)} articles.[/bold green]"
        )
        for i, article in enumerate(deduplicated[:5], 1):
            sources = ", ".join(article.get_all_sources())
            console.print(
                f"  {i}. [cyan]{article.primary.title[:60]}...[/cyan] ({sources})"
            )

        return deduplicated

    except Exception as e:
        logging.exception(f"Pipeline failed: {e}")
        return None


def run(config: dict):
    # Generate newsletter
    date_str = get_date()
    provider = config["deep_think_llm"]["provider"]
    model = config["deep_think_llm"]["model"]

    if provider == "groq":
        report_agent = Report(GroqClient(model))
    elif provider == "gemini":
        report_agent = Report(GeminiClient(model))
    elif provider == "openai":
        report_agent = Report(OpenAIClient(model))
    else:
        console.print(f"[red]Error: Unsupported provider {provider}[/red]")
        return

    deduplicated = article_pipeline()
    newsletter = report_agent.generate_newsletter(deduplicated)

    # Step 5: Save output
    console.print("Step 5: Saving newsletter...")
    newsletter_path = get_newsletter_path(date_str, provider)
    put_object(newsletter, newsletter_path, provider=provider, model=model)

    console.print(
        f"Pipeline completed successfully! Saved to: {newsletter_path}",
        style="bold dim",
    )
