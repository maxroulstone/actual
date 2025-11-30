import os
import sqlite3
import stat
import time
from abc import ABC
from pathlib import Path
from typing import Optional

from pydantic import BaseModel


class TokenData(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    scope: str
    # Unix epoch seconds when access_token expires
    expires_at: int


class Database(ABC):
    """SQLite-backed TokenStore supporting multiple accounts via a fixed account.

    This store keeps tokens in a single table keyed by (provider, account).
    You pass the logical account (e.g., account_id) in the constructor so the
    TokenStore interface remains load()/save() without parameters.

    Notes:
    - Suitable for single-host deployments or low write concurrency.
    - For multi-instance deployments, use a shared DB or secrets manager.
    - The database file is created with 600 permissions when first created.
    """

    def __init__(self, institution: str = None, db_path: Optional[Path] = None):
        if db_path:
            self.db_path = Path(db_path)
        elif os.getenv("DB_PATH"):
            self.db_path = Path(os.getenv("DB_PATH"))
        else:
            self.db_path = Path(__file__).resolve().parent / "truelayer.db"

        self.institution = institution
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        # Improve concurrency characteristics a bit
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self) -> None:
        first_create = not self.db_path.exists()
        conn = self._connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tokens (
                    provider TEXT NOT NULL,
                    institution TEXT NOT NULL,
                    access_token TEXT NOT NULL,
                    refresh_token TEXT NOT NULL,
                    token_type TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    expires_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL,
                    PRIMARY KEY (provider, institution)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT CHECK(type IN ('credit', 'debit')) NOT NULL,
                    institution TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
                    truelayer_account_id TEXT,
                    actual_account_id TEXT
                )
                """
            )
            conn.commit()
        finally:
            conn.close()
        if first_create:
            try:
                os.chmod(self.db_path, stat.S_IRUSR | stat.S_IWUSR)
            except Exception:
                pass

    def get_token(self) -> Optional[TokenData]:
        conn = self._connect()
        try:
            cur = conn.execute(
                "SELECT access_token, refresh_token, token_type, scope, expires_at FROM tokens WHERE institution = ?",
                (self.institution,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return TokenData(
                access_token=row["access_token"],
                refresh_token=row["refresh_token"],
                token_type=row["token_type"],
                scope=row["scope"],
                expires_at=int(row["expires_at"]),
            )
        finally:
            conn.close()

    def save_token(self, token_data: TokenData) -> None:
        now = int(time.time())
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO tokens (provider, institution, access_token, refresh_token, token_type, scope, expires_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(provider, institution) DO UPDATE SET
                    access_token=excluded.access_token,
                    refresh_token=excluded.refresh_token,
                    token_type=excluded.token_type,
                    scope=excluded.scope,
                    expires_at=excluded.expires_at,
                    updated_at=excluded.updated_at
                """,
                (
                    "truelayer",
                    self.institution,
                    token_data.access_token,
                    token_data.refresh_token,
                    token_data.token_type,
                    token_data.scope,
                    int(token_data.expires_at),
                    now,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def get_account_id(self, account_name: str) -> str:
        conn = self._connect()
        try:
            cur = conn.execute(
                "SELECT truelayer_account_id FROM accounts WHERE name = ? AND institution = ?",
                (account_name, self.institution),
            )
            row = cur.fetchone()
            if not row:
                raise RuntimeError(
                    f"No account found with name {account_name} for institution {self.institution}"
                )
            return row["truelayer_account_id"]
        finally:
            conn.close()

    def is_credit_card(self, account_name: str) -> bool:
        conn = self._connect()
        try:
            cur = conn.execute(
                "SELECT type FROM accounts WHERE name = ? AND institution = ?",
                (account_name, self.institution),
            )
            row = cur.fetchone()
            if not row:
                raise RuntimeError(
                    f"No account found with name {account_name} for institution {self.institution}"
                )
            return row["type"] == "credit"
        finally:
            conn.close()

    def get_actual_account_id(self, account_name: str) -> Optional[str]:
        conn = self._connect()
        try:
            cur = conn.execute(
                "SELECT actual_account_id FROM accounts WHERE name = ? AND institution = ?",
                (account_name, self.institution),
            )
            row = cur.fetchone()
            if not row:
                return None
            return row["actual_account_id"]
        finally:
            conn.close()

    def get_actual_accounts(self) -> list[tuple[str, str]]:
        conn = self._connect()
        try:
            cur = conn.execute(
                "SELECT name, institution FROM accounts WHERE actual_account_id IS NOT NULL"
            )
            rows = cur.fetchall()
            return [(row["name"], row["institution"]) for row in rows]
        finally:
            conn.close()
