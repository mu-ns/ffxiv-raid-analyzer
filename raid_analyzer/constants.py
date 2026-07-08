# Hardcoded FFLogs ability IDs for raid-tracking stats, maintained by hand.
# See "Finding ability IDs" in the README for how to fill these in.

# label -> FFLogs ability ID. One cast-count column per entry.
MITIGATION_ABILITIES: dict[str, int] = {
    "Feint": 7549,
    "Addle": 7560,
    "Reprisal": 7535,
    "Shield Samba": 16012,
}

# label -> FFLogs ability ID. One debuff-application-count column per entry.
DAMAGE_DOWN_ABILITIES: dict[str, int] = {
    "Damage Down": 1002911,
}

# masterData.actors(type: "Player") mixes in non-player pseudo-entries;
# filter these out by name when building the player roster.
EXCLUDED_ACTOR_NAMES = {"Multiple Players", "Limit Break"}

# table(dataType: Deaths) silently truncates at 200 entries per request no matter
# how many fightIDs are passed. Fetch in chunks this small to stay well under that.
DEATHS_QUERY_CHUNK_SIZE = 10
