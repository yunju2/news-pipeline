from datetime import datetime

from src.llm_client.base_client import BaseLLMClient
from src.news_letter.models.schema import DeduplicatedArticle
from src.news_letter.prompts import format_articles_for_prompt, build_newsletter_prompt


class Report:
    def __init__(self, llm_client: BaseLLMClient):
        self.llm = llm_client

    def generate_newsletter(self, articles: list[DeduplicatedArticle]) -> str:

        articles_text = format_articles_for_prompt(articles)
        prompt = build_newsletter_prompt(articles_text, datetime.now())

        return self.llm.call(prompt)
