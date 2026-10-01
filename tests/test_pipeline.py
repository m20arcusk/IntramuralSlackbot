from datetime import date
from pathlib import Path

import pytest

from src.errors import ScheduleError
from src.lambda_function import build_message

FIXTURES = Path(__file__).parent / "fixtures"


def test_team_with_no_games_is_included_and_the_other_schedule_is_sent():
    html_by_team_id = {
        "55946": (FIXTURES / "dodgeball.html").read_text(),
        "56253": (FIXTURES / "volleyball_no_schedule.html").read_text(),
    }
    message = build_message(today=date(2026, 9, 30), html_by_team_id=html_by_team_id)
    assert "vs. The Acers" in message
    assert "vs. Dodgeball OT2T1" in message
    assert "vs. IGEN" not in message
    assert "Volleyball — bumpin bizballs" in message
    assert "No games this week." in message


def test_a_bad_game_row_still_blocks_the_whole_message():
    html_by_team_id = {
        "55946": (FIXTURES / "missing_location.html").read_text(),
        "56253": (FIXTURES / "volleyball_no_schedule.html").read_text(),
    }
    with pytest.raises(ScheduleError, match="missing a location") as caught:
        build_message(today=date(2026, 9, 30), html_by_team_id=html_by_team_id)
    assert "vs." not in caught.value.message


def test_both_teams_format_when_both_schedules_are_valid():
    volleyball = """
    <h1>bumpin bizballs (0 - 0 - 0)</h1>
    <table>
      <tr><th>Date</th><th>Time</th><th>Location</th><th>Match-up</th></tr>
      <tr>
        <td>10/06/2026</td>
        <td>7:15PM</td>
        <td>War Memorial Gym</td>
        <td><b>bumpin bizballs</b> <i>vs.</i> <b>Sets on the Beach</b></td>
      </tr>
    </table>
    """
    html_by_team_id = {
        "55946": (FIXTURES / "dodgeball.html").read_text(),
        "56253": volleyball,
    }
    message = build_message(today=date(2026, 9, 30), html_by_team_id=html_by_team_id)
    assert "Dodgeball — Dodge These BizBalls" in message
    assert "vs. The Acers" in message
    assert "vs. IGEN" not in message
    assert "Volleyball — bumpin bizballs" in message
    assert "Tuesday, Oct 6" in message
    assert "vs. Sets on the Beach" in message
