from dotenv import load_dotenv
import os
import time
from urllib.parse import urlencode
from typing import Optional
import requests
from pydantic import BaseModel
from .database import TokenData, Database

load_dotenv()


class TrueLayerConfig(BaseModel):
    client_id: str
    client_secret: str
    code: Optional[str] = None


class TrueLayer:
    """TrueLayer API client with persistent token storage.

    Usage patterns:
    - First run: set TRUE_LAYER_CODE with the one-time authorization code. The client will exchange it
      for access/refresh tokens and persist them. Subsequent runs do not require the code.
    - Normal runs: instantiate the client, it will load tokens and refresh if needed.
    """

    TOKEN_SKEW_SECONDS = 60

    def __init__(self, *, institution: str, ensure_tokens_ready: bool = True):
        self.config = TrueLayerConfig(
            client_id=os.getenv("TRUE_LAYER_CLIENT_ID", ""),
            client_secret=os.getenv("TRUE_LAYER_CLIENT_SECRET", ""),
            code=os.getenv("TRUE_LAYER_CODE") or None,
        )
        if not self.config.client_id or not self.config.client_secret:
            raise ValueError(
                "TRUE_LAYER_CLIENT_ID and TRUE_LAYER_CLIENT_SECRET must be set"
            )
        self.auth_base_url = os.getenv(
            "TRUELAYER_AUTH_BASE_URL", "https://auth.truelayer.com"
        ).rstrip("/")
        self.api_base_url = os.getenv(
            "TRUELAYER_API_BASE_URL", "https://api.truelayer.com"
        ).rstrip("/")

        # Use SQLite-backed store by default; support multi-account with a logical account
        self.db: Database = Database(institution=institution)

        if ensure_tokens_ready:
            self._ensure_tokens_ready()

    def _ensure_tokens_ready(self) -> None:
        tokens = self.db.get_token()
        if tokens is None:
            # First run: require an authorization code to exchange for refresh_token
            if not self.config.code:
                raise RuntimeError(
                    "No stored tokens found and TRUE_LAYER_CODE is not set. "
                    "Provide a one-time authorization code to bootstrap tokens."
                )
            exchanged = self._exchange_code_for_tokens(self.config.code)
            self.db.save_token(exchanged)
        else:
            # Refresh if expiring soon or expired
            now = int(time.time())
            if tokens.expires_at <= now + self.TOKEN_SKEW_SECONDS:
                refreshed = self._refresh_tokens(tokens.refresh_token)
                self.db.save_token(refreshed)

    def _exchange_code_for_tokens(self, code: str, redirect_uri: str | None = None) -> TokenData:
        url = f"{self.auth_base_url}/connect/token"
        headers = {"content-type": "application/x-www-form-urlencoded"}
        payload = {
            "grant_type": "authorization_code",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "code": code,
            "redirect_uri": redirect_uri or os.getenv(
                "TRUELAYER_REDIRECT_URI", "https://console.truelayer.com/redirect-page"
            ),
        }
        response = requests.post(url, headers=headers, data=payload)
        data = response.json()
        if response.status_code != 200:
            raise RuntimeError(
                f"Failed to exchange code: {response.status_code} {data}"
            )
        expires_at = int(time.time()) + data["expires_in"]
        return TokenData(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            token_type=data["token_type"],
            scope=data["scope"],
            expires_at=expires_at,
        )

    def exchange_authorization_code(self, code: str) -> TokenData:
        """Exchange a browser callback code and persist the replacement token set."""
        token_data = self._exchange_code_for_tokens(
            code, redirect_uri=os.environ["TRUELAYER_REDIRECT_URI"]
        )
        self.db.save_token(token_data)
        return token_data

    def authorization_url(self, *, state: str, provider_id: str) -> str:
        redirect_uri = os.getenv("TRUELAYER_REDIRECT_URI")
        if not redirect_uri:
            raise RuntimeError("TRUELAYER_REDIRECT_URI must be set for bank reauthorisation")
        query = urlencode(
            {
                "response_type": "code",
                "client_id": self.config.client_id,
                "redirect_uri": redirect_uri,
                "scope": os.getenv(
                    "TRUELAYER_AUTH_SCOPE",
                    "info accounts balance transactions cards offline_access",
                ),
                "state": state,
                "providers": provider_id,
            }
        )
        return f"{self.auth_base_url}/?{query}"

    def _refresh_tokens(self, refresh_token: str) -> TokenData:
        url = f"{self.auth_base_url}/connect/token"
        headers = {"content-type": "application/x-www-form-urlencoded"}
        payload = {
            "grant_type": "refresh_token",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "refresh_token": refresh_token,
        }
        response = requests.post(url, headers=headers, data=payload)
        data = response.json()
        if response.status_code != 200:
            raise RuntimeError(
                f"Failed to refresh token: {response.status_code} {data}"
            )
        expires_at = int(time.time()) + data["expires_in"]
        return TokenData(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            token_type=data["token_type"],
            scope=self.db.get_token().scope,
            expires_at=expires_at,
        )

    def _list_cards(self):
        url = f"{self.api_base_url}/data/v1/cards"
        headers = {
            "Authorization": f"Bearer {self.db.get_token().access_token}",
            "Content-Type": "application/json",
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise RuntimeError(
                f"Failed to list cards: {response.status_code} {response.json()}"
            )
        return response.json()

    def _list_accounts(self):
        url = f"{self.api_base_url}/data/v1/accounts"
        headers = {
            "Authorization": f"Bearer {self.db.get_token().access_token}",
            "Content-Type": "application/json",
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise RuntimeError(
                f"Failed to list accounts: {response.status_code} {response.json()}"
            )
        return response.json()

    def _list_card_transactions(
        self, account_name: str, date_from: str = None, date_to: str = None
    ):
        card_id = self.db.get_account_id(account_name)

        url = f"{self.api_base_url}/data/v1/cards/{card_id}/transactions"
        headers = {
            "Authorization": f"Bearer {self.db.get_token().access_token}",
        }
        params = {
            "from": date_from,
            "to": date_to,
        }
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            raise RuntimeError(
                f"Failed to list card transactions: {response.status_code} {response.json()}"
            )
        return response.json()

    def _list_account_transactions(
        self,
        account_name: str,
        date_from: str | None = None,
        date_to: str | None = None,
    ):
        account_id = self.db.get_account_id(account_name)

        url = f"{self.api_base_url}/data/v1/accounts/{account_id}/transactions"
        headers = {
            "Authorization": f"Bearer {self.db.get_token().access_token}",
        }
        params = {
            "from": date_from,
            "to": date_to,
        }
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            raise RuntimeError(
                f"Failed to list account transactions: {response.status_code} {response.json()}"
            )
        return response.json()

    def list_transactions(
        self,
        account_name: str,
        date_from: str | None = None,
        date_to: str | None = None,
    ):
        # Determine if account_name is a card or bank account
        is_credit_card = self.db.is_credit_card(account_name)
        if is_credit_card:
            return self._list_card_transactions(account_name, date_from, date_to)
        else:
            return self._list_account_transactions(account_name, date_from, date_to)


if __name__ == "__main__":
    client = TrueLayer(institution="barclays")
    transactions = client._list_cards()
    print(transactions)
