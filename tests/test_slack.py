from unittest.mock import Mock, patch

import pytest

from src.errors import ScheduleError
from src.slack import send_dm


def test_send_dm_posts_to_the_opened_channel(monkeypatch):
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")
    monkeypatch.setenv("SLACK_USER_ID", "U123")
    opened = Mock()
    opened.raise_for_status.return_value = None
    opened.json.return_value = {"ok": True, "channel": {"id": "D999"}}
    posted = Mock()
    posted.raise_for_status.return_value = None
    posted.json.return_value = {"ok": True}

    with patch("src.slack.requests.post", side_effect=[opened, posted]) as post:
        send_dm("hello")

    assert post.call_args_list[0].args[0].endswith("/conversations.open")
    assert post.call_args_list[1].kwargs["json"]["channel"] == "D999"
    assert post.call_args_list[1].kwargs["json"]["text"] == "hello"


def test_slack_api_error_is_reported(monkeypatch):
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")
    monkeypatch.setenv("SLACK_USER_ID", "U123")
    opened = Mock()
    opened.raise_for_status.return_value = None
    opened.json.return_value = {"ok": False, "error": "not_authed"}

    with patch("src.slack.requests.post", return_value=opened):
        with pytest.raises(ScheduleError, match="not_authed"):
            send_dm("hello")
