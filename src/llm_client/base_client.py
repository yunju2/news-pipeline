from abc import ABC, abstractmethod


class BaseLLMClient(ABC):
    """Base class for LLM clients."""

    def __init__(self, model: str, **kwargs):
        self.model = model

    @abstractmethod
    def call(self, prompt: str, **kwargs) -> str:
        pass
