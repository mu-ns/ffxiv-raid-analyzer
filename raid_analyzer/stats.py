from collections import Counter
from dataclasses import dataclass


@dataclass
class PullGroup:
    encounter_id: int
    difficulty: int | None
    name: str
    pulls: int
    cleared: bool
    fight_ids: list[int]
    is_trash: bool = False


def group_pulls(fights: list[dict]) -> list[PullGroup]:
    trash = [f for f in fights if f["encounterID"] == 0 and f.get("originalEncounterID") is None]
    real = [f for f in fights if not (f["encounterID"] == 0 and f.get("originalEncounterID") is None)]

    def effective_id(f: dict) -> int:
        return f.get("originalEncounterID") or f["encounterID"]

    diff_votes: dict[int, Counter] = {}
    for f in real:
        if f.get("difficulty") is not None:
            diff_votes.setdefault(effective_id(f), Counter())[f["difficulty"]] += 1

    def resolved_difficulty(f: dict) -> int | None:
        if f.get("difficulty") is not None:
            return f["difficulty"]
        votes = diff_votes.get(effective_id(f))
        return votes.most_common(1)[0][0] if votes else None

    groups: dict[tuple[int, int | None], list[dict]] = {}
    names: dict[tuple[int, int | None], Counter] = {}
    for f in real:
        key = (effective_id(f), resolved_difficulty(f))
        groups.setdefault(key, []).append(f)
        names.setdefault(key, Counter())[f["name"]] += 1

    result = []
    for (enc_id, diff), pulls in groups.items():
        cleared = any(p.get("kill") is True for p in pulls)
        name = names[(enc_id, diff)].most_common(1)[0][0]
        result.append(PullGroup(enc_id, diff, name, len(pulls), cleared, [p["id"] for p in pulls]))

    if trash:
        result.append(PullGroup(0, None, "Trash", len(trash), False, [f["id"] for f in trash], is_trash=True))
    return result


def count_wipes(fights: list[dict]) -> int:
    return sum(1 for f in fights if f.get("kill") is False)


def total_real_pulls(groups: list[PullGroup]) -> int:
    return sum(g.pulls for g in groups if not g.is_trash)


def per_pull_rate(counts: dict[str, int], total_pulls: int) -> dict[str, float]:
    if total_pulls == 0:
        return {name: 0.0 for name in counts}
    return {name: n / total_pulls for name, n in counts.items()}


def build_roster(actors: list[dict], excluded_names: set[str]) -> dict[str, str]:
    jobs = {a["name"]: a["subType"] for a in actors if a["name"] not in excluded_names}
    return dict(sorted(jobs.items()))


def count_deaths(deaths_table: dict) -> dict[str, int]:
    counts: Counter = Counter()
    for entry in deaths_table["data"].get("entries", []):
        counts[entry["name"]] += 1
    return dict(counts)


def deaths_minus_wipes(deaths: dict[str, int], wipe_count: int) -> dict[str, int]:
    return {name: n - wipe_count for name, n in deaths.items()}


def count_casts(cast_table: dict) -> dict[str, int]:
    return {e["name"]: e["total"] for e in cast_table["data"].get("entries", [])}


def count_debuff_applications(debuff_table: dict) -> dict[str, int]:
    return {e["name"]: e["totalUses"] for e in debuff_table["data"].get("auras", [])}
