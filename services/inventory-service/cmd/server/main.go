// Command server runs the inventory-service gRPC server.
//
// This service is intentionally NOT exposed to the UI or gateway over REST —
// it only speaks gRPC, and only the gateway/orders-service call into it.
// This mirrors a common real-world pattern: REST at the edge, gRPC internally
// for low-latency, strongly-typed service-to-service calls.
//
// NOTE: the generated protobuf/gRPC stubs (inventory.pb.go, inventory_grpc.pb.go)
// are NOT checked into this scaffold because this environment has no protoc
// toolchain available. Generate them locally before building:
//
//	make proto   (see the repo Makefile — runs protoc against proto/inventory.proto)
package main

import (
	"context"
	"log"
	"net"
	"os"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/health"
	healthpb "google.golang.org/grpc/health/grpc_health_v1"
	"google.golang.org/grpc/reflection"
	"google.golang.org/grpc/status"

	pb "tutti-frutti/inventory-service/internal/proto"
	"tutti-frutti/inventory-service/internal/storage"
)

type inventoryServer struct {
	pb.UnimplementedInventoryServiceServer
	store *storage.Store
}

func (s *inventoryServer) GetStock(_ context.Context, req *pb.GetStockRequest) (*pb.StockInfo, error) {
	item, ok := s.store.Get(req.GetSku())
	if !ok {
		return nil, status.Errorf(codes.NotFound, "sku %q not found", req.GetSku())
	}
	return toStockInfo(item), nil
}

func (s *inventoryServer) BatchGetStock(_ context.Context, req *pb.BatchGetStockRequest) (*pb.BatchStockInfo, error) {
	items := s.store.BatchGet(req.GetSkus())
	out := &pb.BatchStockInfo{}
	for _, item := range items {
		out.Items = append(out.Items, toStockInfo(item))
	}
	return out, nil
}

func (s *inventoryServer) ReserveStock(_ context.Context, req *pb.ReserveStockRequest) (*pb.ReserveStockResponse, error) {
	remaining, ok := s.store.Reserve(req.GetSku(), req.GetQuantity())
	if !ok {
		return &pb.ReserveStockResponse{
			Success:            false,
			Message:            "insufficient stock or unknown SKU",
			RemainingQuantity:  remaining,
		}, nil
	}
	return &pb.ReserveStockResponse{
		Success:           true,
		Message:           "reserved",
		RemainingQuantity: remaining,
	}, nil
}

func (s *inventoryServer) HealthCheck(_ context.Context, _ *pb.HealthCheckRequest) (*pb.HealthCheckResponse, error) {
	return &pb.HealthCheckResponse{Status: "ok"}, nil
}

func toStockInfo(item *storage.Item) *pb.StockInfo {
	return &pb.StockInfo{
		Sku:               item.SKU,
		QuantityAvailable: item.QuantityAvailable,
		UnitPriceEur:      item.UnitPriceEUR,
		InStock:           item.QuantityAvailable > 0,
	}
}

func main() {
	port := os.Getenv("GRPC_PORT")
	if port == "" {
		port = "50051"
	}

	lis, err := net.Listen("tcp", ":"+port)
	if err != nil {
		log.Fatalf("failed to listen on port %s: %v", port, err)
	}

	grpcServer := grpc.NewServer()
	pb.RegisterInventoryServiceServer(grpcServer, &inventoryServer{store: storage.NewStore()})

	// Standard gRPC health service so CI/docker-compose healthchecks (grpc_health_probe) work.
	healthServer := health.NewServer()
	healthServer.SetServingStatus("", healthpb.HealthCheckResponse_SERVING)
	healthpb.RegisterHealthServer(grpcServer, healthServer)

	reflection.Register(grpcServer)

	log.Printf("inventory-service gRPC server listening on :%s", port)
	if err := grpcServer.Serve(lis); err != nil {
		log.Fatalf("failed to serve: %v", err)
	}
}
