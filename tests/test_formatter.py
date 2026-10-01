from datetime import date, time
from pathlib import Path

from src.errors import ERROR_SOURCES, NOT_AN_ERROR
from src.formatter import format_error, format_schedule
from src.scraper import Game
from src.teams import TEAMS


def _game(**overrides) -> Game:
    values = {
        "game_date": date(2026, 10, 5),
        "game_time": time(21, 0),
        "location": "Rec North Gym A",
        "opponent": "The Acers",
        "result": "To Be Played",
        "information": "",
        "sport": "Dodgeball",
        "team": "Dodge These BizBalls",
    }
    values.update(overrides)
    return Game(**values)


def test_formats_same_day_games_without_a_result_line():
    message = format_schedule(
        [
            (
                TEAMS[0],
                [
                    _game(),
                    _game(
                        game_time=time(22, 0),
                        opponent="Dodgeball OT2T1",
                        information="Jersey check",
                    ),
                ],
            )
        ]
    )
    assert message == (
        "*UBC Intramurals — Upcoming Games*\n"
        "\n"
        "*Dodgeball — Dodge These BizBalls*\n"
        "Monday, Oct 5:\n"
        "- 9:00 PM — Rec North Gym A vs. The Acers\n"
        "- 10:00 PM — Rec North Gym A vs. Dodgeball OT2T1 — Jersey check\n"
        "\n"
        "Please react with 🏐 if you can attend volleyball, and ☄️ if you can attend dodgeball!"
    )


def test_empty_week_is_called_out_for_that_team():
    message = format_schedule([(TEAMS[1], [])])
    assert message == (
        "*UBC Intramurals — Upcoming Games*\n"
        "\n"
        "*Volleyball — bumpin bizballs*\n"
        "No games this week.\n"
        "\n"
        "Please react with 🏐 if you can attend volleyball, and ☄️ if you can attend dodgeball!"
    )


def test_error_text_names_the_failure_and_lists_every_source():
    message = format_error(
        "Dodgeball (Dodge These BizBalls): game row 1 is missing a location."
    )
    assert "was NOT sent" in message
    assert "vs." not in message
    assert "missing a location" in message
    assert "What can cause an error:" in message
    for source in ERROR_SOURCES:
        assert source in message
    assert NOT_AN_ERROR in message


def test_error_doc_matches_the_slack_list():
    document = Path(__file__).resolve().parent.parent.joinpath("ERRORS.md").read_text()
    for source in ERROR_SOURCES:
        assert source in document
    assert NOT_AN_ERROR in document
