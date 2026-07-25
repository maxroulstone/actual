import tempfile
import time
import unittest
from pathlib import Path

from utils.database import Database, TokenData


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "truelayer.db"
        self.db = Database(institution="monzo", db_path=self.path)

    def tearDown(self):
        self.directory.cleanup()

    def test_oauth_state_is_single_use_and_expires(self):
        self.db.create_oauth_state("state-one", int(time.time()) + 60)
        self.assertTrue(self.db.consume_oauth_state("state-one"))
        self.assertFalse(self.db.consume_oauth_state("state-one"))

        self.db.create_oauth_state("expired-state", int(time.time()) - 1)
        self.assertFalse(self.db.consume_oauth_state("expired-state"))

    def test_health_and_token_metadata_do_not_expose_token_values(self):
        self.db.save_token(
            TokenData(
                access_token="access-secret",
                refresh_token="refresh-secret",
                token_type="Bearer",
                scope="accounts",
                expires_at=int(time.time()) + 3600,
            )
        )
        self.db.record_import_success()
        health = self.db.get_institution_health()

        self.assertIsInstance(self.db.get_token_updated_at(), int)
        self.assertIsNotNone(health["last_success_at"])
        self.assertNotIn("access_token", health)
        self.assertNotIn("refresh_token", health)


if __name__ == "__main__":
    unittest.main()
