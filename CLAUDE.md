# CLAUDE.md — 데일리 테크·투자 뉴스레터 프로젝트

## 프로젝트 개요
TechCrunch, Bloomberg, The Verge, CNBC 4개 글로벌 매체에서 핵심 기사를 수집

**Backend:**
- Python 3.11+,
- feedparser (RSS 피드 파싱)
- trafilatura (기사 본문 추출)
- beautifulsoup4 (HTML 정리)
- requests (HTTP 요청) 
- pyyaml (설정 파일)
- google-genai (Gemini API SDK (최신))

## 프로젝트 구조

```
daily_tech_newsletter/
├── CLAUDE.md                    # 
├── 계획서.md                      # 뉴스레터 기획서 (콘텐츠 방향, 톤, 포맷 정의)
├── pyproject.toml               # 의존성 관리
├── .env.example                 # API 키 템플릿
├── .env                         # 실제 API 키 (gitignored)
├── .gitignore
├── config/
│   ├── __init__.py
│   ├── settings.py              # 메일 발송 시간
│   └── rss_feeds.yaml           # RSS 피드 목록
├── src/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── article.py           # Article, DeduplicatedArticle 데이터클래스
│   ├── collector/
│   │   ├── __init__.py
│   │   ├── rss_fetcher.py       # feedparser 기반 RSS 수집
│   │   ├── article_extractor.py # trafilatura 기반 본문 추출
│   │   └── bloomberg_fetcher.py # Bloomberg 폴백 전략
│   ├── deduplicator/
│   │   ├── __init__.py
│   │   └── similarity.py        # difflib 기반 중복 제거
│   └── generator/
│       ├── __init__.py
│       ├── gemini_client.py     # Gemini API 래퍼
│       └── prompts.py           # 뉴스레터 생성 프롬프트
├── pipeline.py                  # 메인 실행 스크립트
├── articles/                    # 수집된 원본 기사 JSON (gitignored)
└── output/                      # 생성된 뉴스레터 (gitignored)

```

## 데이터 흐름

```
RSS Feeds (4개 매체)
  → [rss_fetcher] feedparser로 기사 목록 수집
  → [article_extractor] trafilatura로 기사 본문 추출
  → [similarity] 제목 유사도로 중복 병합 + 중요도 정렬
  → output/{날짜}/newsletter.md 출력
```

## 실행 방법

```

결과물: `output/{날짜}/newsletter.md` — 완성된 한국어 뉴스레터

## 코딩 컨벤션

- 언어: Python 3.11+, 타입 힌트 사용 (list[str], str | None 등 내장 문법)
- 데이터 모델: dataclasses 사용
- 설정: YAML 파일로 외부화 (config/feeds.yaml)
- 로깅: logging 모듈 사용, print 사용 금지
- 에러 처리: 개별 피드/기사 실패 시 로그 남기고 건너뛰기, 전체 파이프라인은 중단하지 않음
- 인코딩: 모든 파일 I/O에 encoding="utf-8" 명시

```

## 주요 설계 결정

- Bloomberg는 공개 RSS가 불안정하므로 2단계 폴백 (직접 RSS → Google News RSS)
- 중복 제거는 difflib.SequenceMatcher 제목 유사도 (임계값 0.65)
- 기사 본문 추출 실패 시 RSS summary로 폴백
- 본문은 2000자로 truncate하여 토큰 절약
- 중요도 점수 = 보도 매체 수 기반 (여러 매체가 다룬 기사일수록 상위)

## 뉴스레터 톤 가이드라인 (계획서 기반)

프롬프트 작성 시 반드시 반영할 규칙:
- 단순 번역 절대 금지 — 맥락과 배경을 포함한 한국어 재구성
- 경어체 사용 (~합니다, ~입니다)
- 전문 용어에는 괄호 설명 추가 — 예: "Fed(미국 중앙은행)"
- What + Why + Forward 구조 — 사실, 왜 중요한지, 앞으로의 전망
- Quartz Daily Brief 스타일 서술체 — 질문형 소제목 사용 금지
- 투자 조언이 아닌 정보 제공 — 매수/매도 추천 금지

## RSS 피드 URL

- TechCrunch: `https://techcrunch.com/feed/`
- The Verge: `https://www.theverge.com/rss/index.xml`
- CNBC Technology: `https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19854910`
- Bloomberg: 직접 RSS 시도 후 Google News RSS (`site:bloomberg.com`) 폴백

## 향후 확장 계획
- Phase 2: Notion API 연동 (자동 업로드)
- Phase 2: cron 스케줄러 매일 자동 실행
- Phase 3: 이메일 발송 (Stibee) 연동
- Phase 3: 주간 딥다이브 기업 분석 자동화
