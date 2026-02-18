"""Project settings and configuration loader."""

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
SRC_DIR = PROJECT_ROOT / "src"
ARTICLES_DIR = PROJECT_ROOT / "articles"
OUTPUT_DIR = PROJECT_ROOT / "output"

# Ensure directories exist
ARTICLES_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


def load_feeds_config() -> dict:
    """Load feeds configuration from YAML file."""
    config_path = CONFIG_DIR / "rss_feeds.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


# Load configuration
_config = load_feeds_config()

# Feed settings
FEEDS = _config.get("feeds", {})
SETTINGS = _config.get("settings", {})

# Default values
HOURS_LOOKBACK = SETTINGS.get("hours_lookback", 24)
MAX_ARTICLES_PER_FEED = SETTINGS.get("max_articles_per_feed", 20)
MAX_CONTENT_LENGTH = SETTINGS.get("max_content_length", 2000)
SIMILARITY_THRESHOLD = SETTINGS.get("similarity_threshold", 0.65)
MAX_NEWSLETTER_ARTICLES = SETTINGS.get("max_newsletter_articles", 8)

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def get_output_dir(date_str: str) -> Path:
    """Get output directory for a specific date."""
    output_path = OUTPUT_DIR / date_str
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


def get_articles_dir(date_str: str) -> Path:
    """Get articles directory for a specific date."""
    articles_path = ARTICLES_DIR / date_str
    articles_path.mkdir(parents=True, exist_ok=True)
    return articles_path
