# CLI Config via typer.prompt Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** typer.prompt로 default_config.py 설정값을 사용자에게 받아 config/settings.py 글로벌 모듈에 세팅하고, 모든 하위 모듈이 이를 사용하게 한다.

**Architecture:** main.py를 typer CLI 앱으로 전환. 사용자 입력값으로 config/settings.py의 런타임 변수를 세팅. 각 모듈은 `from config.settings import VAR`로 접근.

**Tech Stack:** typer, Python 3.11+

---

### Task 1: config/settings.py에 런타임 config 변수 추가

**Files:**
- Modify: `config/settings.py`

**Step 1: config/settings.py에 default_config 기반 런타임 변수와 set_config 함수 추가**

```python
import os
import yaml
from dotenv import load_dotenv

load_dotenv()

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- Runtime config (set by main.py via set_config) ---

# LLM
DEEP_THINK_PROVIDER = "groq"
DEEP_THINK_MODEL = "llama-3.3-70b-versatile"
QUICK_THINK_PROVIDER = "groq"
QUICK_THINK_MODEL = "llama-3.1-8b-instant"

# News pipeline
HOURS_LOOKBACK = 24
MAX_ARTICLES_PER_FEED = 20
MAX_CONTENT_LENGTH = 2000
SIMILARITY_THRESHOLD = 0.65
MAX_NEWSLETTER_ARTICLES = 8

# RSS feeds (loaded from yaml)
RSS_FEEDS_CONFIG = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "rss_feeds.yaml")
FEEDS: dict = {}


def _load_feeds(config_path: str) -> dict:
    """Load RSS feed config from YAML."""
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    feeds = {}
    for feed_id, feed_config in data.get("feeds", {}).items():
        if feed_config.get("enabled", True):
            feeds[feed_id] = feed_config
    return feeds


def set_config(config: dict) -> None:
    """Set runtime config from user input."""
    global DEEP_THINK_PROVIDER, DEEP_THINK_MODEL
    global QUICK_THINK_PROVIDER, QUICK_THINK_MODEL
    global HOURS_LOOKBACK, MAX_ARTICLES_PER_FEED, MAX_CONTENT_LENGTH
    global SIMILARITY_THRESHOLD, MAX_NEWSLETTER_ARTICLES
    global RSS_FEEDS_CONFIG, FEEDS

    deep = config.get("deep_think_llm", {})
    DEEP_THINK_PROVIDER = deep.get("provider", DEEP_THINK_PROVIDER)
    DEEP_THINK_MODEL = deep.get("model", DEEP_THINK_MODEL)

    quick = config.get("quick_think_llm", {})
    QUICK_THINK_PROVIDER = quick.get("provider", QUICK_THINK_PROVIDER)
    QUICK_THINK_MODEL = quick.get("model", QUICK_THINK_MODEL)

    pipeline = config.get("news_pipeline", {})
    HOURS_LOOKBACK = pipeline.get("hours_lookback", HOURS_LOOKBACK)
    MAX_ARTICLES_PER_FEED = pipeline.get("max_articles_per_feed", MAX_ARTICLES_PER_FEED)
    MAX_CONTENT_LENGTH = pipeline.get("max_content_length", MAX_CONTENT_LENGTH)
    SIMILARITY_THRESHOLD = pipeline.get("similarity_threshold", SIMILARITY_THRESHOLD)
    MAX_NEWSLETTER_ARTICLES = pipeline.get("max_newsletter_articles", MAX_NEWSLETTER_ARTICLES)

    rss_path = config.get("rss_feeds_config", RSS_FEEDS_CONFIG)
    RSS_FEEDS_CONFIG = rss_path
    FEEDS = _load_feeds(rss_path)
```

---

### Task 2: main.py를 typer CLI로 전환

**Files:**
- Modify: `main.py`

**Step 1: typer 기반으로 main.py 재작성**

```python
import typer
from dotenv import load_dotenv

from default_config import DEFAULT_CONFIG
from config.settings import set_config
from src.llm_client.groq_client import GroqClient
from src.llm_client.gemini_client import GeminiClient

load_dotenv()

app = typer.Typer()


def create_llm_client(provider: str, model: str):
    if provider == "groq":
        return GroqClient(model=model)
    elif provider == "gemini":
        return GeminiClient(model=model)
    else:
        raise ValueError(f"Unknown provider: {provider}")


@app.command()
def main():
    """Daily Tech Newsletter CLI"""
    defaults = DEFAULT_CONFIG

    # LLM settings
    deep_provider = typer.prompt(
        "deep_think provider", default=defaults["deep_think_llm"]["provider"]
    )
    deep_model = typer.prompt(
        "deep_think model", default=defaults["deep_think_llm"]["model"]
    )
    quick_provider = typer.prompt(
        "quick_think provider", default=defaults["quick_think_llm"]["provider"]
    )
    quick_model = typer.prompt(
        "quick_think model", default=defaults["quick_think_llm"]["model"]
    )

    # Pipeline settings
    hours_lookback = typer.prompt(
        "hours_lookback", default=defaults["news_pipeline"]["hours_lookback"], type=int
    )
    max_articles = typer.prompt(
        "max_articles_per_feed", default=defaults["news_pipeline"]["max_articles_per_feed"], type=int
    )
    max_content = typer.prompt(
        "max_content_length", default=defaults["news_pipeline"]["max_content_length"], type=int
    )
    similarity = typer.prompt(
        "similarity_threshold", default=defaults["news_pipeline"]["similarity_threshold"], type=float
    )
    max_newsletter = typer.prompt(
        "max_newsletter_articles", default=defaults["news_pipeline"]["max_newsletter_articles"], type=int
    )

    # Build config dict
    config = {
        "deep_think_llm": {"provider": deep_provider, "model": deep_model},
        "quick_think_llm": {"provider": quick_provider, "model": quick_model},
        "rss_feeds_config": defaults["rss_feeds_config"],
        "news_pipeline": {
            "hours_lookback": hours_lookback,
            "max_articles_per_feed": max_articles,
            "max_content_length": max_content,
            "similarity_threshold": similarity,
            "max_newsletter_articles": max_newsletter,
        },
    }

    # Set global config
    set_config(config)

    # Run pipeline
    from src.pipeline import article_pipeline
    article_pipeline()


if __name__ == "__main__":
    app()
```

---

### Task 3: bloomberg_fetcher.py에 누락된 import 추가

**Files:**
- Modify: `src/news_letter/collector/bloomberg_fetcher.py`

**Step 1: config.settings에서 필요한 변수 import**

```python
from config.settings import FEEDS, HOURS_LOOKBACK, MAX_ARTICLES_PER_FEED
```

---

### Task 4: similarity.py에 누락된 import 추가

**Files:**
- Modify: `src/news_letter/deduplicator/similarity.py`

**Step 1: config.settings에서 필요한 변수 import**

```python
from config.settings import SIMILARITY_THRESHOLD, MAX_NEWSLETTER_ARTICLES
```

---

### Task 5: pipeline.py에서 argparse 제거, 함수명 수정

**Files:**
- Modify: `src/pipeline.py`

**Step 1: argparse 관련 코드 제거, 함수명을 article_pipeline으로 수정, config.settings 사용**

---

### Task 6: pyproject.toml에 typer 의존성 추가

**Files:**
- Modify: `pyproject.toml`

**Step 1: dependencies에 typer 추가**

```toml
"typer>=0.9.0",
```
