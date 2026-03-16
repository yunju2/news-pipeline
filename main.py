import logging
import typer
import pathlib
from rich import print
from dotenv import load_dotenv
from src.news_letter.pipeline import run
from src.llm_client.validators import validate_model, SUPPORTED_MODELS
from default_config import DEFAULT_CONFIG
from InquirerPy import prompt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)

load_dotenv()

app = typer.Typer()


def display_banner():
    """Display the ASCII art banner from assets/banner.txt"""
    banner_path = pathlib.Path(__file__).parent / "main" / "banner.txt"
    try:
        with open(banner_path, "r", encoding="utf-8") as f:
            banner_text = f.read()
            # Use style or simple print
            typer.echo(typer.style(banner_text, fg=typer.colors.CYAN, bold=True))
    except FileNotFoundError:
        pass


@app.command()
def main():
    """Daily Tech Newsletter CLI"""
    display_banner()

    print("\n🤍 1. 주식 현재가 조회")
    print("💜 2. 오늘의 뉴스 받기")

    choice = typer.prompt("\n 숫자를 입력하세요. (1 or 2) ", type=int)

    user_config = DEFAULT_CONFIG.copy()

    if choice == 1:
        print("\n 종료합니다. (미완성)")
        raise typer.Exit()
    elif choice == 2:
        print("[blue]사용 가능한 모델을 선택하세요:[/blue]")

        provider_question = [
            {
                "type": "list",
                "name": "provider",
                "message": "사용할 Provider를 선택하세요:",
                "choices": list(SUPPORTED_MODELS.keys()),
            }
        ]
        provider_answer = prompt(provider_question)
        input_provider = provider_answer.get("provider")

        if not input_provider:
            print("선택이 취소되었습니다.")
            raise typer.Exit()

        model_question = [
            {
                "type": "list",
                "name": "model",
                "message": f"{input_provider}의 모델을 선택하세요:",
                "choices": SUPPORTED_MODELS[input_provider],
            }
        ]
        model_answer = prompt(model_question)
        input_model = model_answer.get("model")

        if not input_model:
            print("선택이 취소되었습니다.")
            raise typer.Exit()

        if validate_model(input_provider, input_model):
            user_config["deep_think_llm"] = {
                "provider": input_provider,
                "model": input_model,
            }
            run(user_config)
        else:
            print("죄송합니다. 사용할 수 없는 모델 입니다.")


if __name__ == "__main__":
    app()
