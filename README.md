# UBC Intramurals Slackbot

Weekly schedule DM for two UBC Recreation intramural teams:

- Dodgeball — Dodge These BizBalls (`ID=55946`)
- Volleyball — bumpin bizballs (`ID=56253`)

The [standings pages](https://recreation.ubc.ca/intramurals/leagues/dodgeball/term-1-standings/) do not contain the games. They load a team page from `portal.recreation.ubc.ca` using the `ID` query parameter. This bot reads that portal page directly.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python -m src.lambda_function
```

That prints the message. It does not contact Slack.

`--today YYYY-MM-DD` overrides the run date. The window is that date through the next 6 days (Wednesday through the following Tuesday when it runs on a Wednesday), in America/Vancouver.

A team with no games this week is included as "No games this week." The command exits with an error, and does not print a schedule, only when a page cannot be fetched or read, or a listed game fails validation. Those cases are listed in [ERRORS.md](ERRORS.md), and the same list is included in the error DM.

## Tests

```bash
pytest
```

## Slack, when you are ready

1. Create a Slack app in the club workspace and add a bot user.
2. Bot token scopes: `chat:write` and `im:write`.
3. Install the app to the workspace.
4. Copy `.env.example` to `.env` and set `SLACK_BOT_TOKEN` and `SLACK_USER_ID` (your member ID, starts with `U`).
5. Send a DM with:

```bash
python -m src.lambda_function --send
```

Do not commit `.env`. The token is read from the environment only.

## Wednesday at 9:00am Vancouver

`.github/workflows/wednesday-schedule.yml` runs the same `--send` command. GitHub's scheduler is UTC, so the workflow starts at both 16:00 and 17:00 UTC on Wednesday and sends only when the clock in America/Vancouver says Wednesday 9am. That covers daylight time and standard time. **Run workflow** on the Actions tab sends immediately, any day.

Scheduled runs only happen from the default branch of a GitHub repo. Add `SLACK_BOT_TOKEN` and `SLACK_USER_ID` as repository secrets. Do not put them in the workflow file.
