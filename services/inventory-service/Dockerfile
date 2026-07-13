# NOTE: build context for this Dockerfile MUST be the repo root (not this
# service directory), because it needs access to the shared /proto folder.
# docker-compose.yml in the repo root is already configured that way:
#   build: { context: ., dockerfile: services/inventory-service/Dockerfile }

# Build stage
FROM golang:1.22-alpine AS builder

RUN apk add --no-cache protobuf protobuf-dev

WORKDIR /src

RUN go install google.golang.org/protobuf/cmd/protoc-gen-go@v1.35.2 && \
    go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@v1.5.1
ENV PATH="$PATH:/root/go/bin"

COPY services/inventory-service/go.mod services/inventory-service/go.sum* ./
RUN go mod download || true

COPY services/inventory-service/ .
COPY proto/ ./proto-src/

RUN mkdir -p internal/proto && \
    protoc --go_out=internal/proto --go_opt=paths=source_relative \
           --go-grpc_out=internal/proto --go-grpc_opt=paths=source_relative \
           -I proto-src proto-src/inventory.proto

RUN go mod tidy && go build -o /inventory-service ./cmd/server

# Runtime stage
FROM alpine:3.20
RUN apk add --no-cache ca-certificates
COPY --from=builder /inventory-service /inventory-service

EXPOSE 50051
ENTRYPOINT ["/inventory-service"]
