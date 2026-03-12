from pathlib import Path
from typing import Any
from datetime import datetime
from default_config import DEFAULT_CONFIG

import yaml

PACKAGE_ROOT_DIR = Path(__file__).absolute().parent
PROJECT_ROOT_DIR = PACKAGE_ROOT_DIR.parent.parent
DATA_DIR = PROJECT_ROOT_DIR / "data"


def load_yaml(path: Path) -> dict[str, Any]:
    """Helper to load YAML file."""
    try:
        if not path.exists():
            return {}
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


# Load configuration (User custom feeds/settings)
_config = load_yaml(PROJECT_ROOT_DIR / "config" / "rss_feeds.yaml")

# Feed settings
FEEDS = _config.get("feeds", {})


def get_date() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def get_raw_articles_path(date_str: str) -> Path:
    return DATA_DIR / "raw" / date_str / "articles.json"


def get_newsletter_path(date_str: str, provider: str) -> Path:
    return DATA_DIR / "processed" / date_str / f"newsletter_{provider}.md"


def load_feeds() -> dict:
    """Load RSS feed config from YAML."""
    config_path = DEFAULT_CONFIG["rss_feeds_config"]
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    feeds = {}
    for feed_id, feed_config in data.get("feeds", {}).items():
        if feed_config.get("enabled", True):
            feeds[feed_id] = feed_config
    return feeds
