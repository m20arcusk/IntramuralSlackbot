from dataclasses import dataclass


@dataclass(frozen=True)
class Team:
    sport: str
    name: str
    team_id: str


# The recreation.ubc.ca standings URLs only embed these portal pages.
# The ID is the team, not the league.
TEAMS = (
    Team(sport="Dodgeball", name="Dodge These BizBalls", team_id="55946"),
    Team(sport="Volleyball", name="bumpin bizballs", team_id="56253"),
)

PORTAL_URL = "https://portal.recreation.ubc.ca/intramurals/index.php"
WINDOW_DAYS = 7
