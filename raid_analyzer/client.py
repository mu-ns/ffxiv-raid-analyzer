import json
import urllib.error
import urllib.request

from raid_analyzer import queries

GRAPHQL_URL = "https://www.fflogs.com/api/v2/user"


class GraphQLError(Exception):
    pass


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
            message = "; ".join(e.get("message", "") for e in body["errors"])
            raise GraphQLError(f"FFLogs API error: {message}")
        return body["data"]

    def get_current_user(self) -> dict:
        data = self.execute(queries.CURRENT_USER_QUERY, {})
        return data["userData"]["currentUser"]
