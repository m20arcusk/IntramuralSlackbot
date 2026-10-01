from datetime import date
from pathlib import Path

import pytest

from src.errors import ScheduleError
from src.scraper import filter_upcoming, parse_schedule, window_end
from src.teams import TEAMS

FIXTURES = Path(__file__).parent / "fixtures"
DODGEBALL = TEAMS[0]


def test_parses_team_games_and_opponent_on_either_side():
    html = (FIXTURES / "dodgeball.html").read_text()
    games = parse_schedule(html, DODGEBALL)

    assert [game.opponent for game in games] == [
        "IGEN",
        "Beta Blockers",
        "The Acers",
        "Dodgeball OT2T1",
    ]
    assert games[0].date == date(2026, 9, 28)
    assert games[0].location == "Rec North Gym B"
    assert games[0].time.hour == 17 and games[0].time.minute == 30
    assert games[3].information == "Jersey check"


def test_upcoming_window_is_seven_days_including_today():
    start = date(2026, 9, 30)
    assert window_end(start) == date(2026, 10, 6)

    html = (FIXTURES / "dodgeball.html").read_text()
    games = parse_schedule(html, DODGEBALL)
    upcoming = filter_upcoming(games, start)

    assert [game.date for game in upcoming] == [date(2026, 10, 5), date(2026, 10, 5)]
    assert [game.opponent for game in upcoming] == ["The Acers", "Dodgeball OT2T1"]


def test_missing_schedule_table_means_no_games():
    html = (FIXTURES / "volleyball_no_schedule.html").read_text()
    assert parse_schedule(html, TEAMS[1]) == []


def test_unreadable_schedule_section_is_an_error():
    html = """
    <h1>Dodge These BizBalls (0 - 0 - 0)</h1>
    <h3>Team Schedule &amp; Game Records</h3>
    <table>
      <tr><th>Date</th><th>Opponent</th></tr>
      <tr><td>10/05/2026</td><td>Someone</td></tr>
    </table>
    """
    with pytest.raises(ScheduleError, match="could not be read"):
        parse_schedule(html, DODGEBALL)


def test_missing_location_rejects_the_row():
    html = (FIXTURES / "missing_location.html").read_text()
    with pytest.raises(ScheduleError, match="missing a location"):
        parse_schedule(html, DODGEBALL)


def test_wrong_team_name_is_rejected():
    html = (FIXTURES / "dodgeball.html").read_text()
    with pytest.raises(ScheduleError, match="not this team"):
        parse_schedule(html, TEAMS[1])
