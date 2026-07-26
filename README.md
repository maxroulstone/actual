# Actual Budget bank sync

## Bank reauthorisation admin

The admin panel is served at `admin.budget.maxroulstone.com` and uses the same
Caddy basic-auth credentials as the budget app. It reads safe connection status
from Hornbill and starts a TrueLayer browser flow; browser clients never receive
bank tokens.

Before deploying, add these values to the root `.env` file and allowlist the
callback URL in the TrueLayer Console:

```dotenv
DB_PATH=/data/truelayer.db
TRUELAYER_REDIRECT_URI=https://admin.budget.maxroulstone.com/api/truelayer/callback
ADMIN_TOKENS_URL=https://admin.budget.maxroulstone.com/budget/tokens
TRUELAYER_AUTH_BASE_URL=https://auth.truelayer.com
TRUELAYER_API_BASE_URL=https://api.truelayer.com
TRUELAYER_MONZO_PROVIDER_ID=<TrueLayer provider ID>
TRUELAYER_BARCLAYS_PROVIDER_ID=<TrueLayer provider ID>
TRUELAYER_AMEX_PROVIDER_ID=<TrueLayer provider ID>
```

The `*_PROVIDER_ID` values are TrueLayer's public identifiers for the direct
bank route. They are not your access/refresh tokens and are not secrets.

Set each provider ID from the TrueLayer Console or provider documentation. The
callback is deliberately unauthenticated so TrueLayer can redirect to it; it
accepts only a short-lived, single-use state created by an authenticated admin
request.

## Local environment

For an isolated local stack, see [local/README.md](local/README.md). From that
directory, `docker compose up -d --build` starts the admin panel at
http://localhost:8080 and Actual at http://localhost:5006 without using the
production Compose configuration or volumes.

## Deploying on a small server

Compose builds services in parallel by default, which can temporarily require
far more disk than the final runtime images. On storage-constrained hosts, clear
only disposable Docker build data and build one service at a time:

```bash
docker builder prune --all --force
COMPOSE_PARALLEL_LIMIT=1 docker compose build admin
docker builder prune --all --force
COMPOSE_PARALLEL_LIMIT=1 docker compose build zazu
docker builder prune --all --force
COMPOSE_PARALLEL_LIMIT=1 docker compose build hornbill
docker compose up -d --no-build
docker builder prune --all --force
```

These commands do not prune volumes. The `actual-data`, `hornbill-data`, and
`zazu-data` bind-mounted directories are not removed.
