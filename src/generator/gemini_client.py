"""Gemini API client for newsletter generation."""

import logging
import os
from datetime import datetime

from google import genai

from config.settings import GEMINI_API_KEY
from src.generator.prompts import build_newsletter_prompt, format_articles_for_prompt
from src.models.article import DeduplicatedArticle

logger = logging.getLogger(__name__)

# Model configuration
MODEL_NAME = "gemini-2.5-flash"


def get_client() -> genai.Client:
    """Get Gemini API client."""
    api_key = GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY not found. "
            "Set it in .env file or as environment variable. "
            "Get your key at: https://aistudio.google.com"
        )

    return genai.Client(api_key=api_key)


def generate_newsletter(
    articles: list[DeduplicatedArticle],
    date: datetime,
) -> str:
    """
    Generate newsletter using Gemini API.

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

    # Call Gemini API
    try:
        client = get_client()

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )

        newsletter = response.text
        logger.info(f"Newsletter generated: {len(newsletter)} characters")

        return newsletter

    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        raise
