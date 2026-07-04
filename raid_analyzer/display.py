import pyperclip
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
        if g.is_trash:
            cleared = "[dim]-[/dim]"
        elif g.cleared:
            cleared = "[green]Yes[/green]"
        else:
            cleared = "[red]No[/red]"
        t.add_row(g.name, str(g.pulls), cleared)
    console.print(t)


def render_deaths_table(
    scope_label: str,
    roster: dict[str, str],
    deaths: dict[str, int],
    deaths_minus_wipes: dict[str, int],
    deaths_minus_wipes_rate: dict[str, float],
    damage_downs: dict[str, dict[str, int]],
    damage_down_rates: dict[str, dict[str, float]],
) -> None:
    t = Table(title=f"Deaths / Damage Down ({scope_label})")
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
    scope_label: str,
    mitigations: dict[str, dict[str, int]],
    mitigation_rates: dict[str, dict[str, float]],
) -> None:
    t = Table(title=f"Mitigations ({scope_label})")
    t.add_column("Player")
    t.add_column("Casts")
    t.add_column("Avg/Pull")
    labels = list(mitigations.keys())
    for i, label in enumerate(labels):
        is_last_label = i == len(labels) - 1
        sorted_players = sorted(mitigations[label].items(), key=lambda kv: kv[1], reverse=True)
        t.add_row(f"[bold]{label}[/bold]", "", "", end_section=not sorted_players and not is_last_label)
        for j, (player, count) in enumerate(sorted_players):
            is_last_row = j == len(sorted_players) - 1
            t.add_row(
                player,
                str(count),
                f"{mitigation_rates[label].get(player, 0.0):.2f}",
                end_section=is_last_row and not is_last_label,
            )
    console.print(t)


def copy_tsv(
    scope_label: str,
    groups: list[PullGroup],
    roster: dict[str, str],
    deaths: dict[str, int],
    deaths_minus_wipes: dict[str, int],
    deaths_minus_wipes_rate: dict[str, float],
    damage_downs: dict[str, dict[str, int]],
    damage_down_rates: dict[str, dict[str, float]],
    mitigations: dict[str, dict[str, int]],
    mitigation_rates: dict[str, dict[str, float]],
) -> None:
    lines = [f"Encounter: {scope_label}", "", "Boss\tPulls\tCleared"]
    for g in groups:
        cleared = "-" if g.is_trash else ("Yes" if g.cleared else "No")
        lines.append(f"{g.name}\t{g.pulls}\t{cleared}")

    lines.append("")
    header = ["Player", "Job", "Deaths", "Avg/Pull", "Incl. wipes"]
    for label in damage_downs:
        header += [label, f"{label} Avg/Pull"]
    lines.append("\t".join(header))
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
        lines.append("\t".join(row))

    for label, counts in mitigations.items():
        lines.append("")
        lines.append(label)
        lines.append("Player\tCasts\tAvg/Pull")
        for player, count in sorted(counts.items(), key=lambda kv: kv[1], reverse=True):
            lines.append(f"{player}\t{count}\t{mitigation_rates[label].get(player, 0.0):.2f}")

    pyperclip.copy("\n".join(lines))
    console.print("[green]Copied TSV to clipboard.[/green]")
