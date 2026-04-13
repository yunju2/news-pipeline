import os

DEFAULT_CONFIG = {
    "deep_think_llm": {
        "provider": "groq",
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
    },
    "quick_think_llm": {"provider": "groq", "model": "llama-3.1-8b-instant"},
    "data_vendors": {"core_stock_api": "yfinance"},
    "rss_feeds_config": os.path.join(
        os.path.dirname(__file__), "config", "rss_feeds.yaml"
    ),
    "news_pipeline": {
        "hours_lookback": 24,
        "max_articles_per_feed": 20,
        "max_content_length": 2000,
        "similarity_threshold": 0.65,
        "max_newsletter_articles": 8,
    },
}
