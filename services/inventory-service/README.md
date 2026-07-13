# inventory-service

Go + gRPC service. Internal-only — it is never exposed to the UI or gateway
over REST, only over gRPC, on purpose (a common real-world pattern: REST at
the edge, gRPC between internal services for low-latency, strongly-typed
calls).

## Why this exists in the project

Everything else in Tutti Frutti is Python. This service exists specifically
to demonstrate Go + gRPC contract testing skills: schema/contract validation,
health-check probing (`grpc_health_v1`), and reflection-based test tooling
(e.g. `grpcurl`) alongside the Python-based REST test suite.

## Generating the protobuf/gRPC stubs

This scaffold does **not** check in the generated `*.pb.go` files, because
generating them requires a local `protoc` toolchain that wasn't available in
the environment this project was scaffolded in. You need to generate them
once before the service will build.

### Option A — inside Docker (simplest)

Nothing to do — `docker compose build inventory-service` (or `make up`)
generates the stubs automatically as part of the multi-stage Docker build.

### Option B — locally, for IDE support / `go run`

1. Install `protoc` (the Protocol Buffers compiler):
   - macOS: `brew install protobuf`
   - Ubuntu/Debian: `apt install -y protobuf-compiler`
   - Or download from https://github.com/protocolbuffers/protobuf/releases

2. Install the Go plugins:
   ```bash
   go install google.golang.org/protobuf/cmd/protoc-gen-go@v1.35.2
   go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@v1.5.1
   ```
   Make sure `$(go env GOPATH)/bin` is on your `PATH`.

3. From the repo root, run:
   ```bash
   make proto
   ```
   This generates `internal/proto/inventory.pb.go` and
   `internal/proto/inventory_grpc.pb.go`.

4. Then:
   ```bash
   cd services/inventory-service
   go mod tidy
   go run ./cmd/server
   ```

## Testing the gRPC contract manually

With `grpcurl` (`brew install grpcurl` / see grpcurl releases):

```bash
grpcurl -plaintext localhost:50051 list
grpcurl -plaintext -d '{"sku": "alphonso-mango"}' localhost:50051 inventory.InventoryService/GetStock
grpcurl -plaintext localhost:50051 grpc.health.v1.Health/Check
```

Reflection is enabled, so `list` and `describe` work without needing the
`.proto` file on the client side — useful for exploratory testing.
