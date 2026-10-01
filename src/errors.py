class ScheduleError(Exception):
    """A failure that must block the weekly schedule message."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


# Kept in sync with ERRORS.md. The error DM prints these lines.
ERROR_SOURCES = (
    "The portal page could not be fetched (timeout, connection error, or HTTP error).",
    "The page has no team-name heading, or that heading is empty.",
    "The page is for a different team than Dodge These BizBalls or bumpin bizballs.",
    "A Team Schedule section is present, but its table cannot be read. Expected columns are Date, Time, Location, and Match-up.",
    "A game row is missing a date, time, location, or opponent.",
    "A date, time, or match-up on a game row cannot be parsed.",
    "Slack is not configured, or Slack rejects the DM.",
    "Something else failed while building the schedule.",
)

NOT_AN_ERROR = "A team with no games this week is not an error."


def error_source_guide() -> str:
    lines = ["What can cause an error:"]
    lines.extend(f"- {source}" for source in ERROR_SOURCES)
    lines.append("")
    lines.append(NOT_AN_ERROR)
    return "\n".join(lines)
