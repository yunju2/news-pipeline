# 1. Base Image: Python 3.11의 가벼운 버전 사용
FROM python:3.11-slim

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. 환경 변수 설정
# 한국 시간 기준 설정 (로그 및 시각 관련)
ENV TZ=Asia/Seoul
# 배포 환경임을 명시
ENV app_env=prod
# 파이썬 출력 버퍼링 방지 (컨테이너 로그가 즉각 보이도록)
ENV PYTHONUNBUFFERED=1
# Python 경로를 현재 디렉토리로 설정
ENV PYTHONPATH=/app

# 4. 의존성 설치를 위한 파일 복사 및 설치
# (의존성 파일만 먼저 복사해야 Docker Layer Caching으로 인해 빌드가 빨라집니다)
COPY requirements.txt pyproject.toml ./
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt || pip install --no-cache-dir .

# 5. 소스코드 복사
COPY src/ /app/src/
COPY config/ /app/config/
COPY \
    default_config.py \
    pipeline.py \
    main.py \
    CLAUDE.md \
    README.md \
    /app/

# 6. 기본 실행 명령어
# AWS 컨테이너 환경에서 추가 입력 없이 바로 실행합니다.
ENTRYPOINT ["python", "main.py"]
