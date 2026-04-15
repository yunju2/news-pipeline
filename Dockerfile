FROM python:3.11-slim

WORKDIR /app

ENV TZ=Asia/Seoul
ENV app_env=prod
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

COPY requirements.txt pyproject.toml ./
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt || pip install --no-cache-dir .

COPY src/ /app/src/
COPY config/ /app/config/
COPY \
    default_config.py \
    pipeline.py \
    main.py \
    CLAUDE.md \
    /app/

ENTRYPOINT ["python", "main.py"]
