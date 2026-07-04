from rich.console import Console
from rich.table import Table

from raid_analyzer.stats import PullGroup

console = Console()


def render_pulls_table(groups: list[PullGroup]) -> None:
    t = Table(title="Pulls / Clears")
    t.add_column("Boss")
    t.add_column("Difficulty")
    t.add_column("Pulls")
    t.add_column("Cleared")
    for g in groups:
        diff = "-" if g.is_trash or g.difficulty is None else str(g.difficulty)
        cleared = "-" if g.is_trash else ("Yes" if g.cleared else "No")
        t.add_row(g.name, diff, str(g.pulls), cleared)
    console.print(t)
