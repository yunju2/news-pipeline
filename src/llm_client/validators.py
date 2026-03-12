# 지원하는 모델 목록 정의
SUPPORTED_MODELS = {
    "groq": ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "llama3-70b-8192"],
    "gemini": [
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.5-pro",
    ],
    "openai" : ["gpt-4o-mini", "gpt-4o"]
}


def validate_model(provider: str, model: str) -> bool:
    if provider in SUPPORTED_MODELS:
        return model in SUPPORTED_MODELS[provider]

    return False
