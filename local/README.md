# Local environment

From this directory, run:

```bash
docker compose up -d --build
```

Open the admin panel at http://localhost:8080/budget/tokens. Actual is available
directly at http://localhost:5006. The local stack stores all data below
`local/data/`, never in the production Compose volumes.

The initial UI/API smoke test needs no secrets: Hornbill creates an empty local
SQLite database and reports the three supported institutions as unconnected.

To test imports or bank reauthorisation, copy `.env.example` to `.env` and add
test credentials. For a real TrueLayer journey, localhost cannot receive the
provider redirect. Run an HTTPS tunnel to port 8080, set both callback-related
URLs to that public address, and allowlist its `/api/truelayer/callback` URL in
your TrueLayer test application. Use a sandbox/test app and a separate Actual
budget, never production credentials or a production budget.

Stop and delete local state with:

```bash
docker compose down --volumes
rm -rf data
```
