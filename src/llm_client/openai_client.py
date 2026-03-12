from openai import OpenAI
from config.settings import OPENAI_API_KEY
from .base_client import BaseLLMClient

class OpenAIClient(BaseLLMClient):
    """OpenAI API Client""" 
    def __init__(self, model: str, **kwargs):
        super().__init__(model, **kwargs)
        self._client: OpenAI | None = None

    def _get_client(self) -> OpenAI:
        if not self._client:
            api_key = OPENAI_API_KEY
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found. Set it in .env file.")
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
       
