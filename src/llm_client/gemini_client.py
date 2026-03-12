import os

from google import genai
from config.settings import GEMINI_API_KEY
from .base_client import BaseLLMClient


class GeminiClient(BaseLLMClient):
    """Gemini API client."""

    def __init__(self, model: str, **kwargs):
        super().__init__(model, **kwargs)
        self._client: genai.Client | None = None

    def _get_client(self) -> genai.Client:
        if self._client is None:
            api_key = GEMINI_API_KEY
            if not api_key:
                raise ValueError("GEMINI_API_KEY not found. Set it in .env file.")
            self._client = genai.Client(api_key=api_key)
        return self._client

    def call(self, prompt: str, **kwargs) -> str:
        client = self._get_client()

        llm_kwargs = {
            "model": self.model,
            "contents": prompt,
        }

        llm_kwargs.update(kwargs)

        response = client.models.generate_content(**llm_kwargs)

        return response.text
