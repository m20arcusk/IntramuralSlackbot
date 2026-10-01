from datetime import time

from src.errors import ScheduleError, error_source_guide
from src.scraper import Game
from src.teams import Team


def format_schedule(sections: list[tuple[Team, list[Game]]]) -> str:
    if not sections:
        raise ScheduleError("No games to format.")

    blocks = ["*UBC Intramurals — Upcoming Games*"]
    for team, games in sections:
        blocks.append("")
        blocks.append(f"*{team.sport} — {team.name}*")
        if not games:
            blocks.append("No games this week.")
            continue
        current_date = None
        for game in games:
            if game.date != current_date:
                if current_date is not None:
                    blocks.append("")
                blocks.append(f"{_format_date(game.date)}:")
                current_date = game.date
            line = f"- {_format_time(game.time)} — {game.location} vs. {game.opponent}"
            if _show_result(game.result):
                line += f" — Result: {game.result}"
            if game.information:
                line += f" — {game.information}"
            blocks.append(line)

    blocks.append("")
    blocks.append(
        "Please react with 🏐 if you can attend volleyball, and ☄️ if you can attend dodgeball!"
    )
    return "\n".join(blocks)


def format_error(message: str) -> str:
    return (
        "UBC Intramurals Bot Error\n"
        "\n"
        "The schedule scraper failed.\n"
        "\n"
        "Error:\n"
        f"{message}\n"
        "\n"
        "The weekly schedule was NOT sent.\n"
        "\n"
        f"{error_source_guide()}"
    )


def _format_date(value) -> str:
    return f"{value.strftime('%A, %b')} {value.day}"


def _format_time(value: time) -> str:
    return value.strftime("%I:%M %p").lstrip("0")


def _show_result(result: str) -> bool:
    return result.casefold() not in {"", "-", "to be played"}
