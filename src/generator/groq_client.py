"""Groq API client for newsletter generation."""

import logging
import os
from datetime import datetime

from groq import Groq

from config.settings import GROQ_API_KEY
from src.generator.prompts import build_newsletter_prompt, format_articles_for_prompt
from src.models.article import DeduplicatedArticle

logger = logging.getLogger(__name__)

# Model configuration
MODEL_NAME = "llama-3.3-70b-versatile"


def get_client() -> Groq:
    """Get Groq API client."""
    api_key = GROQ_API_KEY or os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not found. "
            "Set it in .env file or as environment variable. "
            "Get your key at: https://console.groq.com"
        )

    return Groq(api_key=api_key)


def generate_newsletter(
    articles: list[DeduplicatedArticle],
    date: datetime,
) -> str:
    """
    Generate newsletter using Groq API.

    Args:
        articles: List of deduplicated articles
        date: Date for the newsletter

    Returns:
        Generated newsletter in markdown format
    """
    if not articles:
        logger.warning("No articles provided for newsletter generation")
        return ""

    logger.info(f"Generating newsletter for {len(articles)} articles...")

    # Format articles for prompt
    articles_text = format_articles_for_prompt(articles)

    # Build full prompt
    prompt = build_newsletter_prompt(articles_text, date)

    logger.debug(f"Prompt length: {len(prompt)} characters")

    # Call Groq API
    try:
        client = get_client()

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=4096,
        )

        newsletter = response.choices[0].message.content
        logger.info(f"Newsletter generated: {len(newsletter)} characters")

        return newsletter

    except Exception as e:
        logger.error(f"Groq API error: {e}")
        raise
