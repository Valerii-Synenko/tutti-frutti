from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class GetStockRequest(_message.Message):
    __slots__ = ("sku",)
    SKU_FIELD_NUMBER: _ClassVar[int]
    sku: str
    def __init__(self, sku: _Optional[str] = ...) -> None: ...

class BatchGetStockRequest(_message.Message):
    __slots__ = ("skus",)
    SKUS_FIELD_NUMBER: _ClassVar[int]
    skus: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, skus: _Optional[_Iterable[str]] = ...) -> None: ...

class StockInfo(_message.Message):
    __slots__ = ("sku", "quantity_available", "unit_price_eur", "in_stock")
    SKU_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_AVAILABLE_FIELD_NUMBER: _ClassVar[int]
    UNIT_PRICE_EUR_FIELD_NUMBER: _ClassVar[int]
    IN_STOCK_FIELD_NUMBER: _ClassVar[int]
    sku: str
    quantity_available: int
    unit_price_eur: float
    in_stock: bool
    def __init__(self, sku: _Optional[str] = ..., quantity_available: _Optional[int] = ..., unit_price_eur: _Optional[float] = ..., in_stock: bool = ...) -> None: ...

class BatchStockInfo(_message.Message):
    __slots__ = ("items",)
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedCompositeFieldContainer[StockInfo]
    def __init__(self, items: _Optional[_Iterable[_Union[StockInfo, _Mapping]]] = ...) -> None: ...

class ReserveStockRequest(_message.Message):
    __slots__ = ("sku", "quantity")
    SKU_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    sku: str
    quantity: int
    def __init__(self, sku: _Optional[str] = ..., quantity: _Optional[int] = ...) -> None: ...

class ReserveStockResponse(_message.Message):
    __slots__ = ("success", "message", "remaining_quantity")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    REMAINING_QUANTITY_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    remaining_quantity: int
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., remaining_quantity: _Optional[int] = ...) -> None: ...

class HealthCheckRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HealthCheckResponse(_message.Message):
    __slots__ = ("status",)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: str
    def __init__(self, status: _Optional[str] = ...) -> None: ...
