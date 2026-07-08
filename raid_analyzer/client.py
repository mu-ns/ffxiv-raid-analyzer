import json
import urllib.error
import urllib.request

from raid_analyzer import constants, queries

GRAPHQL_URL = "https://www.fflogs.com/api/v2/user"


class GraphQLError(Exception):
    pass


class ReportNotFoundError(Exception):
    pass


class NoFightsError(Exception):
    pass


class ArchivedReportError(Exception):
    pass


def _report_not_found(code: str | None) -> ReportNotFoundError:
    return ReportNotFoundError(
        f"Report '{code}' could not be loaded. Check the code/URL is "
        "correct, and if it's a private report, confirm your FFLogs "
        "account has access to it."
    )


def _raise_for_errors(errors: list[dict], code: str | None = None) -> None:
    message = "; ".join(e.get("message", "") for e in errors)
    lower = message.lower()
    if "archived" in lower:
        raise ArchivedReportError(
            "This report is archived and requires an active FFLogs subscription "
            "to pull fight data from. Analyze the report before it archives, or "
            "log in with a subscribed account."
        )
    if "does not exist" in lower:
        raise _report_not_found(code)
    raise GraphQLError(f"FFLogs API error: {message}")


class GraphQLClient:
    def __init__(self, access_token: str):
        self.access_token = access_token

    def execute(self, query: str, variables: dict) -> dict:
        payload = json.dumps({"query": query, "variables": variables}).encode()
        req = urllib.request.Request(GRAPHQL_URL, data=payload, method="POST", headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}",
        })
        try:
            with urllib.request.urlopen(req) as resp:
                body = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            raise GraphQLError(f"FFLogs API request failed (HTTP {e.code}).") from e
        if body.get("errors"):
            _raise_for_errors(body["errors"], variables.get("code"))
        return body["data"]

    def get_current_user(self) -> dict:
        data = self.execute(queries.CURRENT_USER_QUERY, {})
        return data["userData"]["currentUser"]

    def get_fights_and_actors(self, code: str) -> dict:
        data = self.execute(queries.FIGHTS_AND_ACTORS_QUERY, {"code": code})
        report = data["reportData"]["report"]
        if report is None:
            raise _report_not_found(code)
        if not report.get("fights"):
            raise NoFightsError(f"Report '{code}' has no fights recorded.")
        return report

    def get_tables(self, code: str, fight_ids: list[int], mitigations: dict[str, int], damage_downs: dict[str, int]):
        query, alias_map = queries.build_table_query(mitigations, damage_downs)
        data = self.execute(query, {"code": code, "fightIDs": fight_ids})
        tables = data["reportData"]["report"]
        tables["deaths"] = self._get_deaths_table(code, fight_ids)
        return tables, alias_map

    def _get_deaths_table(self, code: str, fight_ids: list[int]) -> dict:
        entries = []
        chunk_size = constants.DEATHS_QUERY_CHUNK_SIZE
        for i in range(0, len(fight_ids), chunk_size):
            chunk = fight_ids[i:i + chunk_size]
            data = self.execute(queries.DEATHS_QUERY, {"code": code, "fightIDs": chunk})
            entries += data["reportData"]["report"]["table"]["data"]["entries"]
        return {"data": {"entries": entries}}

    def get_abilities(self, code: str) -> list[dict]:
        data = self.execute(queries.ABILITIES_QUERY, {"code": code})
        report = data["reportData"]["report"]
        if report is None:
            raise _report_not_found(code)
        return report["masterData"]["abilities"]
