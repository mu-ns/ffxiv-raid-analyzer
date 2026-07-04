from collections import Counter
from dataclasses import dataclass


@dataclass
class PullGroup:
    encounter_id: int
    difficulty: int | None
    name: str
    pulls: int
    cleared: bool
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
        result.append(PullGroup(enc_id, diff, name, len(pulls), cleared))

    if trash:
        result.append(PullGroup(0, None, "Trash", len(trash), False, is_trash=True))
    return result


def count_wipes(fights: list[dict]) -> int:
    return sum(1 for f in fights if f.get("kill") is False)


def build_roster(actors: list[dict], excluded_names: set[str]) -> dict[str, str]:
    return {str(a["id"]): a["name"] for a in actors if a["name"] not in excluded_names}
