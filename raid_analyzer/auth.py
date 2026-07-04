import base64
import http.server
import json
import os
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser

from raid_analyzer import config

AUTHORIZE_URL = "https://www.fflogs.com/oauth/authorize"
TOKEN_URL = "https://www.fflogs.com/oauth/token"
REDIRECT_URI = "http://localhost:8765/callback"
CALLBACK_PORT = 8765


class NotLoggedInError(Exception):
    pass


class OAuthError(Exception):
    pass


def _get_client_credentials() -> tuple[str, str]:
    client_id = os.environ.get("FFLOGS_CLIENT_ID")
    client_secret = os.environ.get("FFLOGS_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise OAuthError(
            "FFLOGS_CLIENT_ID / FFLOGS_CLIENT_SECRET not set. Copy .env.example to "
            ".env and fill in your FFLogs API client credentials."
        )
    return client_id, client_secret


def _wait_for_callback(expected_state: str) -> str:
    result = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path != "/callback":
                self.send_response(404)
                self.end_headers()
                return
            qs = urllib.parse.parse_qs(parsed.query)
            if qs.get("state", [None])[0] != expected_state:
                result["error"] = "state mismatch"
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"State mismatch, aborting.")
                return
            result["code"] = qs.get("code", [None])[0]
            result["error"] = qs.get("error", [None])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body>Login complete, you can close this tab.</body></html>")

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("localhost", CALLBACK_PORT), Handler)
    server.handle_request()
    server.server_close()
    if result.get("error"):
        raise OAuthError(f"FFLogs login was denied or failed: {result['error']}")
    if not result.get("code"):
        raise OAuthError("Did not receive an authorization code from FFLogs.")
    return result["code"]


def _exchange_code_for_token(code: str) -> dict:
    client_id, client_secret = _get_client_credentials()
    body = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }).encode()
    auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    req = urllib.request.Request(TOKEN_URL, data=body, method="POST", headers={
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded",
    })
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def _refresh(refresh_token: str) -> dict:
    client_id, client_secret = _get_client_credentials()
    body = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }).encode()
    auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    req = urllib.request.Request(TOKEN_URL, data=body, method="POST", headers={
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded",
    })
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def _save_token(token: dict) -> None:
    expires_at = time.time() + token.get("expires_in", 0)
    config.write_json(config.CREDENTIALS_FILE, {
        "access_token": token["access_token"],
        "refresh_token": token.get("refresh_token"),
        "expires_at": expires_at,
    })


def login() -> None:
    client_id, _ = _get_client_credentials()
    state = secrets.token_urlsafe(16)
    params = urllib.parse.urlencode({
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "state": state,
    })
    webbrowser.open(f"{AUTHORIZE_URL}?{params}")
    code = _wait_for_callback(state)
    token = _exchange_code_for_token(code)
    _save_token(token)


def get_valid_access_token() -> str:
    creds = config.read_json(config.CREDENTIALS_FILE)
    if not creds.get("access_token"):
        raise NotLoggedInError("Not logged in. Run: raid-analyzer login")
    if creds.get("expires_at", 0) - 60 > time.time():
        return creds["access_token"]
    if creds.get("refresh_token"):
        try:
            new_token = _refresh(creds["refresh_token"])
            _save_token(new_token)
            return new_token["access_token"]
        except urllib.error.HTTPError:
            pass
    raise NotLoggedInError("Login expired. Run: raid-analyzer login")
