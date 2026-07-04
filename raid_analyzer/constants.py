# Hardcoded FFLogs ability IDs for raid-tracking stats.
#
# masterData.abilities has no concept of "this is a mitigation" or "this is
# the damage-down debuff" - it's just a name/icon lookup, and names can be
# localized while IDs are not. So these are maintained by hand.
#
# How to find an ability's ID:
#   1. Open a report containing a cast/debuff application of that ability.
#   2. Query that report's masterData.abilities, e.g.:
#        query { reportData { report(code: "<code>") {
#          masterData { abilities { gameID name } }
#        } } }
#      and find the row with the matching name. Note some abilities show up
#      twice: a lower "cast" ID (the ability itself) and a 100xxxx-prefixed
#      "debuff" ID (the effect it applies) - use the cast ID for
#      MITIGATION_ABILITIES (dataType: Casts) and the relevant debuff's own ID
#      for DAMAGE_DOWN_ABILITIES (dataType: Debuffs).

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
