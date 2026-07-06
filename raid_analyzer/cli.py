import re
from datetime import datetime

import questionary
import typer
from dotenv import load_dotenv

from raid_analyzer import auth, client, constants, display, stats

load_dotenv()
app = typer.Typer(add_completion=False)

_CODE_RE = re.compile(r"^[A-Za-z0-9]{10,20}$")
_URL_RE = re.compile(r"fflogs\.com/reports/([A-Za-z0-9]+)")

_SELECT_STYLE = questionary.Style([
    ("pointer", "fg:cyan bold"),
    ("highlighted", "fg:cyan bold"),
])


def extract_report_code(raw: str) -> str:
    raw = raw.strip()
    m = _URL_RE.search(raw)
    candidate = m.group(1) if m else raw
    if not _CODE_RE.match(candidate):
        raise typer.BadParameter(
            f"'{raw}' doesn't look like a valid FFLogs report code or URL."
        )
    return candidate


def prompt_boss_selection(groups: list[stats.PullGroup]) -> stats.PullGroup | None:
    """Returns the selected boss's PullGroup, or None for "All fights"."""
    choices = [questionary.Choice(title="All fights", value=None)]
    choices += [questionary.Choice(title=g.name, value=g) for g in groups]
    return questionary.select("Show stats for:", choices=choices, style=_SELECT_STYLE).ask()


@app.command()
def login():
    auth.login()
    token = auth.get_valid_access_token()
    user = client.GraphQLClient(token).get_current_user()
    typer.echo(f"Logged in as {user['name']}.")


@app.command(name="find-ability")
def find_ability(
    report_arg: str = typer.Argument(..., help="Report code or fflogs.com URL"),
    search: str = typer.Argument(..., help="Ability name substring to search for"),
):
    """Look up ability IDs to fill into constants.py, by name, from a real report."""
    try:
        token = auth.get_valid_access_token()
    except auth.NotLoggedInError as e:
        typer.echo(str(e))
        raise typer.Exit(1)

    code = extract_report_code(report_arg)
    gql = client.GraphQLClient(token)

    try:
        abilities = gql.get_abilities(code)
    except (client.ReportNotFoundError, client.GraphQLError) as e:
        typer.echo(str(e))
        raise typer.Exit(1)

    matches = [a for a in abilities if search.lower() in (a["name"] or "").lower()]
    if not matches:
        typer.echo(f"No abilities matching '{search}' found in report '{code}'.")
        raise typer.Exit(1)

    for a in matches:
        typer.echo(f"{a['gameID']}\t{a['name']}")


@app.command()
def analyze(report_arg: str = typer.Argument(..., help="Report code or fflogs.com URL")):
    try:
        token = auth.get_valid_access_token()
    except auth.NotLoggedInError as e:
        typer.echo(str(e))
        raise typer.Exit(1)

    code = extract_report_code(report_arg)
    gql = client.GraphQLClient(token)

    try:
        report = gql.get_fights_and_actors(code)
    except (client.ReportNotFoundError, client.NoFightsError, client.GraphQLError) as e:
        typer.echo(str(e))
        raise typer.Exit(1)

    groups = stats.group_pulls(report["fights"])
    display.render_pulls_table(groups)

    selected = prompt_boss_selection(groups)
    if not isinstance(selected, stats.PullGroup):
        selected = None
        scope_label = "All fights"
        fight_ids = [fid for g in groups for fid in g.fight_ids]
        scoped_fights = [f for f in report["fights"] if f["id"] in set(fight_ids)]
        total_pulls = stats.total_real_pulls(groups)
    else:
        scope_label = selected.name
        selected_ids = set(selected.fight_ids)
        scoped_fights = [f for f in report["fights"] if f["id"] in selected_ids]
        fight_ids = selected.fight_ids
        total_pulls = selected.pulls

    wipe_count = stats.count_wipes(scoped_fights)
    active_ids = stats.active_actor_ids(scoped_fights)
    roster = stats.build_roster(report["masterData"]["actors"], constants.EXCLUDED_ACTOR_NAMES, active_ids)

    try:
        tables, alias_map = gql.get_tables(code, fight_ids, constants.MITIGATION_ABILITIES, constants.DAMAGE_DOWN_ABILITIES)
    except client.ArchivedReportError as e:
        typer.echo(str(e))
        raise typer.Exit(1)
    except client.GraphQLError as e:
        typer.echo(str(e))
        raise typer.Exit(1)

    deaths = stats.count_deaths(tables["deaths"])
    deaths_minus_wipes = stats.deaths_minus_wipes(deaths, wipe_count)
    deaths_minus_wipes_rate = stats.per_pull_rate(deaths_minus_wipes, total_pulls)

    mitigations: dict[str, dict[str, int]] = {}
    damage_downs: dict[str, dict[str, int]] = {}
    for alias, (kind, label) in alias_map.items():
        if kind == "mitigation":
            mitigations[label] = stats.count_casts(tables[alias])
        elif kind == "damage_down":
            damage_downs[label] = stats.count_debuff_applications(tables[alias])

    mitigation_rates = {label: stats.per_pull_rate(counts, total_pulls) for label, counts in mitigations.items()}
    damage_down_rates = {label: stats.per_pull_rate(counts, total_pulls) for label, counts in damage_downs.items()}

    display.render_deaths_table(scope_label, roster, deaths, deaths_minus_wipes, deaths_minus_wipes_rate, damage_downs, damage_down_rates)
    display.render_mitigation_table(scope_label, mitigations, mitigation_rates)

    report_date = datetime.fromtimestamp(report["startTime"] / 1000).strftime("%Y-%m-%d")
    report_url = f"https://www.fflogs.com/reports/{code}"
    display.copy_tsv(
        report_date, report_url, selected, wipe_count, groups,
        roster, deaths, deaths_minus_wipes, deaths_minus_wipes_rate,
        damage_downs, damage_down_rates, mitigations, mitigation_rates,
    )
