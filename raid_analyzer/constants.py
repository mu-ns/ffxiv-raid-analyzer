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
#          masterData { abilities { id name } }
#        } } }
#      and find the row with the matching name.
#
# TODO(user): fill in real ability IDs before mitigation/damage-down columns
# will show up in `analyze` output. Empty for now - those columns are simply
# skipped until filled in.

# label -> FFLogs ability ID. One cast-count column per entry.
MITIGATION_ABILITIES: dict[str, int] = {}

# label -> FFLogs ability ID. One debuff-application-count column per entry.
DAMAGE_DOWN_ABILITIES: dict[str, int] = {}

# masterData.actors(type: "Player") mixes in non-player pseudo-entries;
# filter these out by name when building the player roster.
EXCLUDED_ACTOR_NAMES = {"Multiple Players", "Limit Break"}
