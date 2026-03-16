from groq import Groq
from openai import OpenAI
from config.settings import OPENAI_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY
from .base_client import BaseLLMClient
from typing import Any


class OpenAIClient(BaseLLMClient):
    """Client for OpenAI, OpenRouter, Groq"""

    def __init__(self, provider: str, model: str, **kwargs):
        super().__init__(model, **kwargs)
        self.provider = provider
        self._client: Any = None

    def _get_client(self) -> Any:
        if not self._client:
            if self.provider == "groq":
                api_key = GROQ_API_KEY
                if not api_key:
                    raise ValueError(
                        f"{self.provider}_API_KEY not found. Set it in .env file."
                    )
                self._client = Groq(api_key=api_key)
            elif self.provider == "openrouter":
                api_key = OPENROUTER_API_KEY
                if not api_key:
                    raise ValueError(
                        f"{self.provider}_API_KEY not found. Set it in .env file."
                    )
                self._client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=api_key,
                )
            elif self.provider == "openai":
                api_key = OPENAI_API_KEY
                if not api_key:
                    raise ValueError(
                        f"{self.provider}_API_KEY not found. Set it in .env file."
                    )
                self._client = OpenAI(api_key=api_key)
        return self._client

    def call(self, prompt: str, **kwargs) -> str:
        """Call OpenAI API with prompt."""
        client = self._get_client()

        llm_kwargs = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
        }

        llm_kwargs.update(kwargs)

        response = client.chat.completions.create(**llm_kwargs)
        return response.choices[0].message.content
