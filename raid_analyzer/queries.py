CURRENT_USER_QUERY = """
query {
  userData {
    currentUser {
      id
      name
    }
  }
}
"""

ABILITIES_QUERY = """
query ReportAbilities($code: String!) {
  reportData {
    report(code: $code) {
      masterData {
        abilities {
          gameID
          name
        }
      }
    }
  }
}
"""

FIGHTS_AND_ACTORS_QUERY = """
query ReportFightsAndActors($code: String!) {
  reportData {
    report(code: $code) {
      title
      fights {
        id
        name
        encounterID
        originalEncounterID
        difficulty
        kill
      }
      masterData {
        actors(type: "Player") {
          id
          name
          subType
        }
      }
    }
  }
}
"""


def _alias(prefix: str, label: str) -> str:
    safe = "".join(c if c.isalnum() else "_" for c in label).lower()
    return f"{prefix}_{safe}"


def build_table_query(mitigations: dict[str, int], damage_downs: dict[str, int]):
    """Builds one GraphQL request that pulls Deaths plus one Casts alias per
    mitigation ability and one Debuffs alias per damage-down ability, all
    scoped to $fightIDs in a single round trip.

    Ability IDs are inlined as literal ints (they only ever come from our own
    hardcoded constants.py, never user input, so there's no injection risk),
    which keeps this a plain string builder rather than needing per-ability
    GraphQL variables.

    Returns (query_text, alias_map), where alias_map maps each alias back to
    ("mitigation" | "damage_down", label) so callers know what each result is.
    """
    fields = ["deaths: table(dataType: Deaths, fightIDs: $fightIDs)"]
    alias_map = {}
    for label, ability_id in mitigations.items():
        alias = _alias("mit", label)
        fields.append(f"{alias}: table(dataType: Casts, abilityID: {ability_id}, fightIDs: $fightIDs)")
        alias_map[alias] = ("mitigation", label)
    for label, ability_id in damage_downs.items():
        alias = _alias("dd", label)
        fields.append(f"{alias}: table(dataType: Debuffs, abilityID: {ability_id}, fightIDs: $fightIDs)")
        alias_map[alias] = ("damage_down", label)
    body = "\n      ".join(fields)
    query = f"""
    query ReportTables($code: String!, $fightIDs: [Int]) {{
      reportData {{
        report(code: $code) {{
          {body}
        }}
      }}
    }}
    """
    return query, alias_map
