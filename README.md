# pay-over-time

A pay-over-time checkout for UK and Canadian customers. The customer sees every plan the market allows, picks one, and gets a schedule that adds up to the cent. Repayments can be retried safely, from flaky mobile connections or from a payments processor that delivers twice.

![Checkout flow: UK offers, switching plans, Canada, confirmation](docs/checkout.gif)

## What's in here

| Path | What it does |
| --- | --- |
| `backend/` | **Python** / **FastAPI** service on **MySQL**: quotes, plans and repayments |
| `frontend/` | **React** + **TypeScript** checkout widget built with Vite |
| `k8s/` | **Kubernetes** manifests: deployments, services, probes, resource limits and an HPA |
| `docker-compose.yml` | The whole stack locally, with MySQL |

## How the money works

- **Schedules are exact.** Interest-free plans split the basket evenly and put the leftover cents on the first payment. Interest-bearing plans use the standard annuity formula and round each payment to the cent. The final payment absorbs the rounding, so the principal is always repaid exactly. A property-style test checks this across markets, terms and amounts.
- **Market rules are data.** Each market defines its currency, locale, basket limits and the APR for every term. Adding a market means adding one entry, with no new code paths. The rates in this repo are illustrative.
- **Due dates respect month ends.** A plan started on 31 January is due on 28 February, then 31 March.
- **Repayments are idempotent and serialised.** Each payment carries an `Idempotency-Key`.
  - The plan row is locked with `SELECT … FOR UPDATE` while a payment is applied, so concurrent retries can't record the same payment twice. A unique `(plan_id, idempotency_key)` constraint backs this up.
  - Reusing a key with a different amount is rejected.
  - An integration test fires eight concurrent retries at MySQL and expects one payment.
  - It also fires six concurrent distinct payments at a plan that can only take three, and expects three to succeed.
- **Payments go to the oldest balance first**, partial payments included. Overpaying is rejected, and the plan closes when the balance hits zero.

## Tech stack

- Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0, MySQL 8 (PyMySQL)
- React 19, TypeScript, Vite, Testing Library, Playwright
- Docker, Docker Compose, Kubernetes (kustomize, HPA), nginx
- pytest, vitest, ruff, mypy (strict), tsc (strict), kubeconform, GitHub Actions

## Running it

### Docker Compose

```bash
docker compose up --build
open http://localhost:8080
```

### Locally

```bash
cd backend
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
uvicorn paylater.main:create_app --factory --port 8000    # SQLite by default
```

```bash
cd frontend
npm ci
npm run dev                                               # http://localhost:5173
```

Set `PAYLATER_DATABASE_URL=mysql+pymysql://user:pass@host/db` to run the backend against MySQL. API docs are at <http://localhost:8000/docs>.

### Kubernetes

```bash
kubectl create namespace pay-over-time
kubectl -n pay-over-time create secret generic paylater-database --from-literal=url='mysql+pymysql://…'
kubectl apply -k k8s/
```

## API

| Method | Path | |
| --- | --- | --- |
| `POST` | `/v1/quotes` | All offers for a market and basket amount |
| `POST` | `/v1/plans` | Create a plan from a market, amount and term |
| `GET` | `/v1/plans/{plan_id}` | Plan with installments and outstanding balance |
| `POST` | `/v1/plans/{plan_id}/payments` | Apply a repayment; requires `Idempotency-Key`. Returns `201`, or `200` when replayed |

Errors use one shape: `{"error": {"code": "amount_out_of_range", "message": "GB accepts 30.00-5000.00 GBP"}}`.

## Tests

```bash
cd backend && ruff check . && mypy && pytest
PAYLATER_TEST_MYSQL_URL=mysql+pymysql://paylater:paylater@127.0.0.1/paylater pytest tests/integration
cd frontend && npm run typecheck && npm test
cd frontend && npm run e2e        # boots the API and the built app, runs desktop and mobile journeys
```

## License

MIT
