import boto3
import json
import os
import mimetypes
from botocore.exceptions import ClientError
from functools import lru_cache
from pathlib import Path
from src.news_letter.utils import DATA_DIR


@lru_cache(maxsize=1)
def _get_s3_client():
    client = boto3.client("s3", region_name="ap-northeast-2")
    if client is None:
        raise RuntimeError("Failed to initialize Boto3 S3 client")
    return client


def _is_prod():
    # .env 파일의 app_env 또는 ENV 변수를 모두 확인합니다.
    env = os.getenv("app_env")
    return str(env).lower() == "prod"


def _ensure_bucket_exists(bucket: str):
    s3 = _get_s3_client()
    try:
        s3.head_bucket(Bucket=bucket)
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code == "404":
            print(f"Bucket '{bucket}' not found. Creating it...")
            s3.create_bucket(
                Bucket=bucket,
                CreateBucketConfiguration={"LocationConstraint": "ap-northeast-2"},
            )
        else:
            raise


def put_object(data: any, key: Path, bucket: str = None, **kwargs):
    """
    Saves data to S3 if app_env=prod, otherwise saves locally.
    - If data is a dict or list, it's saved as JSON.
    - If data is a string, it's saved as-is (e.g., Markdown).
    """
    if bucket is None:
        bucket = os.getenv("AWS_S3_BUCKET")

    # 데이터 변환 (dict/list는 JSON으로, 그 외는 문자열로)
    if isinstance(data, (dict, list)):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        default_content_type = "application/json"
    else:
        body = str(data).encode("utf-8")
        default_content_type = "text/plain"

    # Content-Type 결정
    content_type, _ = mimetypes.guess_type(str(key))
    if not content_type:
        content_type = default_content_type

    if _is_prod():
        s3 = _get_s3_client()
        _ensure_bucket_exists(bucket)

        provider = kwargs.get("provider")
        model = kwargs.get("model")
        tagging = f"provider={provider}&model={model}" if provider and model else None

        # S3 키 생성 (DATA_DIR 기준 상대 경로)
        try:
            s3_key = key.relative_to(DATA_DIR).as_posix()
        except ValueError:
            s3_key = key.name

        s3.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=body,
            ContentType=content_type,
            **({"Tagging": tagging} if tagging else {}),
        )
    else:
        # 로컬 저장
        key.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, (dict, list)):
            key.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        else:
            key.write_text(str(data), encoding="utf-8")
