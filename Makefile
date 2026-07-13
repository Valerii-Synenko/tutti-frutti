.PHONY: up down build seed proto logs test-e2e docs

## Start the full stack (builds images on first run)
up:
	docker compose up -d --build

## Stop and remove containers (keeps volumes)
down:
	docker compose down

## Stop and remove containers + volumes (full reset)
reset:
	docker compose down -v

## Rebuild all images without starting
build:
	docker compose build

## Seed the catalogue with demo fruit data (run after `make up`)
seed:
	docker compose exec catalogue-service python -m app.seed

## Follow logs for all services
logs:
	docker compose logs -f

## Regenerate Go protobuf/gRPC stubs for inventory-service (requires local protoc)
## Install protoc + plugins first, see services/inventory-service/README.md
proto:
	protoc --go_out=services/inventory-service/internal/proto --go_opt=paths=source_relative \
	       --go-grpc_out=services/inventory-service/internal/proto --go-grpc_opt=paths=source_relative \
	       -I proto proto/inventory.proto

## Run the UI's Playwright e2e suite against a running stack
test-e2e:
	cd ui && npm install && npx playwright install --with-deps chromium && npx playwright test

## Collect OpenAPI specs from running services and start the Zudoku docs preview
docs:
	python3 scripts/collect_openapi.py
	cd docs && npm install && npm run dev
