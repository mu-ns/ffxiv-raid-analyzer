from rich.console import Console
from rich.table import Table

from raid_analyzer.stats import PullGroup

console = Console()


def render_pulls_table(groups: list[PullGroup]) -> None:
    t = Table(title="Pulls / Clears")
    t.add_column("Boss")
    t.add_column("Pulls")
    t.add_column("Cleared")
    for g in groups:
        cleared = "-" if g.is_trash else ("Yes" if g.cleared else "No")
        t.add_row(g.name, str(g.pulls), cleared)
    console.print(t)


def render_player_table(roster: list[str], deaths: dict[str, int], deaths_minus_wipes: dict[str, int]) -> None:
    t = Table(title="Player Stats")
    t.add_column("Player")
    t.add_column("Deaths")
    t.add_column("Incl. wipes")
    for player in roster:
        t.add_row(player, str(deaths_minus_wipes.get(player, 0)), str(deaths.get(player, 0)))
    console.print(t)
