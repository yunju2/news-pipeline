from abc import ABC, abstractmethod
from typing import Any


class BaseLLMClient(ABC):
    """Base class for LLM clients."""

    def __init__(self, model: str, **kwargs):
        self.model = model

    @abstractmethod
    def call(self, prompt: str, **kwargs) -> str:
        pass
