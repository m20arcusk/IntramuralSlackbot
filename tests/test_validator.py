from datetime import date, time

import pytest

from src.errors import ScheduleError
from src.scraper import Game
from src.validator import validate_games


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


def test_valid_games_pass():
    validate_games([_game(), _game(opponent="Dodgeball OT2T1")])


def test_missing_opponent_rejects_every_game():
    with pytest.raises(ScheduleError, match="missing an opponent"):
        validate_games([_game(), _game(opponent="  ")])
