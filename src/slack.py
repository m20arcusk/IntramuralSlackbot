import logging
import os

import requests

from src.errors import ScheduleError

logger = logging.getLogger("ubc_intramurals")

SLACK_API = "https://slack.com/api"


def slack_is_configured() -> bool:
    return bool(os.environ.get("SLACK_BOT_TOKEN") and os.environ.get("SLACK_USER_ID"))


def send_dm(text: str, timeout: float = 20) -> None:
    token = os.environ.get("SLACK_BOT_TOKEN", "").strip()
    user_id = os.environ.get("SLACK_USER_ID", "").strip()
    if not token or not user_id:
        raise ScheduleError(
            "Slack is not configured. Set SLACK_BOT_TOKEN and SLACK_USER_ID."
        )

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8",
    }
    opened = requests.post(
        f"{SLACK_API}/conversations.open",
        headers=headers,
        json={"users": user_id},
        timeout=timeout,
    )
    opened.raise_for_status()
    open_body = opened.json()
    if not open_body.get("ok"):
        raise ScheduleError(
            f"Slack could not open a DM ({open_body.get('error', 'unknown_error')})."
        )

    channel = open_body["channel"]["id"]
    posted = requests.post(
        f"{SLACK_API}/chat.postMessage",
        headers=headers,
        json={"channel": channel, "text": text},
        timeout=timeout,
    )
    posted.raise_for_status()
    post_body = posted.json()
    if not post_body.get("ok"):
        raise ScheduleError(
            f"Slack could not send the message ({post_body.get('error', 'unknown_error')})."
        )
    logger.info("Slack message sent successfully")
