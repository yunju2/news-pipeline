import logging
import typer
import pathlib
from rich import print
from dotenv import load_dotenv
from src.news_letter.pipeline import run
from src.llm_client.validators import validate_model
from default_config import DEFAULT_CONFIG

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

    print("\n:one: 주식 현재가 조회")
    print(":two: 오늘의 뉴스 받기")

    choice = typer.prompt(f"\n 숫자를 입력하세요. (1 or 2) ", type=int)

    user_config = DEFAULT_CONFIG.copy()

    if choice == 1:
        print("\n 종료합니다. (미완성)")
        raise typer.Exit()
    elif choice == 2:
        print(f"[blue]사용 가능한 모델 : [/blue] groq, gemini, openAI")

        input_provider = typer.prompt(
            "사용할 Provider를 입력하세요.",
            default=user_config["deep_think_llm"]["provider"],
        )

        input_model = typer.prompt(
            "사용할 LLM Model를 입력하세요.",
            default=user_config["deep_think_llm"]["model"],
        )

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
