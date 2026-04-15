import logging
import os

import boto3
import bleach
import markdown
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

DEFAULT_REGION = "ap-northeast-2"
ALLOWED_HTML_TAGS = [
    "a",
    "blockquote",
    "br",
    "code",
    "em",
    "hr",
    "li",
    "ol",
    "p",
    "pre",
    "strong",
    "ul",
    "h1",
    "h2",
    "h3",
]
ALLOWED_HTML_ATTRIBUTES = {
    "a": ["href", "title"],
}


def _is_enabled() -> bool:
    return os.getenv("NEWS_PIPELINE_EMAIL_ENABLED", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _parse_recipients(raw_value: str | None) -> list[str]:
    if not raw_value:
        return []
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def _build_subject(provider: str, model: str, date_str: str) -> str:
    prefix = os.getenv("NEWS_PIPELINE_EMAIL_SUBJECT_PREFIX", "[News Pipeline]")
    return f"{prefix} {date_str} newsletter ({provider}/{model})"


def _build_body(
    newsletter: str,
    *,
    provider: str,
    model: str,
    date_str: str,
) -> str:
    lines = [
        f"Date: {date_str}",
        f"Provider: {provider}",
        f"Model: {model}",
        "",
        newsletter,
    ]
    return "\n".join(lines)


def _build_html_body(
    newsletter: str, *, provider: str, model: str, date_str: str
) -> str:
    newsletter_html = markdown.markdown(newsletter, extensions=["extra", "sane_lists"])
    safe_newsletter_html = bleach.clean(
        newsletter_html,
        tags=ALLOWED_HTML_TAGS,
        attributes=ALLOWED_HTML_ATTRIBUTES,
        protocols=["http", "https", "mailto"],
        strip=True,
    )
    return "\n".join(
        [
            "<html>",
            "  <body>",
            f"    <p><strong>Date:</strong> {date_str}<br><strong>Provider:</strong> {provider}<br><strong>Model:</strong> {model}</p>",
            "    <hr>",
            f"    {safe_newsletter_html}",
            "  </body>",
            "</html>",
        ]
    )


def send_newsletter_email(
    newsletter: str,
    *,
    provider: str,
    model: str,
    date_str: str,
) -> bool:
    """Send the generated newsletter through Amazon SES when enabled."""
    if not _is_enabled():
        logger.info("Newsletter email delivery disabled; skipping SES send.")
        return False

    sender = os.getenv("NEWS_PIPELINE_EMAIL_FROM", "").strip()
    recipients = _parse_recipients(os.getenv("NEWS_PIPELINE_EMAIL_TO"))

    if not sender or not recipients:
        logger.warning(
            "Newsletter email delivery requested but sender/recipients are missing."
        )
        return False

    ses = boto3.client("sesv2", region_name=os.getenv("AWS_REGION", DEFAULT_REGION))
    subject = _build_subject(provider, model, date_str)
    body = _build_body(
        newsletter,
        provider=provider,
        model=model,
        date_str=date_str,
    )
    html_body = _build_html_body(
        newsletter,
        provider=provider,
        model=model,
        date_str=date_str,
    )

    try:
        ses.send_email(
            FromEmailAddress=sender,
            Destination={"ToAddresses": recipients},
            Content={
                "Simple": {
                    "Subject": {"Data": subject, "Charset": "UTF-8"},
                    "Body": {
                        "Text": {"Data": body, "Charset": "UTF-8"},
                        "Html": {"Data": html_body, "Charset": "UTF-8"},
                    },
                }
            },
        )
    except ClientError as exc:
        logger.exception("Failed to send newsletter email: %s", exc)
        return False

    logger.info("Newsletter email sent to %d recipient(s)", len(recipients))
    return True
