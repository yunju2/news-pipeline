import argparse
import logging
import os
import sys

from dotenv import load_dotenv
from rich import print

from default_config import DEFAULT_CONFIG
from src.llm_client.validators import validate_model
from src.news_letter.pipeline import run

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)

load_dotenv()


def parse_args() -> argparse.Namespace:
    """Parse non-interactive runtime overrides."""
    default_provider = DEFAULT_CONFIG["deep_think_llm"]["provider"]
    default_model = DEFAULT_CONFIG["deep_think_llm"]["model"]

    parser = argparse.ArgumentParser(
        description=(
            "Run the daily tech newsletter pipeline without interactive prompts. "
            "CLI args override environment variables, and missing overrides fall back "
            "to default_config.py."
        ),
    )
    parser.add_argument(
        "--provider",
        default=os.getenv("NEWS_PIPELINE_PROVIDER"),
        help=(
            "LLM provider override. If omitted, uses NEWS_PIPELINE_PROVIDER env var; "
            f"otherwise defaults to {default_provider} from default_config.py."
        ),
    )
    parser.add_argument(
        "--model",
        default=os.getenv("NEWS_PIPELINE_MODEL"),
        help=(
            "LLM model override. If omitted, uses NEWS_PIPELINE_MODEL env var; "
            f"otherwise defaults to {default_model} from default_config.py."
        ),
    )
    return parser.parse_args()


def build_runtime_config(provider: str | None, model: str | None) -> dict:
    """Build runtime config for automated environments."""
    user_config = DEFAULT_CONFIG.copy()

    if provider is None and model is None:
        return user_config

    if not provider or not model:
        raise ValueError(
            "LLM override requires both provider and model. "
            "Set both NEWS_PIPELINE_PROVIDER and NEWS_PIPELINE_MODEL, "
            "or pass both --provider and --model."
        )

    if not validate_model(provider, model):
        raise ValueError(
            f"Unsupported LLM override: provider={provider}, model={model}"
        )

    user_config["deep_think_llm"] = {
        "provider": provider,
        "model": model,
    }
    return user_config


def main() -> int:
    """Daily Tech Newsletter automated entry point."""
    args = parse_args()

    try:
        user_config = build_runtime_config(args.provider, args.model)
    except ValueError as exc:
        logging.error(str(exc))
        return 1

    provider = user_config["deep_think_llm"]["provider"]
    model = user_config["deep_think_llm"]["model"]

    print("\n[bold]뉴스 파이프라인을 비대화형 모드로 실행합니다.[/bold]")
    print(f"👉 설정된 LLM: {provider} / {model}")
    run(user_config)
    return 0


if __name__ == "__main__":
    sys.exit(main())
