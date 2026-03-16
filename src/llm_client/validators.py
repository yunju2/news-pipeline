# 지원하는 모델 목록 정의
SUPPORTED_MODELS = {
    "groq": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
    "openrouter": ["qwen/qwen3-next-80b-a3b-instruct:free"],
    "google": [
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.5-pro",
    ],
    "openai": ["gpt-4o-mini", "gpt-4o"],
}


def validate_model(provider: str, model: str) -> bool:
    if provider in SUPPORTED_MODELS:
        return model in SUPPORTED_MODELS[provider]

    return False
