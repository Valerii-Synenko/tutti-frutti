# 🍊 Tutti Frutti

A lightweight, modern microservices demo — a [Sock Shop](https://github.com/microservices-demo/microservices-demo)
alternative that sells fruit instead of socks. Built as a "guinea pig" project
for practising backend/API and UI (Playwright) test automation.

## Architecture

| Service | Stack | Role |
|---|---|---|
| [`users-service`](services/users-service) | FastAPI + PostgreSQL | Registration, login, JWT issuance (access + refresh) |
| [`catalogue-service`](services/catalogue-service) | FastAPI + MongoDB | Fruit catalogue — flexible schema for varied per-fruit attributes |
| [`inventory-service`](services/inventory-service) | Go + gRPC | Stock and pricing; **internal service**, never called directly from the UI |
| [`orders-service`](services/orders-service) | FastAPI + PostgreSQL | Cart/orders; calls inventory-service over gRPC |
| [`fruit-assistant-service`](services/fruit-assistant-service) | FastAPI + Anthropic API | AI chat assistant with on-topic guardrails |
| [`gateway`](services/gateway) | FastAPI (BFF) | Single entry point for the UI, aggregates REST + gRPC |
| [`ui`](ui) | React + TypeScript + Vite | Playwright-friendly (all interactive elements have `data-testid`) |
| [`docs`](docs) | Zudoku | Aggregated API documentation from all services |

```
Browser (UI) ──► gateway ──┬──► users-service ────► Postgres
                            ├──► catalogue-service ─► MongoDB
                            ├──► orders-service ─┬──► Postgres
                            │                     └──► inventory-service (gRPC) 
                            └──► fruit-assistant-service ──► Anthropic API
```

## Quick start

```bash
cp .env.example .env          # fill in JWT_SECRET_KEY and, optionally, ANTHROPIC_API_KEY
make up                       # docker compose up -d --build
make seed                     # populates catalogue-service with demo fruit data
```

- UI: http://localhost:4173
- Gateway (BFF): http://localhost:8080 (Swagger: `/docs`, ReDoc: `/redoc`)
- Each service also exposes its own `/docs`/`/redoc` on its own port
  (users: 8001, catalogue: 8002, orders: 8003, assistant: 8004)

Stop: `make down`. Full reset (including data volumes): `make reset`.

## ⚠️ inventory-service (Go) requires an extra step

`protoc`-generated Go files (`*.pb.go`) are **not committed** to the repo —
the environment this scaffold was created in had no Go toolchain available.
When building via `docker compose build` / `make up` they are generated
automatically inside the Docker image — no manual steps needed.

If you want to work with the service locally (IDE, `go run`), see
[services/inventory-service/README.md](services/inventory-service/README.md).

## Testing

- **API automation**: every service exposes its own OpenAPI contract
  (`/openapi.json`); the gateway aggregates them. The intended "guinea pig"
  test repo for this project is a separate `python-backend-tests` repository —
  this project keeps all endpoints clean and predictable for exactly that purpose.
- **UI automation (Playwright)**: basic e2e tests live in
  [`ui/e2e`](ui/e2e). Run with:
  ```bash
  make test-e2e
  ```
- **gRPC contract**: `inventory-service` enables reflection, so it can be
  explored and tested via `grpcurl` without a local copy of the `.proto`
  file — examples in the service README.
- **AI response testing**: `fruit-assistant-service` is a dedicated service
  for this: guardrail tests (does the bot stay on-topic?), prompt injection
  tests, response regression tests, and chat widget stability tests
  (`data-testid="chat-*"` in [ChatWidget.tsx](ui/src/components/ChatWidget.tsx)).
  Without `ANTHROPIC_API_KEY` the service returns a canonical fallback response —
  the stack and tests work end-to-end even without a real key.

## CI (GitHub Actions)

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs on every push/PR to
`main`:
1. Lints/type-checks Python services (ruff, mypy) and the UI (tsc, eslint).
2. Brings up the full stack via `docker compose up`.
3. Seeds the catalogue and waits for the gateway to become healthy.
4. Runs Playwright e2e tests against the live UI.
5. Publishes the Playwright HTML report as a build artifact, then tears the stack down.

If you add an `ANTHROPIC_API_KEY` secret in GitHub repo settings, chat tests
will run against real Claude; without it they run against the fallback response.

## API documentation (Zudoku)

```bash
make up      # stack must be running
make docs    # collects OpenAPI specs from all services and starts the Zudoku dev server
```

Each service also ships built-in Swagger UI (`/docs`) and ReDoc (`/redoc`) —
no extra steps needed.

## Repository structure

```
services/
  users-service/          # FastAPI + Postgres, JWT auth
  catalogue-service/       # FastAPI + MongoDB
  inventory-service/       # Go + gRPC (internal only)
  orders-service/          # FastAPI + Postgres, gRPC client
  fruit-assistant-service/ # FastAPI + Anthropic API
  gateway/                 # FastAPI BFF
ui/                        # React + TypeScript + Vite
proto/                     # shared .proto contract (inventory)
docs/                      # Zudoku config
scripts/                   # dev helper scripts
.github/workflows/         # CI
```

## UI design

The visual identity is a "fruit market stall" aesthetic: soft crate-green
background, citrus/watermelon/laurel-green accents, Fraunces + Public Sans
typography, and a signature detail — a slightly rotated price-tag "sticker"
on each fruit card (instead of the usual AI-default cream-terracotta or
black-neon palettes).
