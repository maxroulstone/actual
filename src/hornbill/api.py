import fastapi
import requests
import os
import asyncio
from fastapi import HTTPException
from utils import TrueLayer, Database
import logging
import secrets
from datetime import datetime, timedelta
from urllib.parse import urlencode
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

# Configure root logging to emit INFO to stdout with timestamps
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    force=True,
)

app = fastapi.FastAPI()


class InstitutionConfig(BaseModel):
    slug: str
    name: str
    provider_id: str


DEFAULT_INSTITUTIONS = [
    InstitutionConfig(slug="monzo", name="Monzo", provider_id=""),
    InstitutionConfig(slug="barclays", name="Barclays", provider_id=""),
    InstitutionConfig(slug="amex", name="Amex", provider_id=""),
]


def configured_institutions() -> list[InstitutionConfig]:
    """Read direct-bank mappings only from server-side environment configuration."""
    import json

    raw = os.getenv("TRUELAYER_INSTITUTIONS_JSON")
    if raw:
        try:
            return [InstitutionConfig.model_validate(item) for item in json.loads(raw)]
        except (ValueError, TypeError) as exc:
            raise RuntimeError("TRUELAYER_INSTITUTIONS_JSON is invalid") from exc

    return [
        institution.model_copy(
            update={
                "provider_id": os.getenv(
                    f"TRUELAYER_{institution.slug.upper()}_PROVIDER_ID", ""
                )
            }
        )
        for institution in DEFAULT_INSTITUTIONS
    ]


def get_institution(slug: str) -> InstitutionConfig:
    for institution in configured_institutions():
        if institution.slug == slug:
            return institution
    raise HTTPException(status_code=404, detail="Unknown banking institution")


def admin_tokens_url(**params: str) -> str:
    base_url = os.getenv(
        "ADMIN_TOKENS_URL", "https://admin.budget.maxroulstone.com/budget/tokens"
    )
    return f"{base_url}?{urlencode(params)}"


def institution_payload(institution: InstitutionConfig) -> dict:
    db = Database(institution=institution.slug)
    health = db.get_institution_health()
    token_updated_at = db.get_token_updated_at()
    if health["last_failure_at"]:
        status = "needs_attention"
    elif token_updated_at:
        status = "healthy"
    else:
        status = "not_connected"
    return {
        "slug": institution.slug,
        "name": institution.name,
        "status": status,
        "last_token_update_at": token_updated_at,
        "last_successful_import_at": health["last_success_at"],
        "last_failure_at": health["last_failure_at"],
        "last_failure_message": health["last_failure_message"],
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/import/transactions/{institution}/{account}")
def import_transactions(institution: str, account: str, record_health: bool = True):
    client = TrueLayer(institution=institution)

    transactions = client.list_transactions(
        account,
        date_from=(datetime.now()-timedelta(days=7)).strftime("%Y-%m-%d"),
        date_to=datetime.now().strftime("%Y-%m-%d"),
    )
    logging.info(f"Fetched {len(transactions)} transactions from TrueLayer")

    actual_account_id = client.db.get_actual_account_id(account)

    body = {
        "account_id": actual_account_id,
        "transactions": transactions["results"],
    }

    zazu_url = os.getenv("ZAZU_URL", "http://localhost:3000")
    try:
        resp = requests.post(f"{zazu_url}/import", json=body)
    except requests.RequestException as e:
        # POST itself failed (connection error, timeout, etc.)
        raise HTTPException(status_code=502, detail=f"Import service error: {e}")

    if not resp.ok:
        # Import service responded but with an error status
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Import failed: {resp.text}",
        )

    # At this point, we have a successful response; return its body
    # If it's JSON, use resp.json(); if it's plain text, wrap in an object
    try:
        payload = resp.json()
    except ValueError:
        payload = {"message": resp.text}

    if record_health:
        client.db.record_import_success()
    return payload


@app.get("/list_accounts/{institution}")
def list_accounts(institution: str):
    client = TrueLayer(institution=institution)
    accounts = client._list_accounts()
    return accounts


@app.get("/list_cards/{institution}")
def list_cards(institution: str):
    client = TrueLayer(institution=institution)
    cards = client._list_cards()
    return cards


def import_all_accounts():
    """Import transactions for all known accounts (blocking)."""
    accounts = Database().get_actual_accounts()
    institutions = set()
    failed_institutions = set()
    for name, institution in accounts:
        institutions.add(institution)
        try:
            import_transactions(institution, name, record_health=False)
        except Exception as exc:
            failed_institutions.add(institution)
            Database(institution=institution).record_import_failure(str(exc))
            logging.exception(
                f"Failed importing transactions for account '{name}' ({institution})"
            )
    for institution in institutions - failed_institutions:
        Database(institution=institution).record_import_success()


@app.get("/import/transactions")
def import_transactions_root():
    import_all_accounts()
    return {"status": "imported all accounts"}


async def _run_import_all_accounts_async():
    """Run the blocking import in a thread for async scheduling."""
    await asyncio.to_thread(import_all_accounts)


async def periodic_transactions_import():
    """Background task that imports all accounts every configured interval."""
    interval = int(os.getenv("TRANSACTIONS_IMPORT_INTERVAL_SECONDS", "3600"))
    logging.info(f"Starting periodic transactions import task (interval={interval}s)")
    await asyncio.sleep(30)  # Initial delay to allow startup
    while True:
        start = datetime.now()
        try:
            await _run_import_all_accounts_async()
            logging.info(
                f"Periodic import completed in {(datetime.now() - start).total_seconds():.2f}s"
            )
        except Exception:
            logging.exception("Periodic transactions import cycle failed")
        await asyncio.sleep(interval)


@app.on_event("startup")
async def start_periodic_import_task():
    """Schedule the periodic import task once on startup.

    Avoid double-starting during dev reloads by tracking a flag on app.state.
    """
    if getattr(app.state, "import_task_started", False):
        return
    app.state.import_task_started = True
    app.state.import_task = asyncio.create_task(periodic_transactions_import())
    logging.info("Periodic transactions import task scheduled")


@app.get("/api/institutions")
def list_institutions():
    return {"institutions": [institution_payload(item) for item in configured_institutions()]}


@app.post("/api/institutions/{institution_slug}/reauthorize")
def start_reauthorisation(institution_slug: str):
    institution = get_institution(institution_slug)
    if not institution.provider_id:
        raise HTTPException(
            status_code=503,
            detail=f"No TrueLayer provider ID configured for {institution.name}",
        )
    state = secrets.token_urlsafe(32)
    Database(institution=institution.slug).create_oauth_state(
        state, int((datetime.now() + timedelta(minutes=10)).timestamp())
    )
    try:
        # Reauthorisation must remain available precisely when the existing
        # refresh token can no longer be renewed.
        url = TrueLayer(
            institution=institution.slug, ensure_tokens_ready=False
        ).authorization_url(
            state=state, provider_id=institution.provider_id
        )
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"authorization_url": url}


@app.get("/api/truelayer/callback")
def truelayer_callback(state: str | None = None, code: str | None = None, error: str | None = None):
    if not state:
        raise HTTPException(status_code=400, detail="Missing OAuth state")

    matching = None
    for institution in configured_institutions():
        db = Database(institution=institution.slug)
        if db.consume_oauth_state(state):
            matching = institution
            break
    if not matching:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

    if error or not code:
        message = error or "The bank did not return an authorisation code"
        Database(institution=matching.slug).record_import_failure(message)
        return RedirectResponse(
            admin_tokens_url(result="error", institution=matching.slug), status_code=303
        )

    try:
        TrueLayer(institution=matching.slug).exchange_authorization_code(code)
        Database(institution=matching.slug).clear_institution_failure()
    except Exception as exc:
        logging.exception("Token exchange failed for %s", matching.slug)
        Database(institution=matching.slug).record_import_failure(str(exc))
        return RedirectResponse(
            admin_tokens_url(result="error", institution=matching.slug), status_code=303
        )

    return RedirectResponse(
        admin_tokens_url(result="success", institution=matching.slug), status_code=303
    )
