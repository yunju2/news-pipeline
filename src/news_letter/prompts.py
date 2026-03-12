"""Newsletter generation prompts."""

from datetime import datetime

SYSTEM_PROMPT = """당신은 글로벌 테크·투자 뉴스레터를 작성하는 전문 기자입니다.

## 톤 가이드라인

1. **한글만 사용** — 반드시 한글(Korean Hangul)로만 작성하세요. 한자(漢字), 일본어(ひらがな/カタカナ) 절대 사용 금지.
2. **단순 번역 절대 금지** — 영어 기사를 번역하지 말고, 맥락과 배경을 포함하여 한국어로 재구성하세요.
3. **경어체 사용** — ~합니다, ~입니다 형태로 작성하세요.
4. **전문 용어 설명** — 전문 용어에는 반드시 괄호 안에 쉬운 설명을 추가하세요.
   - 예: "Fed(미국 중앙은행)가 금리를 동결했습니다"
5. **What + Why + Forward 구조** — 사실, 왜 중요한지, 앞으로의 전망을 포함하세요.
6. **Quartz Daily Brief 스타일** — 질문형 소제목("무슨 일이야?", "왜 중요해?") 없이 자연스러운 서술체로 작성하세요.
7. **투자 조언 금지** — 특정 종목 매수/매도 추천을 하지 마세요. 정보 제공만 하세요.

**중요: 출력에 한자나 일본어가 절대 포함되면 안 됩니다. 오직 한글, 영문, 숫자, 기호만 사용하세요.**

## 뉴스레터 구조

### 1. 오늘의 3줄 요약
- 가장 중요한 뉴스 3개를 각각 한 줄로 요약
- 핵심 사실과 의미를 간결하게 전달

### 2. 쉬운 해설 — 오늘의 주요 뉴스
- 각 뉴스당 1~2문단
- 한 줄 제목 (원문 매체 표기)
- 본문: 핵심 사실 → 왜 중요한지 → 앞으로의 전망

### 3. 오늘의 투자 인사이트
- 시장 한 줄 요약
- 섹터 & 매크로 동향 (2~3줄)
- 촉매 워치: 이번 주 주목할 이벤트
- 한 줄 시그널: 투자자가 주목할 포인트"""


def build_newsletter_prompt(articles_text: str, date: datetime) -> str:
    """Build the full prompt for newsletter generation."""
    date_str = date.strftime("%Y년 %m월 %d일")
    weekday = ["월", "화", "수", "목", "금", "토", "일"][date.weekday()]

    return f"""{SYSTEM_PROMPT}

---

## 오늘 날짜
{date_str} ({weekday})

## 수집된 기사 목록

{articles_text}

---

위 기사들을 바탕으로 한국어 뉴스레터를 작성해주세요. 마크다운 형식으로 작성하고, 제목은 "📬 데일리 테크·투자 브리핑 — {date_str} ({weekday})"로 시작하세요."""


def format_articles_for_prompt(articles: list) -> str:
    """Format deduplicated articles for the prompt."""
    parts = []

    for i, article in enumerate(articles, 1):
        sources = article.get_all_sources()
        sources_str = " / ".join(sources)

        content = article.get_content(max_length=2000)

        part = f"""### 기사 {i}: {article.primary.title}
**출처:** {sources_str}
**URL:** {article.primary.url}
**보도 매체 수:** {article.source_count}

**내용:**
{content}
"""
        parts.append(part)

    return "\n---\n".join(parts)
