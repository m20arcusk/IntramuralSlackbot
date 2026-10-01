# Error sources

An error means the weekly schedule was not sent. The Slack DM names the specific failure, then lists every source below. One bad team blocks both teams.

A team with no games this week is not an error. That team is included in the normal DM as "No games this week." The same note is used when a schedule exists but every game falls outside Wednesday through the following Tuesday.

## What can cause an error

- The portal page could not be fetched (timeout, connection error, or HTTP error).
- The page has no team-name heading, or that heading is empty.
- The page is for a different team than Dodge These BizBalls or bumpin bizballs.
- A Team Schedule section is present, but its table cannot be read. Expected columns are Date, Time, Location, and Match-up.
- A game row is missing a date, time, location, or opponent.
- A date, time, or match-up on a game row cannot be parsed.
- Slack is not configured, or Slack rejects the DM.
- Something else failed while building the schedule.

## What each one means

### The portal page could not be fetched

The bot requests `https://portal.recreation.ubc.ca/intramurals/index.php` for team IDs `55946` (dodgeball) and `56253` (volleyball). A timeout, a connection failure, or an HTTP error means that team's page never arrived.

### The page has no team-name heading, or that heading is empty

Each team page starts with an `h1`, for example `Dodge These BizBalls (0 - 0 - 0)`. If that heading is missing or blank, the HTML is not a team page.

### The page is for a different team

The heading must match the configured team, ignoring capitalization. A mismatch means the ID is pointing at someone else's page.

### The Team Schedule section cannot be read

If the page has a "Team Schedule" heading but no table with columns Date, Time, Location, and Match-up, the site layout changed and the games cannot be trusted. A page with no schedule section at all is a bye, not this error.

### A game row is missing a required field

Every listed game needs a date, a time, a location, and an opponent taken from the match-up. A blank cell fails the whole run.

### A date, time, or match-up cannot be parsed

Dates must look like `09/28/2026`. Times must look like `9:00PM` or `19:00`. The match-up must look like `Team vs. Opponent`, and one side must be this team. An unreadable value fails the whole run.

### Slack rejects the DM

`SLACK_BOT_TOKEN` or `SLACK_USER_ID` is missing, or Slack refuses to open the DM or post the message. If Slack itself is unreachable, this DM may not arrive. The failure is still in the logs.

### Something else failed

Any other exception while building the schedule, including a Slack HTTP error that is not one of the cases above.
