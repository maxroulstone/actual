import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import api
from utils.database import Database


class FakeTrueLayer:
    exchanged_codes = []
    exchange_error = None

    def __init__(self, *, institution, ensure_tokens_ready=True):
        self.institution = institution

    def authorization_url(self, *, state, provider_id):
        return f"https://bank.example/authorise?state={state}&provider={provider_id}"

    def exchange_authorization_code(self, code):
        if self.exchange_error:
            raise self.exchange_error
        self.exchanged_codes.append(code)


class ReauthorisationApiTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "truelayer.db"
        self.institution = api.InstitutionConfig(
            slug="monzo", name="Monzo", provider_id="uk-ob-monzo"
        )
        FakeTrueLayer.exchanged_codes = []
        FakeTrueLayer.exchange_error = None

    def tearDown(self):
        self.directory.cleanup()

    def database(self, institution=None, db_path=None):
        return Database(institution=institution, db_path=self.path)

    def test_start_and_complete_reauthorisation(self):
        with (
            patch.object(api, "configured_institutions", return_value=[self.institution]),
            patch.object(api, "Database", side_effect=self.database),
            patch.object(api, "TrueLayer", FakeTrueLayer),
            patch.object(api, "admin_tokens_url", return_value="https://admin.example/tokens?result=success"),
        ):
            started = api.start_reauthorisation("monzo")
            state = started["authorization_url"].split("state=")[1].split("&")[0]
            self.database("monzo").record_import_failure("expired consent")
            response = api.truelayer_callback(state=state, code="one-time-code")

        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.headers["location"], "https://admin.example/tokens?result=success")
        self.assertEqual(FakeTrueLayer.exchanged_codes, ["one-time-code"])
        self.assertIsNone(self.database("monzo").get_institution_health()["last_failure_at"])

    def test_callback_rejects_missing_or_reused_state(self):
        with (
            patch.object(api, "configured_institutions", return_value=[self.institution]),
            patch.object(api, "Database", side_effect=self.database),
            patch.object(api, "TrueLayer", FakeTrueLayer),
        ):
            with self.assertRaises(Exception):
                api.truelayer_callback(code="one-time-code")
            with self.assertRaises(Exception):
                api.truelayer_callback(state="unknown", code="one-time-code")

    def test_institution_payload_never_contains_tokens(self):
        with patch.object(api, "Database", side_effect=self.database):
            payload = api.institution_payload(self.institution)

        self.assertNotIn("access_token", payload)
        self.assertNotIn("refresh_token", payload)

    def test_callback_records_provider_and_token_exchange_failures(self):
        def callback_url(**params):
            return f"https://admin.example/tokens?result={params['result']}"

        with (
            patch.object(api, "configured_institutions", return_value=[self.institution]),
            patch.object(api, "Database", side_effect=self.database),
            patch.object(api, "TrueLayer", FakeTrueLayer),
            patch.object(api, "admin_tokens_url", side_effect=callback_url),
        ):
            db = self.database("monzo")
            db.create_oauth_state("provider-error", 2_000_000_000)
            provider_response = api.truelayer_callback(
                state="provider-error", error="access_denied"
            )
            self.assertEqual(provider_response.headers["location"], "https://admin.example/tokens?result=error")
            self.assertEqual(db.get_institution_health()["last_failure_message"], "access_denied")

            db.create_oauth_state("exchange-error", 2_000_000_000)
            FakeTrueLayer.exchange_error = RuntimeError("token exchange failed")
            exchange_response = api.truelayer_callback(
                state="exchange-error", code="one-time-code"
            )

        self.assertEqual(exchange_response.headers["location"], "https://admin.example/tokens?result=error")
        self.assertEqual(db.get_institution_health()["last_failure_message"], "token exchange failed")


if __name__ == "__main__":
    unittest.main()
