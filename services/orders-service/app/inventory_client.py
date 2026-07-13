"""Thin async-friendly wrapper around the inventory-service gRPC client.

Kept deliberately small: orders-service only needs to check stock and
reserve it when an order is placed, everything else about inventory
management stays internal to the Go service.
"""

import grpc

from app.config import settings
from app.grpc_client import inventory_pb2, inventory_pb2_grpc


class InventoryClient:
    def __init__(self, target: str | None = None):
        self._target = target or settings.inventory_grpc_target
        self._channel = grpc.aio.insecure_channel(self._target)
        self._stub = inventory_pb2_grpc.InventoryServiceStub(self._channel)

    async def get_stock(self, sku: str) -> inventory_pb2.StockInfo:
        return await self._stub.GetStock(inventory_pb2.GetStockRequest(sku=sku))

    async def batch_get_stock(self, skus: list[str]) -> list[inventory_pb2.StockInfo]:
        response = await self._stub.BatchGetStock(inventory_pb2.BatchGetStockRequest(skus=skus))
        return list(response.items)

    async def reserve_stock(self, sku: str, quantity: int) -> inventory_pb2.ReserveStockResponse:
        return await self._stub.ReserveStock(
            inventory_pb2.ReserveStockRequest(sku=sku, quantity=quantity)
        )

    async def close(self) -> None:
        await self._channel.close()


inventory_client = InventoryClient()
