from datetime import date, time

from src.errors import ScheduleError
from src.scraper import Game


def validate_games(games: list[Game]) -> None:
    """Reject the whole list if any game is incomplete or unreadable."""
    problems = []
    for index, game in enumerate(games, start=1):
        problems.extend(_problems(game, index))
    if problems:
        joined = " ".join(problems)
        raise ScheduleError(joined)


def _problems(game: Game, index: int) -> list[str]:
    label = f"{game.sport} ({game.team}) game {index}"
    problems = []
    if not isinstance(game.date, date):
        problems.append(f"{label} is missing a valid date.")
    if not isinstance(game.time, time):
        problems.append(f"{label} is missing a valid time.")
    if not game.location.strip():
        problems.append(f"{label} is missing a location.")
    if not game.opponent.strip():
        problems.append(f"{label} is missing an opponent.")
    return problems
