"""One-time OAuth 2.0 authorization flow for Whoop.

Usage:
    python -m scripts.whoop_auth

Opens a browser to authorize the app, catches the callback on localhost:8080,
exchanges the auth code for tokens, and saves them to data/.whoop_tokens.json.
"""

import secrets
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

import httpx

from src.data.config import Config
from src.data.whoop_tokens import save_tokens


def main():
    state = secrets.token_urlsafe(32)
    auth_code: dict = {}

    # Build authorization URL
    params = {
        "client_id": Config.WHOOP_CLIENT_ID,
        "redirect_uri": Config.WHOOP_REDIRECT_URI,
        "response_type": "code",
        "scope": Config.WHOOP_SCOPES,
        "state": state,
    }
    auth_url = f"{Config.WHOOP_AUTH_URL}?{urlencode(params)}"

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse(self.path)

            # Only process the callback path
            if parsed.path != "/callback":
                self.send_response(204)
                self.end_headers()
                return

            qs = parse_qs(parsed.query)

            if qs.get("state", [None])[0] != state:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"State mismatch - possible CSRF. Try again.")
                return

            auth_code["code"] = qs.get("code", [None])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<h2>Authorization successful!</h2>"
                b"<p>You can close this tab and return to the terminal.</p>"
            )

        def log_message(self, format, *args):
            pass  # suppress noisy request logs

    print("Opening browser for Whoop authorization...")
    print(f"  URL: {auth_url}\n")
    webbrowser.open(auth_url)

    # Keep handling requests until we get the auth code
    HTTPServer.allow_reuse_address = True
    server = HTTPServer(("localhost", 8080), CallbackHandler)
    print("Waiting for callback on http://localhost:8080/callback ...")
    while not auth_code.get("code"):
        server.handle_request()
    server.server_close()

    if not auth_code.get("code"):
        print("ERROR: No authorization code received.")
        raise SystemExit(1)

    # Exchange code for tokens
    print("Exchanging authorization code for tokens...")
    response = httpx.post(
        Config.WHOOP_TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": auth_code["code"],
            "redirect_uri": Config.WHOOP_REDIRECT_URI,
            "client_id": Config.WHOOP_CLIENT_ID,
            "client_secret": Config.WHOOP_CLIENT_SECRET,
        },
    )

    if response.status_code != 200:
        print(f"ERROR: Token exchange failed ({response.status_code})")
        print(response.text)
        raise SystemExit(1)

    data = response.json()
    access_token = data["access_token"]
    refresh_token = data.get("refresh_token", "")
    expires_in = data.get("expires_in", 3600)
    save_tokens(access_token, refresh_token, expires_in)
    print("Tokens saved successfully! You're ready to sync Whoop data.")
    if not refresh_token:
        print(f"  Note: No refresh token provided. Token expires in {expires_in}s.")
        print("  Re-run this script when the token expires.")


if __name__ == "__main__":
    main()
