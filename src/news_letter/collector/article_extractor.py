"""Article full text extractor using trafilatura."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import trafilatura
from default_config import DEFAULT_CONFIG
from src.news_letter.models import Article

# Request settings
REQUEST_TIMEOUT = 15
MAX_WORKERS = 5
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def fetch_html(url: str) -> str | None:
    """Fetch HTML content from URL."""
    response = requests.get(
        url,
        timeout=REQUEST_TIMEOUT,
        headers={"User-Agent": USER_AGENT},
    )
    response.raise_for_status()
    return response.text

def extract_text_from_html(html: str) -> str | None:
    """Extract main text content from HTML using trafilatura."""
    text = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=False,
        no_fallback=False,
    )
    return text



def extract_article_text(article: Article) -> Article:
    """Extract full text for a single article."""
    if article.full_text:
        return article

    html = fetch_html(article.url)
    text = extract_text_from_html(html)
    if text:
        # Truncate to max length
        max_len = DEFAULT_CONFIG["news_pipeline"]["max_content_length"]
        if len(text) > max_len:
            text = text[:max_len] + "..."
        article.full_text = text
    else:
        print(f"No text extracted for: {article.title[:50]}")

    return article


def extract_full_text(articles: list[Article]) -> list[Article]:
    """Extract full text for all articles in parallel."""
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(extract_article_text, article): article
            for article in articles
        }

        results = []
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                article = futures[future]
                print(f"Extraction failed for {article.title[:50]}: {e}")
                results.append(article)

    # Count successful extractions
    extracted = sum(1 for a in results if a.full_text)
    return results
