import re

import typer
from dotenv import load_dotenv

from raid_analyzer import auth, client, constants, display, stats

load_dotenv()
app = typer.Typer(add_completion=False)

_CODE_RE = re.compile(r"^[A-Za-z0-9]{10,20}$")
_URL_RE = re.compile(r"fflogs\.com/reports/([A-Za-z0-9]+)")


def extract_report_code(raw: str) -> str:
    raw = raw.strip()
    m = _URL_RE.search(raw)
    candidate = m.group(1) if m else raw
    if not _CODE_RE.match(candidate):
        raise typer.BadParameter(
            f"'{raw}' doesn't look like a valid FFLogs report code or URL."
        )
    return candidate


@app.command()
def login():
    auth.login()
    token = auth.get_valid_access_token()
    user = client.GraphQLClient(token).get_current_user()
    typer.echo(f"Logged in as {user['name']}.")


@app.command()
def analyze(report: str = typer.Argument(..., help="Report code or fflogs.com URL")):
    try:
        token = auth.get_valid_access_token()
    except auth.NotLoggedInError as e:
        typer.echo(str(e))
        raise typer.Exit(1)

    code = extract_report_code(report)
    gql = client.GraphQLClient(token)

    try:
        report = gql.get_fights_and_actors(code)
    except (client.ReportNotFoundError, client.NoFightsError, client.GraphQLError) as e:
        typer.echo(str(e))
        raise typer.Exit(1)

    groups = stats.group_pulls(report["fights"])
    display.render_pulls_table(groups)

    wipe_count = stats.count_wipes(report["fights"])
    roster = stats.build_roster(report["masterData"]["actors"], constants.EXCLUDED_ACTOR_NAMES)
    fight_ids = [f["id"] for f in report["fights"]]

    try:
        tables, _alias_map = gql.get_tables(code, fight_ids, constants.MITIGATION_ABILITIES, constants.DAMAGE_DOWN_ABILITIES)
    except client.ArchivedReportError as e:
        typer.echo(str(e))
        raise typer.Exit(1)
    except client.GraphQLError as e:
        typer.echo(str(e))
        raise typer.Exit(1)

    deaths = stats.count_deaths(tables["deaths"])
    deaths_minus_wipes = stats.deaths_minus_wipes(deaths, wipe_count)
    display.render_player_table(roster, deaths, deaths_minus_wipes)
