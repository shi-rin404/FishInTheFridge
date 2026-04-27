import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import requests
from ui.discord_oauth import web_reply

# ── Configure these once you create your Discord application ─────────────────
# discord.com/developers/applications → OAuth2 → add redirect: http://localhost:5757/callback
DISCORD_CLIENT_ID     = "YOUR_CLIENT_ID"
DISCORD_CLIENT_SECRET = "YOUR_CLIENT_SECRET"
REDIRECT_URI          = "http://localhost:5757/callback"
_CALLBACK_PORT        = 5757

_AUTH_URL = (
    "https://discord.com/oauth2/authorize"
    f"?client_id={DISCORD_CLIENT_ID}"
    f"&redirect_uri={REDIRECT_URI}"
    "&response_type=code"
    "&scope=identify"
)
_TOKEN_URL = "https://discord.com/api/oauth2/token"


def get_discord_token() -> str:
    """
    Opens a browser to Discord OAuth, captures the auth code via a local
    callback server on port 5757, exchanges it for an access token, and
    returns that token string.

    Blocks the calling thread until the user completes the browser flow
    (timeout: 2 minutes).  Raises RuntimeError on failure.
    """
    code_holder:  list[str | None] = [None]
    error_holder: list[str | None] = [None]
    ready = threading.Event()

    class _Handler(BaseHTTPRequestHandler):
        def log_message(self, *args): pass  # suppress server output

        def do_GET(self):
            params = parse_qs(urlparse(self.path).query)
            if "code" in params:
                code_holder[0] = params["code"][0]
                self._reply(200, web_reply.SUCCESS)
            elif "error" in params:
                error_holder[0] = params.get("error_description", ["Unknown error"])[0]
                self._reply(400, web_reply.ERROR(error_holder[0]))
            else:
                self._reply(400, web_reply.BAD_REQUEST)
            ready.set()

        def _reply(self, code: int, body_html: str):
            body = body_html.encode()
            self.send_response(code)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = HTTPServer(("localhost", _CALLBACK_PORT), _Handler)
    threading.Thread(target=server.handle_request, daemon=True).start()

    webbrowser.open(_AUTH_URL)
    ready.wait(timeout=120)
    server.server_close()

    if error_holder[0]:
        raise RuntimeError(f"Discord auth error: {error_holder[0]}")
    if not code_holder[0]:
        raise RuntimeError("Timed out waiting for Discord authorization.")

    resp = requests.post(_TOKEN_URL, data={
        "client_id":     DISCORD_CLIENT_ID,
        "client_secret": DISCORD_CLIENT_SECRET,
        "grant_type":    "authorization_code",
        "code":          code_holder[0],
        "redirect_uri":  REDIRECT_URI,
    }, headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=10)

    if not resp.ok:
        raise RuntimeError(f"Token exchange failed: {resp.text}")

    return resp.json()["access_token"]
