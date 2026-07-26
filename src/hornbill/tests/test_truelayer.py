import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from utils.database import Database
from utils.truelayer import TrueLayer


class TrueLayerTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "truelayer.db"
        self.environment = {
            "DB_PATH": str(self.path),
            "TRUE_LAYER_CLIENT_ID": "sandbox-client",
            "TRUE_LAYER_CLIENT_SECRET": "sandbox-secret",
            "TRUELAYER_REDIRECT_URI": "https://tunnel.example/api/truelayer/callback",
            "TRUELAYER_AUTH_BASE_URL": "https://auth.truelayer-sandbox.com",
            "TRUELAYER_API_BASE_URL": "https://api.truelayer-sandbox.com",
        }

    def tearDown(self):
        self.directory.cleanup()

    def test_disconnected_client_exchanges_callback_code_and_stores_tokens(self):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "access_token": "access-secret",
            "refresh_token": "refresh-secret",
            "token_type": "Bearer",
            "scope": "accounts offline_access",
            "expires_in": 3600,
        }

        with (
            patch.dict(os.environ, self.environment, clear=True),
            patch("utils.truelayer.requests.post", return_value=response) as post,
        ):
            client = TrueLayer(institution="monzo", ensure_tokens_ready=False)
            token = client.exchange_authorization_code("one-time-code")

        request_url = post.call_args.args[0]
        request_payload = post.call_args.kwargs["data"]
        stored = Database(institution="monzo", db_path=self.path).get_token()

        self.assertEqual(
            request_url, "https://auth.truelayer-sandbox.com/connect/token"
        )
        self.assertEqual(request_payload["code"], "one-time-code")
        self.assertEqual(
            request_payload["redirect_uri"],
            "https://tunnel.example/api/truelayer/callback",
        )
        self.assertEqual(token.access_token, "access-secret")
        self.assertEqual(stored.refresh_token, "refresh-secret")
        self.assertGreater(stored.expires_at, int(time.time()))


if __name__ == "__main__":
    unittest.main()
