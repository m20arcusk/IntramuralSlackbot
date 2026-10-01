import argparse
import logging
import os
import sys
from datetime import date, datetime
from pathlib import Path

from src.errors import ScheduleError
from src.formatter import format_error, format_schedule
from src.scraper import (
    fetch_schedule_html,
    filter_upcoming,
    parse_schedule,
    today_in_vancouver,
)
from src.slack import send_dm, slack_is_configured
from src.teams import TEAMS, Team
from src.validator import validate_games

logger = logging.getLogger("ubc_intramurals")


def build_message(today: date | None = None, html_by_team_id: dict[str, str] | None = None) -> str:
    start = today or today_in_vancouver()
    logger.info("Scraper started for %s", start.isoformat())
    sections: list[tuple[Team, list]] = []
    failures: list[str] = []

    for team in TEAMS:
        try:
            sections.append(_section_for_team(team, start, html_by_team_id))
        except ScheduleError as exc:
            logger.error("%s", exc.message)
            failures.append(exc.message)

    if failures:
        raise ScheduleError("\n".join(failures))

    message = format_schedule(sections)
    logger.info("Validation successful")
    return message


def _section_for_team(team: Team, start: date, html_by_team_id: dict[str, str] | None):
    if html_by_team_id is not None:
        html = html_by_team_id[team.team_id]
    else:
        html = fetch_schedule_html(team)
    games = parse_schedule(html, team)
    validate_games(games)
    upcoming = filter_upcoming(games, start)
    logger.info("Found %s upcoming games for %s", len(upcoming), team.name)
    return team, upcoming


def lambda_handler(event, context):
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        message = build_message()
        send_dm(message)
        logger.info("Successful completion")
        return {"statusCode": 200, "body": message}
    except ScheduleError as exc:
        logger.error("Weekly schedule was not sent: %s", exc.message)
        _notify_failure(exc.message)
        return {"statusCode": 500, "body": exc.message}
    except Exception:
        logger.exception("Unexpected exception")
        _notify_failure("Unexpected error while building the schedule.")
        return {"statusCode": 500, "body": "Unexpected error"}


def _notify_failure(message: str) -> None:
    if not slack_is_configured():
        logger.error("Slack is not configured, so the error DM was not sent.")
        return
    try:
        send_dm(format_error(message))
    except Exception:
        logger.exception("Slack API error while sending the error DM")


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    _load_dotenv()
    parser = argparse.ArgumentParser(description="Build the UBC intramurals Slack DM.")
    parser.add_argument(
        "--send",
        action="store_true",
        help="Send the DM. Requires SLACK_BOT_TOKEN and SLACK_USER_ID.",
    )
    parser.add_argument(
        "--today",
        help="Override the run date as YYYY-MM-DD. Defaults to today in Vancouver.",
    )
    args = parser.parse_args(argv)
    today = datetime.strptime(args.today, "%Y-%m-%d").date() if args.today else None

    try:
        message = build_message(today=today)
    except ScheduleError as exc:
        print(format_error(exc.message), file=sys.stderr)
        if args.send:
            _notify_failure(exc.message)
        return 1

    print(message)
    if args.send:
        try:
            send_dm(message)
        except ScheduleError as exc:
            logger.error("%s", exc.message)
            return 1
    return 0


def _load_dotenv() -> None:
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    try:
        lines = env_path.read_text().splitlines()
    except OSError:
        logger.exception("Could not read .env")
        return
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


if __name__ == "__main__":
    raise SystemExit(main())
