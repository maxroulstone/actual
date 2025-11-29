import fastapi
import requests
import os
import asyncio
from fastapi import HTTPException
from utils import TrueLayer, Database
import logging
from datetime import datetime

app = fastapi.FastAPI()


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/import/transactions/{institution}/{account}")
def import_transactions(institution: str, account: str):
    client = TrueLayer(institution=institution)

    transactions = client.list_transactions(
        account,
        date_from="2025-11-01",
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
    for name, institution in accounts:
        try:
            import_transactions(institution, name)
        except Exception:
            logging.exception(
                f"Failed importing transactions for account '{name}' ({institution})"
            )


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
