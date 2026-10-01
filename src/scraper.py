import logging
import re
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

from src.errors import ScheduleError
from src.teams import PORTAL_URL, WINDOW_DAYS, Team

logger = logging.getLogger("ubc_intramurals")

PACIFIC = ZoneInfo("America/Vancouver")
SCHEDULE_HEADERS = ("date", "time", "location", "match-up")
USER_AGENT = "ubc-intramural-bot/0.1"


class Game:
    def __init__(
        self,
        game_date: date,
        game_time: time,
        location: str,
        opponent: str,
        result: str,
        information: str,
        sport: str,
        team: str,
    ):
        self.date = game_date
        self.time = game_time
        self.location = location
        self.opponent = opponent
        self.result = result
        self.information = information
        self.sport = sport
        self.team = team


def team_schedule_url(team: Team) -> str:
    return f"{PORTAL_URL}?r=intramurals/leagues&ID={team.team_id}"


def today_in_vancouver(now: datetime | None = None) -> date:
    current = now or datetime.now(PACIFIC)
    if current.tzinfo is None:
        current = current.replace(tzinfo=PACIFIC)
    return current.astimezone(PACIFIC).date()


def window_end(start: date) -> date:
    return start + timedelta(days=WINDOW_DAYS - 1)


def fetch_schedule_html(team: Team, timeout: float = 20) -> str:
    url = team_schedule_url(team)
    logger.info("URL requested: %s", url)
    try:
        response = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": USER_AGENT},
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ScheduleError(
            f"{team.sport} ({team.name}): failed to fetch the schedule ({exc.__class__.__name__})."
        ) from exc
    return response.text


def parse_schedule(html: str, team: Team) -> list[Game]:
    soup = BeautifulSoup(html, "html.parser")
    page_name = _page_team_name(soup, team)
    if page_name.casefold() != team.name.casefold():
        raise ScheduleError(
            f"{team.sport} ({team.name}): page is for {page_name!r}, not this team."
        )

    tables = _schedule_tables(soup)
    if not tables:
        if _has_team_schedule_heading(soup):
            raise ScheduleError(
                f"{team.sport} ({team.name}): team schedule section could not be read."
            )
        logger.info("No schedule posted for %s", team.name)
        return []

    games = []
    for table in tables:
        games.extend(_games_from_table(table, team))

    logger.info("Extracted %s games for %s", len(games), team.name)
    return games


def filter_upcoming(games: list[Game], start: date) -> list[Game]:
    end = window_end(start)
    upcoming = [game for game in games if start <= game.date <= end]
    upcoming.sort(key=lambda game: (game.date, game.time))
    return upcoming


def _page_team_name(soup: BeautifulSoup, team: Team) -> str:
    heading = soup.find("h1")
    if heading is None:
        raise ScheduleError(
            f"{team.sport} ({team.name}): team name heading could not be found."
        )
    text = _clean(heading.get_text(" ", strip=True))
    text = re.sub(r"\s*\([^)]*\)\s*$", "", text).strip()
    if not text:
        raise ScheduleError(
            f"{team.sport} ({team.name}): team name heading was empty."
        )
    return text


def _schedule_tables(soup: BeautifulSoup) -> list:
    tables = []
    for table in soup.find_all("table"):
        headers = {
            _clean(cell.get_text(" ", strip=True)).casefold()
            for cell in table.find_all("th")
        }
        if set(SCHEDULE_HEADERS).issubset(headers):
            tables.append(table)
    return tables


def _has_team_schedule_heading(soup: BeautifulSoup) -> bool:
    for tag in soup.find_all(["h2", "h3", "h4"]):
        text = _clean(tag.get_text(" ", strip=True)).casefold()
        if "team schedule" in text:
            return True
    return False


def _games_from_table(table, team: Team) -> list[Game]:
    headers = [_clean(cell.get_text(" ", strip=True)) for cell in table.find_all("th")]
    indexes = {header.casefold(): index for index, header in enumerate(headers)}
    missing = [name for name in SCHEDULE_HEADERS if name not in indexes]
    if missing:
        raise ScheduleError(
            f"{team.sport} ({team.name}): schedule table is missing columns: {', '.join(missing)}."
        )

    games = []
    for row_number, row in enumerate(table.find_all("tr"), start=1):
        if not row.find("td"):
            continue
        cells = row.find_all("td")
        games.append(_parse_row(cells, indexes, team, row_number))
    return games


def _parse_row(cells, indexes: dict[str, int], team: Team, row_number: int) -> Game:
    def cell(name: str) -> str:
        index = indexes[name]
        if index >= len(cells):
            raise ScheduleError(
                f"{team.sport} ({team.name}): game row {row_number} is missing {name}."
            )
        return _clean(cells[index].get_text(" ", strip=True))

    raw_date = cell("date")
    raw_time = cell("time")
    location = cell("location")
    matchup = cell("match-up")
    result = cell("result") if "result" in indexes else ""
    information = cell("information") if "information" in indexes else ""

    if not raw_date:
        raise ScheduleError(
            f"{team.sport} ({team.name}): game row {row_number} is missing a date."
        )
    if not raw_time:
        raise ScheduleError(
            f"{team.sport} ({team.name}): game row {row_number} is missing a time."
        )
    if not location:
        raise ScheduleError(
            f"{team.sport} ({team.name}): game row {row_number} is missing a location."
        )

    try:
        game_date = datetime.strptime(raw_date, "%m/%d/%Y").date()
    except ValueError as exc:
        raise ScheduleError(
            f"{team.sport} ({team.name}): game row {row_number} has an invalid date ({raw_date!r})."
        ) from exc

    try:
        game_time = _parse_time(raw_time)
    except ValueError as exc:
        raise ScheduleError(
            f"{team.sport} ({team.name}): game row {row_number} has an invalid time ({raw_time!r})."
        ) from exc

    try:
        opponent = _opponent(matchup, team.name)
    except ValueError as exc:
        raise ScheduleError(
            f"{team.sport} ({team.name}): game row {row_number} has an unreadable match-up ({matchup!r})."
        ) from exc

    return Game(
        game_date=game_date,
        game_time=game_time,
        location=location,
        opponent=opponent,
        result=result,
        information=information,
        sport=team.sport,
        team=team.name,
    )


def _parse_time(value: str) -> time:
    raw = value.strip().upper().replace(" ", "")
    for fmt in ("%I:%M%p", "%H:%M"):
        try:
            return datetime.strptime(raw, fmt).time()
        except ValueError:
            continue
    raise ValueError(value)


def _opponent(matchup: str, team_name: str) -> str:
    parts = re.split(r"\s+vs\.?\s+", matchup, maxsplit=1, flags=re.IGNORECASE)
    if len(parts) != 2:
        raise ValueError(matchup)
    left, right = _clean(parts[0]), _clean(parts[1])
    if left.casefold() == team_name.casefold():
        opponent = right
    elif right.casefold() == team_name.casefold():
        opponent = left
    else:
        raise ValueError(matchup)
    if not opponent:
        raise ValueError(matchup)
    return opponent


def _clean(value: str) -> str:
    return " ".join(value.split())
