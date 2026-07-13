import grpc

from app.config import settings
from app.grpc_client import inventory_pb2, inventory_pb2_grpc


class InventoryClient:
    def __init__(self, target: str | None = None):
        self._target = target or settings.inventory_grpc_target
        self._channel = grpc.aio.insecure_channel(self._target)
        self._stub = inventory_pb2_grpc.InventoryServiceStub(self._channel)

    async def batch_get_stock(self, skus: list[str]) -> list[inventory_pb2.StockInfo]:
        response = await self._stub.BatchGetStock(inventory_pb2.BatchGetStockRequest(skus=skus))
        return list(response.items)

    async def close(self) -> None:
        await self._channel.close()


inventory_client = InventoryClient()
