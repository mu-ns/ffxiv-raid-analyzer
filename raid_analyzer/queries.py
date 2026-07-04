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
        }
      }
    }
  }
}
"""
