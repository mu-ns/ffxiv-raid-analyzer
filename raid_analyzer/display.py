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


def render_deaths_table(
    roster: dict[str, str],
    deaths: dict[str, int],
    deaths_minus_wipes: dict[str, int],
    deaths_minus_wipes_rate: dict[str, float],
    damage_downs: dict[str, dict[str, int]],
    damage_down_rates: dict[str, dict[str, float]],
) -> None:
    t = Table(title="Deaths / Damage Down")
    t.add_column("Player")
    t.add_column("Job")
    t.add_column("Deaths")
    t.add_column("Avg/Pull")
    t.add_column("Incl. wipes")
    for label in damage_downs:
        t.add_column(label)
        t.add_column(f"{label} Avg/Pull")
    for player, job in roster.items():
        row = [
            player,
            job,
            str(deaths_minus_wipes.get(player, 0)),
            f"{deaths_minus_wipes_rate.get(player, 0.0):.2f}",
            str(deaths.get(player, 0)),
        ]
        for label in damage_downs:
            row.append(str(damage_downs[label].get(player, 0)))
            row.append(f"{damage_down_rates[label].get(player, 0.0):.2f}")
        t.add_row(*row)
    console.print(t)


def render_mitigation_table(
    mitigations: dict[str, dict[str, int]],
    mitigation_rates: dict[str, dict[str, float]],
) -> None:
    t = Table(title="Mitigations")
    t.add_column("Player")
    t.add_column("Casts")
    t.add_column("Avg/Pull")
    labels = list(mitigations.keys())
    for i, label in enumerate(labels):
        counts = mitigations[label]
        t.add_row(f"[bold]{label}[/bold]", "", "")
        sorted_players = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
        for j, (player, count) in enumerate(sorted_players):
            is_last_row = j == len(sorted_players) - 1
            t.add_row(
                player,
                str(count),
                f"{mitigation_rates[label].get(player, 0.0):.2f}",
                end_section=is_last_row and i < len(labels) - 1,
            )
    console.print(t)
